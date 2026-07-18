from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.background_task import BackgroundTask, TaskStatus


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: UUID,
        task_type: str,
        organization_id: UUID | None = None,
        idempotency_key: str | None = None,
        expires_at: datetime | None = None,
    ) -> BackgroundTask:
        task = BackgroundTask(
            user_id=user_id,
            organization_id=organization_id,
            task_type=task_type,
            status=TaskStatus.QUEUED,
            progress=0,
            idempotency_key=idempotency_key,
            expires_at=expires_at,
        )
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def get_by_id(self, task_id: UUID) -> BackgroundTask | None:
        result = await self.session.execute(
            select(BackgroundTask).where(BackgroundTask.id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_by_celery_task_id(self, celery_task_id: str) -> BackgroundTask | None:
        result = await self.session.execute(
            select(BackgroundTask).where(
                BackgroundTask.celery_task_id == celery_task_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(
        self,
        *,
        user_id: UUID,
        task_type: str,
        idempotency_key: str,
    ) -> BackgroundTask | None:
        result = await self.session.execute(
            select(BackgroundTask)
            .where(
                BackgroundTask.user_id == user_id,
                BackgroundTask.task_type == task_type,
                BackgroundTask.idempotency_key == idempotency_key,
            )
            .order_by(BackgroundTask.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_tasks(
        self,
        *,
        user_id: UUID,
        organization_id: UUID | None = None,
        status: TaskStatus | None = None,
        task_type: str | None = None,
        limit: int,
        offset: int,
    ) -> tuple[list[BackgroundTask], int]:
        query = select(BackgroundTask).where(BackgroundTask.user_id == user_id)
        if organization_id is not None:
            query = query.where(BackgroundTask.organization_id == organization_id)
        else:
            query = query.where(BackgroundTask.organization_id.is_(None))
        if status is not None:
            query = query.where(BackgroundTask.status == status)
        if task_type is not None:
            query = query.where(BackgroundTask.task_type == task_type)

        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = int(count_result.scalar_one())

        result = await self.session.execute(
            query.order_by(BackgroundTask.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all()), total

    async def list_organization_tasks(
        self,
        *,
        organization_id: UUID,
        status: TaskStatus | None = None,
        task_type: str | None = None,
        limit: int,
        offset: int,
    ) -> tuple[list[BackgroundTask], int]:
        query = select(BackgroundTask).where(
            BackgroundTask.organization_id == organization_id
        )
        if status is not None:
            query = query.where(BackgroundTask.status == status)
        if task_type is not None:
            query = query.where(BackgroundTask.task_type == task_type)

        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = int(count_result.scalar_one())

        result = await self.session.execute(
            query.order_by(BackgroundTask.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all()), total

    async def update(
        self,
        task: BackgroundTask,
        *,
        celery_task_id: str | None = None,
        status: TaskStatus | None = None,
        progress: int | None = None,
        result_json: dict[str, Any] | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        cancelled_at: datetime | None = None,
    ) -> BackgroundTask:
        if celery_task_id is not None:
            task.celery_task_id = celery_task_id
        if status is not None:
            task.status = status
        if progress is not None:
            task.progress = max(0, min(100, progress))
        if result_json is not None:
            task.result_json = result_json
        if error_code is not None:
            task.error_code = error_code
        if error_message is not None:
            task.error_message = error_message
        if started_at is not None:
            task.started_at = started_at
        if completed_at is not None:
            task.completed_at = completed_at
        if cancelled_at is not None:
            task.cancelled_at = cancelled_at
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def delete_expired_before(self, cutoff: datetime) -> int:
        result = await self.session.execute(
            delete(BackgroundTask).where(
                BackgroundTask.created_at < cutoff,
                BackgroundTask.status.in_([TaskStatus.SUCCEEDED, TaskStatus.CANCELLED]),
            )
        )
        return int(getattr(result, "rowcount", 0) or 0)
