from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MessageBase(BaseModel):
    role: str = Field(..., max_length=20)
    content: str
    extra_data: dict[str, Any] | None = None

    @field_validator('extra_data', mode='before')
    @classmethod
    def validate_extra_data(cls, v):
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        return None


class MessageCreate(MessageBase):
    pass


class MessageUpdate(BaseModel):
    content: str | None = None
    extra_data: dict[str, Any] | None = None


class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    conversation_id: int
    content: str
    is_expert: bool | None = Field(False, description="是否使用专家模型")
    enable_thinking: bool | None = Field(False, description="是否启用深度思考模式")
    attachments: list[str] | None = Field(None, description="附件列表（图片或文档路径）")


class ChatMessageItem(BaseModel):
    role: str
    content: str


class ChatHistoryResponse(BaseModel):
    messages: list[MessageResponse]
    total: int
