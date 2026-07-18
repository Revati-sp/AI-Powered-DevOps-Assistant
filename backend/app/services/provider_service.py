from __future__ import annotations

import os
import time
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, LLMProviderError, ValidationAppError
from app.models.organization import OrgRole
from app.models.provider_config import (
    LLMOperation,
    ProviderConfig,
    ProviderRoutingPolicy,
)
from app.models.user import User, UserRole
from app.repositories.provider_repository import (
    ProviderConfigRepository,
    ProviderRoutingRepository,
)
from app.services.llm.base import LLMProvider
from app.services.llm.factory import SUPPORTED_PROVIDERS, get_llm_provider
from app.services.provider_circuit_breaker import (
    get_circuit_breaker,
)
from app.services.rbac import OrganizationAuthService


def is_provider_configured(config: ProviderConfig) -> bool:
    secret = os.environ.get(config.secret_env_key, "").strip()
    return bool(secret)


def estimate_tokens(text: str) -> int:
    cleaned = text.strip()
    if not cleaned:
        return 0
    return max(1, len(cleaned) // 4)


class ProviderManagementService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.configs = ProviderConfigRepository(session)
        self.routing = ProviderRoutingRepository(session)
        self.org_auth = OrganizationAuthService(session)
        self.circuit_breaker = get_circuit_breaker()
        self.settings = get_settings()

    async def require_platform_admin(self, user: User) -> None:
        if user.role != UserRole.ADMIN:
            raise ForbiddenError("Admin privileges required")

    async def require_org_owner(self, user: User, organization_id: UUID) -> None:
        _, membership = await self.org_auth.require_membership(organization_id, user.id)
        if membership.role != OrgRole.OWNER:
            raise ForbiddenError("Organization owner privileges required")

    async def list_configs(
        self, *, organization_id: UUID | None
    ) -> list[ProviderConfig]:
        return await self.configs.list_configs(organization_id=organization_id)

    async def patch_config(
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
        name = provider_name.lower().strip()
        if name not in SUPPORTED_PROVIDERS:
            raise ValidationAppError(
                f"Unsupported provider '{name}'.",
                details={"supported": sorted(SUPPORTED_PROVIDERS)},
            )
        provider_defaults: dict[str, tuple[str, str, str | None, str]] = {
            "gemini": ("gemini-1.5-flash", "GEMINI_API_KEY", None, "GEMINI_MODEL"),
            "llama": (
                "llama-3.1-8b-instruct",
                "LLAMA_API_KEY",
                "LLAMA_BASE_URL",
                "LLAMA_MODEL",
            ),
            "mistral": (
                "mistral-small-latest",
                "MISTRAL_API_KEY",
                "MISTRAL_BASE_URL",
                "MISTRAL_MODEL",
            ),
        }
        if organization_id is None:
            existing = await self.configs.get_config(name, organization_id=None)
            if existing is None and secret_env_key is None:
                _model, secret, base, model_key = provider_defaults[name]
                secret_env_key = secret
                base_url_env_key = base
                model_env_key = model_key
                default_model = default_model or _model
        else:
            existing = await self.configs.get_config(
                name, organization_id=organization_id
            )
            if existing is None:
                platform = await self.configs.get_config(name, organization_id=None)
                if platform is not None:
                    default_model = default_model or platform.default_model
                    secret_env_key = secret_env_key or platform.secret_env_key
                    base_url_env_key = base_url_env_key or platform.base_url_env_key
                    model_env_key = model_env_key or platform.model_env_key
                    timeout_seconds = timeout_seconds or platform.timeout_seconds
                    max_retries = max_retries or platform.max_retries
                    priority = priority or platform.priority
                    max_output_tokens = max_output_tokens or platform.max_output_tokens
                elif secret_env_key is None or default_model is None:
                    model, secret, base, model_key = provider_defaults[name]
                    default_model = default_model or model
                    secret_env_key = secret_env_key or secret
                    base_url_env_key = base_url_env_key or base
                    model_env_key = model_env_key or model_key
        return await self.configs.upsert_config(
            organization_id=organization_id,
            provider_name=name,
            enabled=enabled,
            default_model=default_model,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            priority=priority,
            max_output_tokens=max_output_tokens,
            secret_env_key=secret_env_key,
            base_url_env_key=base_url_env_key,
            model_env_key=model_env_key,
        )

    async def list_routing(
        self, *, organization_id: UUID | None
    ) -> list[ProviderRoutingPolicy]:
        return await self.routing.list_policies(organization_id=organization_id)

    async def patch_routing(
        self,
        *,
        organization_id: UUID | None,
        operation: LLMOperation,
        primary_provider: str | None = None,
        fallback_providers: list[str] | None = None,
    ) -> ProviderRoutingPolicy:
        if primary_provider is not None:
            primary = primary_provider.lower().strip()
            if primary not in SUPPORTED_PROVIDERS:
                raise ValidationAppError(
                    f"Unsupported provider '{primary}'.",
                    details={"supported": sorted(SUPPORTED_PROVIDERS)},
                )
        if fallback_providers is not None:
            normalized = []
            for item in fallback_providers:
                provider = item.lower().strip()
                if provider not in SUPPORTED_PROVIDERS:
                    raise ValidationAppError(
                        f"Unsupported fallback provider '{provider}'.",
                        details={"supported": sorted(SUPPORTED_PROVIDERS)},
                    )
                normalized.append(provider)
            fallback_providers = normalized
        return await self.routing.upsert_policy(
            organization_id=organization_id,
            operation=operation,
            primary_provider=primary_provider.lower().strip()
            if primary_provider
            else None,
            fallback_providers=fallback_providers,
        )

    async def provider_health(self) -> list[dict[str, object]]:
        configs = await self.configs.list_configs(organization_id=None)
        health: list[dict[str, object]] = []
        for config in configs:
            snapshot = await self.circuit_breaker.get_state(config.provider_name)
            health.append(
                {
                    "provider_name": config.provider_name,
                    "enabled": config.enabled,
                    "configured": is_provider_configured(config),
                    "last_failure_category": snapshot.last_failure_category,
                    "circuit_state": snapshot.state.value,
                    "avg_latency_ms": snapshot.avg_latency_ms,
                }
            )
        return health

    async def resolve_provider_chain(
        self,
        operation: LLMOperation,
        *,
        organization_id: UUID | None,
        explicit_provider: str | None = None,
    ) -> list[tuple[str, ProviderConfig | None]]:
        if explicit_provider:
            name = explicit_provider.lower().strip()
            org_config = None
            if organization_id is not None:
                org_config = await self.configs.get_config(
                    name, organization_id=organization_id
                )
                if org_config is not None and not org_config.enabled:
                    raise ValidationAppError(
                        f"Provider '{name}' is disabled for this organization.",
                    )
            platform_config = await self.configs.get_config(name, organization_id=None)
            if org_config is not None:
                return [(name, org_config)]
            if platform_config is not None and platform_config.enabled:
                return [(name, platform_config)]
            if name in SUPPORTED_PROVIDERS:
                return [(name, platform_config)]
            raise ValidationAppError(
                f"Unsupported provider '{name}'.",
                details={"supported": sorted(SUPPORTED_PROVIDERS)},
            )

        org_policy = None
        if organization_id is not None:
            org_policy = await self.routing.get_policy(
                operation, organization_id=organization_id
            )
        policy = org_policy or await self.routing.get_policy(
            operation, organization_id=None
        )
        if policy is None:
            settings = get_settings()
            return [(settings.llm_provider.lower(), None)]

        chain: list[str] = [policy.primary_provider, *policy.fallback_providers]
        resolved: list[tuple[str, ProviderConfig | None]] = []
        seen: set[str] = set()
        for provider_name in chain:
            name = provider_name.lower().strip()
            if not name or name in seen:
                continue
            seen.add(name)
            org_config = None
            if organization_id is not None:
                org_config = await self.configs.get_config(
                    name, organization_id=organization_id
                )
                if org_config is not None and not org_config.enabled:
                    continue
            platform_config = await self.configs.get_config(name, organization_id=None)
            if platform_config is not None and not platform_config.enabled:
                continue
            config = org_config or platform_config
            resolved.append((name, config))
        if not resolved:
            settings = get_settings()
            return [(settings.llm_provider.lower(), None)]
        return resolved

    def build_provider(self, provider_name: str) -> LLMProvider:
        return get_llm_provider(provider_name)

    async def generate_with_routing(
        self,
        *,
        operation: LLMOperation,
        organization_id: UUID | None,
        explicit_provider: str | None,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.2,
        max_output_tokens: int | None = None,
    ) -> tuple[str, str, int, int]:
        chain = await self.resolve_provider_chain(
            operation,
            organization_id=organization_id,
            explicit_provider=explicit_provider,
        )
        last_error: Exception | None = None
        for provider_name, config in chain:
            if await self.circuit_breaker.is_open(provider_name):
                continue
            provider = self.build_provider(provider_name)
            tokens_limit = max_output_tokens or (
                config.max_output_tokens if config else 4096
            )
            started = time.perf_counter()
            try:
                result = await provider.generate(
                    prompt,
                    system_prompt,
                    temperature=temperature,
                    max_output_tokens=tokens_limit,
                )
                latency_ms = (time.perf_counter() - started) * 1000
                await self.circuit_breaker.record_success(provider_name, latency_ms)
                input_tokens = estimate_tokens(prompt)
                if system_prompt:
                    input_tokens += estimate_tokens(system_prompt)
                output_tokens = estimate_tokens(result)
                return result, provider_name, input_tokens, output_tokens
            except (LLMProviderError, httpx.HTTPError, TimeoutError) as exc:
                latency_ms = (time.perf_counter() - started) * 1000
                category = "transient"
                if isinstance(exc, LLMProviderError):
                    category = str(exc.details.get("category", "transient"))
                await self.circuit_breaker.record_failure(
                    provider_name, category=category
                )
                last_error = exc
                continue
            except Exception:  # noqa: BLE001
                await self.circuit_breaker.record_failure(
                    provider_name, category="permanent"
                )
                raise

        if last_error is not None:
            raise LLMProviderError(
                "All configured LLM providers failed.",
                details={"operation": operation.value},
            ) from last_error
        raise LLMProviderError(
            "No enabled LLM providers available.",
            details={"operation": operation.value},
        )
