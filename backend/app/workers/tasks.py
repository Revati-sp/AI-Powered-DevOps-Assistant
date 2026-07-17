from __future__ import annotations

import asyncio
from uuid import UUID

from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.models.analysis import AnalysisStatus
from app.repositories.artifact_repository import ArtifactRepository
from app.services.log_analyzer import analyze_log_content
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


async def _analyze_logs_async(
    analysis_id: str,
    user_id: str,
    content: str,
    provider_name: str,
) -> dict[str, object]:
    async with AsyncSessionLocal() as session:
        repo = ArtifactRepository(session)
        analysis = await repo.get_analysis_for_user(UUID(analysis_id), UUID(user_id))
        if analysis is None:
            return {"error": "Analysis not found"}

        await repo.update_analysis(analysis, status=AnalysisStatus.RUNNING)
        await session.commit()

        try:
            result = await analyze_log_content(content, provider_name=provider_name)
            await repo.update_analysis(
                analysis,
                status=AnalysisStatus.COMPLETED,
                result_json=result.model_dump(),
            )
            await session.commit()
            return result.model_dump()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Async log analysis failed")
            await repo.update_analysis(
                analysis,
                status=AnalysisStatus.FAILED,
                result_json={"error": str(exc)},
            )
            await session.commit()
            return {"error": "Analysis failed"}


@celery_app.task(name="analyze_logs_task", bind=True)
def analyze_logs_task(
    self,
    analysis_id: str,
    user_id: str,
    content: str,
    provider_name: str = "gemini",
) -> dict[str, object]:
    return asyncio.run(
        _analyze_logs_async(analysis_id, user_id, content, provider_name)
    )
