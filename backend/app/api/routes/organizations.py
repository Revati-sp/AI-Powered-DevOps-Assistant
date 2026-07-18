from uuid import UUID

from fastapi import APIRouter, Request

from app.api.dependencies import CurrentUser, DBSession
from app.api.dependencies_org import PaginationParams
from app.api.rate_limit import APIRateLimit
from app.schemas.common import APIResponse
from app.schemas.organization import (
    AddMemberRequest,
    OrganizationCreate,
    OrganizationMemberResponse,
    OrganizationResponse,
    OrganizationUpdate,
    UpdateMemberRequest,
)
from app.schemas.pagination import Page
from app.services.organization_service import OrganizationService
from app.utils.request_context import build_audit_context

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=APIResponse[OrganizationResponse])
async def create_organization(
    payload: OrganizationCreate,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[OrganizationResponse]:
    data = await OrganizationService(db).create(
        current_user, payload, audit_context=build_audit_context(request)
    )
    return APIResponse(success=True, data=data, message="Organization created")


@router.get("", response_model=APIResponse[Page[OrganizationResponse]])
async def list_organizations(
    db: DBSession,
    current_user: CurrentUser,
    pagination: PaginationParams,
    _rl: APIRateLimit,
) -> APIResponse[Page[OrganizationResponse]]:
    data = await OrganizationService(db).list_for_user(current_user, pagination)
    return APIResponse(success=True, data=data)


@router.get("/{organization_id}", response_model=APIResponse[OrganizationResponse])
async def get_organization(
    organization_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[OrganizationResponse]:
    data = await OrganizationService(db).get(current_user, organization_id)
    return APIResponse(success=True, data=data)


@router.patch("/{organization_id}", response_model=APIResponse[OrganizationResponse])
async def update_organization(
    organization_id: UUID,
    payload: OrganizationUpdate,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[OrganizationResponse]:
    data = await OrganizationService(db).update(
        current_user,
        organization_id,
        payload,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data=data)


@router.delete(
    "/{organization_id}",
    response_model=APIResponse[dict[str, str]],
)
async def delete_organization(
    organization_id: UUID,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[dict[str, str]]:
    await OrganizationService(db).delete(
        current_user, organization_id, audit_context=build_audit_context(request)
    )
    return APIResponse(success=True, data={"status": "deleted"})


@router.get(
    "/{organization_id}/members",
    response_model=APIResponse[Page[OrganizationMemberResponse]],
)
async def list_members(
    organization_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    pagination: PaginationParams,
    _rl: APIRateLimit,
) -> APIResponse[Page[OrganizationMemberResponse]]:
    data = await OrganizationService(db).list_members(
        current_user, organization_id, pagination
    )
    return APIResponse(success=True, data=data)


@router.post(
    "/{organization_id}/members",
    response_model=APIResponse[OrganizationMemberResponse],
)
async def add_member(
    organization_id: UUID,
    payload: AddMemberRequest,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[OrganizationMemberResponse]:
    data = await OrganizationService(db).add_member(
        current_user,
        organization_id,
        payload,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data=data, message="Member added")


@router.patch(
    "/{organization_id}/members/{user_id}",
    response_model=APIResponse[OrganizationMemberResponse],
)
async def update_member(
    organization_id: UUID,
    user_id: UUID,
    payload: UpdateMemberRequest,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[OrganizationMemberResponse]:
    data = await OrganizationService(db).update_member(
        current_user,
        organization_id,
        user_id,
        payload,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data=data)


@router.delete(
    "/{organization_id}/members/{user_id}",
    response_model=APIResponse[dict[str, str]],
)
async def remove_member(
    organization_id: UUID,
    user_id: UUID,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[dict[str, str]]:
    await OrganizationService(db).remove_member(
        current_user,
        organization_id,
        user_id,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data={"status": "removed"})
