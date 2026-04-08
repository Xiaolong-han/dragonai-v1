"""
认证 API 端点测试

测试覆盖:
- POST /api/v1/auth/register - 用户注册
- POST /api/v1/auth/login - 用户登录
- GET /api/v1/auth/me - 获取当前用户信息
- POST /api/v1/auth/logout - 用户登出

测试类型:
- 正向测试: 验证正常流程
- 异常测试: 验证错误处理
- 边界测试: 验证参数边界

响应格式:
- 成功: {code: 0, message: "...", data: {...}}
- 错误: {code: ERROR_CODE, message: "...", data: null|details}
"""

import pytest
import pytest_asyncio
from datetime import timedelta
from unittest.mock import patch, AsyncMock


class TestAuthRegister:
    """用户注册 API 测试"""

    @pytest.mark.asyncio
    async def test_register_user_with_valid_data_returns_200(self, client, test_user_data):
        """正向测试: 使用有效数据注册用户应返回 200"""
        response = await client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["username"] == test_user_data["username"]
        assert data["data"]["email"] == test_user_data["email"]
        assert "id" in data["data"]
        assert "hashed_password" not in data["data"]
        assert data["data"]["is_active"] is True

    @pytest.mark.asyncio
    async def test_register_user_with_existing_username_returns_409(self, client, test_user_data):
        """异常测试: 使用已存在的用户名注册应返回 409"""
        # 首先注册一个用户
        await client.post("/api/v1/auth/register", json=test_user_data)

        # 尝试用相同用户名再次注册
        response = await client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 409
        assert "用户名已被注册" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_register_user_with_existing_email_returns_409(self, client, test_user_data):
        """异常测试: 使用已存在的邮箱注册应返回 409"""
        # 首先注册一个用户
        await client.post("/api/v1/auth/register", json=test_user_data)

        # 尝试用相同邮箱但不同用户名注册
        new_user_data = {
            "username": "differentuser",
            "email": test_user_data["email"],
            "password": "password123"
        }
        response = await client.post("/api/v1/auth/register", json=new_user_data)

        assert response.status_code == 409
        assert "邮箱已被注册" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_register_user_with_short_username_returns_422(self, client):
        """边界测试: 用户名少于3个字符应返回 422"""
        user_data = {
            "username": "ab",  # 少于3个字符
            "email": "test@example.com",
            "password": "password123"
        }
        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_user_with_long_username_returns_422(self, client):
        """边界测试: 用户名超过50个字符应返回 422"""
        user_data = {
            "username": "a" * 51,  # 超过50个字符
            "email": "test@example.com",
            "password": "password123"
        }
        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_user_with_short_password_returns_422(self, client):
        """边界测试: 密码少于6个字符应返回 422"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "12345"  # 少于6个字符
        }
        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_user_with_invalid_email_returns_422(self, client):
        """边界测试: 无效邮箱格式应返回 422"""
        user_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "password123"
        }
        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_user_without_email_returns_200(self, client):
        """边界测试: 不提供邮箱（可选字段）应成功注册"""
        user_data = {
            "username": "testuser_no_email",
            "password": "password123"
        }
        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["email"] is None


class TestAuthLogin:
    """用户登录 API 测试"""

    @pytest.mark.asyncio
    async def test_login_with_valid_credentials_returns_token(self, client, test_user_data):
        """正向测试: 使用有效凭据登录应返回 Token"""
        # 先注册用户
        await client.post("/api/v1/auth/register", json=test_user_data)

        # 登录
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        assert len(data["data"]["access_token"]) > 0

    @pytest.mark.asyncio
    async def test_login_with_wrong_password_returns_401(self, client, test_user_data):
        """异常测试: 使用错误密码登录应返回 401"""
        # 先注册用户
        await client.post("/api/v1/auth/register", json=test_user_data)

        # 使用错误密码登录
        login_data = {
            "username": test_user_data["username"],
            "password": "wrongpassword"
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_login_with_nonexistent_user_returns_401(self, client):
        """异常测试: 使用不存在的用户名登录应返回 401"""
        login_data = {
            "username": "nonexistentuser",
            "password": "password123"
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_login_with_empty_username_returns_401(self, client):
        """边界测试: 空用户名应返回 401（认证失败）"""
        login_data = {
            "username": "",
            "password": "password123"
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_with_empty_password_returns_401(self, client):
        """边界测试: 空密码应返回 401（认证失败）"""
        login_data = {
            "username": "testuser",
            "password": ""
        }
        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401


class TestAuthMe:
    """获取当前用户信息 API 测试"""

    @pytest.mark.asyncio
    async def test_get_current_user_with_valid_token_returns_user_info(self, client, test_user_data, auth_token):
        """正向测试: 使用有效 Token 获取当前用户信息"""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["username"] == test_user_data["username"]
        assert data["data"]["email"] == test_user_data["email"]
        assert "id" in data["data"]
        assert "is_active" in data["data"]
        assert "is_superuser" in data["data"]

    @pytest.mark.asyncio
    async def test_get_current_user_without_token_returns_401(self, client):
        """异常测试: 未提供 Token 应返回 401"""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_with_invalid_token_returns_401(self, client):
        """异常测试: 使用无效 Token 应返回 401"""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_with_expired_token_returns_401(self, client, test_user_data):
        """异常测试: 使用过期 Token 应返回 401"""
        from app.security import create_access_token

        # 先注册用户
        await client.post("/api/v1/auth/register", json=test_user_data)

        # 创建已过期 Token
        expired_token = create_access_token(
            data={"sub": test_user_data["username"]},
            expires_delta=timedelta(minutes=-1)  # 已过期
        )

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_with_blacklisted_token_returns_401(self, client, test_user_data, auth_token, mocker):
        """异常测试: 使用已加入黑名单的 Token 应返回 401"""
        from unittest.mock import AsyncMock

        # Mock TokenBlacklist.is_blacklisted 返回 True (在 API 依赖中使用的路径)
        mocker.patch('app.api.dependencies.TokenBlacklist.is_blacklisted', new_callable=AsyncMock, return_value=True)

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 401
        # HTTPException 返回 detail 字段
        data = response.json()
        assert "detail" in data or "message" in data


class TestAuthLogout:
    """用户登出 API 测试"""

    @pytest.mark.asyncio
    async def test_logout_with_valid_token_returns_success(self, client, auth_token):
        """正向测试: 使用有效 Token 登出应成功"""
        response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "登出" in data["message"]

    @pytest.mark.asyncio
    async def test_logout_without_token_returns_401(self, client):
        """异常测试: 未提供 Token 登出应返回 401"""
        response = await client.post("/api/v1/auth/logout")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_makes_token_invalid(self, client, test_user_data, auth_token, mocker):
        """验证测试: 登出后 Token 应失效"""
        from unittest.mock import AsyncMock

        # 先验证 Token 有效
        response1 = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response1.status_code == 200

        # 登出
        await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Mock TokenBlacklist.is_blacklisted 返回 True 模拟 Token 已失效 (在 API 依赖中使用的路径)
        mocker.patch('app.api.dependencies.TokenBlacklist.is_blacklisted', new_callable=AsyncMock, return_value=True)

        # 验证 Token 已失效
        response2 = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response2.status_code == 401