"""Token 黑名单测试"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta, UTC

from app.security.token_blacklist import TokenBlacklist


class TestTokenBlacklist:
    """TokenBlacklist 类测试"""
    
    @pytest.fixture
    def mock_redis_client(self):
        """模拟 Redis 客户端"""
        with patch('app.security.token_blacklist.redis_client') as mock:
            mock.set = AsyncMock()
            mock.get = AsyncMock(return_value=None)
            mock.delete = AsyncMock()
            mock.exists = AsyncMock(return_value=False)
            mock.client = AsyncMock()
            mock.client.ttl = AsyncMock(return_value=-2)
            yield mock

    @pytest.fixture
    def valid_token(self):
        """生成有效的测试 Token"""
        from app.security import create_access_token
        return create_access_token({"sub": "testuser", "jti": "test-jti-123"})

    def test_add_token_to_blacklist(self, mock_redis_client, valid_token):
        """测试将 Token 加入黑名单"""
        import asyncio
        asyncio.get_event_loop().run_until_complete(
            TokenBlacklist.add(valid_token)
        )
        mock_redis_client.set.assert_called_once()

    def test_add_invalid_token(self, mock_redis_client):
        """测试添加无效 Token"""
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            TokenBlacklist.add("invalid.token")
        )
        assert result is False

    def test_is_blacklisted_true(self, mock_redis_client, valid_token):
        """测试检查黑名单中的 Token"""
        mock_redis_client.exists = AsyncMock(return_value=True)
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            TokenBlacklist.is_blacklisted(valid_token)
        )
        assert result is True

    def test_is_blacklisted_false(self, mock_redis_client, valid_token):
        """测试检查不在黑名单中的 Token"""
        mock_redis_client.exists = AsyncMock(return_value=False)
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            TokenBlacklist.is_blacklisted(valid_token)
        )
        assert result is False

    def test_is_blacklisted_invalid_token(self, mock_redis_client):
        """测试检查无效 Token"""
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            TokenBlacklist.is_blacklisted("invalid.token")
        )
        assert result is True

    def test_remove_token_from_blacklist(self, mock_redis_client, valid_token):
        """测试从黑名单移除 Token"""
        import asyncio
        asyncio.get_event_loop().run_until_complete(
            TokenBlacklist.remove(valid_token)
        )
        mock_redis_client.delete.assert_called_once()

    def test_remove_invalid_token(self, mock_redis_client):
        """测试移除无效 Token"""
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            TokenBlacklist.remove("invalid.token")
        )
        assert result is False

    def test_get_ttl(self, mock_redis_client, valid_token):
        """测试获取 TTL"""
        mock_redis_client.client.ttl = AsyncMock(return_value=3600)
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            TokenBlacklist.get_ttl(valid_token)
        )
        assert result == 3600

    def test_get_ttl_not_in_blacklist(self, mock_redis_client, valid_token):
        """测试获取不在黑名单中的 TTL"""
        mock_redis_client.client.ttl = AsyncMock(return_value=-2)
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            TokenBlacklist.get_ttl(valid_token)
        )
        assert result is None

    def test_get_ttl_expired(self, mock_redis_client, valid_token):
        """测试获取已过期的 TTL"""
        mock_redis_client.client.ttl = AsyncMock(return_value=-1)
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            TokenBlacklist.get_ttl(valid_token)
        )
        assert result is None

    def test_each_token_has_unique_jti(self):
        """测试每个 Token 有唯一的 jti"""
        from app.security import create_access_token, decode_access_token
        
        token1 = create_access_token({"sub": "user1"})
        token2 = create_access_token({"sub": "user1"})
        
        payload1 = decode_access_token(token1)
        payload2 = decode_access_token(token2)
        
        assert payload1["jti"] != payload2["jti"]

    def test_logout_does_not_affect_new_token(self, mock_redis_client):
        """测试登出不影响新 Token"""
        from app.security import create_access_token, decode_access_token
        import asyncio
        
        token1 = create_access_token({"sub": "user1"})
        token2 = create_access_token({"sub": "user1"})
        
        asyncio.get_event_loop().run_until_complete(
            TokenBlacklist.add(token1)
        )
        
        payload1 = decode_access_token(token1)
        payload2 = decode_access_token(token2)
        
        assert payload1["jti"] != payload2["jti"]
