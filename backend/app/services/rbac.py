from __future__ import annotations

from enum import Enum
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.organization import Organization, OrganizationMember, OrgRole


class Permission(str, Enum):
    ORGANIZATION_READ = "organization.read"
    ORGANIZATION_UPDATE = "organization.update"
    ORGANIZATION_DELETE = "organization.delete"
    MEMBER_MANAGE = "member.manage"
    ARTIFACT_READ = "artifact.read"
    ARTIFACT_WRITE = "artifact.write"
    POLICY_READ = "policy.read"
    POLICY_MANAGE = "policy.manage"
    AUDIT_READ = "audit.read"
    TASK_CANCEL = "task.cancel"
    RESOURCE_CREATE = "resource.create"


ROLE_PERMISSIONS: dict[OrgRole, set[Permission]] = {
    OrgRole.OWNER: set(Permission),
    OrgRole.ADMIN: {
        Permission.ORGANIZATION_READ,
        Permission.ORGANIZATION_UPDATE,
        Permission.MEMBER_MANAGE,
        Permission.ARTIFACT_READ,
        Permission.ARTIFACT_WRITE,
        Permission.POLICY_READ,
        Permission.POLICY_MANAGE,
        Permission.AUDIT_READ,
        Permission.TASK_CANCEL,
        Permission.RESOURCE_CREATE,
    },
    OrgRole.MEMBER: {
        Permission.ORGANIZATION_READ,
        Permission.ARTIFACT_READ,
        Permission.ARTIFACT_WRITE,
        Permission.POLICY_READ,
        Permission.RESOURCE_CREATE,
        Permission.TASK_CANCEL,
    },
    OrgRole.VIEWER: {
        Permission.ORGANIZATION_READ,
        Permission.ARTIFACT_READ,
        Permission.POLICY_READ,
    },
}


def role_has_permission(role: OrgRole, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())


class OrganizationAuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_membership(
        self, organization_id: UUID, user_id: UUID
    ) -> OrganizationMember | None:
        result = await self.session.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_active_organization(self, organization_id: UUID) -> Organization:
        result = await self.session.execute(
            select(Organization).where(
                Organization.id == organization_id,
                Organization.deleted_at.is_(None),
            )
        )
        org = result.scalar_one_or_none()
        if org is None:
            raise NotFoundError("Organization not found")
        return org

    async def require_membership(
        self, organization_id: UUID, user_id: UUID
    ) -> tuple[Organization, OrganizationMember]:
        org = await self.get_active_organization(organization_id)
        membership = await self.get_membership(organization_id, user_id)
        if membership is None:
            # Non-leaking response for cross-org probes.
            raise NotFoundError("Organization not found")
        return org, membership

    async def require_permission(
        self,
        organization_id: UUID,
        user_id: UUID,
        permission: Permission,
    ) -> tuple[Organization, OrganizationMember]:
        org, membership = await self.require_membership(organization_id, user_id)
        if not role_has_permission(membership.role, permission):
            raise ForbiddenError("Insufficient organization permissions")
        return org, membership

    async def count_owners(self, organization_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(OrganizationMember)
            .where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.role == OrgRole.OWNER,
            )
        )
        return int(result.scalar_one())
