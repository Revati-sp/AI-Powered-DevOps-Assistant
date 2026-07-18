from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
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
        organization_id: UUID | None = None,
        description: str | None = None,
    ) -> GeneratedArtifact:
        artifact = GeneratedArtifact(
            user_id=user_id,
            organization_id=organization_id,
            artifact_type=artifact_type,
            name=name,
            description=description,
            content=content,
            metadata_json=metadata_json,
        )
        self.session.add(artifact)
        await self.session.flush()
        await self.session.refresh(artifact)
        return artifact

    async def get_artifact_for_update(
        self, artifact_id: UUID
    ) -> GeneratedArtifact | None:
        result = await self.session.execute(
            select(GeneratedArtifact)
            .where(
                GeneratedArtifact.id == artifact_id,
                GeneratedArtifact.deleted_at.is_(None),
            )
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_artifact(self, artifact_id: UUID) -> GeneratedArtifact | None:
        result = await self.session.execute(
            select(GeneratedArtifact).where(
                GeneratedArtifact.id == artifact_id,
                GeneratedArtifact.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_artifacts(
        self,
        *,
        user_id: UUID | None = None,
        organization_id: UUID | None = None,
        limit: int,
        offset: int,
    ) -> tuple[list[GeneratedArtifact], int]:
        query = select(GeneratedArtifact).where(GeneratedArtifact.deleted_at.is_(None))
        if organization_id is not None:
            query = query.where(GeneratedArtifact.organization_id == organization_id)
        elif user_id is not None:
            query = query.where(
                GeneratedArtifact.user_id == user_id,
                GeneratedArtifact.organization_id.is_(None),
            )

        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = int(count_result.scalar_one())

        result = await self.session.execute(
            query.order_by(GeneratedArtifact.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    async def update_artifact(
        self,
        artifact: GeneratedArtifact,
        *,
        name: str | None = None,
        description: str | None = None,
        content: str | None = None,
        current_version_id: UUID | None = None,
    ) -> GeneratedArtifact:
        if name is not None:
            artifact.name = name
        if description is not None:
            artifact.description = description
        if content is not None:
            artifact.content = content
        if current_version_id is not None:
            artifact.current_version_id = current_version_id
        artifact.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(artifact)
        return artifact

    async def soft_delete(self, artifact: GeneratedArtifact) -> GeneratedArtifact:
        artifact.deleted_at = datetime.now(UTC)
        artifact.updated_at = datetime.now(UTC)
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
