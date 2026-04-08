from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.schemas.conversation import ConversationCreate, ConversationUpdate
from app.schemas.response import ResponseBuilder
from app.services.conversation_service import conversation_service

router = APIRouter(prefix="/conversations", tags=["会话"])


@router.get("")
async def get_conversations(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=100, description="返回数量"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    conversations = await conversation_service.get_conversations(db, user_id=current_user.id, skip=skip, limit=limit)
    # 处理缓存返回 dict 或 SQLAlchemy 模型两种情况
    if conversations and isinstance(conversations[0], dict):
        data = conversations  # 已经是 dict 列表
    elif conversations:
        from app.schemas.conversation import ConversationResponse
        data = [ConversationResponse.model_validate(c).model_dump() for c in conversations]
    else:
        data = []
    return ResponseBuilder.success(data=data)


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: int,
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
    # 处理缓存返回 dict 或 SQLAlchemy 模型
    if isinstance(conv, dict):
        data = conv
    else:
        from app.schemas.conversation import ConversationResponse
        data = ConversationResponse.model_validate(conv).model_dump()
    return ResponseBuilder.success(data=data)


@router.post("")
async def create_conversation(
    conversation: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    conv = await conversation_service.create_conversation(db, conversation=conversation, user_id=current_user.id)
    # 新创建的对象总是 SQLAlchemy 模型
    from app.schemas.conversation import ConversationResponse
    data = ConversationResponse.model_validate(conv).model_dump()
    return ResponseBuilder.success(data=data, message="会话创建成功")


@router.put("/{conversation_id}")
async def update_conversation(
    conversation_id: int,
    conversation_update: ConversationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    conv = await conversation_service.update_conversation(
        db,
        conversation_id=conversation_id,
        conversation_update=conversation_update,
        user_id=current_user.id
    )
    if not conv:
        raise NotFoundException(
            message="会话不存在",
            resource_type="conversation",
            resource_id=conversation_id
        )
    # 处理 SQLAlchemy 模型或 dict
    if isinstance(conv, dict):
        data = conv
    else:
        from app.schemas.conversation import ConversationResponse
        data = ConversationResponse.model_validate(conv).model_dump()
    return ResponseBuilder.success(data=data)


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    success = await conversation_service.delete_conversation(db, conversation_id=conversation_id, user_id=current_user.id)
    if not success:
        raise NotFoundException(
            message="会话不存在",
            resource_type="conversation",
            resource_id=conversation_id
        )
    return ResponseBuilder.success(message="会话已删除")


@router.post("/{conversation_id}/pin")
async def pin_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    conv = await conversation_service.pin_conversation(db, conversation_id=conversation_id, user_id=current_user.id, pinned=True)
    if not conv:
        raise NotFoundException(
            message="会话不存在",
            resource_type="conversation",
            resource_id=conversation_id
        )
    if isinstance(conv, dict):
        data = conv
    else:
        from app.schemas.conversation import ConversationResponse
        data = ConversationResponse.model_validate(conv).model_dump()
    return ResponseBuilder.success(data=data)


@router.post("/{conversation_id}/unpin")
async def unpin_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    conv = await conversation_service.pin_conversation(db, conversation_id=conversation_id, user_id=current_user.id, pinned=False)
    if not conv:
        raise NotFoundException(
            message="会话不存在",
            resource_type="conversation",
            resource_id=conversation_id
        )
    if isinstance(conv, dict):
        data = conv
    else:
        from app.schemas.conversation import ConversationResponse
        data = ConversationResponse.model_validate(conv).model_dump()
    return ResponseBuilder.success(data=data)
