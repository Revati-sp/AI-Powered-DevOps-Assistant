from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.provider_config import (
    LLMOperation,
    ProviderConfig,
    ProviderRoutingPolicy,
)


class ProviderConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_configs(
        self, *, organization_id: UUID | None
    ) -> list[ProviderConfig]:
        result = await self.session.execute(
            select(ProviderConfig)
            .where(ProviderConfig.organization_id == organization_id)
            .order_by(ProviderConfig.priority.asc(), ProviderConfig.provider_name.asc())
        )
        return list(result.scalars().all())

    async def get_config(
        self,
        provider_name: str,
        *,
        organization_id: UUID | None,
    ) -> ProviderConfig | None:
        result = await self.session.execute(
            select(ProviderConfig).where(
                ProviderConfig.organization_id == organization_id,
                ProviderConfig.provider_name == provider_name,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_config(
        self,
        *,
        organization_id: UUID | None,
        provider_name: str,
        enabled: bool | None = None,
        default_model: str | None = None,
        timeout_seconds: int | None = None,
        max_retries: int | None = None,
        priority: int | None = None,
        max_output_tokens: int | None = None,
        secret_env_key: str | None = None,
        base_url_env_key: str | None = None,
        model_env_key: str | None = None,
    ) -> ProviderConfig:
        config = await self.get_config(provider_name, organization_id=organization_id)
        if config is None:
            if default_model is None or secret_env_key is None:
                raise ValueError("default_model and secret_env_key required for create")
            config = ProviderConfig(
                organization_id=organization_id,
                provider_name=provider_name,
                enabled=enabled if enabled is not None else True,
                default_model=default_model,
                timeout_seconds=timeout_seconds or 60,
                max_retries=max_retries or 3,
                priority=priority or 100,
                max_output_tokens=max_output_tokens or 4096,
                secret_env_key=secret_env_key,
                base_url_env_key=base_url_env_key,
                model_env_key=model_env_key,
            )
            self.session.add(config)
        else:
            if enabled is not None:
                config.enabled = enabled
            if default_model is not None:
                config.default_model = default_model
            if timeout_seconds is not None:
                config.timeout_seconds = timeout_seconds
            if max_retries is not None:
                config.max_retries = max_retries
            if priority is not None:
                config.priority = priority
            if max_output_tokens is not None:
                config.max_output_tokens = max_output_tokens
            if secret_env_key is not None:
                config.secret_env_key = secret_env_key
            if base_url_env_key is not None:
                config.base_url_env_key = base_url_env_key
            if model_env_key is not None:
                config.model_env_key = model_env_key
            config.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(config)
        return config


class ProviderRoutingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_policies(
        self, *, organization_id: UUID | None
    ) -> list[ProviderRoutingPolicy]:
        result = await self.session.execute(
            select(ProviderRoutingPolicy)
            .where(ProviderRoutingPolicy.organization_id == organization_id)
            .order_by(ProviderRoutingPolicy.operation.asc())
        )
        return list(result.scalars().all())

    async def get_policy(
        self,
        operation: LLMOperation,
        *,
        organization_id: UUID | None,
    ) -> ProviderRoutingPolicy | None:
        result = await self.session.execute(
            select(ProviderRoutingPolicy).where(
                ProviderRoutingPolicy.organization_id == organization_id,
                ProviderRoutingPolicy.operation == operation,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_policy(
        self,
        *,
        organization_id: UUID | None,
        operation: LLMOperation,
        primary_provider: str | None = None,
        fallback_providers: list[str] | None = None,
    ) -> ProviderRoutingPolicy:
        policy = await self.get_policy(operation, organization_id=organization_id)
        if policy is None:
            if primary_provider is None:
                raise ValueError("primary_provider required for create")
            policy = ProviderRoutingPolicy(
                organization_id=organization_id,
                operation=operation,
                primary_provider=primary_provider,
                fallback_providers=fallback_providers or [],
            )
            self.session.add(policy)
        else:
            if primary_provider is not None:
                policy.primary_provider = primary_provider
            if fallback_providers is not None:
                policy.fallback_providers = fallback_providers
            policy.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(policy)
        return policy
