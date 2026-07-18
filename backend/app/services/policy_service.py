from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.user import User
from app.repositories.policy_repository import PolicyRepository
from app.schemas.policies import (
    PolicyFinding,
    PolicyPackCreateRequest,
    PolicyPackDetailResponse,
    PolicyPackResponse,
    PolicyPackUpdateRequest,
    PolicyRuleCreateRequest,
    PolicyRuleResponse,
    PolicyRuleUpdateRequest,
    validate_rule_configuration,
)
from app.services.audit_service import AuditRequestContext, AuditService
from app.services.policy_engine import evaluate_policy_rules
from app.services.rbac import OrganizationAuthService, Permission


class PolicyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = PolicyRepository(session)
        self.org_auth = OrganizationAuthService(session)
        self.audit = AuditService(session)

    async def create_pack(
        self,
        user: User,
        organization_id: UUID,
        payload: PolicyPackCreateRequest,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> PolicyPackResponse:
        await self.org_auth.require_permission(
            organization_id, user.id, Permission.POLICY_MANAGE
        )
        pack = await self.repo.create_pack(
            organization_id=organization_id,
            name=payload.name,
            description=payload.description,
            is_active=payload.is_active,
            created_by=user.id,
        )
        await self.audit.record_event(
            action="policy_pack.created",
            actor_user_id=user.id,
            organization_id=organization_id,
            resource_type="policy_pack",
            resource_id=pack.id,
            request_context=audit_context,
            metadata={"name": pack.name},
            fail_on_error=True,
        )
        return PolicyPackResponse.model_validate(pack)

    async def list_packs(
        self,
        user: User,
        organization_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[PolicyPackResponse], int]:
        await self.org_auth.require_permission(
            organization_id, user.id, Permission.POLICY_READ
        )
        items, total = await self.repo.list_packs(
            organization_id, limit=limit, offset=offset
        )
        return [PolicyPackResponse.model_validate(item) for item in items], total

    async def get_pack(
        self, user: User, organization_id: UUID, policy_pack_id: UUID
    ) -> PolicyPackDetailResponse:
        await self.org_auth.require_permission(
            organization_id, user.id, Permission.POLICY_READ
        )
        pack = await self.repo.get_pack(organization_id, policy_pack_id)
        if pack is None:
            raise NotFoundError("Policy pack not found")
        return PolicyPackDetailResponse(
            **PolicyPackResponse.model_validate(pack).model_dump(),
            rules=[PolicyRuleResponse.model_validate(rule) for rule in pack.rules],
        )

    async def update_pack(
        self,
        user: User,
        organization_id: UUID,
        policy_pack_id: UUID,
        payload: PolicyPackUpdateRequest,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> PolicyPackResponse:
        await self.org_auth.require_permission(
            organization_id, user.id, Permission.POLICY_MANAGE
        )
        pack = await self.repo.get_pack(organization_id, policy_pack_id)
        if pack is None:
            raise NotFoundError("Policy pack not found")
        updated = await self.repo.update_pack(
            pack,
            name=payload.name,
            description=payload.description,
            is_active=payload.is_active,
            bump_version=True,
        )
        await self.audit.record_event(
            action="policy_pack.updated",
            actor_user_id=user.id,
            organization_id=organization_id,
            resource_type="policy_pack",
            resource_id=updated.id,
            request_context=audit_context,
            metadata={"version": updated.version},
            fail_on_error=True,
        )
        return PolicyPackResponse.model_validate(updated)

    async def delete_pack(
        self,
        user: User,
        organization_id: UUID,
        policy_pack_id: UUID,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> None:
        await self.org_auth.require_permission(
            organization_id, user.id, Permission.POLICY_MANAGE
        )
        pack = await self.repo.get_pack(organization_id, policy_pack_id)
        if pack is None:
            raise NotFoundError("Policy pack not found")
        await self.repo.soft_delete_pack(pack)
        await self.audit.record_event(
            action="policy_pack.deleted",
            actor_user_id=user.id,
            organization_id=organization_id,
            resource_type="policy_pack",
            resource_id=pack.id,
            request_context=audit_context,
            metadata={"name": pack.name},
            fail_on_error=True,
        )

    async def add_rule(
        self,
        user: User,
        organization_id: UUID,
        policy_pack_id: UUID,
        payload: PolicyRuleCreateRequest,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> PolicyRuleResponse:
        await self.org_auth.require_permission(
            organization_id, user.id, Permission.POLICY_MANAGE
        )
        pack = await self.repo.get_pack(organization_id, policy_pack_id)
        if pack is None:
            raise NotFoundError("Policy pack not found")

        configuration = validate_rule_configuration(
            payload.rule_key, payload.configuration
        )
        rule = await self.repo.create_rule(
            policy_pack_id=pack.id,
            rule_key=payload.rule_key,
            name=payload.name,
            description=payload.description,
            resource_type=payload.resource_type,
            severity=payload.severity,
            configuration_json=configuration,
            remediation=payload.remediation,
            is_enabled=payload.is_enabled,
        )
        await self.repo.update_pack(pack, bump_version=True)
        await self.audit.record_event(
            action="policy_rule.created",
            actor_user_id=user.id,
            organization_id=organization_id,
            resource_type="policy_rule",
            resource_id=rule.id,
            request_context=audit_context,
            metadata={"rule_key": rule.rule_key, "policy_pack_id": str(pack.id)},
            fail_on_error=True,
        )
        return PolicyRuleResponse.model_validate(rule)

    async def update_rule(
        self,
        user: User,
        organization_id: UUID,
        policy_pack_id: UUID,
        rule_id: UUID,
        payload: PolicyRuleUpdateRequest,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> PolicyRuleResponse:
        await self.org_auth.require_permission(
            organization_id, user.id, Permission.POLICY_MANAGE
        )
        pack = await self.repo.get_pack(organization_id, policy_pack_id)
        if pack is None:
            raise NotFoundError("Policy pack not found")
        rule = await self.repo.get_rule(policy_pack_id, rule_id)
        if rule is None:
            raise NotFoundError("Policy rule not found")

        configuration_json = None
        if payload.configuration is not None:
            configuration_json = validate_rule_configuration(
                rule.rule_key, payload.configuration
            )

        updated = await self.repo.update_rule(
            rule,
            name=payload.name,
            description=payload.description,
            severity=payload.severity,
            configuration_json=configuration_json,
            remediation=payload.remediation,
            is_enabled=payload.is_enabled,
        )
        await self.repo.update_pack(pack, bump_version=True)
        await self.audit.record_event(
            action="policy_rule.updated",
            actor_user_id=user.id,
            organization_id=organization_id,
            resource_type="policy_rule",
            resource_id=updated.id,
            request_context=audit_context,
            metadata={"rule_key": updated.rule_key},
            fail_on_error=True,
        )
        return PolicyRuleResponse.model_validate(updated)

    async def delete_rule(
        self,
        user: User,
        organization_id: UUID,
        policy_pack_id: UUID,
        rule_id: UUID,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> None:
        await self.org_auth.require_permission(
            organization_id, user.id, Permission.POLICY_MANAGE
        )
        pack = await self.repo.get_pack(organization_id, policy_pack_id)
        if pack is None:
            raise NotFoundError("Policy pack not found")
        rule = await self.repo.get_rule(policy_pack_id, rule_id)
        if rule is None:
            raise NotFoundError("Policy rule not found")
        rule_key = rule.rule_key
        rule_id_value = rule.id
        await self.repo.delete_rule(rule)
        await self.repo.update_pack(pack, bump_version=True)
        await self.audit.record_event(
            action="policy_rule.deleted",
            actor_user_id=user.id,
            organization_id=organization_id,
            resource_type="policy_rule",
            resource_id=rule_id_value,
            request_context=audit_context,
            metadata={"rule_key": rule_key},
            fail_on_error=True,
        )

    async def evaluate_packs(
        self,
        *,
        organization_id: UUID,
        policy_pack_ids: list[UUID],
        config_type: str,
        content: str,
    ) -> list[PolicyFinding]:
        packs = await self.repo.get_active_packs_by_ids(
            organization_id, policy_pack_ids
        )
        if len(packs) != len(set(policy_pack_ids)):
            raise ValidationAppError("One or more policy packs are invalid or inactive")

        findings: list[PolicyFinding] = []
        for pack in packs:
            findings.extend(
                evaluate_policy_rules(
                    pack.rules,
                    config_type=config_type,
                    content=content,
                    policy_pack_id=pack.id,
                )
            )
        return findings
