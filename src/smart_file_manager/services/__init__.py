"""Services module for Smart File Manager.

This module contains service classes for external integrations
including Ollama API client, model configuration, and cost tracking.
"""

from smart_file_manager.services.cost_tracker import (
    BudgetStatus,
    CostTracker,
)
from smart_file_manager.services.model_config import (
    BALANCED_TIER,
    FAST_TIER,
    FREE_TIER,
    LOW_COST_TIER,
    PREMIUM_TIER,
    VISION_TIER,
    ModelConfig,
    ModelTier,
)
from smart_file_manager.services.openrouter_client import (
    ChatCompletionResponse,
    OllamaClient,
    OpenRouterClient,
)

__all__ = [
    "ModelTier",
    "ModelConfig",
    "FREE_TIER",
    "LOW_COST_TIER",
    "BALANCED_TIER",
    "PREMIUM_TIER",
    "FAST_TIER",
    "VISION_TIER",
    "OpenRouterClient",
    "OllamaClient",
    "ChatCompletionResponse",
    "CostTracker",
    "BudgetStatus",
]
