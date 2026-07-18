from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError
from app.models.generated_artifact import ArtifactType
from app.models.user import User
from app.schemas.artifacts import ArtifactCreateRequest
from app.schemas.generators import GeneratorSaveOptions
from app.schemas.policies import PolicyFinding
from app.services.artifact_service import ArtifactService
from app.services.audit_service import AuditRequestContext
from app.services.policy_engine import has_critical_findings
from app.services.policy_service import PolicyService
from app.services.rbac import OrganizationAuthService, Permission


def _config_type_for_artifact(artifact_type: ArtifactType) -> str:
    mapping = {
        ArtifactType.DOCKERFILE: "dockerfile",
        ArtifactType.KUBERNETES: "kubernetes",
        ArtifactType.GITHUB_ACTIONS: "github-actions",
        ArtifactType.GITLAB_CI: "gitlab-ci",
        ArtifactType.JENKINS: "jenkins",
        ArtifactType.TERRAFORM: "terraform",
        ArtifactType.SHELL_COMMAND: "shell-command",
        ArtifactType.COMMAND: "general",
        ArtifactType.PIPELINE: "github-actions",
    }
    return mapping.get(artifact_type, "general")


async def apply_generator_policies_and_save(
    session: AsyncSession,
    user: User,
    payload: GeneratorSaveOptions,
    *,
    artifact_type: ArtifactType,
    content: str,
    default_name: str,
    metadata: dict[str, Any] | None = None,
    audit_context: AuditRequestContext | None = None,
) -> tuple[list[PolicyFinding], UUID | None]:
    policy_findings: list[PolicyFinding] = []

    if (
        payload.validate_policies
        and payload.organization_id
        and payload.policy_pack_ids
    ):
        await OrganizationAuthService(session).require_permission(
            payload.organization_id, user.id, Permission.POLICY_READ
        )
        policy_findings = await PolicyService(session).evaluate_packs(
            organization_id=payload.organization_id,
            policy_pack_ids=payload.policy_pack_ids,
            config_type=_config_type_for_artifact(artifact_type),
            content=content,
        )

    saved_artifact_id: UUID | None = None
    if payload.save_artifact:
        settings = get_settings()
        if (
            settings.block_artifact_save_on_critical_policy_failure
            and has_critical_findings(policy_findings)
        ):
            raise ValidationAppError(
                "Artifact save blocked due to critical policy failures"
            )

        artifact = await ArtifactService(session).create(
            user,
            ArtifactCreateRequest(
                name=payload.artifact_name or default_name,
                description=payload.artifact_description,
                artifact_type=artifact_type,
                content=content,
                metadata=metadata,
                organization_id=payload.organization_id,
            ),
            audit_context=audit_context,
        )
        saved_artifact_id = artifact.id

    return policy_findings, saved_artifact_id
