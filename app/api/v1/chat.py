import logging

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.api.middleware import CHAT_RATE_LIMIT, limiter
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.schemas.message import ChatRequest, MessageCreate
from app.schemas.response import ResponseBuilder
from app.services.chat_service import chat_service
from app.services.conversation_service import conversation_service
from app.services.stream import sse_with_heartbeat

router = APIRouter(prefix="/chat", tags=["聊天"])
logger = logging.getLogger(__name__)


@router.get("/conversations/{conversation_id}/history")
@limiter.limit(CHAT_RATE_LIMIT)
async def get_chat_history(
    request: Request,
    conversation_id: int,
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=500, description="返回数量"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    conv = await conversation_service.get_conversation(db, conversation_id=conversation_id, user_id=current_user.id)
    if not conv:
        raise NotFoundException(
            message="会话不存在",
            resource_type="conversation",
            resource_id=conversation_id
        )

    messages = await chat_service.get_messages(
        db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return ResponseBuilder.success(data={"messages": messages, "total": len(messages)})


@router.post("/send")
@limiter.limit(CHAT_RATE_LIMIT)
async def send_chat_message(
    request: Request,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    conv = await conversation_service.get_conversation(
        db,
        conversation_id=chat_request.conversation_id,
        user_id=current_user.id
    )
    if not conv:
        raise NotFoundException(
            message="会话不存在",
            resource_type="conversation",
            resource_id=chat_request.conversation_id
        )

    await chat_service.create_message(
        db,
        conversation_id=chat_request.conversation_id,
        message_create=MessageCreate(
            role="user",
            content=chat_request.content,
            extra_data={"attachments": chat_request.attachments} if chat_request.attachments else None
        ),
        user_id=current_user.id
    )

    return StreamingResponse(
        sse_with_heartbeat(chat_service.generate_sse_stream(
            db=db,
            conversation_id=chat_request.conversation_id,
            user_id=current_user.id,
            content=chat_request.content,
            is_expert=chat_request.is_expert,
            enable_thinking=chat_request.enable_thinking,
            attachments=chat_request.attachments
        )),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
