from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.policy import PolicyPack, PolicyRule


class PolicyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_pack(
        self,
        *,
        organization_id: UUID,
        name: str,
        description: str | None,
        is_active: bool,
        created_by: UUID,
    ) -> PolicyPack:
        pack = PolicyPack(
            organization_id=organization_id,
            name=name,
            description=description,
            is_active=is_active,
            created_by=created_by,
        )
        self.session.add(pack)
        await self.session.flush()
        await self.session.refresh(pack)
        return pack

    async def get_pack(
        self, organization_id: UUID, policy_pack_id: UUID
    ) -> PolicyPack | None:
        result = await self.session.execute(
            select(PolicyPack)
            .options(selectinload(PolicyPack.rules))
            .where(
                PolicyPack.id == policy_pack_id,
                PolicyPack.organization_id == organization_id,
                PolicyPack.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_packs(
        self,
        organization_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[PolicyPack], int]:
        query = select(PolicyPack).where(
            PolicyPack.organization_id == organization_id,
            PolicyPack.deleted_at.is_(None),
        )
        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = int(count_result.scalar_one())
        result = await self.session.execute(
            query.order_by(PolicyPack.updated_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all()), total

    async def update_pack(
        self,
        pack: PolicyPack,
        *,
        name: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
        bump_version: bool = False,
    ) -> PolicyPack:
        if name is not None:
            pack.name = name
        if description is not None:
            pack.description = description
        if is_active is not None:
            pack.is_active = is_active
        if bump_version:
            pack.version += 1
        pack.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(pack)
        return pack

    async def soft_delete_pack(self, pack: PolicyPack) -> PolicyPack:
        pack.deleted_at = datetime.now(UTC)
        pack.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(pack)
        return pack

    async def create_rule(
        self,
        *,
        policy_pack_id: UUID,
        rule_key: str,
        name: str,
        description: str,
        resource_type: str,
        severity: str,
        configuration_json: dict[str, Any],
        remediation: str | None,
        is_enabled: bool,
    ) -> PolicyRule:
        rule = PolicyRule(
            policy_pack_id=policy_pack_id,
            rule_key=rule_key,
            name=name,
            description=description,
            resource_type=resource_type,
            severity=severity,
            configuration_json=configuration_json,
            remediation=remediation,
            is_enabled=is_enabled,
        )
        self.session.add(rule)
        await self.session.flush()
        await self.session.refresh(rule)
        return rule

    async def get_rule(self, policy_pack_id: UUID, rule_id: UUID) -> PolicyRule | None:
        result = await self.session.execute(
            select(PolicyRule).where(
                PolicyRule.id == rule_id,
                PolicyRule.policy_pack_id == policy_pack_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_rule(
        self,
        rule: PolicyRule,
        *,
        name: str | None = None,
        description: str | None = None,
        severity: str | None = None,
        configuration_json: dict[str, Any] | None = None,
        remediation: str | None = None,
        is_enabled: bool | None = None,
    ) -> PolicyRule:
        if name is not None:
            rule.name = name
        if description is not None:
            rule.description = description
        if severity is not None:
            rule.severity = severity
        if configuration_json is not None:
            rule.configuration_json = configuration_json
        if remediation is not None:
            rule.remediation = remediation
        if is_enabled is not None:
            rule.is_enabled = is_enabled
        rule.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(rule)
        return rule

    async def delete_rule(self, rule: PolicyRule) -> None:
        await self.session.delete(rule)
        await self.session.flush()

    async def get_active_packs_by_ids(
        self, organization_id: UUID, policy_pack_ids: list[UUID]
    ) -> list[PolicyPack]:
        if not policy_pack_ids:
            return []
        result = await self.session.execute(
            select(PolicyPack)
            .options(selectinload(PolicyPack.rules))
            .where(
                PolicyPack.organization_id == organization_id,
                PolicyPack.id.in_(policy_pack_ids),
                PolicyPack.is_active.is_(True),
                PolicyPack.deleted_at.is_(None),
            )
        )
        packs = list(result.scalars().all())
        if len(packs) != len(set(policy_pack_ids)):
            return []
        return packs
