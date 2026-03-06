
import pytest
import pytest_asyncio
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.chat_service import chat_service
from app.agents.error_classifier import AgentErrorClassifier, AgentErrorType
from app.services.user_service import UserService
from app.services.conversation_service import conversation_service
from app.schemas.message import MessageCreate
from app.schemas.user import UserCreate
from app.schemas.conversation import ConversationCreate
from app.models.user import User
from app.models.conversation import Conversation


@pytest_asyncio.fixture
async def user_service():
    return UserService()


@pytest_asyncio.fixture
async def test_user(db_session, user_service):
    user_create = UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpassword123"
    )
    user = await user_service.create_user(db_session, user_create)
    return user


@pytest_asyncio.fixture
async def test_conversation(db_session, test_user, mock_redis):
    conv_create = ConversationCreate(title="Test Conversation")
    conv = await conversation_service.create_conversation(
        db_session, conv_create, test_user.id
    )
    return conv


@pytest.fixture
def mock_redis():
    mock_redis_client = AsyncMock()
    mock_redis_client.get = AsyncMock(return_value=None)
    mock_redis_client.set = AsyncMock(return_value=None)
    mock_redis_client.delete = AsyncMock(return_value=None)
    mock_redis_client.exists = AsyncMock(return_value=False)
    mock_redis_client.client = AsyncMock()
    mock_redis_client.client.scan = AsyncMock(return_value=(0, []))
    mock_redis_client.client.delete = AsyncMock(return_value=None)
    
    with patch('app.cache.redis.redis_client', mock_redis_client), \
         patch('app.services.conversation_service.redis_client', mock_redis_client), \
         patch('app.services.repositories.message_repository.redis_client', mock_redis_client):
        yield mock_redis_client


class MockAgent:
    def __init__(self, responses):
        self.responses = responses
    
    async def astream(self, *args, **kwargs):
        for response in self.responses:
            yield response


@pytest.fixture
def mock_agent_factory_stream():
    from langchain_core.messages.ai import AIMessageChunk
    
    return MockAgent([
        ("messages", (AIMessageChunk(content="Hello"), {})),
        ("messages", (AIMessageChunk(content=" World"), {}))
    ])


class TestChatService:
    @pytest.mark.asyncio
    async def test_create_message(self, db_session, test_user, test_conversation, mock_redis):
        message_create = MessageCreate(
            role="user",
            content="Hello, world!"
        )
        message = await chat_service.create_message(
            db_session, test_conversation.id, message_create, test_user.id
        )
        assert message is not None
        assert message.id is not None
        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert message.conversation_id == test_conversation.id

    @pytest.mark.asyncio
    async def test_create_message_wrong_conversation(self, db_session, test_user, mock_redis):
        message_create = MessageCreate(role="user", content="Test")
        message = await chat_service.create_message(
            db_session, 9999, message_create, test_user.id
        )
        assert message is None

    @pytest.mark.asyncio
    async def test_get_messages(self, db_session, test_user, test_conversation, mock_redis):
        message_create1 = MessageCreate(role="user", content="Hello")
        message_create2 = MessageCreate(role="assistant", content="Hi there")
        await chat_service.create_message(
            db_session, test_conversation.id, message_create1, test_user.id
        )
        await chat_service.create_message(
            db_session, test_conversation.id, message_create2, test_user.id
        )
        
        messages = await chat_service.get_messages(
            db_session, test_conversation.id, test_user.id
        )
        assert len(messages) == 2

    @pytest.mark.asyncio
    async def test_generate_sse_stream(self, db_session, test_user, test_conversation, mock_redis, mock_agent_factory_stream):
        with patch('app.agents.agent_factory.AgentFactory') as mock_factory:
            mock_factory.create_chat_agent.return_value = mock_agent_factory_stream
            mock_factory.get_agent_config.return_value = {"configurable": {"thread_id": "test"}}
            
            chunks = []
            async for chunk in chat_service.generate_sse_stream(
                db=db_session,
                conversation_id=test_conversation.id,
                user_id=test_user.id,
                content="Hello"
            ):
                if isinstance(chunk, str) and "data:" in chunk:
                    chunks.append(chunk)
            
            assert len(chunks) >= 1


class TestAgentErrorClassifier:
    """AgentErrorClassifier 错误分类测试"""

    def test_classify_timeout_error(self):
        """测试超时错误分类"""
        error = asyncio.TimeoutError()
        error_type = AgentErrorClassifier.classify(error)
        assert error_type == AgentErrorType.TIMEOUT

    def test_classify_tool_call_invalid_error(self):
        """测试工具调用无效错误分类"""
        error = Exception("tool_calls must be followed by tool messages")
        error_type = AgentErrorClassifier.classify(error)
        assert error_type == AgentErrorType.TOOL_CALL_INVALID

    def test_classify_state_error(self):
        """测试状态错误分类"""
        error = Exception("checkpointer thread_id not found")
        error_type = AgentErrorClassifier.classify(error)
        assert error_type == AgentErrorType.STATE_ERROR

    def test_classify_unknown_error(self):
        """测试未知错误分类"""
        error = Exception("Some random error")
        error_type = AgentErrorClassifier.classify(error)
        assert error_type == AgentErrorType.UNKNOWN

    def test_is_retryable_tool_call_error(self):
        """测试工具调用错误可重试"""
        assert AgentErrorClassifier.is_retryable(AgentErrorType.TOOL_CALL_INVALID) is True

    def test_is_retryable_timeout_error(self):
        """测试超时错误不可重试"""
        assert AgentErrorClassifier.is_retryable(AgentErrorType.TIMEOUT) is False

    def test_is_retryable_unknown_error(self):
        """测试未知错误不可重试"""
        assert AgentErrorClassifier.is_retryable(AgentErrorType.UNKNOWN) is False

    def test_get_user_message_production(self):
        """测试生产环境用户消息"""
        msg = AgentErrorClassifier.get_user_message(AgentErrorType.TIMEOUT, is_production=True)
        assert "超时" in msg or "timeout" in msg.lower()

    def test_get_user_message_development(self):
        """测试开发环境用户消息"""
        msg = AgentErrorClassifier.get_user_message(
            AgentErrorType.TOOL_CALL_INVALID, 
            is_production=False
        )
        assert "重试" in msg or "retry" in msg.lower()

    def test_get_user_message_hides_details_in_production(self):
        """测试生产环境隐藏详细信息"""
        msg_prod = AgentErrorClassifier.get_user_message(
            AgentErrorType.TOOL_CALL_INVALID, 
            is_production=True
        )
        msg_dev = AgentErrorClassifier.get_user_message(
            AgentErrorType.TOOL_CALL_INVALID, 
            is_production=False
        )
        assert msg_prod != msg_dev
