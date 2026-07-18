from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEvent
from app.utils.audit_redaction import redact_metadata


@dataclass(frozen=True)
class AuditRequestContext:
    request_id: str = ""
    ip_address: str | None = None
    user_agent: str | None = None


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_event(
        self,
        *,
        action: str,
        actor_user_id: UUID | None,
        organization_id: UUID | None,
        resource_type: str,
        resource_id: UUID | None,
        request_context: AuditRequestContext | None = None,
        metadata: dict[str, Any] | None = None,
        fail_on_error: bool = False,
    ) -> AuditEvent | None:
        ctx = request_context or AuditRequestContext()
        safe_metadata = redact_metadata(metadata) if metadata else None
        event = AuditEvent(
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            request_id=ctx.request_id or "",
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
            metadata_json=safe_metadata,
        )
        try:
            self.session.add(event)
            await self.session.flush()
            await self.session.refresh(event)
            return event
        except Exception:
            if fail_on_error:
                raise
            return None

    async def list_events(
        self,
        organization_id: UUID,
        *,
        limit: int,
        offset: int,
        action: str | None = None,
        actor_user_id: UUID | None = None,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        created_from: Any | None = None,
        created_to: Any | None = None,
    ) -> tuple[list[AuditEvent], int]:
        query = select(AuditEvent).where(AuditEvent.organization_id == organization_id)
        if action:
            query = query.where(AuditEvent.action == action)
        if actor_user_id:
            query = query.where(AuditEvent.actor_user_id == actor_user_id)
        if resource_type:
            query = query.where(AuditEvent.resource_type == resource_type)
        if resource_id:
            query = query.where(AuditEvent.resource_id == resource_id)
        if created_from is not None:
            query = query.where(AuditEvent.created_at >= created_from)
        if created_to is not None:
            query = query.where(AuditEvent.created_at <= created_to)

        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = int(count_result.scalar_one())

        result = await self.session.execute(
            query.order_by(AuditEvent.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all()), total
