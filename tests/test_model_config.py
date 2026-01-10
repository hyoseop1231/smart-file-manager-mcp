"""Tests for model configuration module.

TAG-002: SPEC-API-001
RED Phase: These tests define the expected behavior for model configuration.
"""

from dataclasses import FrozenInstanceError

import pytest


class TestModelTier:
    """Test cases for ModelTier dataclass."""

    def test_model_tier_is_dataclass(self) -> None:
        """ModelTier should be a dataclass."""
        from dataclasses import is_dataclass

        from smart_file_manager.services.model_config import ModelTier

        assert is_dataclass(ModelTier)

    def test_model_tier_has_required_fields(self) -> None:
        """ModelTier should have all required fields."""
        from smart_file_manager.services.model_config import ModelTier

        tier = ModelTier(
            name="test",
            model_id="test/model",
            input_cost_per_million=0.1,
            output_cost_per_million=0.2,
        )
        assert tier.name == "test"
        assert tier.model_id == "test/model"
        assert tier.input_cost_per_million == 0.1
        assert tier.output_cost_per_million == 0.2

    def test_model_tier_is_frozen(self) -> None:
        """ModelTier should be immutable (frozen)."""
        from smart_file_manager.services.model_config import ModelTier

        tier = ModelTier(
            name="test",
            model_id="test/model",
            input_cost_per_million=0.1,
            output_cost_per_million=0.2,
        )
        with pytest.raises(FrozenInstanceError):
            tier.name = "changed"  # type: ignore[misc]

    def test_model_tier_has_optional_description(self) -> None:
        """ModelTier should have optional description field."""
        from smart_file_manager.services.model_config import ModelTier

        tier_without_desc = ModelTier(
            name="test",
            model_id="test/model",
            input_cost_per_million=0.1,
            output_cost_per_million=0.2,
        )
        assert tier_without_desc.description is None

        tier_with_desc = ModelTier(
            name="test",
            model_id="test/model",
            input_cost_per_million=0.1,
            output_cost_per_million=0.2,
            description="Test model",
        )
        assert tier_with_desc.description == "Test model"


class TestPredefinedTiers:
    """Test cases for predefined model tiers."""

    def test_free_tier_exists(self) -> None:
        """FREE_TIER should be defined with correct values."""
        from smart_file_manager.services.model_config import FREE_TIER

        assert FREE_TIER.name == "free"
        assert FREE_TIER.model_id == "google/gemini-2.0-flash-exp:free"
        assert FREE_TIER.input_cost_per_million == 0.0
        assert FREE_TIER.output_cost_per_million == 0.0

    def test_low_cost_tier_exists(self) -> None:
        """LOW_COST_TIER should be defined with correct values."""
        from smart_file_manager.services.model_config import LOW_COST_TIER

        assert LOW_COST_TIER.name == "low_cost"
        assert LOW_COST_TIER.model_id == "qwen/qwen2.5-vl-32b-instruct"
        assert LOW_COST_TIER.input_cost_per_million == 0.05
        assert LOW_COST_TIER.output_cost_per_million == 0.05

    def test_balanced_tier_exists(self) -> None:
        """BALANCED_TIER should be defined with correct values."""
        from smart_file_manager.services.model_config import BALANCED_TIER

        assert BALANCED_TIER.name == "balanced"
        assert BALANCED_TIER.model_id == "google/gemini-2.0-flash-001"
        assert BALANCED_TIER.input_cost_per_million == 0.10
        assert BALANCED_TIER.output_cost_per_million == 0.40

    def test_premium_tier_exists(self) -> None:
        """PREMIUM_TIER should be defined with correct values."""
        from smart_file_manager.services.model_config import PREMIUM_TIER

        assert PREMIUM_TIER.name == "premium"
        assert PREMIUM_TIER.model_id == "openai/gpt-4o-mini"
        assert PREMIUM_TIER.input_cost_per_million == 0.15
        assert PREMIUM_TIER.output_cost_per_million == 0.60


class TestModelConfig:
    """Test cases for ModelConfig class."""

    def test_model_config_can_be_instantiated(self) -> None:
        """ModelConfig should be instantiable."""
        from smart_file_manager.services.model_config import ModelConfig

        config = ModelConfig()
        assert config is not None

    def test_model_config_has_default_primary_tier(self) -> None:
        """ModelConfig should have a default primary tier (balanced)."""
        from smart_file_manager.services.model_config import BALANCED_TIER, ModelConfig

        config = ModelConfig()
        assert config.primary_tier == BALANCED_TIER

    def test_model_config_accepts_custom_primary_tier(self) -> None:
        """ModelConfig should accept a custom primary tier."""
        from smart_file_manager.services.model_config import (
            PREMIUM_TIER,
            ModelConfig,
        )

        config = ModelConfig(primary_tier=PREMIUM_TIER)
        assert config.primary_tier == PREMIUM_TIER

    def test_model_config_get_fallback_chain_returns_list(self) -> None:
        """ModelConfig.get_fallback_chain should return a list of ModelTier."""
        from smart_file_manager.services.model_config import ModelConfig, ModelTier

        config = ModelConfig()
        chain = config.get_fallback_chain()
        assert isinstance(chain, list)
        assert all(isinstance(tier, ModelTier) for tier in chain)

    def test_model_config_fallback_chain_starts_with_primary(self) -> None:
        """Fallback chain should start with the primary tier."""
        from smart_file_manager.services.model_config import BALANCED_TIER, ModelConfig

        config = ModelConfig(primary_tier=BALANCED_TIER)
        chain = config.get_fallback_chain()
        assert chain[0] == BALANCED_TIER

    def test_model_config_fallback_chain_ends_with_free_tier(self) -> None:
        """Fallback chain should end with the free tier."""
        from smart_file_manager.services.model_config import FREE_TIER, ModelConfig

        config = ModelConfig()
        chain = config.get_fallback_chain()
        assert chain[-1] == FREE_TIER

    def test_model_config_fallback_chain_order(self) -> None:
        """Fallback chain should follow cost-descending order to free."""
        from smart_file_manager.services.model_config import (
            BALANCED_TIER,
            FREE_TIER,
            LOW_COST_TIER,
            ModelConfig,
        )

        config = ModelConfig(primary_tier=BALANCED_TIER)
        chain = config.get_fallback_chain()

        # Expected: balanced -> low_cost -> free
        assert chain[0] == BALANCED_TIER
        assert chain[1] == LOW_COST_TIER
        assert chain[2] == FREE_TIER
        assert len(chain) == 3

    def test_model_config_fallback_chain_from_premium(self) -> None:
        """Fallback chain from premium should include all lower tiers."""
        from smart_file_manager.services.model_config import (
            BALANCED_TIER,
            FREE_TIER,
            LOW_COST_TIER,
            PREMIUM_TIER,
            ModelConfig,
        )

        config = ModelConfig(primary_tier=PREMIUM_TIER)
        chain = config.get_fallback_chain()

        # Expected: premium -> balanced -> low_cost -> free
        assert chain[0] == PREMIUM_TIER
        assert chain[1] == BALANCED_TIER
        assert chain[2] == LOW_COST_TIER
        assert chain[3] == FREE_TIER
        assert len(chain) == 4

    def test_model_config_fallback_chain_from_free(self) -> None:
        """Fallback chain from free should only contain free tier."""
        from smart_file_manager.services.model_config import FREE_TIER, ModelConfig

        config = ModelConfig(primary_tier=FREE_TIER)
        chain = config.get_fallback_chain()

        assert chain == [FREE_TIER]
        assert len(chain) == 1

    def test_model_config_get_tier_by_name(self) -> None:
        """ModelConfig should provide a method to get tier by name."""
        from smart_file_manager.services.model_config import FREE_TIER, ModelConfig

        config = ModelConfig()
        tier = config.get_tier_by_name("free")
        assert tier == FREE_TIER

    def test_model_config_get_tier_by_name_returns_none_for_unknown(self) -> None:
        """ModelConfig.get_tier_by_name should return None for unknown tier."""
        from smart_file_manager.services.model_config import ModelConfig

        config = ModelConfig()
        tier = config.get_tier_by_name("unknown_tier")
        assert tier is None

    def test_model_config_get_tier_by_model_id(self) -> None:
        """ModelConfig should provide a method to get tier by model_id."""
        from smart_file_manager.services.model_config import PREMIUM_TIER, ModelConfig

        config = ModelConfig()
        tier = config.get_tier_by_model_id("openai/gpt-4o-mini")
        assert tier == PREMIUM_TIER

    def test_model_config_get_tier_by_model_id_returns_none_for_unknown(self) -> None:
        """ModelConfig.get_tier_by_model_id should return None for unknown model."""
        from smart_file_manager.services.model_config import ModelConfig

        config = ModelConfig()
        tier = config.get_tier_by_model_id("unknown/model")
        assert tier is None


class TestModelTierEquality:
    """Test cases for ModelTier equality and hashing."""

    def test_model_tier_equality(self) -> None:
        """ModelTier instances with same values should be equal."""
        from smart_file_manager.services.model_config import ModelTier

        tier1 = ModelTier(
            name="test",
            model_id="test/model",
            input_cost_per_million=0.1,
            output_cost_per_million=0.2,
        )
        tier2 = ModelTier(
            name="test",
            model_id="test/model",
            input_cost_per_million=0.1,
            output_cost_per_million=0.2,
        )
        assert tier1 == tier2

    def test_model_tier_hashable(self) -> None:
        """ModelTier should be hashable (usable in sets/dicts)."""
        from smart_file_manager.services.model_config import ModelTier

        tier = ModelTier(
            name="test",
            model_id="test/model",
            input_cost_per_million=0.1,
            output_cost_per_million=0.2,
        )
        # Should not raise
        tier_set = {tier}
        assert tier in tier_set
