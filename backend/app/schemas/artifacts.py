from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.generated_artifact import ArtifactType
from app.schemas.common import ORMModel


class ArtifactCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    artifact_type: ArtifactType
    content: str = Field(min_length=1)
    metadata: dict[str, Any] | None = None
    organization_id: UUID | None = None


class ArtifactUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class ArtifactVersionCreateRequest(BaseModel):
    content: str = Field(min_length=1)
    metadata: dict[str, Any] | None = None


class ArtifactVersionResponse(ORMModel):
    id: UUID
    artifact_id: UUID
    version_number: int
    content: str
    content_hash: str
    metadata_json: dict[str, Any] | None = None
    created_by: UUID
    created_at: datetime


class ArtifactSummaryResponse(ORMModel):
    id: UUID
    user_id: UUID
    organization_id: UUID | None = None
    artifact_type: ArtifactType
    name: str
    description: str | None = None
    current_version_id: UUID | None = None
    current_version_number: int | None = None
    created_at: datetime
    updated_at: datetime


class ArtifactDetailResponse(ArtifactSummaryResponse):
    current_version: ArtifactVersionResponse | None = None


class ArtifactDiffResponse(BaseModel):
    artifact_id: UUID
    from_version: int
    to_version: int
    diff: str


class ArtifactRestoreResponse(BaseModel):
    artifact: ArtifactDetailResponse
    restored_from_version: int
    new_version: ArtifactVersionResponse
