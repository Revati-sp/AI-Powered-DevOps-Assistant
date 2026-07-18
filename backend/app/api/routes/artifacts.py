from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app.api.dependencies import CurrentUser, DBSession
from app.schemas.artifacts import (
    ArtifactCreateRequest,
    ArtifactDetailResponse,
    ArtifactDiffResponse,
    ArtifactRestoreResponse,
    ArtifactSummaryResponse,
    ArtifactUpdateRequest,
    ArtifactVersionCreateRequest,
    ArtifactVersionResponse,
)
from app.schemas.common import APIResponse
from app.schemas.pagination import Page, PageParams
from app.services.artifact_service import ArtifactService
from app.utils.request_context import build_audit_context

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.post("", response_model=APIResponse[ArtifactDetailResponse])
async def create_artifact(
    payload: ArtifactCreateRequest,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[ArtifactDetailResponse]:
    result = await ArtifactService(db).create(
        current_user, payload, audit_context=build_audit_context(request)
    )
    return APIResponse(success=True, data=result)


@router.get("", response_model=APIResponse[Page[ArtifactSummaryResponse]])
async def list_artifacts(
    db: DBSession,
    current_user: CurrentUser,
    pagination: PageParams = Depends(),
    organization_id: UUID | None = None,
) -> APIResponse[Page[ArtifactSummaryResponse]]:
    items, total = await ArtifactService(db).list_artifacts(
        current_user,
        organization_id=organization_id,
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


@router.get("/{artifact_id}", response_model=APIResponse[ArtifactDetailResponse])
async def get_artifact(
    artifact_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[ArtifactDetailResponse]:
    result = await ArtifactService(db).get_artifact(current_user, artifact_id)
    return APIResponse(success=True, data=result)


@router.patch("/{artifact_id}", response_model=APIResponse[ArtifactSummaryResponse])
async def update_artifact(
    artifact_id: UUID,
    payload: ArtifactUpdateRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[ArtifactSummaryResponse]:
    result = await ArtifactService(db).update_artifact(
        current_user, artifact_id, payload
    )
    return APIResponse(success=True, data=result)


@router.delete("/{artifact_id}", response_model=APIResponse[dict[str, Any]])
async def delete_artifact(
    artifact_id: UUID,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[dict[str, Any]]:
    await ArtifactService(db).delete_artifact(
        current_user, artifact_id, audit_context=build_audit_context(request)
    )
    return APIResponse(success=True, data={}, message="Artifact deleted")


@router.get(
    "/{artifact_id}/versions",
    response_model=APIResponse[Page[ArtifactVersionResponse]],
)
async def list_versions(
    artifact_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    pagination: PageParams = Depends(),
) -> APIResponse[Page[ArtifactVersionResponse]]:
    items, total = await ArtifactService(db).list_versions(
        current_user,
        artifact_id,
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
    "/{artifact_id}/versions/{version_number}",
    response_model=APIResponse[ArtifactVersionResponse],
)
async def get_version(
    artifact_id: UUID,
    version_number: int,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[ArtifactVersionResponse]:
    result = await ArtifactService(db).get_version(
        current_user, artifact_id, version_number
    )
    return APIResponse(success=True, data=result)


@router.post(
    "/{artifact_id}/versions",
    response_model=APIResponse[ArtifactVersionResponse],
)
async def add_version(
    artifact_id: UUID,
    payload: ArtifactVersionCreateRequest,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[ArtifactVersionResponse]:
    result = await ArtifactService(db).add_version(
        current_user,
        artifact_id,
        payload,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data=result)


@router.post(
    "/{artifact_id}/versions/{version_number}/restore",
    response_model=APIResponse[ArtifactRestoreResponse],
)
async def restore_version(
    artifact_id: UUID,
    version_number: int,
    request: Request,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[ArtifactRestoreResponse]:
    result = await ArtifactService(db).restore_version(
        current_user,
        artifact_id,
        version_number,
        audit_context=build_audit_context(request),
    )
    return APIResponse(success=True, data=result)


@router.get("/{artifact_id}/diff", response_model=APIResponse[ArtifactDiffResponse])
async def diff_versions(
    artifact_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    from_version: int = Query(alias="from_version"),
    to_version: int = Query(alias="to_version"),
) -> APIResponse[ArtifactDiffResponse]:
    result = await ArtifactService(db).diff_versions(
        current_user,
        artifact_id,
        from_version=from_version,
        to_version=to_version,
    )
    return APIResponse(success=True, data=result)
