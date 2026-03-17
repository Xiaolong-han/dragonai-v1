"""
会话 API 端点测试

测试覆盖:
- GET /api/v1/conversations - 获取会话列表
- GET /api/v1/conversations/{id} - 获取单个会话
- POST /api/v1/conversations - 创建会话
- PUT /api/v1/conversations/{id} - 更新会话
- DELETE /api/v1/conversations/{id} - 删除会话
- POST /api/v1/conversations/{id}/pin - 置顶会话
- POST /api/v1/conversations/{id}/unpin - 取消置顶会话

测试类型:
- 正向测试: 验证正常流程
- 异常测试: 验证错误处理
- 边界测试: 验证参数边界
- 安全测试: 验证用户隔离
"""

import pytest
import pytest_asyncio


class TestGetConversations:
    """获取会话列表 API 测试"""

    @pytest.mark.asyncio
    async def test_get_conversations_with_valid_token_returns_list(self, authenticated_client):
        """正向测试: 使用有效 Token 获取会话列表"""
        # 创建几个会话
        for i in range(3):
            await authenticated_client.post(
                "/api/v1/conversations",
                json={"title": f"Test Conversation {i}"}
            )
        
        response = await authenticated_client.get("/api/v1/conversations")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_get_conversations_pagination_with_skip_limit(self, authenticated_client):
        """边界测试: 分页参数 skip 和 limit"""
        # 创建5个会话
        for i in range(5):
            await authenticated_client.post(
                "/api/v1/conversations",
                json={"title": f"Test Conversation {i}"}
            )
        
        # 测试 skip=2, limit=2
        response = await authenticated_client.get("/api/v1/conversations?skip=2&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_conversations_with_negative_skip_returns_422(self, authenticated_client):
        """边界测试: 负数 skip 应返回 422"""
        response = await authenticated_client.get("/api/v1/conversations?skip=-1")
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_conversations_with_zero_limit_returns_422(self, authenticated_client):
        """边界测试: limit 为 0 应返回 422"""
        response = await authenticated_client.get("/api/v1/conversations?limit=0")
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_conversations_with_exceeding_limit_returns_422(self, authenticated_client):
        """边界测试: limit 超过最大值应返回 422"""
        response = await authenticated_client.get("/api/v1/conversations?limit=101")
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_conversations_without_auth_returns_401(self, client):
        """安全测试: 未认证访问应返回 401"""
        response = await client.get("/api/v1/conversations")
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_conversations_only_returns_own_conversations(self, client, test_user_data):
        """安全测试: 只能获取自己的会话"""
        # 注册用户1并创建会话
        await client.post("/api/v1/auth/register", json=test_user_data)
        login1 = await client.post("/api/v1/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        token1 = login1.json()["access_token"]
        
        # 用户1创建会话
        await client.post(
            "/api/v1/conversations",
            json={"title": "User1 Conversation"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        
        # 注册用户2
        user2_data = {
            "username": "user2",
            "email": "user2@example.com",
            "password": "password123"
        }
        await client.post("/api/v1/auth/register", json=user2_data)
        login2 = await client.post("/api/v1/auth/login", json={
            "username": user2_data["username"],
            "password": user2_data["password"]
        })
        token2 = login2.json()["access_token"]
        
        # 用户2获取会话列表
        response = await client.get(
            "/api/v1/conversations",
            headers={"Authorization": f"Bearer {token2}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0  # 用户2没有会话


class TestGetConversation:
    """获取单个会话 API 测试"""

    @pytest.mark.asyncio
    async def test_get_conversation_with_valid_id_returns_conversation(self, authenticated_client, test_conversation):
        """正向测试: 使用有效 ID 获取会话"""
        response = await authenticated_client.get(f"/api/v1/conversations/{test_conversation['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_conversation["id"]
        assert data["title"] == test_conversation["title"]
        assert "user_id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_conversation_not_found_returns_404(self, authenticated_client):
        """异常测试: 获取不存在的会话应返回 404"""
        response = await authenticated_client.get("/api/v1/conversations/99999")
        
        assert response.status_code == 404
        assert "Conversation not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_conversation_wrong_user_returns_404(self, client, test_user_data):
        """安全测试: 访问其他用户的会话应返回 404"""
        # 注册用户1并创建会话
        await client.post("/api/v1/auth/register", json=test_user_data)
        login1 = await client.post("/api/v1/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        token1 = login1.json()["access_token"]
        
        # 用户1创建会话
        conv_response = await client.post(
            "/api/v1/conversations",
            json={"title": "User1 Conversation"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        conv_id = conv_response.json()["id"]
        
        # 注册用户2
        user2_data = {
            "username": "user2",
            "email": "user2@example.com",
            "password": "password123"
        }
        await client.post("/api/v1/auth/register", json=user2_data)
        login2 = await client.post("/api/v1/auth/login", json={
            "username": user2_data["username"],
            "password": user2_data["password"]
        })
        token2 = login2.json()["access_token"]
        
        # 用户2尝试访问用户1的会话
        response = await client.get(
            f"/api/v1/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {token2}"}
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_conversation_without_auth_returns_401(self, client):
        """安全测试: 未认证访问应返回 401"""
        response = await client.get("/api/v1/conversations/1")
        
        assert response.status_code == 401


class TestCreateConversation:
    """创建会话 API 测试"""

    @pytest.mark.asyncio
    async def test_create_conversation_with_valid_data_returns_201(self, authenticated_client):
        """正向测试: 使用有效数据创建会话"""
        conversation_data = {
            "title": "New Test Conversation",
            "model_name": "qwen-flash"
        }
        
        response = await authenticated_client.post("/api/v1/conversations", json=conversation_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == conversation_data["title"]
        assert data["model_name"] == conversation_data["model_name"]
        assert "id" in data
        assert "user_id" in data
        assert data["is_pinned"] is False

    @pytest.mark.asyncio
    async def test_create_conversation_without_model_name_returns_201(self, authenticated_client):
        """边界测试: 不提供 model_name（可选字段）应成功创建"""
        conversation_data = {
            "title": "Conversation without model"
        }
        
        response = await authenticated_client.post("/api/v1/conversations", json=conversation_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == conversation_data["title"]
        assert data["model_name"] is None

    @pytest.mark.asyncio
    async def test_create_conversation_with_empty_title_returns_201(self, authenticated_client):
        """边界测试: 空标题是允许的（虽然不建议）"""
        conversation_data = {
            "title": ""
        }
        
        response = await authenticated_client.post("/api/v1/conversations", json=conversation_data)
        
        # 空字符串是有效的（虽然没有实际意义）
        assert response.status_code == 201
        assert response.json()["title"] == ""

    @pytest.mark.asyncio
    async def test_create_conversation_with_long_title_returns_422(self, authenticated_client):
        """边界测试: 标题超过200字符应返回 422"""
        conversation_data = {
            "title": "a" * 201
        }
        
        response = await authenticated_client.post("/api/v1/conversations", json=conversation_data)
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_conversation_without_auth_returns_401(self, client):
        """安全测试: 未认证创建会话应返回 401"""
        conversation_data = {
            "title": "Test Conversation"
        }
        
        response = await client.post("/api/v1/conversations", json=conversation_data)
        
        assert response.status_code == 401


class TestUpdateConversation:
    """更新会话 API 测试"""

    @pytest.mark.asyncio
    async def test_update_conversation_with_valid_data_returns_updated(self, authenticated_client, test_conversation):
        """正向测试: 使用有效数据更新会话"""
        update_data = {
            "title": "Updated Title",
            "is_pinned": True
        }
        
        response = await authenticated_client.put(
            f"/api/v1/conversations/{test_conversation['id']}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["is_pinned"] is True

    @pytest.mark.asyncio
    async def test_update_conversation_partial_fields(self, authenticated_client, test_conversation):
        """边界测试: 只更新部分字段"""
        update_data = {
            "title": "Only Title Updated"
        }
        
        response = await authenticated_client.put(
            f"/api/v1/conversations/{test_conversation['id']}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        # 其他字段保持不变
        assert data["model_name"] == test_conversation["model_name"]

    @pytest.mark.asyncio
    async def test_update_conversation_not_found_returns_404(self, authenticated_client):
        """异常测试: 更新不存在的会话应返回 404"""
        update_data = {"title": "Updated Title"}
        
        response = await authenticated_client.put(
            "/api/v1/conversations/99999",
            json=update_data
        )
        
        assert response.status_code == 404
        assert "Conversation not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_conversation_wrong_user_returns_404(self, client, test_user_data):
        """安全测试: 更新其他用户的会话应返回 404"""
        # 注册用户1并创建会话
        await client.post("/api/v1/auth/register", json=test_user_data)
        login1 = await client.post("/api/v1/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        token1 = login1.json()["access_token"]
        
        conv_response = await client.post(
            "/api/v1/conversations",
            json={"title": "User1 Conversation"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        conv_id = conv_response.json()["id"]
        
        # 注册用户2
        user2_data = {
            "username": "user2",
            "email": "user2@example.com",
            "password": "password123"
        }
        await client.post("/api/v1/auth/register", json=user2_data)
        login2 = await client.post("/api/v1/auth/login", json={
            "username": user2_data["username"],
            "password": user2_data["password"]
        })
        token2 = login2.json()["access_token"]
        
        # 用户2尝试更新用户1的会话
        response = await client.put(
            f"/api/v1/conversations/{conv_id}",
            json={"title": "Hacked Title"},
            headers={"Authorization": f"Bearer {token2}"}
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_conversation_without_auth_returns_401(self, client):
        """安全测试: 未认证更新会话应返回 401"""
        update_data = {"title": "Updated Title"}
        
        # 使用任意 ID 测试未认证访问
        response = await client.put(
            "/api/v1/conversations/1",
            json=update_data
        )
        
        assert response.status_code == 401


class TestDeleteConversation:
    """删除会话 API 测试"""

    @pytest.mark.asyncio
    async def test_delete_conversation_with_valid_id_returns_204(self, authenticated_client):
        """正向测试: 删除存在的会话应返回 204"""
        # 创建会话
        conv_response = await authenticated_client.post(
            "/api/v1/conversations",
            json={"title": "To Be Deleted"}
        )
        conv_id = conv_response.json()["id"]
        
        # 删除会话
        response = await authenticated_client.delete(f"/api/v1/conversations/{conv_id}")
        
        assert response.status_code == 204
        
        # 验证已删除
        get_response = await authenticated_client.get(f"/api/v1/conversations/{conv_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_conversation_not_found_returns_404(self, authenticated_client):
        """异常测试: 删除不存在的会话应返回 404"""
        response = await authenticated_client.delete("/api/v1/conversations/99999")
        
        assert response.status_code == 404
        assert "Conversation not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_conversation_wrong_user_returns_404(self, client, test_user_data):
        """安全测试: 删除其他用户的会话应返回 404"""
        # 注册用户1并创建会话
        await client.post("/api/v1/auth/register", json=test_user_data)
        login1 = await client.post("/api/v1/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        token1 = login1.json()["access_token"]
        
        conv_response = await client.post(
            "/api/v1/conversations",
            json={"title": "User1 Conversation"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        conv_id = conv_response.json()["id"]
        
        # 注册用户2
        user2_data = {
            "username": "user2",
            "email": "user2@example.com",
            "password": "password123"
        }
        await client.post("/api/v1/auth/register", json=user2_data)
        login2 = await client.post("/api/v1/auth/login", json={
            "username": user2_data["username"],
            "password": user2_data["password"]
        })
        token2 = login2.json()["access_token"]
        
        # 用户2尝试删除用户1的会话
        response = await client.delete(
            f"/api/v1/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {token2}"}
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_conversation_without_auth_returns_401(self, client):
        """安全测试: 未认证删除会话应返回 401"""
        response = await client.delete("/api/v1/conversations/1")
        
        assert response.status_code == 401


class TestPinConversation:
    """置顶/取消置顶会话 API 测试"""

    @pytest.mark.asyncio
    async def test_pin_conversation_returns_pinned(self, authenticated_client, test_conversation):
        """正向测试: 置顶会话"""
        response = await authenticated_client.post(
            f"/api/v1/conversations/{test_conversation['id']}/pin"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_pinned"] is True

    @pytest.mark.asyncio
    async def test_unpin_conversation_returns_unpinned(self, authenticated_client, test_conversation):
        """正向测试: 取消置顶会话"""
        # 先置顶
        await authenticated_client.post(f"/api/v1/conversations/{test_conversation['id']}/pin")
        
        # 再取消置顶
        response = await authenticated_client.post(
            f"/api/v1/conversations/{test_conversation['id']}/unpin"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_pinned"] is False

    @pytest.mark.asyncio
    async def test_pin_conversation_not_found_returns_404(self, authenticated_client):
        """异常测试: 置顶不存在的会话应返回 404"""
        response = await authenticated_client.post("/api/v1/conversations/99999/pin")
        
        assert response.status_code == 404
        assert "Conversation not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_unpin_conversation_not_found_returns_404(self, authenticated_client):
        """异常测试: 取消置顶不存在的会话应返回 404"""
        response = await authenticated_client.post("/api/v1/conversations/99999/unpin")
        
        assert response.status_code == 404
        assert "Conversation not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_pin_conversation_wrong_user_returns_404(self, client, test_user_data):
        """安全测试: 置顶其他用户的会话应返回 404"""
        # 注册用户1并创建会话
        await client.post("/api/v1/auth/register", json=test_user_data)
        login1 = await client.post("/api/v1/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        token1 = login1.json()["access_token"]
        
        conv_response = await client.post(
            "/api/v1/conversations",
            json={"title": "User1 Conversation"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        conv_id = conv_response.json()["id"]
        
        # 注册用户2
        user2_data = {
            "username": "user2",
            "email": "user2@example.com",
            "password": "password123"
        }
        await client.post("/api/v1/auth/register", json=user2_data)
        login2 = await client.post("/api/v1/auth/login", json={
            "username": user2_data["username"],
            "password": user2_data["password"]
        })
        token2 = login2.json()["access_token"]
        
        # 用户2尝试置顶用户1的会话
        response = await client.post(
            f"/api/v1/conversations/{conv_id}/pin",
            headers={"Authorization": f"Bearer {token2}"}
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_pin_conversation_without_auth_returns_401(self, client):
        """安全测试: 未认证置顶会话应返回 401"""
        response = await client.post("/api/v1/conversations/1/pin")
        
        assert response.status_code == 401
