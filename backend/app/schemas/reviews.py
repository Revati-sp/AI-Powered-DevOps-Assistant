from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

ReviewConfigType = Literal[
    "dockerfile",
    "kubernetes",
    "terraform",
    "github-actions",
    "gitlab-ci",
    "jenkins",
]


class ReviewRequest(BaseModel):
    type: ReviewConfigType
    content: str = Field(min_length=1, max_length=500_000)
    provider: str = "gemini"
    organization_id: UUID | None = None
    policy_pack_ids: list[UUID] = Field(default_factory=list)


class ReviewFinding(BaseModel):
    severity: Literal["info", "low", "medium", "high", "critical"]
    title: str
    description: str
    recommendation: str
    line: int | None = None
    source: Literal["static", "llm", "organization_policy"] = "static"
    rule_key: str | None = None
    policy_pack_id: UUID | None = None


class ReviewResponse(BaseModel):
    score: int = Field(ge=0, le=100)
    summary: str
    findings: list[ReviewFinding] = Field(default_factory=list)
    built_in_findings: list[ReviewFinding] = Field(default_factory=list)
    organization_policy_findings: list[ReviewFinding] = Field(default_factory=list)
    llm_findings: list[ReviewFinding] = Field(default_factory=list)
    improved_content: str | None = None
    disclaimer: str = (
        "AI-assisted review combining static checks and LLM suggestions. "
        "Human review required before production use."
    )
