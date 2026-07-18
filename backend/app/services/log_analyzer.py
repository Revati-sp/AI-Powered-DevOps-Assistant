from __future__ import annotations

import json
import re
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.analysis import AnalysisStatus, AnalysisType
from app.models.provider_config import LLMOperation
from app.models.user import User
from app.repositories.artifact_repository import ArtifactRepository
from app.schemas.logs import AsyncTaskResponse, LogAnalyzeResult
from app.services.audit_service import AuditRequestContext
from app.services.llm.factory import get_llm_provider
from app.services.llm.gateway import LLMGateway
from app.services.llm.prompts import LOG_ANALYSIS_SYSTEM_PROMPT
from app.services.task_service import TASK_TYPE_LOG_ANALYSIS, TaskService
from app.services.usage_quota_service import UsageQuotaService
from app.utils.sanitization import preview_text, sanitize_text

logger = get_logger(__name__)

ERROR_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"CrashLoopBackOff", re.I), "Kubernetes CrashLoopBackOff"),
    (
        re.compile(r"ImagePullBackOff|ErrImagePull", re.I),
        "Kubernetes image pull failure",
    ),
    (re.compile(r"OOMKilled", re.I), "Container OOMKilled"),
    (re.compile(r"permission denied", re.I), "Permission denied"),
    (re.compile(r"connection refused", re.I), "Connection refused"),
    (re.compile(r"no space left on device", re.I), "Disk space exhausted"),
    (re.compile(r"Traceback \(most recent call last\):", re.I), "Python stack trace"),
    (re.compile(r"nginx:\s*\[error\]", re.I), "Nginx error"),
    (re.compile(r"Failed to start|Unit .+ failed", re.I), "Linux service failure"),
    (
        re.compile(r"ERROR: Job failed|Process completed with exit code", re.I),
        "CI/CD failure",
    ),
    (
        re.compile(r"docker:\s*Error|Cannot connect to the Docker daemon", re.I),
        "Docker error",
    ),
]


def _static_log_signals(content: str) -> dict[str, Any]:
    detected: list[str] = []
    for pattern, label in ERROR_PATTERNS:
        if pattern.search(content):
            detected.append(label)

    repeats: dict[str, int] = {}
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.search(r"error|exception|failed|fatal", stripped, re.I):
            repeats[stripped[:200]] = repeats.get(stripped[:200], 0) + 1

    repeated = [f"{count}x: {line}" for line, count in repeats.items() if count >= 3]
    severity = "low"
    if any("OOM" in d or "CrashLoop" in d for d in detected):
        severity = "critical"
    elif detected:
        severity = "high"
    elif repeated:
        severity = "medium"

    return {
        "detected_errors": detected + repeated[:10],
        "severity_hint": severity,
    }


def _parse_llm_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def _fallback_result(signals: dict[str, Any]) -> LogAnalyzeResult:
    return LogAnalyzeResult(
        summary="Static analysis completed. LLM enrichment unavailable or failed.",
        severity=signals["severity_hint"],
        detected_errors=signals["detected_errors"],
        possible_causes=[
            "Dependency or configuration mismatch",
            "Resource exhaustion",
            "Permission or networking issue",
        ],
        recommended_actions=[
            "Inspect the most recent error lines and surrounding context",
            "Verify recent deploys and config changes",
            "Check resource usage and health probes",
        ],
        diagnostic_commands=[
            "kubectl describe pod <pod> -n <namespace>",
            "kubectl logs <pod> -n <namespace> --previous",
            "journalctl -u <service> -n 200 --no-pager",
        ],
        confidence=0.45,
    )


async def analyze_log_content(
    content: str,
    *,
    provider_name: str = "gemini",
    session: AsyncSession | None = None,
    user_id: UUID | None = None,
) -> LogAnalyzeResult:
    """Analyze logs with static signals + LLM enrichment.

    When ``session`` and ``user_id`` are provided, records estimated usage after
    a successful LLM call (Celery-friendly path without a full User ORM load).
    """
    cleaned = sanitize_text(content, max_length=500_000)
    signals = _static_log_signals(cleaned)
    fallback = _fallback_result(signals)

    try:
        provider = get_llm_provider(provider_name)
        prompt = (
            "Analyze the following logs. Use the static signals as hints.\n"
            f"Static signals: {json.dumps(signals)}\n\n"
            f"LOGS:\n{cleaned[:120_000]}"
        )
        raw = await provider.generate(prompt, system_prompt=LOG_ANALYSIS_SYSTEM_PROMPT)
        data = _parse_llm_json(raw)
        result = LogAnalyzeResult.model_validate(data)
        if session is not None and user_id is not None:
            await UsageQuotaService(session).record_llm_usage(
                user_id=user_id,
                organization_id=None,
                operation=LLMOperation.LOG_ANALYSIS.value,
                provider=provider.name,
                model=None,
                input_tokens=max(1, len(prompt) // 4),
                output_tokens=max(1, len(raw) // 4),
                is_estimated=True,
            )
        return result
    except Exception:  # noqa: BLE001
        return fallback


class LogAnalyzerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.artifacts = ArtifactRepository(session)
        self.tasks = TaskService(session)

    async def analyze(
        self,
        user: User,
        content: str,
        *,
        provider_name: str = "gemini",
        persist: bool = True,
        organization_id: UUID | None = None,
    ) -> LogAnalyzeResult:
        cleaned = sanitize_text(content, max_length=500_000)
        signals = _static_log_signals(cleaned)
        fallback = _fallback_result(signals)
        result = fallback
        try:
            gateway = LLMGateway(self.session)
            prompt = (
                "Analyze the following logs. Use the static signals as hints.\n"
                f"Static signals: {json.dumps(signals)}\n\n"
                f"LOGS:\n{cleaned[:120_000]}"
            )
            raw, _provider = await gateway.generate(
                user=user,
                operation=LLMOperation.LOG_ANALYSIS,
                organization_id=organization_id,
                prompt=prompt,
                system_prompt=LOG_ANALYSIS_SYSTEM_PROMPT,
                explicit_provider=provider_name,
            )
            result = LogAnalyzeResult.model_validate(_parse_llm_json(raw))
        except Exception:  # noqa: BLE001
            logger.debug("Log analysis LLM enrichment failed; using static fallback")

        if persist:
            await self.artifacts.create_analysis(
                user_id=user.id,
                analysis_type=AnalysisType.LOG,
                input_preview=preview_text(cleaned),
                status=AnalysisStatus.COMPLETED,
                result_json=result.model_dump(),
            )
        return result

    async def enqueue_async(
        self,
        user: User,
        content: str,
        *,
        provider_name: str = "gemini",
        organization_id: UUID | None = None,
        idempotency_key: str | None = None,
        audit_context: AuditRequestContext | None = None,
    ) -> AsyncTaskResponse:
        from app.workers.tasks import analyze_logs_task

        cleaned = sanitize_text(content, max_length=500_000)
        background_task = await self.tasks.create_task(
            user,
            task_type=TASK_TYPE_LOG_ANALYSIS,
            organization_id=organization_id,
            idempotency_key=idempotency_key,
            audit_context=audit_context,
        )

        existing_analysis = await self.artifacts.get_analysis_by_task_id(
            str(background_task.id)
        )
        if existing_analysis is not None:
            return AsyncTaskResponse(
                task_id=str(background_task.id),
                status=background_task.status.value,
                analysis_id=existing_analysis.id,
                celery_task_id=background_task.celery_task_id,
            )

        analysis = await self.artifacts.create_analysis(
            user_id=user.id,
            analysis_type=AnalysisType.LOG,
            input_preview=preview_text(cleaned),
            status=AnalysisStatus.PENDING,
            task_id=str(background_task.id),
        )
        await self.session.flush()

        async_result = analyze_logs_task.delay(
            str(background_task.id),
            str(analysis.id),
            str(user.id),
            cleaned,
            provider_name,
        )
        await self.tasks.attach_celery_task_id(background_task, async_result.id)
        await self.artifacts.update_analysis(
            analysis,
            status=AnalysisStatus.RUNNING,
            task_id=str(background_task.id),
        )
        await self.session.commit()

        return AsyncTaskResponse(
            task_id=str(background_task.id),
            status=background_task.status.value,
            analysis_id=analysis.id,
            celery_task_id=async_result.id,
        )
