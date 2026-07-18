from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class UsagePeriodSummary(BaseModel):
    tokens: int
    requests: int
    estimated: bool = True


class UsageEventResponse(ORMModel):
    id: UUID
    user_id: UUID
    organization_id: UUID | None = None
    operation: str
    provider: str
    model: str | None = None
    input_tokens: int
    output_tokens: int
    total_tokens: int
    is_estimated: bool
    created_at: datetime


class UserUsageResponse(BaseModel):
    user_id: UUID
    daily: UsagePeriodSummary
    monthly: UsagePeriodSummary
    recent_events: list[UsageEventResponse]


class OrganizationQuotaResponse(ORMModel):
    id: UUID
    organization_id: UUID
    daily_token_limit: int | None = None
    daily_request_limit: int | None = None
    monthly_token_limit: int | None = None
    monthly_request_limit: int | None = None
    enforce_quotas: bool
    created_at: datetime
    updated_at: datetime


class OrganizationUsageResponse(BaseModel):
    organization_id: UUID
    daily: UsagePeriodSummary
    monthly: UsagePeriodSummary
    quota: OrganizationQuotaResponse | None = None


class OrganizationQuotaPatchRequest(BaseModel):
    daily_token_limit: int | None = Field(default=None, ge=0)
    daily_request_limit: int | None = Field(default=None, ge=0)
    monthly_token_limit: int | None = Field(default=None, ge=0)
    monthly_request_limit: int | None = Field(default=None, ge=0)
    enforce_quotas: bool | None = None
    clear_daily_limits: bool = False
    clear_monthly_limits: bool = False
