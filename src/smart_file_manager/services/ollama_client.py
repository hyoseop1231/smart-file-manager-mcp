"""Ollama API client for local vision model integration.

This module provides an async client for Ollama Vision API.
Drop-in replacement for OpenRouterClient.
"""

import base64
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from smart_file_manager.infrastructure.cache.base import CacheInterface


@dataclass
class ChatCompletionResponse:
    """Response from a chat completion request."""
    content: str
    prompt_tokens: int
    completion_tokens: int
    model_used: str

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class OllamaClient:
    """Async client for Ollama Vision API.
    
    Drop-in replacement for OpenRouterClient.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5vl:7b",
        timeout: float = 120.0,
        cache: "CacheInterface | None" = None,
        **kwargs,  # Ignore extra args for compatibility
    ) -> None:
        self.base_url = base_url
        self.model = model
        self.cache = cache
        self._http_client = httpx.AsyncClient(timeout=timeout)
        
    async def _check_model_available(self) -> bool:
        """Check if vision model is available."""
        try:
            resp = await self._http_client.get(f"{self.base_url}/api/tags")
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                return any(self.model in m.get("name", "") for m in models)
        except Exception:
            pass
        return False

    def _generate_cache_key(self, messages: list[dict[str, Any]]) -> str:
        """Generate cache key from messages."""
        content = str(messages)
        return f"ollama:{hashlib.sha256(content.encode()).hexdigest()[:16]}"

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        **kwargs,
    ) -> ChatCompletionResponse:
        """Send chat completion request to Ollama."""
        model = model or self.model
        
        # Extract image and text from messages
        images = []
        prompt_parts = []
        
        for msg in messages:
            content = msg.get("content", [])
            if isinstance(content, str):
                prompt_parts.append(content)
            elif isinstance(content, list):
                for item in content:
                    if item.get("type") == "text":
                        prompt_parts.append(item.get("text", ""))
                    elif item.get("type") == "image_url":
                        url = item.get("image_url", {}).get("url", "")
                        if url.startswith("data:"):
                            # Extract base64 from data URL
                            b64 = url.split(",", 1)[-1]
                            images.append(b64)
        
        prompt = "\n".join(prompt_parts)
        
        # Build request
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if images:
            payload["images"] = images
        
        resp = await self._http_client.post(
            f"{self.base_url}/api/generate",
            json=payload,
        )
        
        if resp.status_code != 200:
            raise Exception(f"Ollama API error: {resp.status_code}")
        
        data = resp.json()
        return ChatCompletionResponse(
            content=data.get("response", ""),
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            model_used=model,
        )

    async def chat_completion_with_fallback(
        self,
        messages: list[dict[str, Any]],
        **kwargs,
    ) -> ChatCompletionResponse:
        """Chat completion with cache check."""
        # Check cache first
        if self.cache:
            cache_key = self._generate_cache_key(messages)
            cached = await self.cache.get(cache_key)
            if cached:
                return ChatCompletionResponse(**cached)
        
        # Make request
        response = await self.chat_completion(messages)
        
        # Cache result
        if self.cache:
            await self.cache.set(
                cache_key,
                {
                    "content": response.content,
                    "prompt_tokens": response.prompt_tokens,
                    "completion_tokens": response.completion_tokens,
                    "model_used": response.model_used,
                },
                ttl=86400 * 7,  # 7 days
            )
        
        return response

    async def close(self) -> None:
        await self._http_client.aclose()

    async def __aenter__(self) -> "OllamaClient":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()
