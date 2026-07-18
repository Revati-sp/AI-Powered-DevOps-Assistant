from __future__ import annotations

from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Query

from app.api.dependencies import CurrentUser, DBSession
from app.models.organization import Organization, OrganizationMember
from app.schemas.pagination import PageParams
from app.services.rbac import OrganizationAuthService, Permission


async def get_page_params(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PageParams:
    return PageParams(limit=limit, offset=offset)


PaginationParams = Annotated[PageParams, Depends(get_page_params)]


def require_org_permission(
    permission: Permission,
) -> Callable[..., object]:
    async def _dependency(
        organization_id: UUID,
        current_user: CurrentUser,
        db: DBSession,
    ) -> tuple[Organization, OrganizationMember]:
        return await OrganizationAuthService(db).require_permission(
            organization_id, current_user.id, permission
        )

    return _dependency


OrgReadContext = Annotated[
    tuple[Organization, OrganizationMember],
    Depends(require_org_permission(Permission.ORGANIZATION_READ)),
]
OrgUpdateContext = Annotated[
    tuple[Organization, OrganizationMember],
    Depends(require_org_permission(Permission.ORGANIZATION_UPDATE)),
]
OrgDeleteContext = Annotated[
    tuple[Organization, OrganizationMember],
    Depends(require_org_permission(Permission.ORGANIZATION_DELETE)),
]
OrgMemberManageContext = Annotated[
    tuple[Organization, OrganizationMember],
    Depends(require_org_permission(Permission.MEMBER_MANAGE)),
]
