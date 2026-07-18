from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    conversation_id: UUID | None = None
    organization_id: UUID | None = None
    provider: str = "gemini"


class ChatResponse(BaseModel):
    conversation_id: UUID
    answer: str
    provider: str
    created_at: datetime


class MessageResponse(ORMModel):
    id: UUID
    role: str
    content: str
    created_at: datetime


class ConversationSummary(ORMModel):
    id: UUID
    title: str
    provider: str
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationSummary):
    messages: list[MessageResponse] = Field(default_factory=list)
