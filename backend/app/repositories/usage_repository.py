from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usage import OrganizationQuota, UsageEvent


class UsageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_event(
        self,
        *,
        user_id: UUID,
        organization_id: UUID | None,
        operation: str,
        provider: str,
        model: str | None,
        input_tokens: int,
        output_tokens: int,
        is_estimated: bool = True,
    ) -> UsageEvent:
        total = input_tokens + output_tokens
        event = UsageEvent(
            user_id=user_id,
            organization_id=organization_id,
            operation=operation,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total,
            is_estimated=is_estimated,
        )
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        return event

    async def aggregate_usage(
        self,
        *,
        user_id: UUID | None = None,
        organization_id: UUID | None = None,
        since: datetime | None = None,
    ) -> tuple[int, int]:
        query = select(
            func.coalesce(func.sum(UsageEvent.total_tokens), 0),
            func.count(UsageEvent.id),
        )
        if user_id is not None:
            query = query.where(UsageEvent.user_id == user_id)
        if organization_id is not None:
            query = query.where(UsageEvent.organization_id == organization_id)
        if since is not None:
            query = query.where(UsageEvent.created_at >= since)
        result = await self.session.execute(query)
        tokens, requests = result.one()
        return int(tokens), int(requests)

    async def list_recent_for_user(
        self, user_id: UUID, *, limit: int = 50
    ) -> list[UsageEvent]:
        result = await self.session.execute(
            select(UsageEvent)
            .where(UsageEvent.user_id == user_id)
            .order_by(UsageEvent.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class OrganizationQuotaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_for_organization(
        self, organization_id: UUID
    ) -> OrganizationQuota | None:
        result = await self.session.execute(
            select(OrganizationQuota).where(
                OrganizationQuota.organization_id == organization_id
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        organization_id: UUID,
        *,
        daily_token_limit: int | None = None,
        daily_request_limit: int | None = None,
        monthly_token_limit: int | None = None,
        monthly_request_limit: int | None = None,
        enforce_quotas: bool | None = None,
        unset_fields: set[str] | None = None,
    ) -> OrganizationQuota:
        quota = await self.get_for_organization(organization_id)
        unset = unset_fields or set()
        if quota is None:
            quota = OrganizationQuota(
                organization_id=organization_id,
                daily_token_limit=daily_token_limit,
                daily_request_limit=daily_request_limit,
                monthly_token_limit=monthly_token_limit,
                monthly_request_limit=monthly_request_limit,
                enforce_quotas=True if enforce_quotas is None else enforce_quotas,
            )
            self.session.add(quota)
        else:
            if "daily_token_limit" in unset:
                quota.daily_token_limit = None
            elif daily_token_limit is not None:
                quota.daily_token_limit = daily_token_limit
            if "daily_request_limit" in unset:
                quota.daily_request_limit = None
            elif daily_request_limit is not None:
                quota.daily_request_limit = daily_request_limit
            if "monthly_token_limit" in unset:
                quota.monthly_token_limit = None
            elif monthly_token_limit is not None:
                quota.monthly_token_limit = monthly_token_limit
            if "monthly_request_limit" in unset:
                quota.monthly_request_limit = None
            elif monthly_request_limit is not None:
                quota.monthly_request_limit = monthly_request_limit
            if enforce_quotas is not None:
                quota.enforce_quotas = enforce_quotas
            quota.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(quota)
        return quota

    @staticmethod
    def daily_window_start(now: datetime | None = None) -> datetime:
        current = now or datetime.now(UTC)
        return current.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def monthly_window_start(now: datetime | None = None) -> datetime:
        current = now or datetime.now(UTC)
        return current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
