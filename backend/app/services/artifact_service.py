from __future__ import annotations

import difflib
import hashlib
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.generated_artifact import ArtifactType, GeneratedArtifact
from app.models.user import User
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.artifact_version_repository import ArtifactVersionRepository
from app.schemas.artifacts import (
    ArtifactCreateRequest,
    ArtifactDetailResponse,
    ArtifactDiffResponse,
    ArtifactRestoreResponse,
    ArtifactSummaryResponse,
    ArtifactUpdateRequest,
    ArtifactVersionCreateRequest,
    ArtifactVersionResponse,
)
from app.services.audit_service import AuditRequestContext, AuditService
from app.services.rbac import OrganizationAuthService, Permission


def compute_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _validate_content_size(content: str) -> None:
    settings = get_settings()
    size = len(content.encode("utf-8"))
    if size > settings.max_artifact_content_size_bytes:
        raise ValidationAppError(
            "Artifact content exceeds maximum allowed size",
            details={"max_bytes": settings.max_artifact_content_size_bytes},
        )


def _artifact_type_to_resource_type(artifact_type: ArtifactType) -> str:
    mapping = {
        ArtifactType.DOCKERFILE: "dockerfile",
        ArtifactType.KUBERNETES: "kubernetes",
        ArtifactType.GITHUB_ACTIONS: "github-actions",
        ArtifactType.GITLAB_CI: "gitlab-ci",
        ArtifactType.JENKINS: "jenkins",
        ArtifactType.TERRAFORM: "terraform",
        ArtifactType.SHELL_COMMAND: "shell-command",
        ArtifactType.PIPELINE: "pipeline",
        ArtifactType.COMMAND: "command",
    }
    return mapping.get(artifact_type, "general")


class ArtifactService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.artifacts = ArtifactRepository(session)
        self.versions = ArtifactVersionRepository(session)
        self.org_auth = OrganizationAuthService(session)
        self.audit = AuditService(session)

    async def _require_read(self, user: User, artifact: GeneratedArtifact) -> None:
        if artifact.organization_id is None:
            if artifact.user_id != user.id:
                raise NotFoundError("Artifact not found")
            return
        await self.org_auth.require_permission(
            artifact.organization_id, user.id, Permission.ARTIFACT_READ
        )

    async def _require_write(self, user: User, artifact: GeneratedArtifact) -> None:
        if artifact.organization_id is None:
            if artifact.user_id != user.id:
                raise NotFoundError("Artifact not found")
            return
        await self.org_auth.require_permission(
            artifact.organization_id, user.id, Permission.ARTIFACT_WRITE
        )

    async def _validate_org_create(
        self, user: User, organization_id: UUID | None
    ) -> None:
        if organization_id is None:
            return
        await self.org_auth.require_permission(
            organization_id, user.id, Permission.ARTIFACT_WRITE
        )

    def _to_summary(
        self, artifact: GeneratedArtifact, *, version_number: int | None = None
    ) -> ArtifactSummaryResponse:
        return ArtifactSummaryResponse(
            id=artifact.id,
            user_id=artifact.user_id,
            organization_id=artifact.organization_id,
            artifact_type=artifact.artifact_type,
            name=artifact.name,
            description=artifact.description,
            current_version_id=artifact.current_version_id,
            current_version_number=version_number,
            created_at=artifact.created_at,
            updated_at=artifact.updated_at,
        )

    async def _to_detail(self, artifact: GeneratedArtifact) -> ArtifactDetailResponse:
        from app.models.artifact_version import ArtifactVersion

        current_version = None
        version_number = None
        if artifact.current_version_id:
            version = await self.session.get(
                ArtifactVersion, artifact.current_version_id
            )
            if version:
                version_number = version.version_number
                current_version = ArtifactVersionResponse.model_validate(version)

        summary = self._to_summary(artifact, version_number=version_number)
        return ArtifactDetailResponse(
            **summary.model_dump(),
            current_version=current_version,
        )

    async def create(
        self,
        user: User,
        payload: ArtifactCreateRequest,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> ArtifactDetailResponse:
        _validate_content_size(payload.content)
        await self._validate_org_create(user, payload.organization_id)

        artifact = await self.artifacts.create_artifact(
            user_id=user.id,
            organization_id=payload.organization_id,
            artifact_type=payload.artifact_type,
            name=payload.name,
            description=payload.description,
            content=payload.content,
            metadata_json=payload.metadata,
        )
        content_hash = compute_content_hash(payload.content)
        version = await self.versions.create_version(
            artifact_id=artifact.id,
            version_number=1,
            content=payload.content,
            content_hash=content_hash,
            created_by=user.id,
            metadata_json=payload.metadata,
        )
        await self.artifacts.update_artifact(
            artifact,
            content=payload.content,
            current_version_id=version.id,
        )

        await self.audit.record_event(
            action="artifact.created",
            actor_user_id=user.id,
            organization_id=artifact.organization_id,
            resource_type="artifact",
            resource_id=artifact.id,
            request_context=audit_context,
            metadata={
                "artifact_type": artifact.artifact_type.value,
                "version_number": 1,
                "content_size_bytes": len(payload.content.encode("utf-8")),
            },
        )
        return await self._to_detail(artifact)

    async def list_artifacts(
        self,
        user: User,
        *,
        organization_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[ArtifactSummaryResponse], int]:
        if organization_id is not None:
            await self.org_auth.require_permission(
                organization_id, user.id, Permission.ARTIFACT_READ
            )
            items, total = await self.artifacts.list_artifacts(
                organization_id=organization_id, limit=limit, offset=offset
            )
        else:
            items, total = await self.artifacts.list_artifacts(
                user_id=user.id, limit=limit, offset=offset
            )

        summaries: list[ArtifactSummaryResponse] = []
        for artifact in items:
            version_number = None
            if artifact.current_version_id:
                from app.models.artifact_version import ArtifactVersion

                version = await self.session.get(
                    ArtifactVersion, artifact.current_version_id
                )
                if version:
                    version_number = version.version_number
            summaries.append(self._to_summary(artifact, version_number=version_number))
        return summaries, total

    async def get_artifact(
        self, user: User, artifact_id: UUID
    ) -> ArtifactDetailResponse:
        artifact = await self.artifacts.get_artifact(artifact_id)
        if artifact is None:
            raise NotFoundError("Artifact not found")
        await self._require_read(user, artifact)
        return await self._to_detail(artifact)

    async def update_artifact(
        self,
        user: User,
        artifact_id: UUID,
        payload: ArtifactUpdateRequest,
    ) -> ArtifactSummaryResponse:
        artifact = await self.artifacts.get_artifact(artifact_id)
        if artifact is None:
            raise NotFoundError("Artifact not found")
        await self._require_write(user, artifact)

        if payload.name is None and payload.description is None:
            raise ValidationAppError("No fields to update")

        updated = await self.artifacts.update_artifact(
            artifact,
            name=payload.name,
            description=payload.description,
        )
        version_number = None
        if updated.current_version_id:
            from app.models.artifact_version import ArtifactVersion

            version = await self.session.get(
                ArtifactVersion, updated.current_version_id
            )
            if version:
                version_number = version.version_number
        return self._to_summary(updated, version_number=version_number)

    async def delete_artifact(
        self,
        user: User,
        artifact_id: UUID,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> None:
        artifact = await self.artifacts.get_artifact(artifact_id)
        if artifact is None:
            raise NotFoundError("Artifact not found")
        await self._require_write(user, artifact)
        await self.artifacts.soft_delete(artifact)
        await self.audit.record_event(
            action="artifact.deleted",
            actor_user_id=user.id,
            organization_id=artifact.organization_id,
            resource_type="artifact",
            resource_id=artifact.id,
            request_context=audit_context,
            metadata={"artifact_type": artifact.artifact_type.value},
        )

    async def list_versions(
        self,
        user: User,
        artifact_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[ArtifactVersionResponse], int]:
        artifact = await self.artifacts.get_artifact(artifact_id)
        if artifact is None:
            raise NotFoundError("Artifact not found")
        await self._require_read(user, artifact)
        versions, total = await self.versions.list_versions(
            artifact_id, limit=limit, offset=offset
        )
        return [ArtifactVersionResponse.model_validate(v) for v in versions], total

    async def get_version(
        self, user: User, artifact_id: UUID, version_number: int
    ) -> ArtifactVersionResponse:
        artifact = await self.artifacts.get_artifact(artifact_id)
        if artifact is None:
            raise NotFoundError("Artifact not found")
        await self._require_read(user, artifact)
        version = await self.versions.get_by_number(artifact_id, version_number)
        if version is None:
            raise NotFoundError("Artifact version not found")
        return ArtifactVersionResponse.model_validate(version)

    async def add_version(
        self,
        user: User,
        artifact_id: UUID,
        payload: ArtifactVersionCreateRequest,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> ArtifactVersionResponse:
        _validate_content_size(payload.content)
        artifact = await self.artifacts.get_artifact_for_update(artifact_id)
        if artifact is None:
            raise NotFoundError("Artifact not found")
        await self._require_write(user, artifact)

        content_hash = compute_content_hash(payload.content)
        existing = await self.versions.get_by_hash(artifact_id, content_hash)
        if existing is not None:
            if artifact.current_version_id != existing.id:
                await self.artifacts.update_artifact(
                    artifact, current_version_id=existing.id, content=existing.content
                )
            return ArtifactVersionResponse.model_validate(existing)

        next_number = await self.versions.get_max_version_number(artifact_id) + 1
        version = await self.versions.create_version(
            artifact_id=artifact_id,
            version_number=next_number,
            content=payload.content,
            content_hash=content_hash,
            created_by=user.id,
            metadata_json=payload.metadata,
        )
        await self.artifacts.update_artifact(
            artifact, current_version_id=version.id, content=payload.content
        )

        await self.audit.record_event(
            action="artifact.version_created",
            actor_user_id=user.id,
            organization_id=artifact.organization_id,
            resource_type="artifact",
            resource_id=artifact.id,
            request_context=audit_context,
            metadata={
                "version_number": next_number,
                "content_size_bytes": len(payload.content.encode("utf-8")),
            },
        )
        return ArtifactVersionResponse.model_validate(version)

    async def restore_version(
        self,
        user: User,
        artifact_id: UUID,
        version_number: int,
        *,
        audit_context: AuditRequestContext | None = None,
    ) -> ArtifactRestoreResponse:
        artifact = await self.artifacts.get_artifact_for_update(artifact_id)
        if artifact is None:
            raise NotFoundError("Artifact not found")
        await self._require_write(user, artifact)

        source = await self.versions.get_by_number(artifact_id, version_number)
        if source is None:
            raise NotFoundError("Artifact version not found")

        metadata = {"restored_from_version": version_number}
        if source.metadata_json:
            metadata = {**source.metadata_json, **metadata}

        next_number = await self.versions.get_max_version_number(artifact_id) + 1
        content_hash = compute_content_hash(source.content)
        version = await self.versions.create_version(
            artifact_id=artifact_id,
            version_number=next_number,
            content=source.content,
            content_hash=content_hash,
            created_by=user.id,
            metadata_json=metadata,
        )
        await self.artifacts.update_artifact(
            artifact,
            current_version_id=version.id,
            content=source.content,
        )
        version_response = ArtifactVersionResponse.model_validate(version)

        await self.audit.record_event(
            action="artifact.version_created",
            actor_user_id=user.id,
            organization_id=artifact.organization_id,
            resource_type="artifact",
            resource_id=artifact.id,
            request_context=audit_context,
            metadata={
                "version_number": next_number,
                "restored_from_version": version_number,
            },
        )
        await self.audit.record_event(
            action="artifact.restored",
            actor_user_id=user.id,
            organization_id=artifact.organization_id,
            resource_type="artifact",
            resource_id=artifact.id,
            request_context=audit_context,
            metadata={
                "restored_from_version": version_number,
                "new_version_number": version_response.version_number,
            },
        )
        detail = await self._to_detail(artifact)
        return ArtifactRestoreResponse(
            artifact=detail,
            restored_from_version=version_number,
            new_version=version_response,
        )

    async def diff_versions(
        self,
        user: User,
        artifact_id: UUID,
        *,
        from_version: int,
        to_version: int,
    ) -> ArtifactDiffResponse:
        artifact = await self.artifacts.get_artifact(artifact_id)
        if artifact is None:
            raise NotFoundError("Artifact not found")
        await self._require_read(user, artifact)

        left = await self.versions.get_by_number(artifact_id, from_version)
        right = await self.versions.get_by_number(artifact_id, to_version)
        if left is None or right is None:
            raise NotFoundError("Artifact version not found")

        diff_lines = difflib.unified_diff(
            left.content.splitlines(keepends=True),
            right.content.splitlines(keepends=True),
            fromfile=f"v{from_version}",
            tofile=f"v{to_version}",
        )
        return ArtifactDiffResponse(
            artifact_id=artifact_id,
            from_version=from_version,
            to_version=to_version,
            diff="".join(diff_lines),
        )

    @staticmethod
    def map_config_type_to_artifact_type(config_type: str) -> ArtifactType:
        mapping = {
            "dockerfile": ArtifactType.DOCKERFILE,
            "kubernetes": ArtifactType.KUBERNETES,
            "terraform": ArtifactType.TERRAFORM,
            "github-actions": ArtifactType.GITHUB_ACTIONS,
            "gitlab-ci": ArtifactType.GITLAB_CI,
            "jenkins": ArtifactType.JENKINS,
        }
        return mapping.get(config_type, ArtifactType.OTHER)
