from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import Analysis, AnalysisStatus, AnalysisType
from app.models.generated_artifact import ArtifactType, GeneratedArtifact


class ArtifactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_artifact(
        self,
        *,
        user_id: UUID,
        artifact_type: ArtifactType,
        name: str,
        content: str,
        metadata_json: dict[str, Any] | None = None,
    ) -> GeneratedArtifact:
        artifact = GeneratedArtifact(
            user_id=user_id,
            artifact_type=artifact_type,
            name=name,
            content=content,
            metadata_json=metadata_json,
        )
        self.session.add(artifact)
        await self.session.flush()
        await self.session.refresh(artifact)
        return artifact

    async def create_analysis(
        self,
        *,
        user_id: UUID,
        analysis_type: AnalysisType,
        input_preview: str,
        status: AnalysisStatus = AnalysisStatus.PENDING,
        result_json: dict[str, Any] | None = None,
        task_id: str | None = None,
    ) -> Analysis:
        analysis = Analysis(
            user_id=user_id,
            analysis_type=analysis_type,
            input_preview=input_preview,
            status=status,
            result_json=result_json,
            task_id=task_id,
        )
        self.session.add(analysis)
        await self.session.flush()
        await self.session.refresh(analysis)
        return analysis

    async def get_analysis_by_task_id(self, task_id: str) -> Analysis | None:
        result = await self.session.execute(
            select(Analysis).where(Analysis.task_id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_analysis_for_user(
        self, analysis_id: UUID, user_id: UUID
    ) -> Analysis | None:
        result = await self.session.execute(
            select(Analysis).where(
                Analysis.id == analysis_id,
                Analysis.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_analysis(
        self,
        analysis: Analysis,
        *,
        status: AnalysisStatus | None = None,
        result_json: dict[str, Any] | None = None,
        task_id: str | None = None,
    ) -> Analysis:
        if status is not None:
            analysis.status = status
        if result_json is not None:
            analysis.result_json = result_json
        if task_id is not None:
            analysis.task_id = task_id
        await self.session.flush()
        await self.session.refresh(analysis)
        return analysis
