from __future__ import annotations

from uuid import uuid4

import pytest
from app.models.organization import Organization, OrganizationMember, OrgRole
from app.models.user import User, UserRole
from app.services.audit_service import AuditRequestContext, AuditService


async def _seed_org(db_session) -> tuple[Organization, User]:
    user = User(
        id=uuid4(),
        email="audit-user@example.com",
        username="audituser",
        hashed_password="hashed",
        role=UserRole.USER,
        is_active=True,
    )
    org = Organization(
        id=uuid4(),
        name="Audit Org",
        slug=f"audit-org-{uuid4().hex[:8]}",
        created_by=user.id,
    )
    membership = OrganizationMember(
        id=uuid4(),
        organization_id=org.id,
        user_id=user.id,
        role=OrgRole.OWNER,
    )
    db_session.add_all([user, org, membership])
    await db_session.flush()
    return org, user


@pytest.mark.asyncio
async def test_record_event_persists_and_lists(db_session) -> None:
    org, user = await _seed_org(db_session)
    service = AuditService(db_session)
    ctx = AuditRequestContext(
        request_id="req-123",
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    event = await service.record_event(
        action="organization.updated",
        actor_user_id=user.id,
        organization_id=org.id,
        resource_type="organization",
        resource_id=org.id,
        request_context=ctx,
        metadata={"password": "secret-value", "note": "safe"},
        fail_on_error=True,
    )
    assert event is not None
    assert event.id is not None
    assert event.action == "organization.updated"
    assert event.request_id == "req-123"

    events, total = await service.list_events(
        org.id,
        limit=10,
        offset=0,
        action="organization.updated",
        actor_user_id=user.id,
        resource_type="organization",
        resource_id=org.id,
    )
    assert total == 1
    assert events[0].metadata_json["password"] == "[REDACTED]"
    assert events[0].metadata_json["note"] == "safe"


@pytest.mark.asyncio
async def test_record_event_fail_on_error_false_returns_none(
    db_session, monkeypatch
) -> None:
    org, user = await _seed_org(db_session)
    service = AuditService(db_session)

    async def _fail_flush(*args, **kwargs):
        raise RuntimeError("db flush failed")

    monkeypatch.setattr(db_session, "flush", _fail_flush)

    result = await service.record_event(
        action="organization.updated",
        actor_user_id=user.id,
        organization_id=org.id,
        resource_type="organization",
        resource_id=org.id,
        fail_on_error=False,
    )
    assert result is None
