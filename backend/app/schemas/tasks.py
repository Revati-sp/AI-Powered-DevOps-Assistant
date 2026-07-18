from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.background_task import TaskStatus


class TaskSummaryResponse(BaseModel):
    id: UUID
    task_type: str
    status: TaskStatus
    progress: int
    organization_id: UUID | None = None
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None


class TaskDetailResponse(TaskSummaryResponse):
    task_id: UUID | None = None
    result_json: dict[str, Any] | None = None
    celery_task_id: str | None = None
    analysis_id: UUID | None = None


class TaskListParams(BaseModel):
    status: TaskStatus | None = None
    task_type: str | None = None
    organization_id: UUID | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class TaskCancelResponse(BaseModel):
    id: UUID
    status: TaskStatus
    cancelled_at: datetime | None = None
