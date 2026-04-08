import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.schemas.message import MessageCreate
from app.services.formatters.message_formatter import MessageFormatter
from app.services.repositories.message_repository import MessageRepository
from app.services.stream.sse_emitter import SSEEmitter
from app.services.stream.stream_processor import StreamProcessor

logger = logging.getLogger(__name__)


class ChatService:
    """聊天服务，作为业务编排层，协调各个服务类完成业务逻辑"""

    def __init__(
        self,
        message_repository: MessageRepository | None = None,
        message_formatter: MessageFormatter | None = None,
        stream_processor: StreamProcessor | None = None,
        sse_emitter: SSEEmitter | None = None
    ):
        self.message_repository = message_repository or MessageRepository()
        self.message_formatter = message_formatter or MessageFormatter()
        self.stream_processor = stream_processor or StreamProcessor(self.message_formatter)
        self.sse_emitter = sse_emitter or SSEEmitter(self.stream_processor, self.message_repository)

    async def get_messages(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[Message]:
        """获取会话消息列表"""
        return await self.message_repository.get_messages(
            db, conversation_id, user_id, skip, limit
        )

    async def create_message(
        self,
        db: AsyncSession,
        conversation_id: int,
        message_create: MessageCreate,
        user_id: int
    ) -> Message | None:
        """创建消息"""
        return await self.message_repository.create_message(
            db, conversation_id, message_create, user_id
        )

    async def generate_sse_stream(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        content: str,
        is_expert: bool = False,
        enable_thinking: bool = False,
        attachments: list[str] | None = None
    ) -> AsyncGenerator[str, None]:
        """生成 SSE 格式的流式响应"""
        async for chunk in self.sse_emitter.generate_sse_stream(
            db, conversation_id, user_id, content, is_expert, enable_thinking, attachments
        ):
            yield chunk


chat_service = ChatService()
