"""Model configuration for OpenRouter API.

TAG-002: SPEC-API-001
This module defines model tiers and fallback chain configuration
for the OpenRouter vision API integration.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelTier:
    """Represents a model tier with pricing information.

    Attributes:
        name: The tier name (e.g., 'free', 'balanced', 'premium').
        model_id: The OpenRouter model identifier.
        input_cost_per_million: Cost per million input tokens in USD.
        output_cost_per_million: Cost per million output tokens in USD.
        description: Optional description of the model tier.
    """

    name: str
    model_id: str
    input_cost_per_million: float
    output_cost_per_million: float
    description: str | None = None


# =============================================================================
# Predefined Model Tiers
# =============================================================================

FREE_TIER = ModelTier(
    name="free",
    model_id="google/gemini-2.0-flash-exp:free",
    input_cost_per_million=0.0,
    output_cost_per_million=0.0,
    description="Free tier with Gemini 2.0 Flash experimental model",
)

LOW_COST_TIER = ModelTier(
    name="low_cost",
    model_id="qwen/qwen2.5-vl-32b-instruct",
    input_cost_per_million=0.05,
    output_cost_per_million=0.05,
    description="Low-cost tier with Qwen 2.5 VL model",
)

BALANCED_TIER = ModelTier(
    name="balanced",
    model_id="google/gemini-2.0-flash-001",
    input_cost_per_million=0.10,
    output_cost_per_million=0.40,
    description="Balanced tier with Gemini 2.0 Flash model",
)

PREMIUM_TIER = ModelTier(
    name="premium",
    model_id="openai/gpt-4o-mini",
    input_cost_per_million=0.15,
    output_cost_per_million=0.60,
    description="Premium tier with GPT-4o Mini model",
)

# Ordered list of all tiers from highest cost to lowest
ALL_TIERS: list[ModelTier] = [PREMIUM_TIER, BALANCED_TIER, LOW_COST_TIER, FREE_TIER]


class ModelConfig:
    """Configuration manager for model tiers and fallback chains.

    This class manages the primary model tier and provides methods
    to get fallback chains for graceful degradation when models fail.
    """

    def __init__(self, primary_tier: ModelTier = BALANCED_TIER) -> None:
        """Initialize ModelConfig with a primary tier.

        Args:
            primary_tier: The primary model tier to use. Defaults to BALANCED_TIER.
        """
        self._primary_tier = primary_tier
        self._tier_by_name: dict[str, ModelTier] = {tier.name: tier for tier in ALL_TIERS}
        self._tier_by_model_id: dict[str, ModelTier] = {tier.model_id: tier for tier in ALL_TIERS}

    @property
    def primary_tier(self) -> ModelTier:
        """Get the primary model tier."""
        return self._primary_tier

    def get_fallback_chain(self) -> list[ModelTier]:
        """Get the fallback chain starting from the primary tier.

        The fallback chain includes the primary tier and all lower-cost tiers,
        ending with the free tier. This ensures graceful degradation when
        higher-tier models fail or are unavailable.

        Returns:
            A list of ModelTier objects in fallback order.
        """
        # Find the index of the primary tier in the ordered list
        try:
            primary_index = ALL_TIERS.index(self._primary_tier)
        except ValueError:
            # If primary tier is not in the list, start from balanced
            primary_index = ALL_TIERS.index(BALANCED_TIER)

        # Return all tiers from primary to free (inclusive)
        return ALL_TIERS[primary_index:]

    def get_tier_by_name(self, name: str) -> ModelTier | None:
        """Get a model tier by its name.

        Args:
            name: The tier name (e.g., 'free', 'balanced', 'premium').

        Returns:
            The ModelTier if found, None otherwise.
        """
        return self._tier_by_name.get(name)

    def get_tier_by_model_id(self, model_id: str) -> ModelTier | None:
        """Get a model tier by its model ID.

        Args:
            model_id: The OpenRouter model identifier.

        Returns:
            The ModelTier if found, None otherwise.
        """
        return self._tier_by_model_id.get(model_id)
