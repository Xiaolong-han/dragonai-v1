"""
聊天 API 端点测试

测试覆盖:
- GET /api/v1/chat/conversations/{id}/history - 获取聊天历史
- POST /api/v1/chat/send - 发送消息 (SSE 流)

测试类型:
- 正向测试: 验证正常流程
- 异常测试: 验证错误处理
- 边界测试: 验证参数边界
- 安全测试: 验证用户隔离

响应格式:
- 成功: {code: 0, message: "...", data: {...}}
- 错误: {code: ERROR_CODE, message: "...", data: null|details}
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock


# =============================================================================
# 辅助函数
# =============================================================================

def get_response_data(response):
    """从统一响应格式中提取 data"""
    json_data = response.json()
    if isinstance(json_data, dict) and "data" in json_data:
        return json_data["data"]
    return json_data


def get_access_token(login_response):
    """从登录响应中提取 token"""
    data = get_response_data(login_response)
    return data["access_token"]


def get_conversation_id(create_response):
    """从创建会话响应中提取 ID"""
    data = get_response_data(create_response)
    return data["id"]

async def _mock_sse_stream():
    """模拟 SSE 流"""
    yield b'data: {"type": "content", "content": "Hello"}\n\n'
    yield b'data: {"type": "done"}\n\n'


async def _mock_sse_stream_with_thinking():
    """模拟带思考过程的 SSE 流"""
    yield b'data: {"type": "thinking", "content": "Let me think..."}\n\n'
    yield b'data: {"type": "thinking_end"}\n\n'
    yield b'data: {"type": "content", "content": "Hello!"}\n\n'
    yield b'data: {"type": "done"}\n\n'


async def _mock_sse_stream_with_tool_call():
    """模拟带工具调用的 SSE 流"""
    yield b'data: {"type": "tool_call", "tool": "web_search", "input": "test query"}\n\n'
    yield b'data: {"type": "tool_result", "tool": "web_search", "output": "search results"}\n\n'
    yield b'data: {"type": "content", "content": "Based on search..."}\n\n'
    yield b'data: {"type": "done"}\n\n'


# =============================================================================
# 测试类
# =============================================================================

class TestGetChatHistory:
    """获取聊天历史 API 测试"""

    @pytest.mark.asyncio
    async def test_get_chat_history_with_valid_conversation_returns_messages(self, authenticated_client, test_conversation):
        """正向测试: 获取有效会话的聊天历史"""
        # 先发送一条消息
        with patch('app.services.chat_service.chat_service.generate_sse_stream') as mock_stream:
            mock_stream.return_value = _mock_sse_stream()
            await authenticated_client.post(
                "/api/v1/chat/send",
                json={
                    "conversation_id": test_conversation["id"],
                    "content": "Hello, this is a test message"
                }
            )
        
        response = await authenticated_client.get(
            f"/api/v1/chat/conversations/{test_conversation['id']}/history"
        )

        assert response.status_code == 200
        data = get_response_data(response)
        assert "messages" in data
        assert "total" in data
        assert isinstance(data["messages"], list)

    @pytest.mark.asyncio
    async def test_get_chat_history_with_pagination(self, authenticated_client, test_conversation):
        """边界测试: 分页参数 skip 和 limit"""
        response = await authenticated_client.get(
            f"/api/v1/chat/conversations/{test_conversation['id']}/history?skip=0&limit=10"
        )

        assert response.status_code == 200
        data = get_response_data(response)
        assert "messages" in data

    @pytest.mark.asyncio
    async def test_get_chat_history_with_negative_skip_returns_422(self, authenticated_client, test_conversation):
        """边界测试: 负数 skip 应返回 422"""
        response = await authenticated_client.get(
            f"/api/v1/chat/conversations/{test_conversation['id']}/history?skip=-1"
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_chat_history_with_exceeding_limit_returns_422(self, authenticated_client, test_conversation):
        """边界测试: limit 超过最大值应返回 422"""
        response = await authenticated_client.get(
            f"/api/v1/chat/conversations/{test_conversation['id']}/history?limit=501"
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_chat_history_conversation_not_found_returns_404(self, authenticated_client):
        """异常测试: 获取不存在会话的历史应返回 404"""
        response = await authenticated_client.get(
            "/api/v1/chat/conversations/99999/history"
        )

        assert response.status_code == 404
        json_data = response.json()
        # 新格式使用 message 字段
        assert "message" in json_data or "detail" in json_data

    @pytest.mark.asyncio
    async def test_get_chat_history_wrong_user_returns_404(self, client, test_user_data):
        """安全测试: 访问其他用户的会话历史应返回 404"""
        # 注册用户1并创建会话
        await client.post("/api/v1/auth/register", json=test_user_data)
        login1 = await client.post("/api/v1/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        token1 = get_access_token(login1)

        conv_response = await client.post(
            "/api/v1/conversations",
            json={"title": "User1 Conversation"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        conv_id = get_conversation_id(conv_response)

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
        token2 = get_access_token(login2)

        # 用户2尝试访问用户1的会话历史
        response = await client.get(
            f"/api/v1/chat/conversations/{conv_id}/history",
            headers={"Authorization": f"Bearer {token2}"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_chat_history_without_auth_returns_401(self, client):
        """安全测试: 未认证访问应返回 401"""
        response = await client.get(
            "/api/v1/chat/conversations/1/history"
        )
        
        assert response.status_code == 401


class TestSendChatMessage:
    """发送聊天消息 API 测试"""

    @pytest.mark.asyncio
    async def test_send_message_with_valid_data_returns_sse_stream(self, authenticated_client, test_conversation):
        """正向测试: 发送消息返回 SSE 流"""
        with patch('app.services.chat_service.chat_service.generate_sse_stream') as mock_stream:
            mock_stream.return_value = _mock_sse_stream()
            
            chat_request = {
                "conversation_id": test_conversation["id"],
                "content": "Hello, how are you?",
                "is_expert": False,
                "enable_thinking": False
            }
            
            response = await authenticated_client.post(
                "/api/v1/chat/send",
                json=chat_request
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            assert response.headers["cache-control"] == "no-cache"
            mock_stream.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_with_attachments(self, authenticated_client, test_conversation):
        """正向测试: 发送带附件的消息 - 使用正确的附件格式"""
        with patch('app.services.chat_service.chat_service.generate_sse_stream') as mock_stream:
            mock_stream.return_value = _mock_sse_stream()
            
            # 根据 ChatMessage schema，attachments 是 List[str] 类型
            chat_request = {
                "conversation_id": test_conversation["id"],
                "content": "Check this image",
                "attachments": ["http://example.com/image.png"]  # 字符串列表
            }
            
            response = await authenticated_client.post(
                "/api/v1/chat/send",
                json=chat_request
            )
            
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_send_message_with_expert_mode(self, authenticated_client, test_conversation):
        """正向测试: 使用专家模式发送消息"""
        with patch('app.services.chat_service.chat_service.generate_sse_stream') as mock_stream:
            mock_stream.return_value = _mock_sse_stream()
            
            chat_request = {
                "conversation_id": test_conversation["id"],
                "content": "Complex question",
                "is_expert": True,
                "enable_thinking": True
            }
            
            response = await authenticated_client.post(
                "/api/v1/chat/send",
                json=chat_request
            )
            
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_send_message_conversation_not_found_returns_404(self, authenticated_client):
        """异常测试: 向不存在的会话发送消息应返回 404"""
        chat_request = {
            "conversation_id": 99999,
            "content": "Hello"
        }

        response = await authenticated_client.post(
            "/api/v1/chat/send",
            json=chat_request
        )

        assert response.status_code == 404
        json_data = response.json()
        # 新格式使用 message 字段
        assert "message" in json_data or "detail" in json_data

    @pytest.mark.asyncio
    async def test_send_message_wrong_user_returns_404(self, client, test_user_data):
        """安全测试: 向其他用户的会话发送消息应返回 404"""
        # 注册用户1并创建会话
        await client.post("/api/v1/auth/register", json=test_user_data)
        login1 = await client.post("/api/v1/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        token1 = get_access_token(login1)

        conv_response = await client.post(
            "/api/v1/conversations",
            json={"title": "User1 Conversation"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        conv_id = get_conversation_id(conv_response)

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
        token2 = get_access_token(login2)

        # 用户2尝试向用户1的会话发送消息
        chat_request = {
            "conversation_id": conv_id,
            "content": "Hacked message"
        }

        response = await client.post(
            "/api/v1/chat/send",
            json=chat_request,
            headers={"Authorization": f"Bearer {token2}"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_send_message_without_auth_returns_401(self, client):
        """安全测试: 未认证发送消息应返回 401"""
        chat_request = {
            "conversation_id": 1,
            "content": "Hello"
        }
        
        response = await client.post(
            "/api/v1/chat/send",
            json=chat_request
        )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_send_message_empty_content(self, authenticated_client, test_conversation):
        """边界测试: 发送空内容消息"""
        with patch('app.services.chat_service.chat_service.generate_sse_stream') as mock_stream:
            mock_stream.return_value = _mock_sse_stream()
            
            chat_request = {
                "conversation_id": test_conversation["id"],
                "content": ""
            }
            
            response = await authenticated_client.post(
                "/api/v1/chat/send",
                json=chat_request
            )
            
            # 根据业务逻辑，可能接受或拒绝空内容
            # 这里假设空内容被接受
            assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_send_message_long_content(self, authenticated_client, test_conversation):
        """边界测试: 发送超长内容消息"""
        with patch('app.services.chat_service.chat_service.generate_sse_stream') as mock_stream:
            mock_stream.return_value = _mock_sse_stream()
            
            chat_request = {
                "conversation_id": test_conversation["id"],
                "content": "a" * 10000  # 超长内容
            }
            
            response = await authenticated_client.post(
                "/api/v1/chat/send",
                json=chat_request
            )
            
            # 根据业务逻辑，可能接受或拒绝超长内容
            assert response.status_code in [200, 413, 422]


class TestChatFlowIntegration:
    """聊天流程集成测试"""

    @pytest.mark.asyncio
    async def test_chat_flow_with_thinking_mode(self, authenticated_client, test_conversation):
        """集成测试: 带思考模式的完整聊天流程"""
        with patch('app.services.chat_service.chat_service.generate_sse_stream') as mock_stream:
            mock_stream.return_value = _mock_sse_stream_with_thinking()
            
            chat_request = {
                "conversation_id": test_conversation["id"],
                "content": "Complex question requiring thinking",
                "enable_thinking": True
            }
            
            response = await authenticated_client.post(
                "/api/v1/chat/send",
                json=chat_request
            )
            
            assert response.status_code == 200
            
            # 验证历史记录
            history_response = await authenticated_client.get(
                f"/api/v1/chat/conversations/{test_conversation['id']}/history"
            )
            assert history_response.status_code == 200
            history_data = get_response_data(history_response)
            assert history_data["total"] >= 1

    @pytest.mark.asyncio
    async def test_chat_flow_with_tool_call(self, authenticated_client, test_conversation):
        """集成测试: 带工具调用的完整聊天流程"""
        with patch('app.services.chat_service.chat_service.generate_sse_stream') as mock_stream:
            mock_stream.return_value = _mock_sse_stream_with_tool_call()
            
            chat_request = {
                "conversation_id": test_conversation["id"],
                "content": "Search for something"
            }
            
            response = await authenticated_client.post(
                "/api/v1/chat/send",
                json=chat_request
            )
            
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, authenticated_client, test_conversation):
        """集成测试: 多轮对话流程"""
        messages = [
            "Hello",
            "How are you?",
            "What's the weather like?"
        ]
        
        with patch('app.services.chat_service.chat_service.generate_sse_stream') as mock_stream:
            mock_stream.return_value = _mock_sse_stream()
            
            for message in messages:
                response = await authenticated_client.post(
                    "/api/v1/chat/send",
                    json={
                        "conversation_id": test_conversation["id"],
                        "content": message
                    }
                )
                assert response.status_code == 200
        
        # 验证所有消息都在历史中
        history_response = await authenticated_client.get(
            f"/api/v1/chat/conversations/{test_conversation['id']}/history"
        )
        assert history_response.status_code == 200
        history_data = get_response_data(history_response)
        # 应该有用户消息（3条）
        assert history_data["total"] >= 3
