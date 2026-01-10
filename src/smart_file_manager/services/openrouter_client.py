"""OpenRouter API client for vision model integration.

TAG-003 to TAG-008: SPEC-API-001
This module provides an async client for the OpenRouter API with:
- Bearer token authentication
- Configurable timeouts
- Fallback chain support
- Exponential backoff retry with jitter
- Response caching with content hash keys
"""

import asyncio
import hashlib
import json
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from smart_file_manager.infrastructure.cache.base import CacheInterface

from smart_file_manager.core.exceptions import (
    APIConnectionError,
    APIResponseError,
    APITimeoutError,
    ModelUnavailableError,
    RateLimitError,
)
from smart_file_manager.services.model_config import ModelConfig


@dataclass
class ChatCompletionResponse:
    """Response from a chat completion request.

    Attributes:
        content: The generated text content.
        prompt_tokens: Number of tokens in the prompt.
        completion_tokens: Number of tokens in the completion.
        model_used: The model ID that was actually used.
    """

    content: str
    prompt_tokens: int
    completion_tokens: int
    model_used: str

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens used."""
        return self.prompt_tokens + self.completion_tokens


# Status codes that should trigger a retry
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class OpenRouterClient:
    """Async client for OpenRouter API.

    This client provides:
    - Bearer token authentication
    - Configurable connection, read, and total timeouts
    - Automatic retry with exponential backoff and jitter
    - Fallback chain support for graceful degradation
    - Response caching with content hash keys

    Attributes:
        api_key: The OpenRouter API key.
        base_url: The API base URL.
        connect_timeout: Connection timeout in seconds.
        read_timeout: Read timeout in seconds.
        total_timeout: Total request timeout in seconds.
        model_config: Configuration for model tiers and fallback.
        max_retries: Maximum number of retry attempts.
        cache: Optional cache interface for response caching.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        connect_timeout: float = 5.0,
        read_timeout: float = 30.0,
        total_timeout: float = 60.0,
        model_config: ModelConfig | None = None,
        max_retries: int = 3,
        cache: "CacheInterface | None" = None,
    ) -> None:
        """Initialize the OpenRouter client.

        Args:
            api_key: The OpenRouter API key for authentication.
            base_url: The API base URL. Defaults to OpenRouter's API.
            connect_timeout: Connection timeout in seconds. Defaults to 5.0.
            read_timeout: Read timeout in seconds. Defaults to 30.0.
            total_timeout: Total request timeout in seconds. Defaults to 60.0.
            model_config: Model configuration. Defaults to a new ModelConfig.
            max_retries: Maximum retry attempts. Defaults to 3.
            cache: Optional cache interface for response caching.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.total_timeout = total_timeout
        self.model_config = model_config or ModelConfig()
        self.max_retries = max_retries
        self.cache = cache

        # Initialize HTTP client with timeout configuration
        timeout = httpx.Timeout(
            connect=connect_timeout,
            read=read_timeout,
            write=read_timeout,
            pool=total_timeout,
        )
        self._http_client = httpx.AsyncClient(timeout=timeout)

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers for API requests.

        Returns:
            Dictionary of HTTP headers.
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _calculate_backoff(self, attempt: int, retry_after: int | None = None) -> float:
        """Calculate backoff delay with exponential backoff and jitter.

        Args:
            attempt: The current retry attempt (0-indexed).
            retry_after: Optional Retry-After header value in seconds.

        Returns:
            Delay in seconds before the next retry.
        """
        if retry_after is not None:
            return float(retry_after)

        # Exponential backoff: 1s, 2s, 4s, ...
        base_delay: float = float(2**attempt)
        # Add jitter: 0-500ms (using random for non-cryptographic timing jitter)
        jitter: float = random.uniform(0, 0.5)  # noqa: S311
        return base_delay + jitter

    def _is_retryable(self, status_code: int) -> bool:
        """Check if a status code should trigger a retry.

        Args:
            status_code: The HTTP status code.

        Returns:
            True if the request should be retried.
        """
        return status_code in RETRYABLE_STATUS_CODES

    def _generate_cache_key(self, messages: list[dict[str, Any]], model: str) -> str:
        """Generate a cache key from messages and model.

        Uses SHA-256 hash of the serialized messages and model ID
        to create a deterministic cache key.

        Args:
            messages: List of message dictionaries.
            model: The model ID.

        Returns:
            A cache key string.
        """
        # Create a canonical representation of the request
        cache_data = {
            "messages": messages,
            "model": model,
        }
        # Serialize with sorted keys for deterministic output
        serialized = json.dumps(cache_data, sort_keys=True, separators=(",", ":"))
        # Generate SHA-256 hash
        hash_digest = hashlib.sha256(serialized.encode()).hexdigest()
        return f"openrouter:chat:{hash_digest}"

    async def _make_request(
        self,
        messages: list[dict[str, Any]],
        model: str,
    ) -> httpx.Response:
        """Make a single API request.

        Args:
            messages: List of message dictionaries.
            model: The model ID to use.

        Returns:
            The HTTP response.

        Raises:
            APIConnectionError: If connection fails.
            APITimeoutError: If request times out.
        """
        url = f"{self.base_url}/chat/completions"
        headers = self._build_headers()
        payload = {
            "model": model,
            "messages": messages,
        }

        try:
            response = await self._http_client.post(url, headers=headers, json=payload)
            return response
        except httpx.ConnectError as e:
            raise APIConnectionError(f"Failed to connect to API: {e}") from e
        except httpx.TimeoutException as e:
            raise APITimeoutError(f"API request timed out: {e}") from e

    def _parse_response(
        self,
        response: httpx.Response,
        model: str,
    ) -> ChatCompletionResponse:
        """Parse a successful API response.

        Args:
            response: The HTTP response.
            model: The model ID that was used.

        Returns:
            Parsed ChatCompletionResponse.
        """
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        return ChatCompletionResponse(
            content=content,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            model_used=model,
        )

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses by raising appropriate exceptions.

        Args:
            response: The HTTP response.

        Raises:
            RateLimitError: For 429 responses.
            APIResponseError: For other error responses.
        """
        status_code = response.status_code

        if status_code == 429:
            retry_after_str = response.headers.get("Retry-After")
            retry_after = int(retry_after_str) if retry_after_str else None
            raise RateLimitError(
                f"Rate limit exceeded: {response.text}",
                retry_after=retry_after,
            )

        raise APIResponseError(
            f"API error: {response.text}",
            status_code=status_code,
        )

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
    ) -> ChatCompletionResponse:
        """Send a chat completion request with retry and cache support.

        This method automatically:
        - Checks cache for existing response (if cache configured)
        - Retries on retryable errors (429, 5xx) with exponential backoff
        - Stores successful responses in cache (if cache configured)

        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            model: Optional model override. Uses primary tier model if not specified.

        Returns:
            ChatCompletionResponse with the generated content.

        Raises:
            APIConnectionError: If connection fails.
            APITimeoutError: If request times out.
            RateLimitError: If rate limit exceeded and retries exhausted.
            APIResponseError: For other API errors.
        """
        model_to_use = model or self.model_config.primary_tier.model_id

        # Check cache first (if configured)
        if self.cache is not None:
            cache_key = self._generate_cache_key(messages, model_to_use)
            cached_data: dict[str, Any] | None = await self.cache.get(cache_key)
            if cached_data is not None:
                return ChatCompletionResponse(
                    content=cached_data["content"],
                    prompt_tokens=cached_data["prompt_tokens"],
                    completion_tokens=cached_data["completion_tokens"],
                    model_used=cached_data["model_used"],
                )

        last_exception: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = await self._make_request(messages, model_to_use)

                if response.status_code == 200:
                    result = self._parse_response(response, model_to_use)

                    # Store in cache (if configured)
                    if self.cache is not None:
                        cache_key = self._generate_cache_key(messages, model_to_use)
                        await self.cache.set(
                            cache_key,
                            {
                                "content": result.content,
                                "prompt_tokens": result.prompt_tokens,
                                "completion_tokens": result.completion_tokens,
                                "model_used": result.model_used,
                            },
                        )

                    return result

                if self._is_retryable(response.status_code) and attempt < self.max_retries:
                    # Get retry-after if available (for 429)
                    retry_after_str = response.headers.get("Retry-After")
                    retry_after = int(retry_after_str) if retry_after_str else None

                    delay = self._calculate_backoff(attempt, retry_after)
                    await asyncio.sleep(delay)
                    continue

                # Non-retryable error or retries exhausted
                self._handle_error_response(response)

            except (APIConnectionError, APITimeoutError):
                # Don't retry connection/timeout errors
                raise
            except RateLimitError:
                # Re-raise rate limit errors
                raise
            except APIResponseError as e:
                last_exception = e
                if attempt >= self.max_retries:
                    raise

        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
        raise APIResponseError("Unexpected error during chat completion")

    async def chat_completion_with_fallback(
        self,
        messages: list[dict[str, Any]],
    ) -> ChatCompletionResponse:
        """Send a chat completion request with fallback chain support.

        This method tries each model in the fallback chain until one succeeds.
        If all models fail, raises ModelUnavailableError.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.

        Returns:
            ChatCompletionResponse with the generated content.

        Raises:
            ModelUnavailableError: If all models in the fallback chain fail.
            APIConnectionError: If connection fails.
            APITimeoutError: If request times out.
        """
        fallback_chain = self.model_config.get_fallback_chain()

        for tier in fallback_chain:
            try:
                # Try with single attempt per tier (no retry within fallback)
                response = await self._make_request(messages, tier.model_id)

                if response.status_code == 200:
                    return self._parse_response(response, tier.model_id)

                # Model unavailable (503) or other error, try next tier
                if response.status_code in {503, 502, 500}:
                    continue

                # For other errors, handle normally
                self._handle_error_response(response)

            except (APIConnectionError, APITimeoutError):
                # These are infrastructure errors, not model errors
                raise
            except APIResponseError:
                # API error from this tier, try next tier
                continue

        # All fallbacks exhausted
        raise ModelUnavailableError(
            "All models in fallback chain are unavailable",
            model_id=fallback_chain[-1].model_id if fallback_chain else None,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http_client.aclose()

    async def __aenter__(self) -> "OpenRouterClient":
        """Enter async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit async context manager."""
        await self.close()
