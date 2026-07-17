from typing import Literal

from pydantic import BaseModel, Field


class ReviewRequest(BaseModel):
    type: Literal["dockerfile", "kubernetes", "terraform", "github-actions"]
    content: str = Field(min_length=1, max_length=500_000)
    provider: str = "gemini"


class ReviewFinding(BaseModel):
    severity: Literal["info", "low", "medium", "high", "critical"]
    title: str
    description: str
    recommendation: str
    line: int | None = None
    source: Literal["static", "llm"] = "static"


class ReviewResponse(BaseModel):
    score: int = Field(ge=0, le=100)
    summary: str
    findings: list[ReviewFinding] = Field(default_factory=list)
    improved_content: str | None = None
    disclaimer: str = (
        "AI-assisted review combining static checks and LLM suggestions. "
        "Human review required before production use."
    )
