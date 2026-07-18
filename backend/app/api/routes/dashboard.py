from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DBSession
from app.api.rate_limit import APIRateLimit
from app.schemas.common import APIResponse
from app.schemas.dashboard import (
    DashboardActivity,
    DashboardFindings,
    DashboardSummary,
    DashboardTasks,
    TimeRange,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=APIResponse[DashboardSummary])
async def get_summary(
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
    organization_id: UUID | None = None,
    time_range: TimeRange = "7d",
) -> APIResponse[DashboardSummary]:
    return APIResponse(
        success=True,
        data=await DashboardService(db).summary(
            current_user, organization_id=organization_id, time_range=time_range
        ),
    )


@router.get("/activity", response_model=APIResponse[DashboardActivity])
async def get_activity(
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
    organization_id: UUID | None = None,
    time_range: TimeRange = "7d",
) -> APIResponse[DashboardActivity]:
    return APIResponse(
        success=True,
        data=await DashboardService(db).activity(
            current_user, organization_id=organization_id, time_range=time_range
        ),
    )


@router.get("/findings", response_model=APIResponse[DashboardFindings])
async def get_findings(
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
    organization_id: UUID | None = None,
    time_range: TimeRange = "7d",
) -> APIResponse[DashboardFindings]:
    return APIResponse(
        success=True,
        data=await DashboardService(db).findings(
            current_user, organization_id=organization_id, time_range=time_range
        ),
    )


@router.get("/tasks", response_model=APIResponse[DashboardTasks])
async def get_tasks(
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
    organization_id: UUID | None = None,
    time_range: TimeRange = "7d",
) -> APIResponse[DashboardTasks]:
    return APIResponse(
        success=True,
        data=await DashboardService(db).tasks(
            current_user, organization_id=organization_id, time_range=time_range
        ),
    )
