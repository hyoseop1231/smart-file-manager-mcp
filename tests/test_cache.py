"""Tests for cache infrastructure module.

RED Phase: These tests define the expected behavior for cache implementations.
"""

import asyncio
import json
from abc import ABC
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestCacheInterface:
    """Test cases for CacheInterface abstract base class."""

    def test_cache_interface_is_abstract(self) -> None:
        """CacheInterface should be an abstract base class."""
        from smart_file_manager.infrastructure.cache.base import CacheInterface

        assert issubclass(CacheInterface, ABC)

    def test_cache_interface_cannot_be_instantiated(self) -> None:
        """CacheInterface should not be directly instantiable."""
        from smart_file_manager.infrastructure.cache.base import CacheInterface

        with pytest.raises(TypeError):
            CacheInterface()  # type: ignore[abstract]

    def test_cache_interface_defines_get_method(self) -> None:
        """CacheInterface should define an async get method."""
        from smart_file_manager.infrastructure.cache.base import CacheInterface

        assert hasattr(CacheInterface, "get")

    def test_cache_interface_defines_set_method(self) -> None:
        """CacheInterface should define an async set method."""
        from smart_file_manager.infrastructure.cache.base import CacheInterface

        assert hasattr(CacheInterface, "set")

    def test_cache_interface_defines_delete_method(self) -> None:
        """CacheInterface should define an async delete method."""
        from smart_file_manager.infrastructure.cache.base import CacheInterface

        assert hasattr(CacheInterface, "delete")

    def test_cache_interface_defines_exists_method(self) -> None:
        """CacheInterface should define an async exists method."""
        from smart_file_manager.infrastructure.cache.base import CacheInterface

        assert hasattr(CacheInterface, "exists")

    def test_cache_interface_defines_clear_method(self) -> None:
        """CacheInterface should define an async clear method."""
        from smart_file_manager.infrastructure.cache.base import CacheInterface

        assert hasattr(CacheInterface, "clear")

    def test_cache_interface_defines_health_check_method(self) -> None:
        """CacheInterface should define an async health_check method."""
        from smart_file_manager.infrastructure.cache.base import CacheInterface

        assert hasattr(CacheInterface, "health_check")


class TestMemoryCache:
    """Test cases for MemoryCache implementation."""

    @pytest.fixture
    def memory_cache(self) -> Any:
        """Create a MemoryCache instance for testing."""
        from smart_file_manager.infrastructure.cache.memory_cache import MemoryCache

        return MemoryCache()

    def test_memory_cache_implements_interface(self) -> None:
        """MemoryCache should implement CacheInterface."""
        from smart_file_manager.infrastructure.cache.base import CacheInterface
        from smart_file_manager.infrastructure.cache.memory_cache import MemoryCache

        assert issubclass(MemoryCache, CacheInterface)

    @pytest.mark.asyncio
    async def test_memory_cache_set_and_get(self, memory_cache: Any) -> None:
        """MemoryCache should store and retrieve values."""
        await memory_cache.set("test_key", {"data": "value"})
        result = await memory_cache.get("test_key")
        assert result == {"data": "value"}

    @pytest.mark.asyncio
    async def test_memory_cache_get_returns_none_for_missing_key(self, memory_cache: Any) -> None:
        """MemoryCache.get should return None for non-existent keys."""
        result = await memory_cache.get("non_existent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_memory_cache_delete(self, memory_cache: Any) -> None:
        """MemoryCache should delete keys."""
        await memory_cache.set("key_to_delete", "value")
        await memory_cache.delete("key_to_delete")
        result = await memory_cache.get("key_to_delete")
        assert result is None

    @pytest.mark.asyncio
    async def test_memory_cache_delete_non_existent_key(self, memory_cache: Any) -> None:
        """MemoryCache.delete should not raise error for non-existent keys."""
        # Should not raise
        await memory_cache.delete("non_existent_key")

    @pytest.mark.asyncio
    async def test_memory_cache_exists_true(self, memory_cache: Any) -> None:
        """MemoryCache.exists should return True for existing keys."""
        await memory_cache.set("existing_key", "value")
        result = await memory_cache.exists("existing_key")
        assert result is True

    @pytest.mark.asyncio
    async def test_memory_cache_exists_false(self, memory_cache: Any) -> None:
        """MemoryCache.exists should return False for non-existent keys."""
        result = await memory_cache.exists("non_existent_key")
        assert result is False

    @pytest.mark.asyncio
    async def test_memory_cache_clear(self, memory_cache: Any) -> None:
        """MemoryCache.clear should remove all entries."""
        await memory_cache.set("key1", "value1")
        await memory_cache.set("key2", "value2")
        await memory_cache.clear()
        assert await memory_cache.get("key1") is None
        assert await memory_cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_memory_cache_health_check(self, memory_cache: Any) -> None:
        """MemoryCache.health_check should return True."""
        result = await memory_cache.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_memory_cache_set_with_ttl(self, memory_cache: Any) -> None:
        """MemoryCache should support TTL for entries."""
        await memory_cache.set("ttl_key", "value", ttl=1)
        # Value should exist immediately
        result = await memory_cache.get("ttl_key")
        assert result == "value"

    @pytest.mark.asyncio
    async def test_memory_cache_expired_entry_returns_none(self, memory_cache: Any) -> None:
        """MemoryCache should return None for expired entries."""
        await memory_cache.set("expiring_key", "value", ttl=0)
        # Small delay to ensure expiration
        await asyncio.sleep(0.1)
        result = await memory_cache.get("expiring_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_memory_cache_stores_complex_data(self, memory_cache: Any) -> None:
        """MemoryCache should store complex data structures."""
        complex_data = {
            "summary": "Test summary",
            "tags": ["tag1", "tag2"],
            "nested": {"key": "value"},
            "list": [1, 2, 3],
        }
        await memory_cache.set("complex_key", complex_data)
        result = await memory_cache.get("complex_key")
        assert result == complex_data


class TestRedisCache:
    """Test cases for RedisCache implementation."""

    def test_redis_cache_implements_interface(self) -> None:
        """RedisCache should implement CacheInterface."""
        from smart_file_manager.infrastructure.cache.base import CacheInterface
        from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

        assert issubclass(RedisCache, CacheInterface)

    def test_redis_cache_accepts_redis_url(self) -> None:
        """RedisCache should accept a Redis URL on initialization."""
        from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

        cache = RedisCache(redis_url="redis://localhost:6379/0")
        assert cache.redis_url == "redis://localhost:6379/0"

    def test_redis_cache_accepts_default_ttl(self) -> None:
        """RedisCache should accept a default TTL on initialization."""
        from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

        cache = RedisCache(redis_url="redis://localhost:6379/0", default_ttl=3600)
        assert cache.default_ttl == 3600

    @pytest.mark.asyncio
    async def test_redis_cache_set_serializes_to_json(self) -> None:
        """RedisCache.set should serialize values to JSON."""
        from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

        mock_redis = MagicMock()
        mock_redis.setex = AsyncMock()
        mock_redis.set = AsyncMock()

        cache = RedisCache(redis_url="redis://localhost:6379/0")
        cache._client = mock_redis

        await cache.set("test_key", {"data": "value"}, ttl=3600)

        # Verify JSON serialization
        call_args = mock_redis.setex.call_args
        assert call_args is not None
        key, ttl, value = call_args[0]
        assert key == "test_key"
        assert ttl == 3600
        assert json.loads(value) == {"data": "value"}

    @pytest.mark.asyncio
    async def test_redis_cache_get_deserializes_from_json(self) -> None:
        """RedisCache.get should deserialize values from JSON."""
        from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=json.dumps({"data": "value"}))

        cache = RedisCache(redis_url="redis://localhost:6379/0")
        cache._client = mock_redis

        result = await cache.get("test_key")
        assert result == {"data": "value"}

    @pytest.mark.asyncio
    async def test_redis_cache_get_returns_none_for_missing_key(self) -> None:
        """RedisCache.get should return None for non-existent keys."""
        from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)

        cache = RedisCache(redis_url="redis://localhost:6379/0")
        cache._client = mock_redis

        result = await cache.get("non_existent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_redis_cache_delete_calls_redis_delete(self) -> None:
        """RedisCache.delete should call Redis delete."""
        from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

        mock_redis = MagicMock()
        mock_redis.delete = AsyncMock()

        cache = RedisCache(redis_url="redis://localhost:6379/0")
        cache._client = mock_redis

        await cache.delete("key_to_delete")
        mock_redis.delete.assert_called_once_with("key_to_delete")

    @pytest.mark.asyncio
    async def test_redis_cache_exists_returns_boolean(self) -> None:
        """RedisCache.exists should return a boolean."""
        from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

        mock_redis = MagicMock()
        mock_redis.exists = AsyncMock(return_value=1)

        cache = RedisCache(redis_url="redis://localhost:6379/0")
        cache._client = mock_redis

        result = await cache.exists("existing_key")
        assert result is True

    @pytest.mark.asyncio
    async def test_redis_cache_clear_uses_flushdb(self) -> None:
        """RedisCache.clear should use flushdb."""
        from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

        mock_redis = MagicMock()
        mock_redis.flushdb = AsyncMock()

        cache = RedisCache(redis_url="redis://localhost:6379/0")
        cache._client = mock_redis

        await cache.clear()
        mock_redis.flushdb.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_cache_health_check_uses_ping(self) -> None:
        """RedisCache.health_check should use ping."""
        from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

        mock_redis = MagicMock()
        mock_redis.ping = AsyncMock(return_value=True)

        cache = RedisCache(redis_url="redis://localhost:6379/0")
        cache._client = mock_redis

        result = await cache.health_check()
        assert result is True
        mock_redis.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_cache_health_check_returns_false_on_error(self) -> None:
        """RedisCache.health_check should return False on connection error."""
        from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

        mock_redis = MagicMock()
        mock_redis.ping = AsyncMock(side_effect=Exception("Connection refused"))

        cache = RedisCache(redis_url="redis://localhost:6379/0")
        cache._client = mock_redis

        result = await cache.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_redis_cache_uses_default_ttl_when_not_specified(self) -> None:
        """RedisCache.set should use default TTL when not specified."""
        from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

        mock_redis = MagicMock()
        mock_redis.setex = AsyncMock()

        cache = RedisCache(redis_url="redis://localhost:6379/0", default_ttl=7200)
        cache._client = mock_redis

        await cache.set("test_key", {"data": "value"})

        call_args = mock_redis.setex.call_args
        assert call_args is not None
        _, ttl, _ = call_args[0]
        assert ttl == 7200


class TestCacheGracefulDegradation:
    """Test cases for graceful degradation from Redis to Memory cache."""

    @pytest.mark.asyncio
    async def test_redis_cache_connect_raises_on_failure(self) -> None:
        """RedisCache.connect should raise CacheConnectionError on failure."""
        from smart_file_manager.core.exceptions import CacheConnectionError
        from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

        cache = RedisCache(redis_url="redis://invalid-host:6379/0")

        with pytest.raises(CacheConnectionError):
            await cache.connect()

    @pytest.mark.asyncio
    async def test_redis_cache_has_is_connected_property(self) -> None:
        """RedisCache should have is_connected property."""
        from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

        cache = RedisCache(redis_url="redis://localhost:6379/0")
        assert hasattr(cache, "is_connected")
        assert cache.is_connected is False


class TestRedisCacheWithoutClient:
    """Test cases for RedisCache when client is None (not connected)."""

    @pytest.mark.asyncio
    async def test_redis_cache_get_returns_none_when_not_connected(self) -> None:
        """RedisCache.get should return None when client is None."""
        from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

        cache = RedisCache(redis_url="redis://localhost:6379/0")
        # _client is None by default
        result = await cache.get("any_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_redis_cache_set_does_nothing_when_not_connected(self) -> None:
        """RedisCache.set should do nothing when client is None."""
        from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

        cache = RedisCache(redis_url="redis://localhost:6379/0")
        # Should not raise
        await cache.set("any_key", "any_value")

    @pytest.mark.asyncio
    async def test_redis_cache_delete_does_nothing_when_not_connected(self) -> None:
        """RedisCache.delete should do nothing when client is None."""
        from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

        cache = RedisCache(redis_url="redis://localhost:6379/0")
        # Should not raise
        await cache.delete("any_key")

    @pytest.mark.asyncio
    async def test_redis_cache_exists_returns_false_when_not_connected(self) -> None:
        """RedisCache.exists should return False when client is None."""
        from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

        cache = RedisCache(redis_url="redis://localhost:6379/0")
        result = await cache.exists("any_key")
        assert result is False

    @pytest.mark.asyncio
    async def test_redis_cache_clear_does_nothing_when_not_connected(self) -> None:
        """RedisCache.clear should do nothing when client is None."""
        from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

        cache = RedisCache(redis_url="redis://localhost:6379/0")
        # Should not raise
        await cache.clear()

    @pytest.mark.asyncio
    async def test_redis_cache_health_check_returns_false_when_not_connected(self) -> None:
        """RedisCache.health_check should return False when client is None."""
        from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

        cache = RedisCache(redis_url="redis://localhost:6379/0")
        result = await cache.health_check()
        assert result is False


class TestRedisCacheJsonHandling:
    """Test cases for RedisCache JSON handling edge cases."""

    @pytest.mark.asyncio
    async def test_redis_cache_get_returns_raw_value_on_json_decode_error(self) -> None:
        """RedisCache.get should return raw value if JSON decode fails."""
        from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

        mock_redis = MagicMock()
        # Return invalid JSON
        mock_redis.get = AsyncMock(return_value="not valid json {")

        cache = RedisCache(redis_url="redis://localhost:6379/0")
        cache._client = mock_redis

        result = await cache.get("test_key")
        assert result == "not valid json {"

    @pytest.mark.asyncio
    async def test_redis_cache_disconnect(self) -> None:
        """RedisCache.disconnect should close the connection."""
        from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

        mock_redis = MagicMock()
        mock_redis.close = AsyncMock()

        cache = RedisCache(redis_url="redis://localhost:6379/0")
        cache._client = mock_redis
        cache._is_connected = True

        await cache.disconnect()
        mock_redis.close.assert_called_once()
        assert cache.is_connected is False


class TestMemoryCacheExpiredExists:
    """Test cases for MemoryCache exists with expired entries."""

    @pytest.mark.asyncio
    async def test_memory_cache_exists_returns_false_for_expired_entry(self) -> None:
        """MemoryCache.exists should return False for expired entries."""
        from smart_file_manager.infrastructure.cache.memory_cache import MemoryCache

        cache = MemoryCache()
        await cache.set("expiring_key", "value", ttl=0)
        await asyncio.sleep(0.1)
        result = await cache.exists("expiring_key")
        assert result is False
