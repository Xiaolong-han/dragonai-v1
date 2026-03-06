
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from app.cache.redis import RedisClient, cache_aside, cached


class TestRedisClient:
    @pytest.fixture
    def mock_redis(self):
        with patch('app.cache.redis.redis') as mock:
            mock_client = AsyncMock()
            mock.from_url.return_value = mock_client
            yield mock_client

    @pytest.mark.asyncio
    async def test_connect(self, mock_redis):
        client = RedisClient()
        await client.connect()
        assert client._client is not None

    @pytest.mark.asyncio
    async def test_disconnect(self, mock_redis):
        client = RedisClient()
        await client.connect()
        await client.disconnect()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_get_set_string(self, mock_redis):
        mock_redis.get = AsyncMock(return_value="test_value")
        mock_redis.set = AsyncMock()
        
        client = RedisClient()
        client._client = mock_redis
        
        await client.set("test_key", "test_value")
        result = await client.get("test_key")
        
        assert result == "test_value"

    @pytest.mark.asyncio
    async def test_get_set_json(self, mock_redis):
        mock_redis.get = AsyncMock(return_value='{"key": "value"}')
        mock_redis.set = AsyncMock()
        
        client = RedisClient()
        client._client = mock_redis
        
        await client.set("test_key", {"key": "value"})
        result = await client.get("test_key")
        
        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_delete(self, mock_redis):
        mock_redis.delete = AsyncMock()
        
        client = RedisClient()
        client._client = mock_redis
        
        await client.delete("test_key")
        mock_redis.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_exists(self, mock_redis):
        mock_redis.exists = AsyncMock(return_value=1)
        
        client = RedisClient()
        client._client = mock_redis
        
        result = await client.exists("test_key")
        assert result is True


class TestCacheAside:
    @pytest.fixture
    def mock_redis_client(self):
        with patch('app.cache.redis.redis_client') as mock:
            mock.get = AsyncMock(return_value=None)
            mock.set = AsyncMock()
            mock.exists = AsyncMock(return_value=False)
            mock.acquire_lock = AsyncMock(return_value=True)
            mock.release_lock = AsyncMock()
            yield mock

    @pytest.mark.asyncio
    async def test_cache_aside_miss(self, mock_redis_client):
        """测试缓存未命中"""
        async def data_func():
            return {"data": "test"}
        
        result = await cache_aside(
            key="test_key",
            ttl=3600,
            data_func=data_func
        )
        
        assert result == {"data": "test"}

    @pytest.mark.asyncio
    async def test_cache_aside_hit(self, mock_redis_client):
        """测试缓存命中"""
        mock_redis_client.get = AsyncMock(return_value={"data": "cached"})
        
        result = await cache_aside(
            key="test_key",
            ttl=3600,
            data_func=lambda: {"data": "new"}
        )
        
        assert result == {"data": "cached"}

    @pytest.mark.asyncio
    async def test_cache_aside_no_data_func(self, mock_redis_client):
        """测试无数据函数"""
        result = await cache_aside(key="test_key", ttl=3600)
        assert result is None
