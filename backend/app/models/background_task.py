from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TaskStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BackgroundTask(Base):
    __tablename__ = "background_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    celery_task_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True, index=True
    )
    task_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(
            TaskStatus,
            name="task_status",
            values_callable=lambda x: [e.value for e in x],
            native_enum=False,
        ),
        default=TaskStatus.QUEUED,
        nullable=False,
        index=True,
    )
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
