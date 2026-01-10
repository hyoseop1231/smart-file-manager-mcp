"""Tests for cost tracking module.

TAG-006 & TAG-007: SPEC-API-001
RED Phase: These tests define the expected behavior for cost tracking and budget control.
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

# =============================================================================
# TAG-006: Cost Tracker Basic Tests
# =============================================================================


class TestCostTrackerInit:
    """Test cases for CostTracker initialization."""

    def test_cost_tracker_can_be_instantiated(self) -> None:
        """CostTracker should be instantiable."""
        from smart_file_manager.services.cost_tracker import CostTracker

        tracker = CostTracker()
        assert tracker is not None

    def test_cost_tracker_has_default_budget_limits(self) -> None:
        """CostTracker should have default budget limits."""
        from smart_file_manager.services.cost_tracker import CostTracker

        tracker = CostTracker()
        assert tracker.daily_budget_limit == 1.0  # $1/day
        assert tracker.monthly_budget_limit == 30.0  # $30/month

    def test_cost_tracker_accepts_custom_budget_limits(self) -> None:
        """CostTracker should accept custom budget limits."""
        from smart_file_manager.services.cost_tracker import CostTracker

        tracker = CostTracker(daily_budget_limit=5.0, monthly_budget_limit=100.0)
        assert tracker.daily_budget_limit == 5.0
        assert tracker.monthly_budget_limit == 100.0

    def test_cost_tracker_accepts_cache_interface(self) -> None:
        """CostTracker should accept a cache interface for persistence."""
        from smart_file_manager.services.cost_tracker import CostTracker

        from smart_file_manager.infrastructure.cache.base import CacheInterface

        mock_cache = MagicMock(spec=CacheInterface)
        tracker = CostTracker(cache=mock_cache)
        assert tracker.cache == mock_cache


class TestCostCalculation:
    """Test cases for cost calculation."""

    def test_calculate_cost_for_model_tier(self) -> None:
        """CostTracker should calculate cost based on model tier pricing."""
        from smart_file_manager.services.cost_tracker import CostTracker

        from smart_file_manager.services.model_config import BALANCED_TIER

        tracker = CostTracker()
        # 1000 prompt tokens, 500 completion tokens
        cost = tracker.calculate_cost(
            model_tier=BALANCED_TIER,
            prompt_tokens=1000,
            completion_tokens=500,
        )
        # Input: 1000 / 1_000_000 * 0.10 = 0.0001
        # Output: 500 / 1_000_000 * 0.40 = 0.0002
        # Total: 0.0003
        assert cost == pytest.approx(0.0003, rel=1e-6)

    def test_calculate_cost_for_free_tier(self) -> None:
        """CostTracker should return 0 cost for free tier."""
        from smart_file_manager.services.cost_tracker import CostTracker

        from smart_file_manager.services.model_config import FREE_TIER

        tracker = CostTracker()
        cost = tracker.calculate_cost(
            model_tier=FREE_TIER,
            prompt_tokens=10000,
            completion_tokens=5000,
        )
        assert cost == 0.0


class TestCostTracking:
    """Test cases for tracking costs."""

    @pytest.mark.asyncio
    async def test_track_cost_stores_in_cache(self) -> None:
        """track_cost should store the cost in cache."""
        from smart_file_manager.services.cost_tracker import CostTracker

        from smart_file_manager.services.model_config import BALANCED_TIER

        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()

        tracker = CostTracker(cache=mock_cache)
        await tracker.track_cost(
            model_tier=BALANCED_TIER,
            prompt_tokens=1000,
            completion_tokens=500,
        )

        # Should have called cache.set to update daily cost
        mock_cache.set.assert_called()

    @pytest.mark.asyncio
    async def test_track_cost_accumulates_daily_cost(self) -> None:
        """track_cost should accumulate costs for the same day."""
        from smart_file_manager.services.cost_tracker import CostTracker

        from smart_file_manager.services.model_config import BALANCED_TIER

        mock_cache = MagicMock()
        # Existing daily cost: $0.001
        mock_cache.get = AsyncMock(return_value={"cost": 0.001})
        mock_cache.set = AsyncMock()

        tracker = CostTracker(cache=mock_cache)
        await tracker.track_cost(
            model_tier=BALANCED_TIER,
            prompt_tokens=1000,
            completion_tokens=500,
        )

        # New cost: 0.0003, Total should be 0.0013
        call_args = mock_cache.set.call_args_list
        # Find the daily cost update call
        daily_cost_call = [c for c in call_args if "daily" in str(c)]
        assert len(daily_cost_call) > 0

    @pytest.mark.asyncio
    async def test_get_daily_cost(self) -> None:
        """get_daily_cost should return the current day's cost."""
        from smart_file_manager.services.cost_tracker import CostTracker

        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value={"cost": 0.5})

        tracker = CostTracker(cache=mock_cache)
        daily_cost = await tracker.get_daily_cost()

        assert daily_cost == 0.5

    @pytest.mark.asyncio
    async def test_get_daily_cost_returns_zero_when_no_data(self) -> None:
        """get_daily_cost should return 0 when no cost data exists."""
        from smart_file_manager.services.cost_tracker import CostTracker

        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value=None)

        tracker = CostTracker(cache=mock_cache)
        daily_cost = await tracker.get_daily_cost()

        assert daily_cost == 0.0

    @pytest.mark.asyncio
    async def test_get_monthly_cost(self) -> None:
        """get_monthly_cost should return the current month's cost."""
        from smart_file_manager.services.cost_tracker import CostTracker

        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value={"cost": 15.0})

        tracker = CostTracker(cache=mock_cache)
        monthly_cost = await tracker.get_monthly_cost()

        assert monthly_cost == 15.0

    @pytest.mark.asyncio
    async def test_get_monthly_cost_returns_zero_when_no_data(self) -> None:
        """get_monthly_cost should return 0 when no cost data exists."""
        from smart_file_manager.services.cost_tracker import CostTracker

        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value=None)

        tracker = CostTracker(cache=mock_cache)
        monthly_cost = await tracker.get_monthly_cost()

        assert monthly_cost == 0.0


# =============================================================================
# TAG-007: Budget Control Tests
# =============================================================================


class TestBudgetCheck:
    """Test cases for budget checking."""

    @pytest.mark.asyncio
    async def test_check_budget_returns_ok_when_under_limit(self) -> None:
        """check_budget should return OK when under both limits."""
        from smart_file_manager.services.cost_tracker import BudgetStatus, CostTracker

        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value={"cost": 0.5})

        tracker = CostTracker(cache=mock_cache, daily_budget_limit=1.0, monthly_budget_limit=30.0)
        status = await tracker.check_budget()

        assert status == BudgetStatus.OK

    @pytest.mark.asyncio
    async def test_check_budget_returns_daily_exceeded(self) -> None:
        """check_budget should return DAILY_EXCEEDED when daily limit exceeded."""
        from smart_file_manager.services.cost_tracker import BudgetStatus, CostTracker

        mock_cache = MagicMock()
        # Daily cost exceeds limit
        mock_cache.get = AsyncMock(side_effect=[{"cost": 1.5}, {"cost": 10.0}])

        tracker = CostTracker(cache=mock_cache, daily_budget_limit=1.0, monthly_budget_limit=30.0)
        status = await tracker.check_budget()

        assert status == BudgetStatus.DAILY_EXCEEDED

    @pytest.mark.asyncio
    async def test_check_budget_returns_monthly_exceeded(self) -> None:
        """check_budget should return MONTHLY_EXCEEDED when monthly limit exceeded."""
        from smart_file_manager.services.cost_tracker import BudgetStatus, CostTracker

        mock_cache = MagicMock()
        # Daily OK, but monthly exceeds
        mock_cache.get = AsyncMock(side_effect=[{"cost": 0.5}, {"cost": 35.0}])

        tracker = CostTracker(cache=mock_cache, daily_budget_limit=1.0, monthly_budget_limit=30.0)
        status = await tracker.check_budget()

        assert status == BudgetStatus.MONTHLY_EXCEEDED

    @pytest.mark.asyncio
    async def test_is_budget_exceeded_true_when_exceeded(self) -> None:
        """is_budget_exceeded should return True when any budget exceeded."""
        from smart_file_manager.services.cost_tracker import CostTracker

        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(side_effect=[{"cost": 1.5}, {"cost": 10.0}])

        tracker = CostTracker(cache=mock_cache, daily_budget_limit=1.0, monthly_budget_limit=30.0)
        exceeded = await tracker.is_budget_exceeded()

        assert exceeded is True

    @pytest.mark.asyncio
    async def test_is_budget_exceeded_false_when_ok(self) -> None:
        """is_budget_exceeded should return False when under limits."""
        from smart_file_manager.services.cost_tracker import CostTracker

        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value={"cost": 0.5})

        tracker = CostTracker(cache=mock_cache, daily_budget_limit=1.0, monthly_budget_limit=30.0)
        exceeded = await tracker.is_budget_exceeded()

        assert exceeded is False


class TestForceFreeMode:
    """Test cases for force free mode when budget exceeded."""

    @pytest.mark.asyncio
    async def test_should_force_free_tier_when_daily_exceeded(self) -> None:
        """should_force_free_tier should return True when daily budget exceeded."""
        from smart_file_manager.services.cost_tracker import CostTracker

        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(side_effect=[{"cost": 1.5}, {"cost": 10.0}])

        tracker = CostTracker(cache=mock_cache, daily_budget_limit=1.0, monthly_budget_limit=30.0)
        force_free = await tracker.should_force_free_tier()

        assert force_free is True

    @pytest.mark.asyncio
    async def test_should_force_free_tier_when_monthly_exceeded(self) -> None:
        """should_force_free_tier should return True when monthly budget exceeded."""
        from smart_file_manager.services.cost_tracker import CostTracker

        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(side_effect=[{"cost": 0.5}, {"cost": 35.0}])

        tracker = CostTracker(cache=mock_cache, daily_budget_limit=1.0, monthly_budget_limit=30.0)
        force_free = await tracker.should_force_free_tier()

        assert force_free is True

    @pytest.mark.asyncio
    async def test_should_not_force_free_tier_when_under_budget(self) -> None:
        """should_force_free_tier should return False when under budget."""
        from smart_file_manager.services.cost_tracker import CostTracker

        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value={"cost": 0.5})

        tracker = CostTracker(cache=mock_cache, daily_budget_limit=1.0, monthly_budget_limit=30.0)
        force_free = await tracker.should_force_free_tier()

        assert force_free is False


class TestBudgetStatusEnum:
    """Test cases for BudgetStatus enum."""

    def test_budget_status_has_expected_values(self) -> None:
        """BudgetStatus should have OK, DAILY_EXCEEDED, MONTHLY_EXCEEDED."""
        from smart_file_manager.services.cost_tracker import BudgetStatus

        assert hasattr(BudgetStatus, "OK")
        assert hasattr(BudgetStatus, "DAILY_EXCEEDED")
        assert hasattr(BudgetStatus, "MONTHLY_EXCEEDED")


class TestCostTrackerCacheKeys:
    """Test cases for cache key generation."""

    def test_daily_cache_key_includes_date(self) -> None:
        """Daily cache key should include today's date."""
        from smart_file_manager.services.cost_tracker import CostTracker

        tracker = CostTracker()
        key = tracker._get_daily_cache_key()

        today = date.today().isoformat()
        assert today in key
        assert "daily" in key.lower()

    def test_monthly_cache_key_includes_year_month(self) -> None:
        """Monthly cache key should include year and month."""
        from smart_file_manager.services.cost_tracker import CostTracker

        tracker = CostTracker()
        key = tracker._get_monthly_cache_key()

        today = date.today()
        assert str(today.year) in key
        assert f"{today.month:02d}" in key
        assert "monthly" in key.lower()


class TestCostTrackerWithoutCache:
    """Test cases for CostTracker when cache is not provided."""

    @pytest.mark.asyncio
    async def test_track_cost_works_without_cache(self) -> None:
        """track_cost should work without cache (in-memory tracking)."""
        from smart_file_manager.services.cost_tracker import CostTracker

        from smart_file_manager.services.model_config import BALANCED_TIER

        tracker = CostTracker()
        # Should not raise
        await tracker.track_cost(
            model_tier=BALANCED_TIER,
            prompt_tokens=1000,
            completion_tokens=500,
        )

    @pytest.mark.asyncio
    async def test_get_daily_cost_works_without_cache(self) -> None:
        """get_daily_cost should work without cache."""
        from smart_file_manager.services.cost_tracker import CostTracker

        tracker = CostTracker()
        daily_cost = await tracker.get_daily_cost()
        assert daily_cost == 0.0
