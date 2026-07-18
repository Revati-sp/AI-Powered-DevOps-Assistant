from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ArtifactTagResponse(ORMModel):
    id: UUID
    organization_id: UUID | None = None
    user_id: UUID
    name: str
    color: str | None = None
    created_at: datetime


class ArtifactTagCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    color: str | None = Field(default=None, max_length=20)


class ArtifactTagAssignRequest(BaseModel):
    tag_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=80)
    color: str | None = Field(default=None, max_length=20)
