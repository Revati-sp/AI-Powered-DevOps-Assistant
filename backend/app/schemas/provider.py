from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.provider_config import LLMOperation


class ProviderConfigResponse(BaseModel):
    id: UUID
    organization_id: UUID | None = None
    provider_name: str
    enabled: bool
    default_model: str
    timeout_seconds: int
    max_retries: int
    priority: int
    max_output_tokens: int
    secret_env_key: str
    base_url_env_key: str | None = None
    model_env_key: str | None = None
    configured: bool = False
    created_at: datetime
    updated_at: datetime


class ProviderConfigPatchRequest(BaseModel):
    enabled: bool | None = None
    default_model: str | None = Field(default=None, max_length=120)
    timeout_seconds: int | None = Field(default=None, ge=1, le=600)
    max_retries: int | None = Field(default=None, ge=0, le=10)
    priority: int | None = Field(default=None, ge=0, le=1000)
    max_output_tokens: int | None = Field(default=None, ge=1, le=128000)
    secret_env_key: str | None = Field(default=None, max_length=120)
    base_url_env_key: str | None = Field(default=None, max_length=120)
    model_env_key: str | None = Field(default=None, max_length=120)


class ProviderRoutingResponse(BaseModel):
    id: UUID
    organization_id: UUID | None = None
    operation: LLMOperation
    primary_provider: str
    fallback_providers: list[str]
    created_at: datetime
    updated_at: datetime


class ProviderRoutingPatchRequest(BaseModel):
    primary_provider: str | None = Field(default=None, max_length=50)
    fallback_providers: list[str] | None = None


class ProviderHealthResponse(BaseModel):
    provider_name: str
    enabled: bool
    configured: bool
    last_failure_category: str | None = None
    circuit_state: str
    avg_latency_ms: float | None = None
