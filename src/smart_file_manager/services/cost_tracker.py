"""Cost tracking and budget control for API usage.

TAG-006 & TAG-007: SPEC-API-001
This module provides cost tracking, budget monitoring, and automatic
free tier enforcement when budget limits are exceeded.
"""

from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, Any

from smart_file_manager.services.model_config import ModelTier

if TYPE_CHECKING:
    from smart_file_manager.infrastructure.cache.base import CacheInterface


class BudgetStatus(Enum):
    """Status of budget usage."""

    OK = "ok"
    DAILY_EXCEEDED = "daily_exceeded"
    MONTHLY_EXCEEDED = "monthly_exceeded"


class CostTracker:
    """Tracks API usage costs and enforces budget limits.

    This class provides:
    - Cost calculation based on model tier pricing
    - Daily and monthly cost tracking
    - Budget limit enforcement
    - Automatic free tier fallback when limits exceeded

    Attributes:
        daily_budget_limit: Maximum daily spending in USD.
        monthly_budget_limit: Maximum monthly spending in USD.
        cache: Optional cache interface for persistent storage.
    """

    def __init__(
        self,
        daily_budget_limit: float = 1.0,
        monthly_budget_limit: float = 30.0,
        cache: "CacheInterface | None" = None,
    ) -> None:
        """Initialize the cost tracker.

        Args:
            daily_budget_limit: Maximum daily spending in USD. Defaults to $1.
            monthly_budget_limit: Maximum monthly spending in USD. Defaults to $30.
            cache: Optional cache interface for persistent cost storage.
        """
        self.daily_budget_limit = daily_budget_limit
        self.monthly_budget_limit = monthly_budget_limit
        self.cache = cache

        # In-memory tracking when no cache is provided
        self._in_memory_daily_cost: float = 0.0
        self._in_memory_monthly_cost: float = 0.0
        self._in_memory_date: date = date.today()

    def calculate_cost(
        self,
        model_tier: ModelTier,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """Calculate the cost for a request based on model tier pricing.

        Args:
            model_tier: The model tier with pricing information.
            prompt_tokens: Number of tokens in the prompt.
            completion_tokens: Number of tokens in the completion.

        Returns:
            The total cost in USD.
        """
        input_cost = (prompt_tokens / 1_000_000) * model_tier.input_cost_per_million
        output_cost = (completion_tokens / 1_000_000) * model_tier.output_cost_per_million
        return input_cost + output_cost

    def _get_daily_cache_key(self) -> str:
        """Generate the cache key for daily cost tracking.

        Returns:
            Cache key string including today's date.
        """
        today = date.today().isoformat()
        return f"cost:daily:{today}"

    def _get_monthly_cache_key(self) -> str:
        """Generate the cache key for monthly cost tracking.

        Returns:
            Cache key string including current year and month.
        """
        today = date.today()
        return f"cost:monthly:{today.year}-{today.month:02d}"

    async def _get_cached_cost(self, key: str) -> float:
        """Get cost from cache or return 0.

        Args:
            key: The cache key.

        Returns:
            The cached cost or 0.0 if not found.
        """
        if self.cache is None:
            return 0.0

        data: dict[str, Any] | None = await self.cache.get(key)
        if data is None:
            return 0.0
        return float(data.get("cost", 0.0))

    async def _set_cached_cost(self, key: str, cost: float, ttl: int | None = None) -> None:
        """Store cost in cache.

        Args:
            key: The cache key.
            cost: The cost value to store.
            ttl: Optional time-to-live in seconds.
        """
        if self.cache is None:
            return

        await self.cache.set(key, {"cost": cost}, ttl=ttl)

    async def track_cost(
        self,
        model_tier: ModelTier,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """Track the cost of a request.

        Calculates the cost and updates both daily and monthly totals.

        Args:
            model_tier: The model tier with pricing information.
            prompt_tokens: Number of tokens in the prompt.
            completion_tokens: Number of tokens in the completion.

        Returns:
            The cost of this request in USD.
        """
        cost = self.calculate_cost(model_tier, prompt_tokens, completion_tokens)

        if self.cache is not None:
            # Update daily cost
            daily_key = self._get_daily_cache_key()
            current_daily = await self._get_cached_cost(daily_key)
            new_daily = current_daily + cost
            # TTL of 2 days for daily cost (to handle timezone edge cases)
            await self._set_cached_cost(daily_key, new_daily, ttl=172800)

            # Update monthly cost
            monthly_key = self._get_monthly_cache_key()
            current_monthly = await self._get_cached_cost(monthly_key)
            new_monthly = current_monthly + cost
            # TTL of 35 days for monthly cost
            await self._set_cached_cost(monthly_key, new_monthly, ttl=3024000)
        else:
            # In-memory tracking
            today = date.today()
            if self._in_memory_date != today:
                # Reset daily cost on new day
                self._in_memory_daily_cost = 0.0
                self._in_memory_date = today

            self._in_memory_daily_cost += cost
            self._in_memory_monthly_cost += cost

        return cost

    async def get_daily_cost(self) -> float:
        """Get the current day's total cost.

        Returns:
            The daily cost in USD.
        """
        if self.cache is not None:
            daily_key = self._get_daily_cache_key()
            return await self._get_cached_cost(daily_key)
        return self._in_memory_daily_cost

    async def get_monthly_cost(self) -> float:
        """Get the current month's total cost.

        Returns:
            The monthly cost in USD.
        """
        if self.cache is not None:
            monthly_key = self._get_monthly_cache_key()
            return await self._get_cached_cost(monthly_key)
        return self._in_memory_monthly_cost

    async def check_budget(self) -> BudgetStatus:
        """Check if budget limits have been exceeded.

        Returns:
            BudgetStatus indicating current budget state.
        """
        daily_cost = await self.get_daily_cost()
        if daily_cost >= self.daily_budget_limit:
            return BudgetStatus.DAILY_EXCEEDED

        monthly_cost = await self.get_monthly_cost()
        if monthly_cost >= self.monthly_budget_limit:
            return BudgetStatus.MONTHLY_EXCEEDED

        return BudgetStatus.OK

    async def is_budget_exceeded(self) -> bool:
        """Check if any budget limit has been exceeded.

        Returns:
            True if any budget is exceeded, False otherwise.
        """
        status = await self.check_budget()
        return status != BudgetStatus.OK

    async def should_force_free_tier(self) -> bool:
        """Check if free tier should be forced due to budget constraints.

        Returns:
            True if free tier should be used, False otherwise.
        """
        return await self.is_budget_exceeded()
