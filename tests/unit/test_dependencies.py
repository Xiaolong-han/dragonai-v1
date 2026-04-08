"""核心依赖注入测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.dependencies import (
    get_token_from_header,
    get_current_user,
    get_current_active_user,
)


class TestGetTokenFromHeader:
    """get_token_from_header 函数测试"""

    @pytest.mark.asyncio
    async def test_extract_token(self):
        """测试从 header 提取 token"""
        credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = "test-token-123"

        result = await get_token_from_header(credentials)
        assert result == "test-token-123"

    @pytest.mark.asyncio
    async def test_extract_different_token(self):
        """测试提取不同的 token"""
        credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        credentials.credentials = "another-token-xyz"

        result = await get_token_from_header(credentials)
        assert result == "another-token-xyz"


class TestGetCurrentUser:
    """get_current_user 函数测试"""

    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self):
        """测试有效 token 返回用户"""
        from app.models.user import User

        # Mock 数据
        mock_user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True
        )

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        with patch('app.core.dependencies.TokenBlacklist.is_blacklisted', return_value=False), \
             patch('app.core.dependencies.decode_access_token') as mock_decode:
            mock_decode.return_value = {"sub": "testuser"}

            result = await get_current_user(token="valid-token", db=mock_db)

        assert result == mock_user
        assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_blacklisted_token_raises_exception(self):
        """测试黑名单 token 抛出异常"""
        mock_db = AsyncMock()

        with patch('app.core.dependencies.TokenBlacklist.is_blacklisted', return_value=True):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token="blacklisted-token", db=mock_db)

        assert exc_info.value.status_code == 401
        assert "revoked" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_invalid_token_raises_exception(self):
        """测试无效 token 抛出异常"""
        mock_db = AsyncMock()

        with patch('app.core.dependencies.TokenBlacklist.is_blacklisted', return_value=False), \
             patch('app.core.dependencies.decode_access_token', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token="invalid-token", db=mock_db)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_token_without_sub_raises_exception(self):
        """测试没有 sub 的 token 抛出异常"""
        mock_db = AsyncMock()

        with patch('app.core.dependencies.TokenBlacklist.is_blacklisted', return_value=False), \
             patch('app.core.dependencies.decode_access_token', return_value={"other": "data"}):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token="token-no-sub", db=mock_db)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_user_not_found_raises_exception(self):
        """测试用户不存在抛出异常"""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch('app.core.dependencies.TokenBlacklist.is_blacklisted', return_value=False), \
             patch('app.core.dependencies.decode_access_token', return_value={"sub": "nonexistent"}):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token="valid-token", db=mock_db)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_none_sub_raises_exception(self):
        """测试 sub 为 None 抛出异常"""
        mock_db = AsyncMock()

        with patch('app.core.dependencies.TokenBlacklist.is_blacklisted', return_value=False), \
             patch('app.core.dependencies.decode_access_token', return_value={"sub": None}):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token="token", db=mock_db)

        assert exc_info.value.status_code == 401


class TestGetCurrentActiveUser:
    """get_current_active_user 函数测试"""

    def test_active_user_returns_user(self):
        """测试活跃用户返回用户"""
        from app.models.user import User

        mock_user = User(
            id=1,
            username="activeuser",
            email="active@example.com",
            hashed_password="hashed",
            is_active=True
        )

        result = asyncio.run(get_current_active_user(current_user=mock_user))
        assert result == mock_user

    def test_inactive_user_raises_exception(self):
        """测试非活跃用户抛出异常"""
        from app.models.user import User

        mock_user = User(
            id=1,
            username="inactiveuser",
            email="inactive@example.com",
            hashed_password="hashed",
            is_active=False
        )

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_active_user(current_user=mock_user))

        assert exc_info.value.status_code == 400
        assert "Inactive" in exc_info.value.detail


# 用于同步测试的 asyncio 导入
import asyncio