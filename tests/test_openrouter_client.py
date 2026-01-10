"""Tests for OpenRouter client module.

TAG-003 to TAG-005: SPEC-API-001
RED Phase: These tests define the expected behavior for OpenRouter client.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# =============================================================================
# TAG-003: OpenRouter Client Basic Tests
# =============================================================================


class TestOpenRouterClientInit:
    """Test cases for OpenRouterClient initialization."""

    def test_client_can_be_instantiated(self) -> None:
        """OpenRouterClient should be instantiable with API key."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")
        assert client is not None

    def test_client_stores_api_key(self) -> None:
        """OpenRouterClient should store the API key."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")
        assert client.api_key == "test-api-key"

    def test_client_has_default_base_url(self) -> None:
        """OpenRouterClient should have default OpenRouter base URL."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")
        assert client.base_url == "https://openrouter.ai/api/v1"

    def test_client_accepts_custom_base_url(self) -> None:
        """OpenRouterClient should accept custom base URL."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(
            api_key="test-api-key",
            base_url="https://custom.api.com",
        )
        assert client.base_url == "https://custom.api.com"

    def test_client_has_default_timeouts(self) -> None:
        """OpenRouterClient should have default timeout settings."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")
        assert client.connect_timeout == 5.0
        assert client.read_timeout == 30.0
        assert client.total_timeout == 60.0

    def test_client_accepts_custom_timeouts(self) -> None:
        """OpenRouterClient should accept custom timeout settings."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(
            api_key="test-api-key",
            connect_timeout=10.0,
            read_timeout=60.0,
            total_timeout=120.0,
        )
        assert client.connect_timeout == 10.0
        assert client.read_timeout == 60.0
        assert client.total_timeout == 120.0

    def test_client_accepts_model_config(self) -> None:
        """OpenRouterClient should accept ModelConfig."""
        from smart_file_manager.services.model_config import PREMIUM_TIER, ModelConfig
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        model_config = ModelConfig(primary_tier=PREMIUM_TIER)
        client = OpenRouterClient(api_key="test-api-key", model_config=model_config)
        assert client.model_config == model_config

    def test_client_creates_default_model_config(self) -> None:
        """OpenRouterClient should create default ModelConfig if not provided."""
        from smart_file_manager.services.model_config import ModelConfig
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")
        assert isinstance(client.model_config, ModelConfig)


class TestOpenRouterClientHeaders:
    """Test cases for OpenRouterClient HTTP headers."""

    def test_client_builds_auth_header(self) -> None:
        """OpenRouterClient should build Authorization header with Bearer token."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")
        headers = client._build_headers()
        assert headers["Authorization"] == "Bearer test-api-key"

    def test_client_builds_content_type_header(self) -> None:
        """OpenRouterClient should build Content-Type header."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")
        headers = client._build_headers()
        assert headers["Content-Type"] == "application/json"


class TestOpenRouterClientChatCompletion:
    """Test cases for OpenRouterClient chat completion."""

    @pytest.mark.asyncio
    async def test_chat_completion_makes_post_request(self) -> None:
        """chat_completion should make POST request to /chat/completions."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        with patch.object(client, "_http_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)

            await client.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
            )

            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "/chat/completions" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_chat_completion_returns_response_content(self) -> None:
        """chat_completion should return the response content."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        with patch.object(client, "_http_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)

            result = await client.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
            )

            assert result.content == "Test response"
            assert result.prompt_tokens == 10
            assert result.completion_tokens == 5

    @pytest.mark.asyncio
    async def test_chat_completion_uses_primary_model_by_default(self) -> None:
        """chat_completion should use primary model from ModelConfig."""
        from smart_file_manager.services.model_config import BALANCED_TIER
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        with patch.object(client, "_http_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)

            await client.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
            )

            call_args = mock_client.post.call_args
            request_body = call_args[1]["json"]
            assert request_body["model"] == BALANCED_TIER.model_id

    @pytest.mark.asyncio
    async def test_chat_completion_accepts_custom_model(self) -> None:
        """chat_completion should accept custom model override."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        with patch.object(client, "_http_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)

            await client.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                model="custom/model",
            )

            call_args = mock_client.post.call_args
            request_body = call_args[1]["json"]
            assert request_body["model"] == "custom/model"


class TestOpenRouterClientErrorHandling:
    """Test cases for OpenRouterClient error handling."""

    @pytest.mark.asyncio
    async def test_raises_api_connection_error_on_connection_failure(self) -> None:
        """chat_completion should raise APIConnectionError on connection failure."""
        import httpx

        from smart_file_manager.core.exceptions import APIConnectionError
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")

        with patch.object(client, "_http_client") as mock_client:
            mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

            with pytest.raises(APIConnectionError):
                await client.chat_completion(
                    messages=[{"role": "user", "content": "Hello"}],
                )

    @pytest.mark.asyncio
    async def test_raises_api_timeout_error_on_timeout(self) -> None:
        """chat_completion should raise APITimeoutError on timeout."""
        import httpx

        from smart_file_manager.core.exceptions import APITimeoutError
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")

        with patch.object(client, "_http_client") as mock_client:
            mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

            with pytest.raises(APITimeoutError):
                await client.chat_completion(
                    messages=[{"role": "user", "content": "Hello"}],
                )

    @pytest.mark.asyncio
    async def test_raises_api_response_error_on_4xx(self) -> None:
        """chat_completion should raise APIResponseError on 4xx responses."""
        from smart_file_manager.core.exceptions import APIResponseError
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        with patch.object(client, "_http_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)

            with pytest.raises(APIResponseError) as exc_info:
                await client.chat_completion(
                    messages=[{"role": "user", "content": "Hello"}],
                )
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_rate_limit_error_on_429(self) -> None:
        """chat_completion should raise RateLimitError on 429 response."""
        from smart_file_manager.core.exceptions import RateLimitError
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.text = "Too Many Requests"

        with patch.object(client, "_http_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)

            with pytest.raises(RateLimitError) as exc_info:
                await client.chat_completion(
                    messages=[{"role": "user", "content": "Hello"}],
                )
            assert exc_info.value.retry_after == 60


# =============================================================================
# TAG-004: Fallback Chain Tests
# =============================================================================


class TestOpenRouterClientFallback:
    """Test cases for OpenRouterClient fallback chain."""

    @pytest.mark.asyncio
    async def test_fallback_to_next_tier_on_model_unavailable(self) -> None:
        """chat_completion should fallback to next tier when model unavailable."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")

        # First call fails with model unavailable, second succeeds
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 503
        mock_response_fail.text = "Model unavailable"

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Fallback response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        with patch.object(client, "_http_client") as mock_client:
            mock_client.post = AsyncMock(side_effect=[mock_response_fail, mock_response_success])

            result = await client.chat_completion_with_fallback(
                messages=[{"role": "user", "content": "Hello"}],
            )

            assert result.content == "Fallback response"
            # Verify two calls were made
            assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_fallback_chain_exhausted_raises_error(self) -> None:
        """chat_completion should raise error when all fallbacks exhausted."""
        from smart_file_manager.core.exceptions import ModelUnavailableError
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")

        # All calls fail
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 503
        mock_response_fail.text = "Model unavailable"

        with patch.object(client, "_http_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response_fail)

            with pytest.raises(ModelUnavailableError):
                await client.chat_completion_with_fallback(
                    messages=[{"role": "user", "content": "Hello"}],
                )

    @pytest.mark.asyncio
    async def test_fallback_records_used_model(self) -> None:
        """chat_completion result should include which model was actually used."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")

        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 503
        mock_response_fail.text = "Model unavailable"

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        with patch.object(client, "_http_client") as mock_client:
            mock_client.post = AsyncMock(side_effect=[mock_response_fail, mock_response_success])

            result = await client.chat_completion_with_fallback(
                messages=[{"role": "user", "content": "Hello"}],
            )

            # Result should indicate which model was used
            assert result.model_used is not None


# =============================================================================
# TAG-005: Exponential Backoff Retry Tests
# =============================================================================


class TestOpenRouterClientRetry:
    """Test cases for OpenRouterClient retry with exponential backoff."""

    @pytest.mark.asyncio
    async def test_retries_on_5xx_errors(self) -> None:
        """chat_completion should retry on 5xx server errors."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")

        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500
        mock_response_fail.text = "Internal Server Error"

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Success after retry"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        with patch.object(client, "_http_client") as mock_client:
            mock_client.post = AsyncMock(side_effect=[mock_response_fail, mock_response_success])

            result = await client.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
            )

            assert result.content == "Success after retry"
            assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_max_retries_exceeded_raises_error(self) -> None:
        """chat_completion should raise error after max retries exceeded."""
        from smart_file_manager.core.exceptions import APIResponseError
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key", max_retries=3)

        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500
        mock_response_fail.text = "Internal Server Error"

        with patch.object(client, "_http_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response_fail)

            with pytest.raises(APIResponseError):
                await client.chat_completion(
                    messages=[{"role": "user", "content": "Hello"}],
                )

            # Should have tried max_retries + 1 times (initial + retries)
            assert mock_client.post.call_count == 4

    @pytest.mark.asyncio
    async def test_respects_retry_after_header(self) -> None:
        """chat_completion should respect Retry-After header on 429."""

        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")

        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "1"}
        mock_response_429.text = "Too Many Requests"

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Success"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        with patch.object(client, "_http_client") as mock_client:
            mock_client.post = AsyncMock(side_effect=[mock_response_429, mock_response_success])
            with patch(
                "smart_file_manager.services.openrouter_client.asyncio.sleep",
                new_callable=AsyncMock,
            ) as mock_sleep:
                await client.chat_completion(
                    messages=[{"role": "user", "content": "Hello"}],
                )

                # Should have slept for at least 1 second (Retry-After value)
                mock_sleep.assert_called()

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self) -> None:
        """Retry delays should follow exponential backoff pattern."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key", max_retries=3)

        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 502
        mock_response_fail.headers = {}  # No Retry-After header
        mock_response_fail.text = "Bad Gateway"

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Success"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        sleep_times: list[float] = []

        async def track_sleep(seconds: float) -> None:
            sleep_times.append(seconds)

        with patch.object(client, "_http_client") as mock_client:
            mock_client.post = AsyncMock(
                side_effect=[
                    mock_response_fail,
                    mock_response_fail,
                    mock_response_success,
                ]
            )
            with patch(
                "smart_file_manager.services.openrouter_client.asyncio.sleep",
                side_effect=track_sleep,
            ):
                await client.chat_completion(
                    messages=[{"role": "user", "content": "Hello"}],
                )

                # Backoff should be approximately 1s, 2s (with jitter 0-0.5s)
                assert len(sleep_times) == 2
                # First delay: 2^0 = 1s + jitter (0-0.5s) = 1.0-1.5s
                assert 1.0 <= sleep_times[0] <= 1.5
                # Second delay: 2^1 = 2s + jitter (0-0.5s) = 2.0-2.5s
                assert 2.0 <= sleep_times[1] <= 2.5

    @pytest.mark.asyncio
    async def test_retryable_status_codes(self) -> None:
        """Should retry on specific status codes: 429, 500, 502, 503, 504."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")

        retryable_codes = [429, 500, 502, 503, 504]

        for status_code in retryable_codes:
            mock_response_fail = MagicMock()
            mock_response_fail.status_code = status_code
            mock_response_fail.headers = {}
            mock_response_fail.text = f"Error {status_code}"

            mock_response_success = MagicMock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {
                "choices": [{"message": {"content": "Success"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            }

            with patch.object(client, "_http_client") as mock_client:
                mock_client.post = AsyncMock(
                    side_effect=[mock_response_fail, mock_response_success]
                )
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    result = await client.chat_completion(
                        messages=[{"role": "user", "content": "Hello"}],
                    )
                    assert result.content == "Success"
                    assert mock_client.post.call_count == 2


class TestChatCompletionResponse:
    """Test cases for ChatCompletionResponse dataclass."""

    def test_chat_completion_response_has_required_fields(self) -> None:
        """ChatCompletionResponse should have all required fields."""
        from smart_file_manager.services.openrouter_client import ChatCompletionResponse

        response = ChatCompletionResponse(
            content="Test content",
            prompt_tokens=10,
            completion_tokens=5,
            model_used="test/model",
        )
        assert response.content == "Test content"
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 5
        assert response.model_used == "test/model"

    def test_chat_completion_response_total_tokens(self) -> None:
        """ChatCompletionResponse should calculate total tokens."""
        from smart_file_manager.services.openrouter_client import ChatCompletionResponse

        response = ChatCompletionResponse(
            content="Test content",
            prompt_tokens=10,
            completion_tokens=5,
            model_used="test/model",
        )
        assert response.total_tokens == 15


# =============================================================================
# TAG-008: Cache Integration Tests
# =============================================================================


class TestOpenRouterClientCacheInit:
    """Test cases for OpenRouterClient cache initialization."""

    def test_client_accepts_cache_interface(self) -> None:
        """OpenRouterClient should accept a cache interface."""
        from smart_file_manager.infrastructure.cache.base import CacheInterface
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        mock_cache = MagicMock(spec=CacheInterface)
        client = OpenRouterClient(api_key="test-api-key", cache=mock_cache)
        assert client.cache == mock_cache

    def test_client_works_without_cache(self) -> None:
        """OpenRouterClient should work without a cache."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")
        assert client.cache is None


class TestOpenRouterClientCacheKey:
    """Test cases for cache key generation."""

    def test_generate_cache_key_from_messages(self) -> None:
        """OpenRouterClient should generate cache key from messages and model."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")
        messages = [{"role": "user", "content": "Hello"}]
        model = "test/model"

        key = client._generate_cache_key(messages, model)

        assert isinstance(key, str)
        assert len(key) > 0

    def test_cache_key_is_deterministic(self) -> None:
        """Same messages and model should produce same cache key."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")
        messages = [{"role": "user", "content": "Hello"}]
        model = "test/model"

        key1 = client._generate_cache_key(messages, model)
        key2 = client._generate_cache_key(messages, model)

        assert key1 == key2

    def test_different_messages_produce_different_keys(self) -> None:
        """Different messages should produce different cache keys."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")
        messages1 = [{"role": "user", "content": "Hello"}]
        messages2 = [{"role": "user", "content": "World"}]
        model = "test/model"

        key1 = client._generate_cache_key(messages1, model)
        key2 = client._generate_cache_key(messages2, model)

        assert key1 != key2

    def test_different_models_produce_different_keys(self) -> None:
        """Different models should produce different cache keys."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key="test-api-key")
        messages = [{"role": "user", "content": "Hello"}]

        key1 = client._generate_cache_key(messages, "model-a")
        key2 = client._generate_cache_key(messages, "model-b")

        assert key1 != key2


class TestOpenRouterClientCacheHit:
    """Test cases for cache hit scenarios."""

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_response(self) -> None:
        """chat_completion should return cached response on cache hit."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        cached_data = {
            "content": "Cached response",
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "model_used": "cached/model",
        }

        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value=cached_data)

        client = OpenRouterClient(api_key="test-api-key", cache=mock_cache)

        result = await client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
        )

        assert result.content == "Cached response"
        assert result.prompt_tokens == 10
        assert result.completion_tokens == 5

    @pytest.mark.asyncio
    async def test_cache_hit_does_not_call_api(self) -> None:
        """chat_completion should not call API on cache hit."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        cached_data = {
            "content": "Cached response",
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "model_used": "cached/model",
        }

        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value=cached_data)

        client = OpenRouterClient(api_key="test-api-key", cache=mock_cache)

        with patch.object(client, "_http_client") as mock_http:
            mock_http.post = AsyncMock()

            await client.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
            )

            # API should not be called
            mock_http.post.assert_not_called()


class TestOpenRouterClientCacheMiss:
    """Test cases for cache miss scenarios."""

    @pytest.mark.asyncio
    async def test_cache_miss_calls_api(self) -> None:
        """chat_completion should call API on cache miss."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "API response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        client = OpenRouterClient(api_key="test-api-key", cache=mock_cache)

        with patch.object(client, "_http_client") as mock_http:
            mock_http.post = AsyncMock(return_value=mock_response)

            result = await client.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
            )

            assert result.content == "API response"
            mock_http.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_miss_stores_response_in_cache(self) -> None:
        """chat_completion should store API response in cache on miss."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "API response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        client = OpenRouterClient(api_key="test-api-key", cache=mock_cache)

        with patch.object(client, "_http_client") as mock_http:
            mock_http.post = AsyncMock(return_value=mock_response)

            await client.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
            )

            # Cache should be updated
            mock_cache.set.assert_called_once()


class TestOpenRouterClientCacheDisabled:
    """Test cases when cache is not configured."""

    @pytest.mark.asyncio
    async def test_no_cache_always_calls_api(self) -> None:
        """chat_completion should always call API when cache not configured."""
        from smart_file_manager.services.openrouter_client import OpenRouterClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "API response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        client = OpenRouterClient(api_key="test-api-key")  # No cache

        with patch.object(client, "_http_client") as mock_http:
            mock_http.post = AsyncMock(return_value=mock_response)

            result = await client.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
            )

            assert result.content == "API response"
            mock_http.post.assert_called_once()
