from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact_version import ArtifactVersion


class ArtifactVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_number(
        self, artifact_id: UUID, version_number: int
    ) -> ArtifactVersion | None:
        result = await self.session.execute(
            select(ArtifactVersion).where(
                ArtifactVersion.artifact_id == artifact_id,
                ArtifactVersion.version_number == version_number,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_hash(
        self, artifact_id: UUID, content_hash: str
    ) -> ArtifactVersion | None:
        result = await self.session.execute(
            select(ArtifactVersion)
            .where(
                ArtifactVersion.artifact_id == artifact_id,
                ArtifactVersion.content_hash == content_hash,
            )
            .order_by(ArtifactVersion.version_number.desc())
        )
        return result.scalars().first()

    async def get_max_version_number(self, artifact_id: UUID) -> int:
        result = await self.session.execute(
            select(func.coalesce(func.max(ArtifactVersion.version_number), 0)).where(
                ArtifactVersion.artifact_id == artifact_id
            )
        )
        return int(result.scalar_one())

    async def list_versions(
        self,
        artifact_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[ArtifactVersion], int]:
        base = select(ArtifactVersion).where(ArtifactVersion.artifact_id == artifact_id)
        count_result = await self.session.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = int(count_result.scalar_one())

        result = await self.session.execute(
            base.order_by(ArtifactVersion.version_number.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    async def create_version(
        self,
        *,
        artifact_id: UUID,
        version_number: int,
        content: str,
        content_hash: str,
        created_by: UUID,
        metadata_json: dict[str, Any] | None = None,
    ) -> ArtifactVersion:
        version = ArtifactVersion(
            artifact_id=artifact_id,
            version_number=version_number,
            content=content,
            content_hash=content_hash,
            metadata_json=metadata_json,
            created_by=created_by,
        )
        self.session.add(version)
        await self.session.flush()
        await self.session.refresh(version)
        return version
