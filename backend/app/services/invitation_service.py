from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.core.security import generate_secure_token, hash_secure_token
from app.models.organization import OrgRole
from app.models.organization_invitation import InvitationStatus, OrganizationInvitation
from app.models.user import User
from app.repositories.organization_invitation_repository import (
    OrganizationInvitationRepository,
)
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.invitation import (
    CreateInvitationRequest,
    InvitationAcceptResponse,
    InvitationResponse,
)
from app.schemas.pagination import Page, PageParams
from app.services.audit_service import AuditRequestContext, AuditService
from app.services.email_service import EmailService
from app.services.onboarding_service import OnboardingService
from app.services.rbac import OrganizationAuthService, Permission

logger = get_logger(__name__)


class InvitationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.invitations = OrganizationInvitationRepository(session)
        self.orgs = OrganizationRepository(session)
        self.users = UserRepository(session)
        self.auth = OrganizationAuthService(session)
        self.audit = AuditService(session)
        self.email = EmailService()

    def _to_response(self, invitation: OrganizationInvitation) -> InvitationResponse:
        return InvitationResponse.model_validate(invitation)

    async def create(
        self,
        user: User,
        organization_id: UUID,
        payload: CreateInvitationRequest,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> InvitationResponse:
        _, actor = await self.auth.require_permission(
            organization_id, user.id, Permission.MEMBER_MANAGE
        )
        if payload.role == OrgRole.OWNER and actor.role != OrgRole.OWNER:
            raise ForbiddenError("Only owners may assign the owner role")

        org = await self.auth.get_active_organization(organization_id)
        email = payload.email.lower()

        target_user = await self.users.get_by_email(email)
        if target_user is not None:
            member = await self.orgs.get_member(organization_id, target_user.id)
            if member is not None:
                raise ConflictError("User is already a member of this organization")

        active = await self.invitations.get_active_pending(organization_id, email)
        if active is not None:
            raise ConflictError("An active invitation already exists for this email")

        settings = get_settings()
        raw_token = generate_secure_token()
        invitation = await self.invitations.create(
            organization_id=organization_id,
            email=email,
            role=payload.role,
            token_hash=hash_secure_token(raw_token),
            invited_by_user_id=user.id,
            expires_at=datetime.now(UTC)
            + timedelta(hours=settings.invitation_expire_hours),
            created_ip=audit_context.ip_address if audit_context else None,
        )
        invite_url = f"{settings.frontend_base_url.rstrip('/')}/invitations/accept?token={raw_token}"
        await self.email.send_organization_invitation(
            to=email,
            invite_url=invite_url,
            organization_name=org.name,
            role=payload.role.value,
        )
        await self.audit.record_event(
            action="organization.invitation.created",
            actor_user_id=user.id,
            organization_id=organization_id,
            resource_type="organization_invitation",
            resource_id=invitation.id,
            request_context=audit_context,
            metadata={"email": email, "role": payload.role.value},
            fail_on_error=True,
        )
        try:
            await OnboardingService(self.session).mark_flag(
                user.id, invite_team_completed=True
            )
        except Exception:  # noqa: BLE001
            logger.exception("Failed to mark invite_team_completed onboarding flag")
        return self._to_response(invitation)

    async def list_for_organization(
        self,
        user: User,
        organization_id: UUID,
        params: PageParams,
    ) -> Page[InvitationResponse]:
        await self.auth.require_permission(
            organization_id, user.id, Permission.MEMBER_MANAGE
        )
        invitations, total = await self.invitations.list_for_organization(
            organization_id,
            limit=params.limit,
            offset=params.offset,
        )
        return Page(
            items=[self._to_response(item) for item in invitations],
            total=total,
            limit=params.limit,
            offset=params.offset,
        )

    async def resend(
        self,
        user: User,
        organization_id: UUID,
        invitation_id: UUID,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> InvitationResponse:
        await self.auth.require_permission(
            organization_id, user.id, Permission.MEMBER_MANAGE
        )
        invitation = await self.invitations.get_by_id(
            invitation_id, organization_id=organization_id
        )
        if invitation is None:
            raise NotFoundError("Invitation not found")
        if invitation.status != InvitationStatus.PENDING:
            raise ConflictError("Only pending invitations can be resent")
        if invitation.revoked_at is not None:
            raise ConflictError("Invitation has been revoked")

        org = await self.auth.get_active_organization(organization_id)
        settings = get_settings()
        raw_token = generate_secure_token()
        updated = await self.invitations.update_token(
            invitation,
            token_hash=hash_secure_token(raw_token),
            expires_at=datetime.now(UTC)
            + timedelta(hours=settings.invitation_expire_hours),
        )
        invite_url = f"{settings.frontend_base_url.rstrip('/')}/invitations/accept?token={raw_token}"
        await self.email.send_organization_invitation(
            to=updated.email,
            invite_url=invite_url,
            organization_name=org.name,
            role=updated.role.value,
        )
        await self.audit.record_event(
            action="organization.invitation.resent",
            actor_user_id=user.id,
            organization_id=organization_id,
            resource_type="organization_invitation",
            resource_id=updated.id,
            request_context=audit_context,
            fail_on_error=True,
        )
        return self._to_response(updated)

    async def revoke(
        self,
        user: User,
        organization_id: UUID,
        invitation_id: UUID,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> None:
        await self.auth.require_permission(
            organization_id, user.id, Permission.MEMBER_MANAGE
        )
        invitation = await self.invitations.get_by_id(
            invitation_id, organization_id=organization_id
        )
        if invitation is None:
            raise NotFoundError("Invitation not found")
        if invitation.status != InvitationStatus.PENDING:
            raise ConflictError("Only pending invitations can be revoked")

        now = datetime.now(UTC)
        invitation.status = InvitationStatus.REVOKED
        invitation.revoked_at = now
        await self.session.flush()
        await self.audit.record_event(
            action="organization.invitation.revoked",
            actor_user_id=user.id,
            organization_id=organization_id,
            resource_type="organization_invitation",
            resource_id=invitation.id,
            request_context=audit_context,
            fail_on_error=True,
        )

    async def accept(
        self,
        user: User,
        raw_token: str,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> InvitationAcceptResponse:
        token_hash = hash_secure_token(raw_token)
        invitation = await self.invitations.get_by_hash_for_update(token_hash)
        if invitation is None:
            raise NotFoundError("Invitation not found")

        now = datetime.now(UTC)
        if (
            invitation.status != InvitationStatus.PENDING
            or invitation.revoked_at is not None
        ):
            raise NotFoundError("Invitation not found")
        if _as_utc(invitation.expires_at) <= now:
            if invitation.status == InvitationStatus.PENDING:
                invitation.status = InvitationStatus.EXPIRED
                await self.session.flush()
                # Persist expiry before raising so get_db rollback cannot undo it.
                await self.session.commit()
            raise NotFoundError("Invitation not found")

        if user.email.lower() != invitation.email.lower():
            raise ForbiddenError("Invitation email does not match your account")

        existing = await self.orgs.get_member(invitation.organization_id, user.id)
        if existing is not None:
            raise ConflictError("You are already a member of this organization")

        await self.orgs.add_member(
            organization_id=invitation.organization_id,
            user_id=user.id,
            role=invitation.role,
        )
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = now
        await self.session.flush()

        org = invitation.organization
        await self.audit.record_event(
            action="organization.invitation.accepted",
            actor_user_id=user.id,
            organization_id=invitation.organization_id,
            resource_type="organization_invitation",
            resource_id=invitation.id,
            request_context=audit_context,
            fail_on_error=True,
        )
        return InvitationAcceptResponse(
            organization_id=invitation.organization_id,
            organization_name=org.name,
            role=invitation.role,
        )

    async def decline(
        self,
        raw_token: str,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> None:
        token_hash = hash_secure_token(raw_token)
        invitation = await self.invitations.get_by_hash_for_update(token_hash)
        if invitation is None:
            raise NotFoundError("Invitation not found")

        now = datetime.now(UTC)
        if (
            invitation.status != InvitationStatus.PENDING
            or invitation.revoked_at is not None
        ):
            raise NotFoundError("Invitation not found")
        if _as_utc(invitation.expires_at) <= now:
            if invitation.status == InvitationStatus.PENDING:
                invitation.status = InvitationStatus.EXPIRED
                await self.session.flush()
                # Persist expiry before raising so get_db rollback cannot undo it.
                await self.session.commit()
            raise NotFoundError("Invitation not found")

        invitation.status = InvitationStatus.DECLINED
        invitation.declined_at = now
        await self.session.flush()
        await self.audit.record_event(
            action="organization.invitation.declined",
            actor_user_id=None,
            organization_id=invitation.organization_id,
            resource_type="organization_invitation",
            resource_id=invitation.id,
            request_context=audit_context,
            fail_on_error=True,
        )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
