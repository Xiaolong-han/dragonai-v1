import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import cache_aside, redis_client
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.message import MessageCreate

logger = logging.getLogger(__name__)


class MessageRepository:
    """消息数据访问仓库，负责消息的持久化和缓存管理"""

    @staticmethod
    async def get_messages(
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[Message]:
        """获取会话消息列表，使用缓存"""
        cache_key = MessageRepository._build_cache_key(conversation_id, user_id, skip, limit)

        async def fetch():
            result = await db.execute(
                select(Message)
                .join(Conversation, Message.conversation_id == Conversation.id)
                .where(
                    Message.conversation_id == conversation_id,
                    Conversation.user_id == user_id
                )
                .order_by(Message.created_at.asc())
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()

        messages = await cache_aside(key=cache_key, ttl=3600, data_func=fetch)
        return messages if messages else []

    @staticmethod
    async def create_message(
        db: AsyncSession,
        conversation_id: int,
        message_create: MessageCreate,
        user_id: int
    ) -> Message | None:
        """创建消息并失效相关缓存"""
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        conv = result.scalar_one_or_none()
        if not conv:
            return None

        db_message = Message(
            conversation_id=conversation_id,
            role=message_create.role,
            content=message_create.content,
            extra_data=message_create.extra_data
        )
        db.add(db_message)
        await db.flush()
        await db.refresh(db_message)

        logger.debug(f"[DB] Saved message id={db_message.id}")

        verify_result = await db.execute(
            select(Message).where(Message.id == db_message.id)
        )
        verify_msg = verify_result.scalar_one_or_none()
        if verify_msg:
            logger.debug(f"[DB] Verify saved: id={verify_msg.id}")

        await MessageRepository._invalidate_messages_cache(conversation_id, user_id)
        return db_message

    @staticmethod
    def _build_cache_key(conversation_id: int, user_id: int, skip: int, limit: int) -> str:
        """构建缓存键"""
        return f"messages:conversation:{conversation_id}:user:{user_id}:skip:{skip}:limit:{limit}"

    @staticmethod
    async def _invalidate_messages_cache(conversation_id: int, user_id: int):
        """失效消息缓存 - 使用 SCAN 和 pipeline 优化"""
        pattern = f"messages:conversation:{conversation_id}:user:{user_id}:*"
        cursor = 0
        deleted_count = 0
        keys_to_delete = []

        # 收集所有需要删除的 key
        while True:
            cursor, keys = await redis_client.client.scan(cursor, match=pattern, count=100)
            if keys:
                keys_to_delete.extend(keys)
            if cursor == 0:
                break

        # 使用 pipeline 批量删除
        if keys_to_delete:
            pipe = redis_client.client.pipeline()
            for key in keys_to_delete:
                pipe.delete(key)
            await pipe.execute()
            deleted_count = len(keys_to_delete)

        if deleted_count > 0:
            logger.debug(f"[CACHE DELETE] 已删除消息缓存: conversation_id={conversation_id}, keys={deleted_count}")
