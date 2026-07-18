from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

TimeRange = Literal["24h", "7d", "30d"]


class CountSummary(BaseModel):
    total: int = 0
    recent: int = 0


class ArtifactCountSummary(BaseModel):
    total: int = 0
    favorites: int = 0
    archived: int = 0


class TaskCountSummary(BaseModel):
    queued: int = 0
    running: int = 0
    succeeded: int = 0
    failed: int = 0


class FindingCountSummary(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class UsageSummary(BaseModel):
    requests_used: int = 0
    requests_limit: int = 0


class OrganizationSummary(BaseModel):
    member_count: int = 0
    active_policy_packs: int = 0


class DashboardSummary(BaseModel):
    conversations: CountSummary
    artifacts: ArtifactCountSummary
    tasks: TaskCountSummary
    findings: FindingCountSummary
    usage: UsageSummary
    organization: OrganizationSummary | None = None


class ActivityItem(BaseModel):
    id: UUID | str
    type: Literal["conversation", "analysis", "artifact", "task", "policy", "member"]
    title: str
    timestamp: datetime
    status: str | None = None
    organization_id: UUID | None = None
    route_target: str


class DashboardActivity(BaseModel):
    items: list[ActivityItem] = Field(default_factory=list)


class FindingItem(BaseModel):
    analysis_id: UUID
    severity: Literal["critical", "high", "medium", "low"]
    title: str
    timestamp: datetime
    organization_id: UUID | None = None


class DashboardFindings(BaseModel):
    counts: FindingCountSummary
    items: list[FindingItem] = Field(default_factory=list)


class DashboardTasks(BaseModel):
    counts: TaskCountSummary
    items: list[ActivityItem] = Field(default_factory=list)
