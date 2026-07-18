from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.organization import Organization, OrganizationMember, OrgRole
from app.models.user import User, UserRole
from app.services.rbac import (
    ROLE_PERMISSIONS,
    OrganizationAuthService,
    Permission,
    role_has_permission,
)


async def _seed_org_with_member(
    db_session,
    *,
    member_role: OrgRole = OrgRole.VIEWER,
) -> tuple[Organization, User, OrganizationMember]:
    owner = User(
        id=uuid4(),
        email="rbac-owner@example.com",
        username="rbacowner",
        hashed_password="hashed",
        role=UserRole.USER,
        is_active=True,
    )
    member = User(
        id=uuid4(),
        email="rbac-member@example.com",
        username="rbacmember",
        hashed_password="hashed",
        role=UserRole.USER,
        is_active=True,
    )
    org = Organization(
        id=uuid4(),
        name="RBAC Org",
        slug=f"rbac-org-{uuid4().hex[:8]}",
        created_by=owner.id,
    )
    owner_membership = OrganizationMember(
        id=uuid4(),
        organization_id=org.id,
        user_id=owner.id,
        role=OrgRole.OWNER,
    )
    member_membership = OrganizationMember(
        id=uuid4(),
        organization_id=org.id,
        user_id=member.id,
        role=member_role,
    )
    db_session.add_all([owner, member, org, owner_membership, member_membership])
    await db_session.flush()
    return org, member, member_membership


@pytest.mark.asyncio
async def test_require_permission_denied_for_viewer(db_session) -> None:
    org, member, _ = await _seed_org_with_member(db_session, member_role=OrgRole.VIEWER)
    auth = OrganizationAuthService(db_session)

    with pytest.raises(ForbiddenError, match="Insufficient organization permissions"):
        await auth.require_permission(org.id, member.id, Permission.POLICY_MANAGE)


@pytest.mark.asyncio
async def test_require_membership_denied_for_outsider(db_session) -> None:
    org, _, _ = await _seed_org_with_member(db_session)
    outsider = User(
        id=uuid4(),
        email="outsider@example.com",
        username="outsider",
        hashed_password="hashed",
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add(outsider)
    await db_session.flush()

    auth = OrganizationAuthService(db_session)
    with pytest.raises(NotFoundError, match="Organization not found"):
        await auth.require_membership(org.id, outsider.id)


@pytest.mark.asyncio
async def test_get_active_organization_rejects_soft_deleted(db_session) -> None:
    org, member, _ = await _seed_org_with_member(db_session)
    org.deleted_at = datetime.now(UTC)
    await db_session.flush()

    auth = OrganizationAuthService(db_session)
    with pytest.raises(NotFoundError, match="Organization not found"):
        await auth.get_active_organization(org.id)

    with pytest.raises(NotFoundError, match="Organization not found"):
        await auth.require_membership(org.id, member.id)


@pytest.mark.asyncio
async def test_count_owners_and_role_has_permission(db_session) -> None:
    org, _, _ = await _seed_org_with_member(db_session)
    auth = OrganizationAuthService(db_session)

    assert await auth.count_owners(org.id) == 1
    assert role_has_permission(OrgRole.VIEWER, Permission.ORGANIZATION_READ) is True
    assert role_has_permission(OrgRole.VIEWER, Permission.MEMBER_MANAGE) is False
    assert role_has_permission(OrgRole.ADMIN, Permission.AUDIT_READ) is True


@pytest.mark.parametrize(
    ("role", "permission"),
    [
        (role, permission)
        for role, permissions in ROLE_PERMISSIONS.items()
        for permission in Permission
    ],
)
def test_role_permission_matrix(role: OrgRole, permission: Permission) -> None:
    expected = permission in ROLE_PERMISSIONS[role]
    assert role_has_permission(role, permission) is expected
