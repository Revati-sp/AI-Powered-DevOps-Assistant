from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DBSession
from app.api.rate_limit import APIRateLimit
from app.schemas.common import APIResponse
from app.schemas.usage import (
    OrganizationQuotaPatchRequest,
    OrganizationQuotaResponse,
    OrganizationUsageResponse,
    UsageEventResponse,
    UsagePeriodSummary,
    UserUsageResponse,
)
from app.services.usage_quota_service import UsageQuotaService

router = APIRouter(tags=["usage"])


@router.get("/usage/me", response_model=APIResponse[UserUsageResponse])
async def get_my_usage(
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[UserUsageResponse]:
    data = await UsageQuotaService(db).get_my_usage(current_user)
    recent_events = data["recent_events"]
    assert isinstance(recent_events, list)
    return APIResponse(
        success=True,
        data=UserUsageResponse(
            user_id=current_user.id,
            daily=UsagePeriodSummary.model_validate(data["daily"]),
            monthly=UsagePeriodSummary.model_validate(data["monthly"]),
            recent_events=[
                UsageEventResponse.model_validate(item) for item in recent_events
            ],
        ),
    )


@router.get(
    "/organizations/{organization_id}/usage",
    response_model=APIResponse[OrganizationUsageResponse],
)
async def get_organization_usage(
    organization_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[OrganizationUsageResponse]:
    data = await UsageQuotaService(db).get_org_usage(current_user, organization_id)
    quota = data.get("quota")
    return APIResponse(
        success=True,
        data=OrganizationUsageResponse(
            organization_id=organization_id,
            daily=UsagePeriodSummary.model_validate(data["daily"]),
            monthly=UsagePeriodSummary.model_validate(data["monthly"]),
            quota=OrganizationQuotaResponse.model_validate(quota) if quota else None,
        ),
    )


@router.get(
    "/organizations/{organization_id}/quotas",
    response_model=APIResponse[OrganizationQuotaResponse | None],
)
async def get_organization_quotas(
    organization_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[OrganizationQuotaResponse | None]:
    quota = await UsageQuotaService(db).get_org_quota(current_user, organization_id)
    return APIResponse(
        success=True,
        data=OrganizationQuotaResponse.model_validate(quota) if quota else None,
    )


@router.patch(
    "/organizations/{organization_id}/quotas",
    response_model=APIResponse[OrganizationQuotaResponse],
)
async def patch_organization_quotas(
    organization_id: UUID,
    payload: OrganizationQuotaPatchRequest,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[OrganizationQuotaResponse]:
    unset: set[str] = set()
    if payload.clear_daily_limits:
        unset.update({"daily_token_limit", "daily_request_limit"})
    if payload.clear_monthly_limits:
        unset.update({"monthly_token_limit", "monthly_request_limit"})
    quota = await UsageQuotaService(db).patch_org_quota(
        current_user,
        organization_id,
        daily_token_limit=payload.daily_token_limit,
        daily_request_limit=payload.daily_request_limit,
        monthly_token_limit=payload.monthly_token_limit,
        monthly_request_limit=payload.monthly_request_limit,
        enforce_quotas=payload.enforce_quotas,
        unset_fields=unset,
    )
    return APIResponse(
        success=True, data=OrganizationQuotaResponse.model_validate(quota)
    )
