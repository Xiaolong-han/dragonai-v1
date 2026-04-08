"""消息仓库测试"""

import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.repositories.message_repository import MessageRepository
from app.schemas.message import MessageCreate
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message


@pytest_asyncio.fixture
async def test_user(db_session):
    """创建测试用户"""
    user = User(
        username="testuser_repo",
        email="test_repo@example.com",
        hashed_password="hashed"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_conversation(db_session, test_user):
    """创建测试会话"""
    conv = Conversation(
        user_id=test_user.id,
        title="Test Conversation"
    )
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)
    return conv


@pytest_asyncio.fixture
def mock_redis():
    """Mock Redis 客户端"""
    mock_redis_client = AsyncMock()
    mock_redis_client.get = AsyncMock(return_value=None)
    mock_redis_client.set = AsyncMock(return_value=None)
    mock_redis_client.client = AsyncMock()
    mock_redis_client.client.scan = AsyncMock(return_value=(0, []))
    mock_redis_client.client.delete = AsyncMock()
    # Mock pipeline for batch delete
    mock_pipeline = AsyncMock()
    mock_pipeline.delete = MagicMock()
    mock_pipeline.execute = AsyncMock()
    mock_redis_client.client.pipeline = MagicMock(return_value=mock_pipeline)
    mock_redis_client.acquire_lock = AsyncMock(return_value=True)
    mock_redis_client.release_lock = AsyncMock()

    with patch('app.services.repositories.message_repository.redis_client', mock_redis_client), \
         patch('app.cache.redis.redis_client', mock_redis_client):
        yield mock_redis_client


class TestMessageRepository:
    """MessageRepository 测试"""

    @pytest.mark.asyncio
    async def test_create_message(self, db_session, test_conversation, test_user, mock_redis):
        """测试创建消息"""
        message_create = MessageCreate(
            role="user",
            content="Hello, world!"
        )

        message = await MessageRepository.create_message(
            db_session,
            test_conversation.id,
            message_create,
            test_user.id
        )

        assert message is not None
        assert message.id is not None
        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert message.conversation_id == test_conversation.id

    @pytest.mark.asyncio
    async def test_create_message_with_extra_data(self, db_session, test_conversation, test_user, mock_redis):
        """测试创建带额外数据的消息"""
        message_create = MessageCreate(
            role="assistant",
            content="回复内容",
            extra_data={"thinking_content": "思考过程", "model": "expert"}
        )

        message = await MessageRepository.create_message(
            db_session,
            test_conversation.id,
            message_create,
            test_user.id
        )

        assert message is not None
        assert message.extra_data is not None
        assert message.extra_data.get("thinking_content") == "思考过程"

    @pytest.mark.asyncio
    async def test_create_message_invalid_conversation(self, db_session, test_user, mock_redis):
        """测试创建消息到无效会话"""
        message_create = MessageCreate(
            role="user",
            content="Test"
        )

        message = await MessageRepository.create_message(
            db_session,
            99999,  # 不存在的会话 ID
            message_create,
            test_user.id
        )

        assert message is None

    @pytest.mark.asyncio
    async def test_get_messages(self, db_session, test_conversation, test_user, mock_redis):
        """测试获取消息列表"""
        # 创建多条消息
        for i in range(3):
            msg = Message(
                conversation_id=test_conversation.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}"
            )
            db_session.add(msg)
        await db_session.commit()

        messages = await MessageRepository.get_messages(
            db_session,
            test_conversation.id,
            test_user.id
        )

        assert len(messages) == 3
        # 验证按时间排序
        contents = [m.content for m in messages]
        assert "Message 0" in contents

    @pytest.mark.asyncio
    async def test_get_messages_with_pagination(self, db_session, test_conversation, test_user, mock_redis):
        """测试分页获取消息"""
        # 创建多条消息
        for i in range(10):
            msg = Message(
                conversation_id=test_conversation.id,
                role="user",
                content=f"Message {i}"
            )
            db_session.add(msg)
        await db_session.commit()

        # 获取第一页
        messages_page1 = await MessageRepository.get_messages(
            db_session,
            test_conversation.id,
            test_user.id,
            skip=0,
            limit=5
        )

        # 获取第二页
        messages_page2 = await MessageRepository.get_messages(
            db_session,
            test_conversation.id,
            test_user.id,
            skip=5,
            limit=5
        )

        assert len(messages_page1) == 5
        assert len(messages_page2) == 5

        # 验证两页不重复
        ids_page1 = {m.id for m in messages_page1}
        ids_page2 = {m.id for m in messages_page2}
        assert ids_page1.isdisjoint(ids_page2)

    @pytest.mark.asyncio
    async def test_get_messages_wrong_user(self, db_session, test_conversation, mock_redis):
        """测试获取其他用户的消息"""
        messages = await MessageRepository.get_messages(
            db_session,
            test_conversation.id,
            99999  # 错误的用户 ID
        )

        assert len(messages) == 0

    def test_build_cache_key(self):
        """测试构建缓存键"""
        key = MessageRepository._build_cache_key(
            conversation_id=1,
            user_id=2,
            skip=0,
            limit=10
        )

        assert "conversation:1" in key
        assert "user:2" in key
        assert "skip:0" in key
        assert "limit:10" in key

    @pytest.mark.asyncio
    async def test_invalidate_cache(self, mock_redis):
        """测试缓存失效"""
        mock_redis.client.scan.return_value = (0, ["key1", "key2"])

        await MessageRepository._invalidate_messages_cache(1, 1)

        mock_redis.client.scan.assert_called_once()
        # 验证 pipeline 被调用
        mock_redis.client.pipeline.assert_called_once()
        # 验证 pipeline.execute 被调用
        mock_redis.client.pipeline.return_value.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_message_invalidates_cache(self, db_session, test_conversation, test_user, mock_redis):
        """测试创建消息后缓存失效"""
        mock_redis.client.scan.return_value = (0, [])

        message_create = MessageCreate(role="user", content="test")

        await MessageRepository.create_message(
            db_session,
            test_conversation.id,
            message_create,
            test_user.id
        )

        # 验证调用了缓存失效
        mock_redis.client.scan.assert_called()