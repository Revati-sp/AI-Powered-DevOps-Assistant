from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, QuotaExceededError
from app.models.organization import OrgRole
from app.models.usage import OrganizationQuota
from app.models.user import User
from app.repositories.usage_repository import (
    OrganizationQuotaRepository,
    UsageRepository,
)
from app.services.rbac import OrganizationAuthService, Permission


def estimate_tokens(text: str) -> int:
    cleaned = text.strip()
    if not cleaned:
        return 0
    return max(1, len(cleaned) // 4)


class UsageQuotaService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.usage = UsageRepository(session)
        self.quotas = OrganizationQuotaRepository(session)
        self.org_auth = OrganizationAuthService(session)

    async def enforce_quotas(
        self,
        *,
        user_id: UUID,
        organization_id: UUID | None,
        estimated_tokens: int = 1,
    ) -> None:
        if organization_id is not None:
            await self.enforce_org_quota(
                organization_id, estimated_tokens=estimated_tokens
            )
            return

        settings = get_settings()
        if not settings.usage_enforce_personal_quotas:
            return

        daily_limit = settings.usage_default_daily_token_limit
        monthly_limit = settings.usage_default_monthly_token_limit
        if daily_limit is None and monthly_limit is None:
            return

        daily_start = OrganizationQuotaRepository.daily_window_start()
        monthly_start = OrganizationQuotaRepository.monthly_window_start()
        if daily_limit is not None:
            daily_tokens, _ = await self.usage.aggregate_usage(
                user_id=user_id, since=daily_start
            )
            if daily_tokens + estimated_tokens > daily_limit:
                raise QuotaExceededError(
                    "Personal daily token quota exceeded.",
                    details={
                        "period": "daily",
                        "limit": daily_limit,
                        "used": daily_tokens,
                        "estimated": estimated_tokens,
                    },
                )
        if monthly_limit is not None:
            monthly_tokens, _ = await self.usage.aggregate_usage(
                user_id=user_id, since=monthly_start
            )
            if monthly_tokens + estimated_tokens > monthly_limit:
                raise QuotaExceededError(
                    "Personal monthly token quota exceeded.",
                    details={
                        "period": "monthly",
                        "limit": monthly_limit,
                        "used": monthly_tokens,
                        "estimated": estimated_tokens,
                    },
                )

    async def enforce_org_quota(
        self,
        organization_id: UUID | None,
        *,
        estimated_tokens: int = 1,
    ) -> None:
        if organization_id is None:
            return
        quota = await self.quotas.get_for_organization(organization_id)
        if quota is None or not quota.enforce_quotas:
            return

        daily_start = OrganizationQuotaRepository.daily_window_start()
        monthly_start = OrganizationQuotaRepository.monthly_window_start()
        daily_tokens, daily_requests = await self.usage.aggregate_usage(
            organization_id=organization_id, since=daily_start
        )
        monthly_tokens, monthly_requests = await self.usage.aggregate_usage(
            organization_id=organization_id, since=monthly_start
        )

        if quota.daily_request_limit is not None:
            if daily_requests + 1 > quota.daily_request_limit:
                raise QuotaExceededError(
                    "Organization daily request quota exceeded.",
                    details={
                        "period": "daily",
                        "limit": quota.daily_request_limit,
                        "used": daily_requests,
                    },
                )
        if quota.monthly_request_limit is not None:
            if monthly_requests + 1 > quota.monthly_request_limit:
                raise QuotaExceededError(
                    "Organization monthly request quota exceeded.",
                    details={
                        "period": "monthly",
                        "limit": quota.monthly_request_limit,
                        "used": monthly_requests,
                    },
                )
        if quota.daily_token_limit is not None:
            if daily_tokens + estimated_tokens > quota.daily_token_limit:
                raise QuotaExceededError(
                    "Organization daily token quota exceeded.",
                    details={
                        "period": "daily",
                        "limit": quota.daily_token_limit,
                        "used": daily_tokens,
                        "estimated": estimated_tokens,
                    },
                )
        if quota.monthly_token_limit is not None:
            if monthly_tokens + estimated_tokens > quota.monthly_token_limit:
                raise QuotaExceededError(
                    "Organization monthly token quota exceeded.",
                    details={
                        "period": "monthly",
                        "limit": quota.monthly_token_limit,
                        "used": monthly_tokens,
                        "estimated": estimated_tokens,
                    },
                )

    async def record_llm_usage(
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
    ) -> None:
        await self.usage.record_event(
            user_id=user_id,
            organization_id=organization_id,
            operation=operation,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            is_estimated=is_estimated,
        )

    async def get_my_usage(self, user: User) -> dict[str, object]:
        daily_start = OrganizationQuotaRepository.daily_window_start()
        monthly_start = OrganizationQuotaRepository.monthly_window_start()
        daily_tokens, daily_requests = await self.usage.aggregate_usage(
            user_id=user.id, since=daily_start
        )
        monthly_tokens, monthly_requests = await self.usage.aggregate_usage(
            user_id=user.id, since=monthly_start
        )
        recent = await self.usage.list_recent_for_user(user.id, limit=20)
        return {
            "user_id": user.id,
            "daily": {
                "tokens": daily_tokens,
                "requests": daily_requests,
                "estimated": True,
            },
            "monthly": {
                "tokens": monthly_tokens,
                "requests": monthly_requests,
                "estimated": True,
            },
            "recent_events": recent,
        }

    async def get_org_usage(
        self, user: User, organization_id: UUID
    ) -> dict[str, object]:
        await self.org_auth.require_permission(
            organization_id, user.id, Permission.ORGANIZATION_READ
        )
        daily_start = OrganizationQuotaRepository.daily_window_start()
        monthly_start = OrganizationQuotaRepository.monthly_window_start()
        daily_tokens, daily_requests = await self.usage.aggregate_usage(
            organization_id=organization_id, since=daily_start
        )
        monthly_tokens, monthly_requests = await self.usage.aggregate_usage(
            organization_id=organization_id, since=monthly_start
        )
        quota = await self.quotas.get_for_organization(organization_id)
        return {
            "organization_id": organization_id,
            "daily": {
                "tokens": daily_tokens,
                "requests": daily_requests,
                "estimated": True,
            },
            "monthly": {
                "tokens": monthly_tokens,
                "requests": monthly_requests,
                "estimated": True,
            },
            "quota": quota,
        }

    async def require_quota_manage(self, user: User, organization_id: UUID) -> None:
        _, membership = await self.org_auth.require_membership(organization_id, user.id)
        if membership.role not in {OrgRole.OWNER, OrgRole.ADMIN}:
            raise ForbiddenError("Insufficient organization permissions")

    async def get_org_quota(
        self, user: User, organization_id: UUID
    ) -> OrganizationQuota | None:
        await self.org_auth.require_permission(
            organization_id, user.id, Permission.ORGANIZATION_READ
        )
        return await self.quotas.get_for_organization(organization_id)

    async def patch_org_quota(
        self,
        user: User,
        organization_id: UUID,
        *,
        daily_token_limit: int | None = None,
        daily_request_limit: int | None = None,
        monthly_token_limit: int | None = None,
        monthly_request_limit: int | None = None,
        enforce_quotas: bool | None = None,
        unset_fields: set[str] | None = None,
    ) -> OrganizationQuota:
        await self.require_quota_manage(user, organization_id)
        return await self.quotas.upsert(
            organization_id,
            daily_token_limit=daily_token_limit,
            daily_request_limit=daily_request_limit,
            monthly_token_limit=monthly_token_limit,
            monthly_request_limit=monthly_request_limit,
            enforce_quotas=enforce_quotas,
            unset_fields=unset_fields,
        )
