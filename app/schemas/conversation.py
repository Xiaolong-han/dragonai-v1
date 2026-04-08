from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConversationBase(BaseModel):
    title: str = Field(..., max_length=200)
    model_name: str | None = None


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseModel):
    title: str | None = Field(None, max_length=200)
    is_pinned: bool | None = None
    model_name: str | None = None


class ConversationResponse(ConversationBase):
    id: int
    user_id: int
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
