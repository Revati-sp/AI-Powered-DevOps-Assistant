from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies import CurrentUser, DBSession
from app.api.rate_limit import APIRateLimit
from app.models.provider_config import (
    LLMOperation,
    ProviderConfig,
    ProviderRoutingPolicy,
)
from app.schemas.common import APIResponse
from app.schemas.provider import (
    ProviderConfigPatchRequest,
    ProviderConfigResponse,
    ProviderRoutingPatchRequest,
    ProviderRoutingResponse,
)
from app.services.provider_service import (
    ProviderManagementService,
    is_provider_configured,
)

router = APIRouter(tags=["organization-providers"])


def _config_response(config: ProviderConfig) -> ProviderConfigResponse:
    return ProviderConfigResponse(
        id=config.id,
        organization_id=config.organization_id,
        provider_name=config.provider_name,
        enabled=config.enabled,
        default_model=config.default_model,
        timeout_seconds=config.timeout_seconds,
        max_retries=config.max_retries,
        priority=config.priority,
        max_output_tokens=config.max_output_tokens,
        secret_env_key=config.secret_env_key,
        base_url_env_key=config.base_url_env_key,
        model_env_key=config.model_env_key,
        configured=is_provider_configured(config),
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


def _routing_response(policy: ProviderRoutingPolicy) -> ProviderRoutingResponse:
    return ProviderRoutingResponse(
        id=policy.id,
        organization_id=policy.organization_id,
        operation=policy.operation,
        primary_provider=policy.primary_provider,
        fallback_providers=policy.fallback_providers,
        created_at=policy.created_at,
        updated_at=policy.updated_at,
    )


@router.get(
    "/organizations/{organization_id}/providers/configs",
    response_model=APIResponse[list[ProviderConfigResponse]],
)
async def list_org_provider_configs(
    organization_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[list[ProviderConfigResponse]]:
    service = ProviderManagementService(db)
    await service.require_org_owner(current_user, organization_id)
    configs = await service.list_configs(organization_id=organization_id)
    return APIResponse(
        success=True,
        data=[_config_response(item) for item in configs],
    )


@router.patch(
    "/organizations/{organization_id}/providers/configs/{provider_name}",
    response_model=APIResponse[ProviderConfigResponse],
)
async def patch_org_provider_config(
    organization_id: UUID,
    provider_name: str,
    payload: ProviderConfigPatchRequest,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[ProviderConfigResponse]:
    service = ProviderManagementService(db)
    await service.require_org_owner(current_user, organization_id)
    config = await service.patch_config(
        organization_id=organization_id,
        provider_name=provider_name,
        enabled=payload.enabled,
        default_model=payload.default_model,
        timeout_seconds=payload.timeout_seconds,
        max_retries=payload.max_retries,
        priority=payload.priority,
        max_output_tokens=payload.max_output_tokens,
    )
    return APIResponse(success=True, data=_config_response(config))


@router.get(
    "/organizations/{organization_id}/providers/routing",
    response_model=APIResponse[list[ProviderRoutingResponse]],
)
async def list_org_provider_routing(
    organization_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[list[ProviderRoutingResponse]]:
    service = ProviderManagementService(db)
    await service.require_org_owner(current_user, organization_id)
    policies = await service.list_routing(organization_id=organization_id)
    return APIResponse(
        success=True,
        data=[_routing_response(item) for item in policies],
    )


@router.patch(
    "/organizations/{organization_id}/providers/routing/{operation}",
    response_model=APIResponse[ProviderRoutingResponse],
)
async def patch_org_provider_routing(
    organization_id: UUID,
    operation: LLMOperation,
    payload: ProviderRoutingPatchRequest,
    db: DBSession,
    current_user: CurrentUser,
    _rl: APIRateLimit,
) -> APIResponse[ProviderRoutingResponse]:
    service = ProviderManagementService(db)
    await service.require_org_owner(current_user, organization_id)
    policy = await service.patch_routing(
        organization_id=organization_id,
        operation=operation,
        primary_provider=payload.primary_provider,
        fallback_providers=payload.fallback_providers,
    )
    return APIResponse(success=True, data=_routing_response(policy))
