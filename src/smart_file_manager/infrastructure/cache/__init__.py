"""Cache infrastructure for Smart File Manager."""

from smart_file_manager.infrastructure.cache.base import CacheInterface
from smart_file_manager.infrastructure.cache.memory_cache import MemoryCache
from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

__all__ = [
    "CacheInterface",
    "MemoryCache",
    "RedisCache",
]
