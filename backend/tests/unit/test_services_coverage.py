from __future__ import annotations

from uuid import uuid4

import pytest
from app.core.exceptions import ForbiddenError, ValidationAppError
from app.models.background_task import TaskStatus
from app.models.organization import Organization, OrganizationMember, OrgRole
from app.models.user import User, UserRole
from app.schemas.organization import OrganizationUpdate
from app.services.artifact_service import (
    ArtifactService,
    compute_content_hash,
)
from app.services.organization_service import OrganizationService, normalize_slug
from app.services.task_service import TASK_TYPE_LOG_ANALYSIS, TaskService


def test_normalize_slug_and_invalid() -> None:
    assert normalize_slug("My Team!!") == "my-team"
    with pytest.raises(ValidationAppError):
        normalize_slug("!!!")


def test_compute_content_hash_and_config_type_mapping() -> None:
    content = "hello"
    assert compute_content_hash(content) == compute_content_hash(content)
    artifact_type = ArtifactService.map_config_type_to_artifact_type("dockerfile")
    assert artifact_type.value == "dockerfile"
    other = ArtifactService.map_config_type_to_artifact_type("unknown-type")
    assert other.value == "other"


@pytest.mark.asyncio
async def test_organization_service_update_slug_requires_owner(db_session) -> None:
    owner = User(
        id=uuid4(),
        email="org-svc-owner@example.com",
        username="orgsvcowner",
        hashed_password="hashed",
        role=UserRole.USER,
        is_active=True,
    )
    admin = User(
        id=uuid4(),
        email="org-svc-admin@example.com",
        username="orgsvcadmin",
        hashed_password="hashed",
        role=UserRole.USER,
        is_active=True,
    )
    org = Organization(
        id=uuid4(),
        name="Service Org",
        slug="service-org",
        created_by=owner.id,
    )
    db_session.add_all(
        [
            owner,
            admin,
            org,
            OrganizationMember(
                id=uuid4(),
                organization_id=org.id,
                user_id=owner.id,
                role=OrgRole.OWNER,
            ),
            OrganizationMember(
                id=uuid4(),
                organization_id=org.id,
                user_id=admin.id,
                role=OrgRole.ADMIN,
            ),
        ]
    )
    await db_session.flush()

    service = OrganizationService(db_session)
    with pytest.raises(ForbiddenError, match="Only owners may change"):
        await service.update(
            admin,
            org.id,
            OrganizationUpdate(slug="new-slug"),
        )


@pytest.mark.asyncio
async def test_task_service_org_scoped_and_mark_failed(db_session) -> None:
    user = User(
        id=uuid4(),
        email="task-org-user@example.com",
        username="taskorguser",
        hashed_password="hashed",
        role=UserRole.USER,
        is_active=True,
    )
    org = Organization(
        id=uuid4(),
        name="Task Org",
        slug=f"task-org-{uuid4().hex[:8]}",
        created_by=user.id,
    )
    db_session.add_all(
        [
            user,
            org,
            OrganizationMember(
                id=uuid4(),
                organization_id=org.id,
                user_id=user.id,
                role=OrgRole.OWNER,
            ),
        ]
    )
    await db_session.flush()

    service = TaskService(db_session)
    task = await service.create_task(
        user,
        task_type=TASK_TYPE_LOG_ANALYSIS,
        organization_id=org.id,
    )
    await service.mark_failed(
        task.id,
        error_code="LLM_ERROR",
        error_message="provider unavailable",
    )
    detail = await service.get_task(user, task.id)
    assert detail.status == TaskStatus.FAILED
    assert detail.error_code == "LLM_ERROR"

    items, total = await service.list_tasks(user, organization_id=org.id)
    assert total == 1
    assert items[0].id == task.id

    await service.validate_organization_scope(user, org.id)
