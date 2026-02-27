"""Model configuration for Ollama API.

This module defines model tiers and fallback chain configuration
for the Ollama vision API integration.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelTier:
    """Represents a model tier.

    Attributes:
        name: The tier name (e.g., 'vision', 'balanced', 'fast').
        model_id: The Ollama model identifier.
        input_cost_per_million: Cost per million input tokens (0 for local).
        output_cost_per_million: Cost per million output tokens (0 for local).
        description: Optional description of the model tier.
        is_vision: Whether the model supports vision/image analysis.
    """

    name: str
    model_id: str
    input_cost_per_million: float
    output_cost_per_million: float
    description: str | None = None
    is_vision: bool = False


# =============================================================================
# Ollama Model Tiers (Local - No API costs)
# =============================================================================

# Vision model for image analysis
VISION_TIER = ModelTier(
    name="vision",
    model_id="qwen2.5vl:7b",
    input_cost_per_million=0.0,
    output_cost_per_million=0.0,
    description="Qwen2.5-VL 7B vision model for image analysis",
    is_vision=True,
)

# High quality text model
PREMIUM_TIER = ModelTier(
    name="premium",
    model_id="glm-4.7-flash",
    input_cost_per_million=0.0,
    output_cost_per_million=0.0,
    description="GLM-4.7-Flash 29.9B for high-quality text generation",
)

# Balanced/default text model
BALANCED_TIER = ModelTier(
    name="balanced",
    model_id="qwen2.5:7b",
    input_cost_per_million=0.0,
    output_cost_per_million=0.0,
    description="Qwen2.5 7B for balanced text generation",
)

# Fast/lightweight model
FAST_TIER = ModelTier(
    name="fast",
    model_id="qwen2.5:7b",
    input_cost_per_million=0.0,
    output_cost_per_million=0.0,
    description="Qwen2.5 7B for fast responses",
)

# Ordered list of all text tiers from highest quality to fastest
ALL_TIERS: list[ModelTier] = [PREMIUM_TIER, BALANCED_TIER, FAST_TIER]


class ModelConfig:
    """Configuration manager for model tiers and fallback chains.

    This class manages the primary model tier and provides methods
    to get fallback chains for graceful degradation when models fail.
    """

    def __init__(
        self,
        primary_tier: ModelTier = BALANCED_TIER,
        vision_tier: ModelTier = VISION_TIER,
    ) -> None:
        """Initialize ModelConfig with primary and vision tiers.

        Args:
            primary_tier: The primary text model tier. Defaults to BALANCED_TIER.
            vision_tier: The vision model tier. Defaults to VISION_TIER.
        """
        self._primary_tier = primary_tier
        self._vision_tier = vision_tier
        self._tier_by_name: dict[str, ModelTier] = {tier.name: tier for tier in ALL_TIERS}
        self._tier_by_name["vision"] = VISION_TIER
        self._tier_by_model_id: dict[str, ModelTier] = {tier.model_id: tier for tier in ALL_TIERS}
        self._tier_by_model_id[VISION_TIER.model_id] = VISION_TIER

    @property
    def primary_tier(self) -> ModelTier:
        """Get the primary model tier for text generation."""
        return self._primary_tier

    @property
    def vision_tier(self) -> ModelTier:
        """Get the vision model tier for image analysis."""
        return self._vision_tier

    def get_fallback_chain(self) -> list[ModelTier]:
        """Get the fallback chain starting from the primary tier.

        The fallback chain includes the primary tier and all lower tiers.
        This ensures graceful degradation when higher-tier models fail.

        Returns:
            A list of ModelTier objects in fallback order.
        """
        try:
            primary_index = ALL_TIERS.index(self._primary_tier)
        except ValueError:
            primary_index = ALL_TIERS.index(BALANCED_TIER)

        return ALL_TIERS[primary_index:]

    def get_vision_fallback_chain(self) -> list[ModelTier]:
        """Get the fallback chain for vision models.

        Currently only one vision model, but can be extended.

        Returns:
            A list of vision ModelTier objects in fallback order.
        """
        return [self._vision_tier]

    def get_tier_by_name(self, name: str) -> ModelTier | None:
        """Get a model tier by its name.

        Args:
            name: The tier name (e.g., 'vision', 'balanced', 'premium').

        Returns:
            The ModelTier if found, None otherwise.
        """
        return self._tier_by_name.get(name)

    def get_tier_by_model_id(self, model_id: str) -> ModelTier | None:
        """Get a model tier by its model ID.

        Args:
            model_id: The Ollama model identifier.

        Returns:
            The ModelTier if found, None otherwise.
        """
        return self._tier_by_model_id.get(model_id)


# Legacy aliases for backward compatibility
FREE_TIER = FAST_TIER
LOW_COST_TIER = BALANCED_TIER
