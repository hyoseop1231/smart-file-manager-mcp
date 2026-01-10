"""In-memory cache implementation.

This module provides a simple in-memory cache that can be used as a fallback
when Redis is unavailable, or for development/testing purposes.
"""

import time
from dataclasses import dataclass
from typing import Any

from smart_file_manager.infrastructure.cache.base import CacheInterface


@dataclass
class CacheEntry:
    """Represents a cached entry with optional expiration."""

    value: Any
    expires_at: float | None = None

    def is_expired(self) -> bool:
        """Check if the entry has expired.

        Returns:
            True if expired, False otherwise.
        """
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class MemoryCache(CacheInterface):
    """In-memory cache implementation.

    This cache stores data in a Python dictionary. It supports TTL-based
    expiration and is suitable for development, testing, or as a fallback
    when Redis is unavailable.

    Note: This cache is not persistent and will be cleared when the
    application restarts. It is also not suitable for multi-process
    deployments as each process will have its own cache.
    """

    def __init__(self, default_ttl: int | None = None) -> None:
        """Initialize the memory cache.

        Args:
            default_ttl: Optional default TTL in seconds for cache entries.
        """
        self._cache: dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl

    async def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache.

        Args:
            key: The cache key to retrieve.

        Returns:
            The cached value, or None if the key does not exist or is expired.
        """
        entry = self._cache.get(key)
        if entry is None:
            return None

        if entry.is_expired():
            # Clean up expired entry
            del self._cache[key]
            return None

        return entry.value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store a value in the cache.

        Args:
            key: The cache key.
            value: The value to store.
            ttl: Optional time-to-live in seconds. If None, uses default TTL.
        """
        effective_ttl = ttl if ttl is not None else self.default_ttl
        expires_at = None

        if effective_ttl is not None:
            expires_at = time.time() + effective_ttl

        self._cache[key] = CacheEntry(value=value, expires_at=expires_at)

    async def delete(self, key: str) -> None:
        """Delete a key from the cache.

        Args:
            key: The cache key to delete.
        """
        self._cache.pop(key, None)

    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: The cache key to check.

        Returns:
            True if the key exists and is not expired, False otherwise.
        """
        entry = self._cache.get(key)
        if entry is None:
            return False

        if entry.is_expired():
            # Clean up expired entry
            del self._cache[key]
            return False

        return True

    async def clear(self) -> None:
        """Clear all entries from the cache."""
        self._cache.clear()

    async def health_check(self) -> bool:
        """Check if the cache is healthy.

        For memory cache, this always returns True as there is no
        external dependency.

        Returns:
            True always.
        """
        return True
