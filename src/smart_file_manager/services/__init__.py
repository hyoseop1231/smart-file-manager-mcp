"""Services module for Smart File Manager.

This module contains service classes for external integrations
including OpenRouter API client, model configuration, and cost tracking.
"""

from smart_file_manager.services.cost_tracker import (
    BudgetStatus,
    CostTracker,
)
from smart_file_manager.services.model_config import (
    BALANCED_TIER,
    FREE_TIER,
    LOW_COST_TIER,
    PREMIUM_TIER,
    ModelConfig,
    ModelTier,
)
from smart_file_manager.services.openrouter_client import (
    ChatCompletionResponse,
    OpenRouterClient,
)

__all__ = [
    "ModelTier",
    "ModelConfig",
    "FREE_TIER",
    "LOW_COST_TIER",
    "BALANCED_TIER",
    "PREMIUM_TIER",
    "OpenRouterClient",
    "ChatCompletionResponse",
    "CostTracker",
    "BudgetStatus",
]
