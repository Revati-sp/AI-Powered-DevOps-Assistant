from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.artifact_tag import (
    ArtifactFavorite,
    ArtifactTag,
    ArtifactTagAssociation,
)
from app.models.artifact_version import ArtifactVersion
from app.models.generated_artifact import GeneratedArtifact


class ArtifactTagRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create_tag(
        self,
        *,
        user_id: UUID,
        name: str,
        organization_id: UUID | None = None,
        color: str | None = None,
    ) -> ArtifactTag:
        normalized = name.strip().lower()
        result = await self.session.execute(
            select(ArtifactTag).where(
                ArtifactTag.user_id == user_id,
                ArtifactTag.organization_id == organization_id,
                func.lower(ArtifactTag.name) == normalized,
            )
        )
        tag = result.scalar_one_or_none()
        if tag is not None:
            if color is not None:
                tag.color = color
            return tag
        tag = ArtifactTag(
            user_id=user_id,
            organization_id=organization_id,
            name=name.strip(),
            color=color,
        )
        self.session.add(tag)
        await self.session.flush()
        await self.session.refresh(tag)
        return tag

    async def list_tags_for_scope(
        self,
        *,
        user_id: UUID,
        organization_id: UUID | None,
    ) -> list[ArtifactTag]:
        result = await self.session.execute(
            select(ArtifactTag)
            .where(
                ArtifactTag.user_id == user_id,
                ArtifactTag.organization_id == organization_id,
            )
            .order_by(ArtifactTag.name.asc())
        )
        return list(result.scalars().all())

    async def get_tag(self, tag_id: UUID) -> ArtifactTag | None:
        return await self.session.get(ArtifactTag, tag_id)

    async def add_tag_to_artifact(
        self, *, artifact_id: UUID, tag_id: UUID
    ) -> ArtifactTagAssociation:
        result = await self.session.execute(
            select(ArtifactTagAssociation).where(
                ArtifactTagAssociation.artifact_id == artifact_id,
                ArtifactTagAssociation.tag_id == tag_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            return existing
        association = ArtifactTagAssociation(artifact_id=artifact_id, tag_id=tag_id)
        self.session.add(association)
        await self.session.flush()
        await self.session.refresh(association)
        return association

    async def remove_tag_from_artifact(
        self, *, artifact_id: UUID, tag_id: UUID
    ) -> bool:
        cursor = await self.session.execute(
            delete(ArtifactTagAssociation).where(
                ArtifactTagAssociation.artifact_id == artifact_id,
                ArtifactTagAssociation.tag_id == tag_id,
            )
        )
        return (cursor.rowcount or 0) > 0 if isinstance(cursor, CursorResult) else False

    async def list_tags_for_artifact(self, artifact_id: UUID) -> list[ArtifactTag]:
        result = await self.session.execute(
            select(ArtifactTag)
            .join(
                ArtifactTagAssociation,
                ArtifactTagAssociation.tag_id == ArtifactTag.id,
            )
            .where(ArtifactTagAssociation.artifact_id == artifact_id)
            .order_by(ArtifactTag.name.asc())
        )
        return list(result.scalars().all())

    async def favorite_artifact(
        self, *, user_id: UUID, artifact_id: UUID
    ) -> ArtifactFavorite:
        result = await self.session.execute(
            select(ArtifactFavorite).where(
                ArtifactFavorite.user_id == user_id,
                ArtifactFavorite.artifact_id == artifact_id,
            )
        )
        favorite = result.scalar_one_or_none()
        if favorite is not None:
            return favorite
        favorite = ArtifactFavorite(user_id=user_id, artifact_id=artifact_id)
        self.session.add(favorite)
        await self.session.flush()
        await self.session.refresh(favorite)
        return favorite

    async def unfavorite_artifact(self, *, user_id: UUID, artifact_id: UUID) -> bool:
        cursor = await self.session.execute(
            delete(ArtifactFavorite).where(
                ArtifactFavorite.user_id == user_id,
                ArtifactFavorite.artifact_id == artifact_id,
            )
        )
        return (cursor.rowcount or 0) > 0 if isinstance(cursor, CursorResult) else False

    async def is_favorited(self, *, user_id: UUID, artifact_id: UUID) -> bool:
        result = await self.session.execute(
            select(func.count())
            .select_from(ArtifactFavorite)
            .where(
                ArtifactFavorite.user_id == user_id,
                ArtifactFavorite.artifact_id == artifact_id,
            )
        )
        return int(result.scalar_one()) > 0

    async def list_tags_for_artifacts(
        self, artifact_ids: list[UUID]
    ) -> dict[UUID, list[str]]:
        if not artifact_ids:
            return {}
        result = await self.session.execute(
            select(ArtifactTagAssociation.artifact_id, ArtifactTag.name)
            .join(ArtifactTag, ArtifactTag.id == ArtifactTagAssociation.tag_id)
            .where(ArtifactTagAssociation.artifact_id.in_(artifact_ids))
            .order_by(ArtifactTag.name.asc())
        )
        tags: dict[UUID, list[str]] = {artifact_id: [] for artifact_id in artifact_ids}
        for artifact_id, name in result.all():
            tags[artifact_id].append(name)
        return tags

    async def list_favorited_artifact_ids(
        self, *, user_id: UUID, artifact_ids: list[UUID]
    ) -> set[UUID]:
        if not artifact_ids:
            return set()
        result = await self.session.execute(
            select(ArtifactFavorite.artifact_id).where(
                ArtifactFavorite.user_id == user_id,
                ArtifactFavorite.artifact_id.in_(artifact_ids),
            )
        )
        return set(result.scalars().all())

    async def set_archived(
        self, artifact: GeneratedArtifact, *, archived: bool
    ) -> GeneratedArtifact:
        artifact.archived_at = datetime.now(UTC) if archived else None
        artifact.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(artifact)
        return artifact

    async def list_artifacts_filtered(
        self,
        *,
        user_id: UUID | None = None,
        organization_id: UUID | None = None,
        search: str | None = None,
        tag_names: list[str] | None = None,
        favorites_only: bool = False,
        favorites_user_id: UUID | None = None,
        include_archived: bool = False,
        archived_only: bool = False,
        creator_id: UUID | None = None,
        artifact_type: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        updated_from: datetime | None = None,
        updated_to: datetime | None = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
        limit: int,
        offset: int,
    ) -> tuple[list[GeneratedArtifact], int]:
        query = select(GeneratedArtifact).where(GeneratedArtifact.deleted_at.is_(None))
        if archived_only:
            query = query.where(GeneratedArtifact.archived_at.is_not(None))
        elif not include_archived:
            query = query.where(GeneratedArtifact.archived_at.is_(None))
        if organization_id is not None:
            query = query.where(GeneratedArtifact.organization_id == organization_id)
        elif user_id is not None:
            query = query.where(
                GeneratedArtifact.user_id == user_id,
                GeneratedArtifact.organization_id.is_(None),
            )
        if creator_id is not None:
            query = query.where(GeneratedArtifact.user_id == creator_id)
        if artifact_type is not None:
            query = query.where(GeneratedArtifact.artifact_type == artifact_type)
        if created_from is not None:
            query = query.where(GeneratedArtifact.created_at >= created_from)
        if created_to is not None:
            query = query.where(GeneratedArtifact.created_at <= created_to)
        if updated_from is not None:
            query = query.where(GeneratedArtifact.updated_at >= updated_from)
        if updated_to is not None:
            query = query.where(GeneratedArtifact.updated_at <= updated_to)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    GeneratedArtifact.name.ilike(pattern),
                    GeneratedArtifact.description.ilike(pattern),
                )
            )
        if favorites_only and favorites_user_id is not None:
            query = query.join(
                ArtifactFavorite,
                ArtifactFavorite.artifact_id == GeneratedArtifact.id,
            ).where(ArtifactFavorite.user_id == favorites_user_id)
        if tag_names:
            normalized = [name.strip().lower() for name in tag_names if name.strip()]
            for name in normalized:
                query = query.where(
                    GeneratedArtifact.id.in_(
                        select(ArtifactTagAssociation.artifact_id)
                        .join(
                            ArtifactTag, ArtifactTag.id == ArtifactTagAssociation.tag_id
                        )
                        .where(func.lower(ArtifactTag.name) == name)
                    )
                )

        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = int(count_result.scalar_one())
        if sort_by == "current_version_number":
            query = query.outerjoin(
                ArtifactVersion,
                ArtifactVersion.id == GeneratedArtifact.current_version_id,
            )
            sort_column = ArtifactVersion.version_number
        else:
            sort_column = getattr(GeneratedArtifact, sort_by)
        ordering = sort_column.asc() if sort_order == "asc" else sort_column.desc()
        id_ordering = (
            GeneratedArtifact.id.asc()
            if sort_order == "asc"
            else GeneratedArtifact.id.desc()
        )
        result = await self.session.execute(
            query.options(selectinload(GeneratedArtifact.versions))
            .order_by(ordering, id_ordering)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().unique().all()), total
