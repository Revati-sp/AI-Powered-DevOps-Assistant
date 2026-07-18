from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import LLMProviderError
from app.models.provider_config import LLMOperation
from app.models.user import User
from app.services.llm.base import LLMProvider
from app.services.provider_service import ProviderManagementService
from app.services.usage_quota_service import UsageQuotaService


class LLMGateway:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.providers = ProviderManagementService(session)
        self.usage = UsageQuotaService(session)

    async def generate(
        self,
        *,
        user: User,
        operation: LLMOperation,
        organization_id: UUID | None,
        prompt: str,
        system_prompt: str | None = None,
        explicit_provider: str | None = None,
        temperature: float = 0.2,
        max_output_tokens: int | None = None,
    ) -> tuple[str, str]:
        estimated_input = len(prompt.strip()) // 4 + (
            len(system_prompt.strip()) // 4 if system_prompt else 0
        )
        await self.usage.enforce_quotas(
            user_id=user.id,
            organization_id=organization_id,
            estimated_tokens=max(1, estimated_input),
        )
        (
            result,
            provider_name,
            input_tokens,
            output_tokens,
        ) = await self.providers.generate_with_routing(
            operation=operation,
            organization_id=organization_id,
            explicit_provider=explicit_provider,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        await self.usage.record_llm_usage(
            user_id=user.id,
            organization_id=organization_id,
            operation=operation.value,
            provider=provider_name,
            model=None,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            is_estimated=True,
        )
        return result, provider_name

    async def resolve_stream_provider(
        self,
        *,
        user: User,
        operation: LLMOperation,
        organization_id: UUID | None,
        estimated_tokens: int = 1,
        explicit_provider: str | None = None,
    ) -> tuple[LLMProvider, str]:
        await self.usage.enforce_quotas(
            user_id=user.id,
            organization_id=organization_id,
            estimated_tokens=max(1, estimated_tokens),
        )
        chain = await self.providers.resolve_provider_chain(
            operation,
            organization_id=organization_id,
            explicit_provider=explicit_provider,
        )
        for provider_name, _config in chain:
            if await self.providers.circuit_breaker.is_open(provider_name):
                continue
            return self.providers.build_provider(provider_name), provider_name
        raise LLMProviderError(
            "No available LLM providers for this request.",
            details={"operation": operation.value},
        )
