from __future__ import annotations

import asyncio
import concurrent.futures
from collections.abc import Coroutine
from typing import Any, TypeVar
from uuid import UUID

from celery.exceptions import SoftTimeLimitExceeded

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.core.metrics import record_background_task
from app.models.analysis import AnalysisStatus
from app.repositories.artifact_repository import ArtifactRepository
from app.services.log_analyzer import analyze_log_content
from app.services.task_service import TaskService
from app.workers.celery_app import celery_app

logger = get_logger(__name__)
settings = get_settings()
T = TypeVar("T")


def _run_async[T](coro: Coroutine[Any, Any, T]) -> T:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(asyncio.run, coro).result()


async def _analyze_logs_async(
    background_task_id: str,
    analysis_id: str,
    user_id: str,
    content: str,
    provider_name: str,
) -> dict[str, object]:
    task_uuid = UUID(background_task_id)
    async with AsyncSessionLocal() as session:
        repo = ArtifactRepository(session)
        task_service = TaskService(session)
        analysis = await repo.get_analysis_for_user(UUID(analysis_id), UUID(user_id))
        if analysis is None:
            await task_service.mark_failed(
                task_uuid,
                error_code="NOT_FOUND",
                error_message="Analysis not found",
            )
            await session.commit()
            record_background_task("log_analysis", "failed")
            return {"error": "Analysis not found"}

        await task_service.mark_running(task_uuid, progress=10)
        await repo.update_analysis(analysis, status=AnalysisStatus.RUNNING)
        await session.commit()

        try:
            result = await analyze_log_content(content, provider_name=provider_name)
            payload = result.model_dump()
            payload["analysis_id"] = analysis_id
            await repo.update_analysis(
                analysis,
                status=AnalysisStatus.COMPLETED,
                result_json=payload,
            )
            await task_service.mark_succeeded(task_uuid, payload)
            await session.commit()
            record_background_task("log_analysis", "succeeded")
            return payload
        except SoftTimeLimitExceeded:
            logger.warning("Async log analysis hit soft time limit")
            await repo.update_analysis(
                analysis,
                status=AnalysisStatus.FAILED,
                result_json={"error": "Analysis timed out"},
            )
            await task_service.mark_failed(
                task_uuid,
                error_code="TIMEOUT",
                error_message="Analysis timed out",
                result_json={"analysis_id": analysis_id},
            )
            await session.commit()
            record_background_task("log_analysis", "failed")
            return {"error": "Analysis timed out"}
        except Exception as exc:  # noqa: BLE001
            logger.exception("Async log analysis failed")
            await repo.update_analysis(
                analysis,
                status=AnalysisStatus.FAILED,
                result_json={"error": "Analysis failed"},
            )
            await task_service.mark_failed(
                task_uuid,
                error_code="ANALYSIS_FAILED",
                error_message="Analysis failed",
                result_json={"analysis_id": analysis_id},
            )
            await session.commit()
            record_background_task("log_analysis", "failed")
            return {"error": "Analysis failed", "detail": type(exc).__name__}


@celery_app.task(
    name="analyze_logs_task",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError, OSError),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=settings.celery_max_retries,
)
def analyze_logs_task(
    self,
    background_task_id: str,
    analysis_id: str,
    user_id: str,
    content: str,
    provider_name: str = "gemini",
) -> dict[str, object]:
    try:
        return _run_async(
            _analyze_logs_async(
                background_task_id,
                analysis_id,
                user_id,
                content,
                provider_name,
            )
        )
    except (ConnectionError, TimeoutError, OSError):
        record_background_task("log_analysis", "retry")
        raise


@celery_app.task(name="cleanup_background_tasks")
def cleanup_background_tasks() -> int:
    async def _cleanup() -> int:
        async with AsyncSessionLocal() as session:
            deleted = await TaskService(session).cleanup_expired_tasks()
            await session.commit()
            return deleted

    return _run_async(_cleanup())
