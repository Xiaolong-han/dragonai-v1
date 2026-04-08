"""缓存模块测试 - 补充测试"""

import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock

from app.cache.redis import RedisClient, cache_aside, cached, NULL_VALUE_MARKER
from app.cache.metrics import CacheMetrics, cache_metrics


class TestRedisClient:
    """RedisClient 测试"""

    def test_init(self):
        """测试初始化"""
        client = RedisClient()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_connect(self):
        """测试连接"""
        client = RedisClient()
        with patch('app.cache.redis.redis.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_from_url.return_value = mock_redis

            await client.connect()

            assert client._client is not None

    @pytest.mark.asyncio
    async def test_get_json_value(self):
        """测试获取 JSON 值"""
        client = RedisClient()
        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value='{"key": "value"}')

        result = await client.get("test_key")

        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_string_value(self):
        """测试获取字符串值"""
        client = RedisClient()
        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value="plain string")

        result = await client.get("test_key")

        assert result == "plain string"

    @pytest.mark.asyncio
    async def test_get_none_value(self):
        """测试获取空值"""
        client = RedisClient()
        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value=None)

        result = await client.get("test_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_set_dict_value(self):
        """测试设置字典值"""
        client = RedisClient()
        client._client = AsyncMock()
        client._client.set = AsyncMock()

        await client.set("test_key", {"key": "value"}, ttl=3600)

        client._client.set.assert_called_once()
        call_args = client._client.set.call_args
        assert call_args[1]["ex"] == 3600

    @pytest.mark.asyncio
    async def test_delete(self):
        """测试删除键"""
        client = RedisClient()
        client._client = AsyncMock()
        client._client.delete = AsyncMock()

        await client.delete("test_key")

        client._client.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_exists(self):
        """测试键存在检查"""
        client = RedisClient()
        client._client = AsyncMock()
        client._client.exists = AsyncMock(return_value=1)

        result = await client.exists("test_key")

        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_lock_success(self):
        """测试获取锁成功"""
        client = RedisClient()
        client._client = AsyncMock()
        client._client.set = AsyncMock(return_value=True)

        result = await client.acquire_lock("lock:test", expire_seconds=10)

        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_lock_failed(self):
        """测试获取锁失败"""
        client = RedisClient()
        client._client = AsyncMock()
        client._client.set = AsyncMock(return_value=False)

        result = await client.acquire_lock("lock:test")

        assert result is False

    @pytest.mark.asyncio
    async def test_release_lock(self):
        """测试释放锁"""
        client = RedisClient()
        client._client = AsyncMock()
        client._client.delete = AsyncMock()

        await client.release_lock("lock:test")

        client._client.delete.assert_called_once_with("lock:test")


class TestCacheAside:
    """cache_aside 函数测试"""

    @pytest.mark.asyncio
    async def test_cache_hit(self):
        """测试缓存命中"""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value={"data": "cached"})

        with patch('app.cache.redis.redis_client', mock_redis):
            result = await cache_aside(
                key="test_key",
                ttl=3600,
                data_func=AsyncMock(return_value="new_data")
            )

        assert result == {"data": "cached"}

    @pytest.mark.asyncio
    async def test_cache_miss(self):
        """测试缓存未命中"""
        call_count = 0

        async def data_func():
            nonlocal call_count
            call_count += 1
            return "new_data"

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=[None, None])  # 两次检查都未命中
        mock_redis.set = AsyncMock()
        mock_redis.acquire_lock = AsyncMock(return_value=True)
        mock_redis.release_lock = AsyncMock()

        with patch('app.cache.redis.redis_client', mock_redis):
            result = await cache_aside(
                key="test_key",
                ttl=3600,
                data_func=data_func,
                enable_random_ttl=False
            )

        assert result == "new_data"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_cache_null_value(self):
        """测试缓存空值（防穿透）"""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()
        mock_redis.acquire_lock = AsyncMock(return_value=True)
        mock_redis.release_lock = AsyncMock()

        with patch('app.cache.redis.redis_client', mock_redis):
            result = await cache_aside(
                key="test_key",
                ttl=3600,
                data_func=AsyncMock(return_value=None),
                enable_null_cache=True
            )

        assert result is None
        # 验证设置了空值标记
        set_calls = mock_redis.set.call_args_list
        assert any(NULL_VALUE_MARKER in str(call) for call in set_calls)

    @pytest.mark.asyncio
    async def test_cache_hit_null_marker(self):
        """测试命中空值标记"""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=NULL_VALUE_MARKER)

        with patch('app.cache.redis.redis_client', mock_redis):
            result = await cache_aside(
                key="test_key",
                ttl=3600,
                data_func=AsyncMock(return_value="should_not_call")
            )

        assert result is None


class TestCacheMetrics:
    """CacheMetrics 测试"""

    def test_record_hit(self):
        """测试记录命中"""
        metrics = CacheMetrics()
        metrics.record_hit()
        metrics.record_hit()

        stats = metrics.get_stats()
        assert stats["hits"] == 2

    def test_record_miss(self):
        """测试记录未命中"""
        metrics = CacheMetrics()
        metrics.record_miss()

        stats = metrics.get_stats()
        assert stats["misses"] == 1

    def test_record_null_hit(self):
        """测试记录空值命中"""
        metrics = CacheMetrics()
        metrics.record_null_hit()

        stats = metrics.get_stats()
        assert stats["null_hits"] == 1

    def test_hit_rate(self):
        """测试命中率计算"""
        metrics = CacheMetrics()
        metrics.record_hit()
        metrics.record_hit()
        metrics.record_miss()

        stats = metrics.get_stats()
        assert stats["hit_rate"] == pytest.approx(66.67, rel=0.1)

    def test_reset(self):
        """测试重置"""
        metrics = CacheMetrics()
        metrics.record_hit()
        metrics.record_miss()

        metrics.reset()

        stats = metrics.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0

    def test_record_set_and_delete(self):
        """测试记录写入和删除操作"""
        metrics = CacheMetrics()

        metrics.record_set(success=True)
        metrics.record_set(success=False)
        metrics.record_delete(success=True)

        # 验证 Prometheus 指标被调用（不抛异常即可）
        assert True


class TestCachedDecorator:
    """cached 装饰器测试"""

    @pytest.mark.asyncio
    async def test_cached_decorator(self):
        """测试缓存装饰器"""
        call_count = 0

        @cached(ttl=3600, key_prefix="test")
        async def get_data(user_id: int):
            nonlocal call_count
            call_count += 1
            return {"user_id": user_id, "data": "test"}

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()
        mock_redis.acquire_lock = AsyncMock(return_value=True)
        mock_redis.release_lock = AsyncMock()

        with patch('app.cache.redis.redis_client', mock_redis):
            result = await get_data(user_id=1)

        assert result["user_id"] == 1
        assert call_count == 1