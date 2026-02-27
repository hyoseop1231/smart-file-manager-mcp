"""OpenRouter API client (Ollama compatibility layer).

This module provides backward compatibility by re-exporting
the OllamaClient as OpenRouterClient.
"""

from smart_file_manager.services.ollama_client import (
    ChatCompletionResponse,
    OllamaClient,
    OllamaClient as OpenRouterClient,
    RETRYABLE_STATUS_CODES,
)

__all__ = [
    "ChatCompletionResponse",
    "OllamaClient",
    "OpenRouterClient",
    "RETRYABLE_STATUS_CODES",
]
