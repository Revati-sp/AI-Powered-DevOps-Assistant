from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import CurrentUser, DBSession
from app.schemas.common import APIResponse, ORMModel
from app.schemas.pagination import Page, PageParams
from app.schemas.policies import (
    PolicyPackCreateRequest,
    PolicyPackDetailResponse,
    PolicyPackResponse,
    PolicyPackUpdateRequest,
    PolicyRuleCreateRequest,
    PolicyRuleResponse,
    PolicyRuleUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.policy_service import PolicyService
from app.services.rbac import OrganizationAuthService, Permission
from app.utils.audit_redaction import redact_metadata
from app.utils.request_context import build_audit_context

router = APIRouter(prefix="/organizations", tags=["policy-packs"])


@router.post(
    "/{organization_id}/policy-packs",
    response_model=APIResponse[PolicyPackResponse],
)
async def create_policy_pack(
    organization_id: UUID,
    payload: PolicyPackCreateRequest,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[PolicyPackResponse]:
    result = await PolicyService(db).create_pack(
        current_user,
        organization_id,
        payload,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data=result)


@router.get(
    "/{organization_id}/policy-packs",
    response_model=APIResponse[Page[PolicyPackResponse]],
)
async def list_policy_packs(
    organization_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    pagination: PageParams = Depends(),
) -> APIResponse[Page[PolicyPackResponse]]:
    items, total = await PolicyService(db).list_packs(
        current_user,
        organization_id,
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


@router.get(
    "/{organization_id}/policy-packs/{policy_pack_id}",
    response_model=APIResponse[PolicyPackDetailResponse],
)
async def get_policy_pack(
    organization_id: UUID,
    policy_pack_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[PolicyPackDetailResponse]:
    result = await PolicyService(db).get_pack(
        current_user, organization_id, policy_pack_id
    )
    return APIResponse(success=True, data=result)


@router.patch(
    "/{organization_id}/policy-packs/{policy_pack_id}",
    response_model=APIResponse[PolicyPackResponse],
)
async def update_policy_pack(
    organization_id: UUID,
    policy_pack_id: UUID,
    payload: PolicyPackUpdateRequest,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[PolicyPackResponse]:
    result = await PolicyService(db).update_pack(
        current_user,
        organization_id,
        policy_pack_id,
        payload,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data=result)


@router.delete(
    "/{organization_id}/policy-packs/{policy_pack_id}",
    response_model=APIResponse[dict[str, Any]],
)
async def delete_policy_pack(
    organization_id: UUID,
    policy_pack_id: UUID,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[dict[str, Any]]:
    await PolicyService(db).delete_pack(
        current_user,
        organization_id,
        policy_pack_id,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data={}, message="Policy pack deleted")


@router.post(
    "/{organization_id}/policy-packs/{policy_pack_id}/rules",
    response_model=APIResponse[PolicyRuleResponse],
)
async def create_policy_rule(
    organization_id: UUID,
    policy_pack_id: UUID,
    payload: PolicyRuleCreateRequest,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[PolicyRuleResponse]:
    result = await PolicyService(db).add_rule(
        current_user,
        organization_id,
        policy_pack_id,
        payload,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data=result)


@router.patch(
    "/{organization_id}/policy-packs/{policy_pack_id}/rules/{rule_id}",
    response_model=APIResponse[PolicyRuleResponse],
)
async def update_policy_rule(
    organization_id: UUID,
    policy_pack_id: UUID,
    rule_id: UUID,
    payload: PolicyRuleUpdateRequest,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[PolicyRuleResponse]:
    result = await PolicyService(db).update_rule(
        current_user,
        organization_id,
        policy_pack_id,
        rule_id,
        payload,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data=result)


@router.delete(
    "/{organization_id}/policy-packs/{policy_pack_id}/rules/{rule_id}",
    response_model=APIResponse[dict[str, Any]],
)
async def delete_policy_rule(
    organization_id: UUID,
    policy_pack_id: UUID,
    rule_id: UUID,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[dict[str, Any]]:
    await PolicyService(db).delete_rule(
        current_user,
        organization_id,
        policy_pack_id,
        rule_id,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data={}, message="Policy rule deleted")


class AuditEventResponse(ORMModel):
    id: UUID
    actor_user_id: UUID | None
    organization_id: UUID | None
    action: str
    resource_type: str
    resource_id: UUID | None
    request_id: str
    ip_address: str | None
    user_agent: str | None
    metadata_json: dict[str, Any] | None
    created_at: datetime


audit_router = APIRouter(prefix="/organizations", tags=["audit"])


@audit_router.get(
    "/{organization_id}/audit-events",
    response_model=APIResponse[Page[AuditEventResponse]],
)
async def list_audit_events(
    organization_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    pagination: PageParams = Depends(),
    action: str | None = None,
    actor_user_id: UUID | None = None,
    resource_type: str | None = None,
    resource_id: UUID | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
) -> APIResponse[Page[AuditEventResponse]]:
    await OrganizationAuthService(db).require_permission(
        organization_id, current_user.id, Permission.AUDIT_READ
    )
    events, total = await AuditService(db).list_events(
        organization_id,
        limit=pagination.limit,
        offset=pagination.offset,
        action=action,
        actor_user_id=actor_user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        created_from=created_from,
        created_to=created_to,
    )
    items = [
        AuditEventResponse.model_validate(
            {
                **event.__dict__,
                "metadata_json": redact_metadata(event.metadata_json)
                if event.metadata_json
                else None,
            }
        )
        for event in events
    ]
    return APIResponse(
        success=True,
        data=Page(
            items=items,
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
        ),
    )
