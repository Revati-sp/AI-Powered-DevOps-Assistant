from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationAppError,
)
from app.models.organization import Organization, OrganizationMember, OrgRole
from app.models.user import User
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.organization import (
    AddMemberRequest,
    OrganizationCreate,
    OrganizationMemberResponse,
    OrganizationResponse,
    OrganizationUpdate,
    UpdateMemberRequest,
)
from app.schemas.pagination import Page, PageParams
from app.services.audit_service import AuditRequestContext, AuditService
from app.services.rbac import OrganizationAuthService, Permission

_SLUG_INVALID = re.compile(r"[^a-z0-9-]")
_SLUG_MULTI_HYPHEN = re.compile(r"-+")


def normalize_slug(raw: str) -> str:
    slug = raw.strip().lower().replace(" ", "-")
    slug = _SLUG_INVALID.sub("-", slug)
    slug = _SLUG_MULTI_HYPHEN.sub("-", slug).strip("-")
    if not slug or not re.fullmatch(r"[a-z0-9-]+", slug):
        raise ValidationAppError(
            "Slug must contain only lowercase letters, numbers, and hyphens"
        )
    return slug


class OrganizationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.orgs = OrganizationRepository(session)
        self.users = UserRepository(session)
        self.auth = OrganizationAuthService(session)
        self.audit = AuditService(session)

    def _to_org_response(self, org: Organization) -> OrganizationResponse:
        return OrganizationResponse.model_validate(org)

    def _to_member_response(
        self, member: OrganizationMember
    ) -> OrganizationMemberResponse:
        return OrganizationMemberResponse(
            id=member.id,
            organization_id=member.organization_id,
            user_id=member.user_id,
            role=member.role,
            email=member.user.email,
            username=member.user.username,
            created_at=member.created_at,
            updated_at=member.updated_at,
        )

    async def create(
        self,
        user: User,
        payload: OrganizationCreate,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> OrganizationResponse:
        slug = normalize_slug(payload.slug or payload.name)
        if await self.orgs.get_by_slug(slug):
            raise ConflictError("Organization slug already taken")

        org = await self.orgs.create(
            name=payload.name.strip(), slug=slug, created_by=user.id
        )
        await self.orgs.add_member(
            organization_id=org.id,
            user_id=user.id,
            role=OrgRole.OWNER,
        )
        await self.audit.record_event(
            action="organization.created",
            actor_user_id=user.id,
            organization_id=org.id,
            resource_type="organization",
            resource_id=org.id,
            request_context=audit_context,
            metadata={"slug": org.slug},
            fail_on_error=True,
        )
        return self._to_org_response(org)

    async def list_for_user(
        self, user: User, params: PageParams
    ) -> Page[OrganizationResponse]:
        orgs, total = await self.orgs.list_for_user(
            user.id, limit=params.limit, offset=params.offset
        )
        return Page(
            items=[self._to_org_response(org) for org in orgs],
            total=total,
            limit=params.limit,
            offset=params.offset,
        )

    async def get(self, user: User, organization_id: UUID) -> OrganizationResponse:
        await self.auth.require_permission(
            organization_id, user.id, Permission.ORGANIZATION_READ
        )
        org = await self.auth.get_active_organization(organization_id)
        return self._to_org_response(org)

    async def update(
        self,
        user: User,
        organization_id: UUID,
        payload: OrganizationUpdate,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> OrganizationResponse:
        org, membership = await self.auth.require_permission(
            organization_id, user.id, Permission.ORGANIZATION_UPDATE
        )
        if payload.name is None and payload.slug is None:
            raise ValidationAppError("At least one field must be provided")

        name = payload.name.strip() if payload.name is not None else None
        slug: str | None = None
        if payload.slug is not None:
            if membership.role != OrgRole.OWNER:
                raise ForbiddenError("Only owners may change the organization slug")
            slug = normalize_slug(payload.slug)
            existing = await self.orgs.get_by_slug(slug)
            if existing is not None and existing.id != org.id:
                raise ConflictError("Organization slug already taken")

        updated = await self.orgs.update(org, name=name, slug=slug)
        await self.audit.record_event(
            action="organization.updated",
            actor_user_id=user.id,
            organization_id=org.id,
            resource_type="organization",
            resource_id=org.id,
            request_context=audit_context,
            fail_on_error=True,
        )
        return self._to_org_response(updated)

    async def delete(
        self,
        user: User,
        organization_id: UUID,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> None:
        org, _ = await self.auth.require_permission(
            organization_id, user.id, Permission.ORGANIZATION_DELETE
        )
        await self.orgs.soft_delete(org)
        await self.audit.record_event(
            action="organization.deleted",
            actor_user_id=user.id,
            organization_id=org.id,
            resource_type="organization",
            resource_id=org.id,
            request_context=audit_context,
            fail_on_error=True,
        )

    async def list_members(
        self, user: User, organization_id: UUID, params: PageParams
    ) -> Page[OrganizationMemberResponse]:
        await self.auth.require_permission(
            organization_id, user.id, Permission.ORGANIZATION_READ
        )
        members, total = await self.orgs.list_members(
            organization_id, limit=params.limit, offset=params.offset
        )
        return Page(
            items=[self._to_member_response(m) for m in members],
            total=total,
            limit=params.limit,
            offset=params.offset,
        )

    def _ensure_can_manage_target(
        self,
        actor: OrganizationMember,
        target: OrganizationMember,
        *,
        assigning_role: OrgRole | None = None,
    ) -> None:
        if actor.role == OrgRole.ADMIN:
            if target.role == OrgRole.OWNER:
                raise ForbiddenError("Admins cannot modify owners")
            if assigning_role == OrgRole.OWNER:
                raise ForbiddenError("Admins cannot assign the owner role")

    async def add_member(
        self,
        user: User,
        organization_id: UUID,
        payload: AddMemberRequest,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> OrganizationMemberResponse:
        _, actor = await self.auth.require_permission(
            organization_id, user.id, Permission.MEMBER_MANAGE
        )
        if payload.role == OrgRole.OWNER and actor.role != OrgRole.OWNER:
            raise ForbiddenError("Only owners may assign the owner role")

        target_user = await self.users.get_by_email(payload.email.lower())
        if target_user is None:
            raise NotFoundError("User not found")

        existing = await self.orgs.get_member(organization_id, target_user.id)
        if existing is not None:
            raise ConflictError("User is already a member of this organization")

        member = await self.orgs.add_member(
            organization_id=organization_id,
            user_id=target_user.id,
            role=payload.role,
        )
        member.user = target_user
        await self.audit.record_event(
            action="organization.member.added",
            actor_user_id=user.id,
            organization_id=organization_id,
            resource_type="organization_member",
            resource_id=member.id,
            request_context=audit_context,
            metadata={"role": member.role.value},
            fail_on_error=True,
        )
        return self._to_member_response(member)

    async def update_member(
        self,
        user: User,
        organization_id: UUID,
        target_user_id: UUID,
        payload: UpdateMemberRequest,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> OrganizationMemberResponse:
        _, actor = await self.auth.require_permission(
            organization_id, user.id, Permission.MEMBER_MANAGE
        )
        target = await self.orgs.get_member(organization_id, target_user_id)
        if target is None:
            raise NotFoundError("Member not found")

        self._ensure_can_manage_target(actor, target, assigning_role=payload.role)

        if target.role == OrgRole.OWNER and payload.role != OrgRole.OWNER:
            owner_count = await self.auth.count_owners(organization_id)
            if owner_count <= 1:
                raise ForbiddenError("Cannot demote the final owner")

        if payload.role == OrgRole.OWNER and actor.role != OrgRole.OWNER:
            raise ForbiddenError("Only owners may assign the owner role")

        updated = await self.orgs.update_member_role(target, payload.role)
        await self.audit.record_event(
            action="organization.member.role_changed",
            actor_user_id=user.id,
            organization_id=organization_id,
            resource_type="organization_member",
            resource_id=updated.id,
            request_context=audit_context,
            metadata={"role": updated.role.value},
            fail_on_error=True,
        )
        return self._to_member_response(updated)

    async def remove_member(
        self,
        user: User,
        organization_id: UUID,
        target_user_id: UUID,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> None:
        _, actor = await self.auth.require_permission(
            organization_id, user.id, Permission.MEMBER_MANAGE
        )
        target = await self.orgs.get_member(organization_id, target_user_id)
        if target is None:
            raise NotFoundError("Member not found")

        self._ensure_can_manage_target(actor, target)

        if target.role == OrgRole.OWNER:
            owner_count = await self.auth.count_owners(organization_id)
            if owner_count <= 1:
                raise ForbiddenError("Cannot remove the final owner")

        await self.orgs.remove_member(target)
        await self.audit.record_event(
            action="organization.member.removed",
            actor_user_id=user.id,
            organization_id=organization_id,
            resource_type="organization_member",
            resource_id=target.id,
            request_context=audit_context,
            fail_on_error=True,
        )
