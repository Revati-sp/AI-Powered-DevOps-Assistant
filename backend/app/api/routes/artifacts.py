from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from app.api.dependencies import CurrentUser, DBSession
from app.models.generated_artifact import ArtifactType
from app.schemas.artifact_tags import (
    ArtifactTagAssignRequest,
    ArtifactTagCreateRequest,
    ArtifactTagResponse,
)
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
from app.schemas.pagination import Page, PageParams, SortParams, create_sort_params
from app.services.artifact_service import ArtifactService
from app.utils.request_context import build_audit_context

router = APIRouter(prefix="/artifacts", tags=["artifacts"])
_ArtifactSortParams = create_sort_params(
    frozenset(
        {"created_at", "updated_at", "name", "artifact_type", "current_version_number"}
    ),
    default_field="updated_at",
)


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
    pagination: Annotated[PageParams, Depends()],
    sorting: Annotated[SortParams, Depends(_ArtifactSortParams)],
    organization_id: UUID | None = None,
    search: str | None = Query(default=None, max_length=255),
    tags: list[str] | None = Query(default=None),
    favorites_only: bool = False,
    include_archived: bool = False,
    archived_only: bool = False,
    creator_id: UUID | None = None,
    artifact_type: ArtifactType | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    updated_from: datetime | None = None,
    updated_to: datetime | None = None,
) -> APIResponse[Page[ArtifactSummaryResponse]]:
    items, total = await ArtifactService(db).list_artifacts(
        current_user,
        organization_id=organization_id,
        limit=pagination.limit,
        offset=pagination.offset,
        search=search,
        tags=tags,
        favorites_only=favorites_only,
        include_archived=include_archived,
        archived_only=archived_only,
        creator_id=creator_id,
        artifact_type=artifact_type,
        created_from=created_from,
        created_to=created_to,
        updated_from=updated_from,
        updated_to=updated_to,
        sort_by=sorting.sort_by,
        sort_order=sorting.sort_order,
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


@router.get("/tags/list", response_model=APIResponse[list[ArtifactTagResponse]])
async def list_artifact_tags(
    db: DBSession,
    current_user: CurrentUser,
    organization_id: UUID | None = None,
) -> APIResponse[list[ArtifactTagResponse]]:
    result = await ArtifactService(db).list_tags(
        current_user, organization_id=organization_id
    )
    return APIResponse(success=True, data=result)


@router.post("/tags", response_model=APIResponse[ArtifactTagResponse])
async def create_artifact_tag(
    payload: ArtifactTagCreateRequest,
    db: DBSession,
    current_user: CurrentUser,
    organization_id: UUID | None = None,
) -> APIResponse[ArtifactTagResponse]:
    result = await ArtifactService(db).create_tag(
        current_user, payload, organization_id=organization_id
    )
    return APIResponse(success=True, data=result)


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


@router.post(
    "/{artifact_id}/tags",
    response_model=APIResponse[list[ArtifactTagResponse]],
)
async def add_artifact_tag(
    artifact_id: UUID,
    payload: ArtifactTagAssignRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[list[ArtifactTagResponse]]:
    result = await ArtifactService(db).add_tag(current_user, artifact_id, payload)
    return APIResponse(success=True, data=result)


@router.delete(
    "/{artifact_id}/tags/{tag_id}",
    response_model=APIResponse[list[ArtifactTagResponse]],
)
async def remove_artifact_tag(
    artifact_id: UUID,
    tag_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[list[ArtifactTagResponse]]:
    result = await ArtifactService(db).remove_tag(current_user, artifact_id, tag_id)
    return APIResponse(success=True, data=result)


@router.post("/{artifact_id}/favorite", response_model=APIResponse[dict[str, Any]])
async def favorite_artifact(
    artifact_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[dict[str, Any]]:
    await ArtifactService(db).favorite(current_user, artifact_id)
    return APIResponse(success=True, data={}, message="Artifact favorited")


@router.delete("/{artifact_id}/favorite", response_model=APIResponse[dict[str, Any]])
async def unfavorite_artifact(
    artifact_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[dict[str, Any]]:
    await ArtifactService(db).unfavorite(current_user, artifact_id)
    return APIResponse(success=True, data={}, message="Artifact unfavorited")


@router.post(
    "/{artifact_id}/archive",
    response_model=APIResponse[ArtifactSummaryResponse],
)
async def archive_artifact(
    artifact_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[ArtifactSummaryResponse]:
    result = await ArtifactService(db).archive(current_user, artifact_id)
    return APIResponse(success=True, data=result)


@router.post(
    "/{artifact_id}/unarchive",
    response_model=APIResponse[ArtifactSummaryResponse],
)
async def unarchive_artifact(
    artifact_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[ArtifactSummaryResponse]:
    result = await ArtifactService(db).unarchive(current_user, artifact_id)
    return APIResponse(success=True, data=result)
