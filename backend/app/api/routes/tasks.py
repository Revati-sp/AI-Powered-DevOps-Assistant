from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import CurrentUser, DBSession
from app.api.rate_limit import APIRateLimit
from app.models.background_task import TaskStatus
from app.schemas.common import APIResponse
from app.schemas.pagination import Page, PageParams
from app.schemas.tasks import (
    TaskCancelResponse,
    TaskDetailResponse,
    TaskSummaryResponse,
)
from app.services.task_service import TaskService
from app.utils.request_context import build_audit_context

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=APIResponse[Page[TaskSummaryResponse]])
async def list_tasks(
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
    status: TaskStatus | None = None,
    task_type: str | None = None,
    organization_id: UUID | None = None,
    pagination: PageParams = Depends(),
) -> APIResponse[Page[TaskSummaryResponse]]:
    items, total = await TaskService(db).list_tasks(
        current_user,
        organization_id=organization_id,
        status=status,
        task_type=task_type,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return APIResponse(
        success=True,
        data=Page(
            items=items,
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
        ),
    )


@router.get("/{task_id}", response_model=APIResponse[TaskDetailResponse])
async def get_task(
    task_id: str,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[TaskDetailResponse]:
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        result = await TaskService(db).resolve_task_identifier(current_user, task_id)
    else:
        result = await TaskService(db).get_task(current_user, task_uuid)
    return APIResponse(success=True, data=result)


@router.post("/{task_id}/cancel", response_model=APIResponse[TaskCancelResponse])
async def cancel_task(
    task_id: UUID,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[TaskCancelResponse]:
    result = await TaskService(db).cancel_task(
        current_user,
        task_id,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data=result)
