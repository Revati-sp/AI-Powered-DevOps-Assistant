from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.models.background_task import BackgroundTask, TaskStatus
from app.models.organization import OrgRole
from app.models.user import User
from app.repositories.task_repository import TaskRepository
from app.schemas.tasks import (
    TaskCancelResponse,
    TaskDetailResponse,
    TaskSummaryResponse,
)
from app.services.audit_service import AuditRequestContext, AuditService
from app.services.rbac import OrganizationAuthService, Permission

TASK_TYPE_LOG_ANALYSIS = "log_analysis"
TERMINAL_STATUSES = {
    TaskStatus.SUCCEEDED,
    TaskStatus.FAILED,
    TaskStatus.CANCELLED,
}
logger = get_logger(__name__)


class TaskService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.tasks = TaskRepository(session)
        self.org_auth = OrganizationAuthService(session)
        self.audit = AuditService(session)

    def _retention_cutoff(self) -> datetime:
        settings = get_settings()
        return datetime.now(UTC) - timedelta(
            days=settings.background_task_retention_days
        )

    def _default_expires_at(self) -> datetime:
        settings = get_settings()
        return datetime.now(UTC) + timedelta(
            days=settings.background_task_retention_days
        )

    async def _require_view(self, user: User, task: BackgroundTask) -> None:
        if task.organization_id is None:
            if task.user_id != user.id:
                raise NotFoundError("Task not found")
            return
        await self.org_auth.require_membership(task.organization_id, user.id)

    async def _require_cancel(self, user: User, task: BackgroundTask) -> None:
        if task.organization_id is None:
            if task.user_id != user.id:
                raise NotFoundError("Task not found")
            return

        _, membership = await self.org_auth.require_membership(
            task.organization_id, user.id
        )
        if membership.role == OrgRole.VIEWER:
            raise ForbiddenError("Insufficient organization permissions")
        if task.user_id == user.id:
            return
        await self.org_auth.require_permission(
            task.organization_id, user.id, Permission.TASK_CANCEL
        )

    def _to_summary(self, task: BackgroundTask) -> TaskSummaryResponse:
        return TaskSummaryResponse(
            id=task.id,
            task_type=task.task_type,
            status=task.status,
            progress=task.progress,
            organization_id=task.organization_id,
            error_code=task.error_code,
            error_message=task.error_message,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            cancelled_at=task.cancelled_at,
        )

    def _to_detail(
        self,
        task: BackgroundTask,
        *,
        analysis_id: UUID | None = None,
    ) -> TaskDetailResponse:
        return TaskDetailResponse(
            **self._to_summary(task).model_dump(),
            task_id=task.id,
            result_json=task.result_json,
            celery_task_id=task.celery_task_id,
            analysis_id=analysis_id,
        )

    async def get_existing_idempotent_task(
        self,
        *,
        user: User,
        task_type: str,
        idempotency_key: str | None,
    ) -> BackgroundTask | None:
        if not idempotency_key:
            return None
        existing = await self.tasks.get_by_idempotency_key(
            user_id=user.id,
            task_type=task_type,
            idempotency_key=idempotency_key,
        )
        if existing is None:
            return None
        if existing.status in TERMINAL_STATUSES and existing.completed_at:
            cutoff = self._retention_cutoff()
            if existing.completed_at < cutoff:
                return None
        return existing

    async def create_task(
        self,
        user: User,
        *,
        task_type: str,
        organization_id: UUID | None = None,
        idempotency_key: str | None = None,
        audit_context: AuditRequestContext | None = None,
    ) -> BackgroundTask:
        if organization_id is not None:
            await self.org_auth.require_permission(
                organization_id, user.id, Permission.RESOURCE_CREATE
            )

        if idempotency_key:
            existing = await self.get_existing_idempotent_task(
                user=user,
                task_type=task_type,
                idempotency_key=idempotency_key,
            )
            if existing is not None:
                return existing

        task = await self.tasks.create(
            user_id=user.id,
            task_type=task_type,
            organization_id=organization_id,
            idempotency_key=idempotency_key,
            expires_at=self._default_expires_at(),
        )
        await self.audit.record_event(
            action="task.created",
            actor_user_id=user.id,
            organization_id=organization_id,
            resource_type="background_task",
            resource_id=task.id,
            request_context=audit_context,
            metadata={"task_type": task_type},
        )
        return task

    async def attach_celery_task_id(
        self, task: BackgroundTask, celery_task_id: str
    ) -> BackgroundTask:
        return await self.tasks.update(task, celery_task_id=celery_task_id)

    async def get_task(
        self,
        user: User,
        task_id: UUID,
        *,
        analysis_id: UUID | None = None,
    ) -> TaskDetailResponse:
        task = await self.tasks.get_by_id(task_id)
        if task is None:
            raise NotFoundError("Task not found")
        await self._require_view(user, task)
        return self._to_detail(task, analysis_id=analysis_id)

    async def resolve_task_identifier(
        self,
        user: User,
        identifier: str,
    ) -> TaskDetailResponse:
        try:
            task_uuid = UUID(identifier)
        except ValueError:
            task = await self.tasks.get_by_celery_task_id(identifier)
        else:
            task = await self.tasks.get_by_id(task_uuid)

        if task is None:
            raise NotFoundError("Task not found")
        await self._require_view(user, task)
        analysis_id = None
        if task.result_json and "analysis_id" in task.result_json:
            raw = task.result_json.get("analysis_id")
            if raw:
                analysis_id = UUID(str(raw))
        return self._to_detail(task, analysis_id=analysis_id)

    async def list_tasks(
        self,
        user: User,
        *,
        organization_id: UUID | None = None,
        status: TaskStatus | None = None,
        task_type: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[TaskSummaryResponse], int]:
        if organization_id is not None:
            await self.org_auth.require_membership(organization_id, user.id)
            items, total = await self.tasks.list_organization_tasks(
                organization_id=organization_id,
                status=status,
                task_type=task_type,
                limit=limit,
                offset=offset,
            )
        else:
            items, total = await self.tasks.list_tasks(
                user_id=user.id,
                organization_id=None,
                status=status,
                task_type=task_type,
                limit=limit,
                offset=offset,
            )
        return [self._to_summary(item) for item in items], total

    async def cancel_task(
        self,
        user: User,
        task_id: UUID,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> TaskCancelResponse:
        task = await self.tasks.get_by_id(task_id)
        if task is None:
            raise NotFoundError("Task not found")
        await self._require_cancel(user, task)

        if task.status in TERMINAL_STATUSES:
            return TaskCancelResponse(
                id=task.id,
                status=task.status,
                cancelled_at=task.cancelled_at,
            )

        now = datetime.now(UTC)
        updated = await self.tasks.update(
            task,
            status=TaskStatus.CANCELLED,
            cancelled_at=now,
            completed_at=now,
        )

        if updated.celery_task_id:
            from app.workers.celery_app import celery_app

            try:
                celery_app.control.revoke(updated.celery_task_id, terminate=False)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to revoke Celery task %s: %s",
                    updated.celery_task_id,
                    exc.__class__.__name__,
                )

        await self.audit.record_event(
            action="task.cancelled",
            actor_user_id=user.id,
            organization_id=updated.organization_id,
            resource_type="background_task",
            resource_id=updated.id,
            request_context=audit_context,
            metadata={"task_type": updated.task_type},
        )
        return TaskCancelResponse(
            id=updated.id,
            status=updated.status,
            cancelled_at=updated.cancelled_at,
        )

    async def mark_running(self, task_id: UUID, *, progress: int = 0) -> None:
        task = await self.tasks.get_by_id(task_id)
        if task is None or task.status in TERMINAL_STATUSES:
            return
        await self.tasks.update(
            task,
            status=TaskStatus.RUNNING,
            progress=progress,
            started_at=task.started_at or datetime.now(UTC),
        )

    async def mark_succeeded(
        self,
        task_id: UUID,
        result_json: dict[str, Any],
        *,
        progress: int = 100,
    ) -> None:
        task = await self.tasks.get_by_id(task_id)
        if task is None or task.status == TaskStatus.CANCELLED:
            return
        await self.tasks.update(
            task,
            status=TaskStatus.SUCCEEDED,
            progress=progress,
            result_json=result_json,
            completed_at=datetime.now(UTC),
        )

    async def mark_failed(
        self,
        task_id: UUID,
        *,
        error_code: str,
        error_message: str,
        result_json: dict[str, Any] | None = None,
    ) -> None:
        task = await self.tasks.get_by_id(task_id)
        if task is None or task.status == TaskStatus.CANCELLED:
            return
        safe_message = error_message[:500]
        await self.tasks.update(
            task,
            status=TaskStatus.FAILED,
            error_code=error_code,
            error_message=safe_message,
            result_json=result_json,
            completed_at=datetime.now(UTC),
        )

    async def cleanup_expired_tasks(self) -> int:
        cutoff = self._retention_cutoff()
        return await self.tasks.delete_expired_before(cutoff)

    async def validate_organization_scope(
        self,
        user: User,
        organization_id: UUID | None,
    ) -> None:
        if organization_id is None:
            return
        await self.org_auth.require_permission(
            organization_id, user.id, Permission.RESOURCE_CREATE
        )
