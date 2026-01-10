"""Abstract base class for cache implementations.

This module defines the CacheInterface that all cache implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Any


class CacheInterface(ABC):
    """Abstract base class for cache implementations.

    All cache implementations (Redis, Memory, etc.) must inherit from this class
    and implement all abstract methods.
    """

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache.

        Args:
            key: The cache key to retrieve.

        Returns:
            The cached value, or None if the key does not exist.
        """

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store a value in the cache.

        Args:
            key: The cache key.
            value: The value to store.
            ttl: Optional time-to-live in seconds. If None, uses default TTL.
        """

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a key from the cache.

        Args:
            key: The cache key to delete.
        """

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: The cache key to check.

        Returns:
            True if the key exists, False otherwise.
        """

    @abstractmethod
    async def clear(self) -> None:
        """Clear all entries from the cache."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the cache is healthy and accessible.

        Returns:
            True if the cache is healthy, False otherwise.
        """
