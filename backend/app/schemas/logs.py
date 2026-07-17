from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class LogAnalyzeRequest(BaseModel):
    content: str = Field(min_length=1, max_length=500_000)
    provider: str = "gemini"
    async_mode: bool = False


class LogAnalyzeResult(BaseModel):
    summary: str
    severity: Literal["low", "medium", "high", "critical"]
    detected_errors: list[str] = Field(default_factory=list)
    possible_causes: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    diagnostic_commands: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    disclaimer: str = (
        "AI-generated analysis for review only. Commands are suggestions and "
        "were not executed."
    )


class AsyncTaskResponse(BaseModel):
    task_id: str
    analysis_id: UUID
    status: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None
