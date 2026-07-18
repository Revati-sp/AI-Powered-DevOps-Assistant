from __future__ import annotations

from uuid import uuid4

import pytest
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationAppError,
)
from app.models.generated_artifact import ArtifactType
from app.models.organization import Organization, OrganizationMember, OrgRole
from app.models.user import User, UserRole
from app.schemas.artifacts import (
    ArtifactCreateRequest,
    ArtifactUpdateRequest,
    ArtifactVersionCreateRequest,
)
from app.schemas.organization import (
    AddMemberRequest,
    OrganizationCreate,
    OrganizationUpdate,
    UpdateMemberRequest,
)
from app.schemas.pagination import PageParams
from app.schemas.policies import (
    PolicyPackCreateRequest,
    PolicyPackUpdateRequest,
    PolicyRuleCreateRequest,
    PolicyRuleUpdateRequest,
)
from app.services.artifact_service import ArtifactService
from app.services.organization_service import OrganizationService
from app.services.policy_service import PolicyService
from app.services.task_service import TASK_TYPE_LOG_ANALYSIS, TaskService


async def _seed_owner_org(db_session) -> tuple[User, Organization]:
    owner = User(
        id=uuid4(),
        email=f"svc-owner-{uuid4().hex[:6]}@example.com",
        username=f"svcowner{uuid4().hex[:6]}",
        hashed_password="hashed",
        role=UserRole.USER,
        is_active=True,
    )
    org = Organization(
        id=uuid4(),
        name="Service Test Org",
        slug=f"svc-org-{uuid4().hex[:8]}",
        created_by=owner.id,
    )
    db_session.add_all(
        [
            owner,
            org,
            OrganizationMember(
                id=uuid4(),
                organization_id=org.id,
                user_id=owner.id,
                role=OrgRole.OWNER,
            ),
        ]
    )
    await db_session.flush()
    return owner, org


@pytest.mark.asyncio
async def test_organization_service_create(db_session) -> None:
    owner, _ = await _seed_owner_org(db_session)
    service = OrganizationService(db_session)

    created = await service.create(
        owner,
        OrganizationCreate(name="New Team", slug="new-team"),
    )
    assert created.slug == "new-team"


@pytest.mark.asyncio
async def test_organization_service_full_lifecycle(db_session) -> None:
    owner, org = await _seed_owner_org(db_session)
    invitee = User(
        id=uuid4(),
        email="invitee@example.com",
        username="invitee",
        hashed_password="hashed",
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add(invitee)
    await db_session.flush()

    service = OrganizationService(db_session)
    listed = await service.list_for_user(owner, PageParams())
    assert listed.total == 1

    detail = await service.get(owner, org.id)
    assert detail.slug == org.slug

    updated = await service.update(
        owner,
        org.id,
        OrganizationUpdate(name="Renamed Org", slug="renamed-org"),
    )
    assert updated.name == "Renamed Org"

    member = await service.add_member(
        owner,
        org.id,
        AddMemberRequest(email=invitee.email, role=OrgRole.MEMBER),
    )
    assert member.role == OrgRole.MEMBER

    members = await service.list_members(
        owner,
        org.id,
        PageParams(),
    )
    assert members.total == 2

    changed = await service.update_member(
        owner,
        org.id,
        invitee.id,
        UpdateMemberRequest(role=OrgRole.ADMIN),
    )
    assert changed.role == OrgRole.ADMIN

    await service.remove_member(owner, org.id, invitee.id)
    await service.delete(owner, org.id)

    with pytest.raises(NotFoundError):
        await service.get(owner, org.id)


@pytest.mark.asyncio
async def test_organization_service_validation_errors(db_session) -> None:
    owner, org = await _seed_owner_org(db_session)
    service = OrganizationService(db_session)

    with pytest.raises(ValidationAppError):
        await service.update(owner, org.id, OrganizationUpdate())

    with pytest.raises(NotFoundError):
        await service.add_member(
            owner,
            org.id,
            AddMemberRequest(email="missing@example.com", role=OrgRole.MEMBER),
        )

    with pytest.raises(ConflictError):
        await service.add_member(
            owner,
            org.id,
            AddMemberRequest(email=owner.email, role=OrgRole.MEMBER),
        )


@pytest.mark.asyncio
async def test_artifact_service_personal_lifecycle(db_session) -> None:
    user, _ = await _seed_owner_org(db_session)
    service = ArtifactService(db_session)

    created = await service.create(
        user,
        ArtifactCreateRequest(
            name="Personal",
            artifact_type=ArtifactType.DOCKERFILE,
            content="FROM alpine:3.20\nUSER app\n",
        ),
    )
    artifact_id = created.id

    fetched = await service.get_artifact(user, artifact_id)
    assert fetched.current_version_number == 1

    items, total = await service.list_artifacts(
        user, organization_id=None, limit=10, offset=0
    )
    assert total == 1

    version = await service.add_version(
        user,
        artifact_id,
        ArtifactVersionCreateRequest(content="FROM alpine:3.21\nUSER app\n"),
    )
    assert version.version_number == 2

    versions, version_total = await service.list_versions(
        user, artifact_id, limit=10, offset=0
    )
    assert version_total == 2

    got_v1 = await service.get_version(user, artifact_id, 1)
    assert "3.20" in got_v1.content

    diff = await service.diff_versions(user, artifact_id, from_version=1, to_version=2)
    assert diff.diff

    restored = await service.restore_version(user, artifact_id, 1)
    assert restored.new_version.version_number == 3

    renamed = await service.update_artifact(
        user,
        artifact_id,
        ArtifactUpdateRequest(name="Renamed Personal", description="desc"),
    )
    assert renamed.name == "Renamed Personal"

    await service.delete_artifact(user, artifact_id)

    with pytest.raises(NotFoundError):
        await service.get_artifact(user, artifact_id)


@pytest.mark.asyncio
async def test_artifact_service_org_scoped_and_access_control(db_session) -> None:
    owner, org = await _seed_owner_org(db_session)
    outsider = User(
        id=uuid4(),
        email="art-outsider@example.com",
        username="artoutsider",
        hashed_password="hashed",
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add(outsider)
    await db_session.flush()

    service = ArtifactService(db_session)
    created = await service.create(
        owner,
        ArtifactCreateRequest(
            name="Org Artifact",
            artifact_type=ArtifactType.KUBERNETES,
            content="kind: Deployment\n",
            organization_id=org.id,
        ),
    )

    items, total = await service.list_artifacts(
        owner, organization_id=org.id, limit=10, offset=0
    )
    assert total == 1
    assert items[0].id == created.id

    with pytest.raises(NotFoundError):
        await service.get_artifact(outsider, created.id)


@pytest.mark.asyncio
async def test_policy_service_full_lifecycle(db_session) -> None:
    owner, org = await _seed_owner_org(db_session)
    service = PolicyService(db_session)

    pack = await service.create_pack(
        owner,
        org.id,
        PolicyPackCreateRequest(
            name="Baseline",
            description="Checks",
            is_active=True,
        ),
    )

    packs, total = await service.list_packs(owner, org.id, limit=10, offset=0)
    assert total == 1
    assert packs[0].id == pack.id

    rule = await service.add_rule(
        owner,
        org.id,
        pack.id,
        PolicyRuleCreateRequest(
            rule_key="forbid_latest_image_tag",
            name="No latest tag",
            description="Disallow latest tags",
            resource_type="kubernetes",
            severity="high",
            configuration={},
        ),
    )

    detail = await service.get_pack(owner, org.id, pack.id)
    assert len(detail.rules) == 1

    updated_rule = await service.update_rule(
        owner,
        org.id,
        pack.id,
        rule.id,
        PolicyRuleUpdateRequest(severity="critical"),
    )
    assert updated_rule.severity == "critical"

    updated_pack = await service.update_pack(
        owner,
        org.id,
        pack.id,
        PolicyPackUpdateRequest(name="Baseline v2"),
    )
    assert updated_pack.name == "Baseline v2"

    findings = await service.evaluate_packs(
        organization_id=org.id,
        policy_pack_ids=[pack.id],
        config_type="kubernetes",
        content="image: nginx:latest\n",
    )
    assert findings

    await service.delete_rule(owner, org.id, pack.id, rule.id)
    await service.delete_pack(owner, org.id, pack.id)

    with pytest.raises(NotFoundError):
        await service.get_pack(owner, org.id, pack.id)


@pytest.mark.asyncio
async def test_policy_service_invalid_pack_ids(db_session) -> None:
    _, org = await _seed_owner_org(db_session)
    service = PolicyService(db_session)

    with pytest.raises(ValidationAppError):
        await service.evaluate_packs(
            organization_id=org.id,
            policy_pack_ids=[uuid4()],
            config_type="kubernetes",
            content="image: nginx:1.2.3\n",
        )


@pytest.mark.asyncio
async def test_task_service_cancel_and_resolve(db_session) -> None:
    user, org = await _seed_owner_org(db_session)
    service = TaskService(db_session)

    task = await service.create_task(
        user,
        task_type=TASK_TYPE_LOG_ANALYSIS,
        organization_id=org.id,
        idempotency_key="idem-1",
    )
    same = await service.create_task(
        user,
        task_type=TASK_TYPE_LOG_ANALYSIS,
        organization_id=org.id,
        idempotency_key="idem-1",
    )
    assert same.id == task.id

    await service.mark_running(task.id, progress=50)
    cancelled = await service.cancel_task(user, task.id)
    assert cancelled.status.value == "cancelled"

    detail = await service.resolve_task_identifier(user, str(task.id))
    assert detail.id == task.id

    viewer = User(
        id=uuid4(),
        email="task-viewer@example.com",
        username="taskviewer",
        hashed_password="hashed",
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add(viewer)
    db_session.add(
        OrganizationMember(
            id=uuid4(),
            organization_id=org.id,
            user_id=viewer.id,
            role=OrgRole.VIEWER,
        )
    )
    await db_session.flush()

    task2 = await service.create_task(
        user,
        task_type=TASK_TYPE_LOG_ANALYSIS,
        organization_id=org.id,
    )
    with pytest.raises(ForbiddenError):
        await service.cancel_task(viewer, task2.id)
