"""Redis cache implementation.

This module provides a Redis-based cache implementation with support for
TTL-based expiration and graceful degradation.
"""

import json
from typing import Any

import redis.asyncio as redis

from smart_file_manager.core.exceptions import CacheConnectionError
from smart_file_manager.infrastructure.cache.base import CacheInterface


class RedisCache(CacheInterface):
    """Redis-based cache implementation.

    This cache uses Redis as the backend for persistent caching across
    application restarts and multiple processes.

    Attributes:
        redis_url: The Redis connection URL.
        default_ttl: Default TTL in seconds for cache entries.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: int = 86400,
    ) -> None:
        """Initialize the Redis cache.

        Args:
            redis_url: The Redis connection URL.
            default_ttl: Default TTL in seconds (default: 24 hours).
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self._client: redis.Redis | None = None
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        """Check if the cache is connected to Redis.

        Returns:
            True if connected, False otherwise.
        """
        return self._is_connected

    async def connect(self) -> None:
        """Connect to Redis.

        Raises:
            CacheConnectionError: If connection fails.
        """
        try:
            self._client = redis.from_url(  # type: ignore[no-untyped-call]
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection with ping
            await self._client.ping()  # type: ignore[misc]
            self._is_connected = True
        except Exception as e:
            self._is_connected = False
            raise CacheConnectionError(f"Failed to connect to Redis: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()
            self._is_connected = False

    async def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache.

        Args:
            key: The cache key to retrieve.

        Returns:
            The cached value, or None if the key does not exist.
        """
        if self._client is None:
            return None

        value = await self._client.get(key)
        if value is None:
            return None

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store a value in the cache.

        Args:
            key: The cache key.
            value: The value to store (will be JSON serialized).
            ttl: Optional time-to-live in seconds. If None, uses default TTL.
        """
        if self._client is None:
            return

        effective_ttl = ttl if ttl is not None else self.default_ttl
        serialized_value = json.dumps(value, ensure_ascii=False)

        await self._client.setex(key, effective_ttl, serialized_value)

    async def delete(self, key: str) -> None:
        """Delete a key from the cache.

        Args:
            key: The cache key to delete.
        """
        if self._client is None:
            return

        await self._client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: The cache key to check.

        Returns:
            True if the key exists, False otherwise.
        """
        if self._client is None:
            return False

        result = await self._client.exists(key)
        return bool(result)

    async def clear(self) -> None:
        """Clear all entries from the cache."""
        if self._client is None:
            return

        await self._client.flushdb()

    async def health_check(self) -> bool:
        """Check if the cache is healthy and accessible.

        Returns:
            True if the cache is healthy, False otherwise.
        """
        if self._client is None:
            return False

        try:
            await self._client.ping()  # type: ignore[misc]
            return True
        except Exception:
            return False
