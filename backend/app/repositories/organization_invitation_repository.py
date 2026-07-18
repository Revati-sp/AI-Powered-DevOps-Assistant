from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.organization import OrgRole
from app.models.organization_invitation import InvitationStatus, OrganizationInvitation


class OrganizationInvitationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        organization_id: UUID,
        email: str,
        role: OrgRole,
        token_hash: str,
        invited_by_user_id: UUID,
        expires_at: datetime,
        created_ip: str | None = None,
    ) -> OrganizationInvitation:
        invitation = OrganizationInvitation(
            organization_id=organization_id,
            email=email.lower(),
            role=role,
            token_hash=token_hash,
            invited_by_user_id=invited_by_user_id,
            expires_at=expires_at,
            created_ip=created_ip,
            status=InvitationStatus.PENDING,
        )
        self.session.add(invitation)
        await self.session.flush()
        await self.session.refresh(invitation)
        return invitation

    async def get_by_id(
        self, invitation_id: UUID, *, organization_id: UUID | None = None
    ) -> OrganizationInvitation | None:
        query = select(OrganizationInvitation).where(
            OrganizationInvitation.id == invitation_id
        )
        if organization_id is not None:
            query = query.where(
                OrganizationInvitation.organization_id == organization_id
            )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_hash_for_update(
        self, token_hash: str
    ) -> OrganizationInvitation | None:
        result = await self.session.execute(
            select(OrganizationInvitation)
            .options(selectinload(OrganizationInvitation.organization))
            .where(OrganizationInvitation.token_hash == token_hash)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_active_pending(
        self, organization_id: UUID, email: str
    ) -> OrganizationInvitation | None:
        now = datetime.now(UTC)
        result = await self.session.execute(
            select(OrganizationInvitation).where(
                OrganizationInvitation.organization_id == organization_id,
                OrganizationInvitation.email == email.lower(),
                OrganizationInvitation.status == InvitationStatus.PENDING,
                OrganizationInvitation.expires_at > now,
                OrganizationInvitation.revoked_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_for_organization(
        self, organization_id: UUID, *, limit: int, offset: int
    ) -> tuple[list[OrganizationInvitation], int]:
        base = (
            select(OrganizationInvitation)
            .where(OrganizationInvitation.organization_id == organization_id)
            .order_by(OrganizationInvitation.created_at.desc())
        )
        count_result = await self.session.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = int(count_result.scalar_one())
        result = await self.session.execute(base.limit(limit).offset(offset))
        return list(result.scalars().all()), total

    async def update_token(
        self,
        invitation: OrganizationInvitation,
        *,
        token_hash: str,
        expires_at: datetime,
    ) -> OrganizationInvitation:
        invitation.token_hash = token_hash
        invitation.expires_at = expires_at
        await self.session.flush()
        await self.session.refresh(invitation)
        return invitation
