from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.organization import Organization, OrganizationMember, OrgRole


class OrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, organization_id: UUID) -> Organization | None:
        result = await self.session.execute(
            select(Organization).where(
                Organization.id == organization_id,
                Organization.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Organization | None:
        result = await self.session.execute(
            select(Organization).where(
                Organization.slug == slug,
                Organization.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        name: str,
        slug: str,
        created_by: UUID,
    ) -> Organization:
        org = Organization(name=name, slug=slug, created_by=created_by)
        self.session.add(org)
        await self.session.flush()
        await self.session.refresh(org)
        return org

    async def add_member(
        self,
        *,
        organization_id: UUID,
        user_id: UUID,
        role: OrgRole,
    ) -> OrganizationMember:
        member = OrganizationMember(
            organization_id=organization_id,
            user_id=user_id,
            role=role,
        )
        self.session.add(member)
        await self.session.flush()
        await self.session.refresh(member)
        return member

    async def list_for_user(
        self, user_id: UUID, *, limit: int, offset: int
    ) -> tuple[list[Organization], int]:
        base = (
            select(Organization)
            .join(OrganizationMember)
            .where(
                OrganizationMember.user_id == user_id,
                Organization.deleted_at.is_(None),
            )
            .order_by(Organization.created_at.desc())
        )
        count_result = await self.session.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = int(count_result.scalar_one())

        result = await self.session.execute(base.limit(limit).offset(offset))
        return list(result.scalars().all()), total

    async def update(
        self,
        org: Organization,
        *,
        name: str | None = None,
        slug: str | None = None,
    ) -> Organization:
        if name is not None:
            org.name = name
        if slug is not None:
            org.slug = slug
        org.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(org)
        return org

    async def soft_delete(self, org: Organization) -> Organization:
        org.deleted_at = datetime.now(UTC)
        org.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(org)
        return org

    async def get_member(
        self, organization_id: UUID, user_id: UUID
    ) -> OrganizationMember | None:
        result = await self.session.execute(
            select(OrganizationMember)
            .options(selectinload(OrganizationMember.user))
            .where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_members(
        self, organization_id: UUID, *, limit: int, offset: int
    ) -> tuple[list[OrganizationMember], int]:
        base = (
            select(OrganizationMember)
            .options(selectinload(OrganizationMember.user))
            .where(OrganizationMember.organization_id == organization_id)
            .order_by(OrganizationMember.created_at.asc())
        )
        count_result = await self.session.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = int(count_result.scalar_one())

        result = await self.session.execute(base.limit(limit).offset(offset))
        return list(result.scalars().all()), total

    async def update_member_role(
        self, member: OrganizationMember, role: OrgRole
    ) -> OrganizationMember:
        member.role = role
        member.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(member)
        return member

    async def remove_member(self, member: OrganizationMember) -> None:
        await self.session.delete(member)
        await self.session.flush()

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
