from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from app.core.config import get_settings
from app.core.security import hash_secure_token
from app.models.organization import OrgRole
from app.models.organization_invitation import InvitationStatus, OrganizationInvitation
from app.models.provider_config import (
    LLMOperation,
    ProviderConfig,
    ProviderRoutingPolicy,
)
from app.models.user import UserRole
from app.repositories.user_repository import UserRepository
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def _register_and_login(
    client: AsyncClient,
    *,
    username: str,
    email: str,
    password: str = "DevOpsPass123!",
) -> dict[str, str]:
    register = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    assert register.status_code == 200, register.text
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _promote_to_admin(db_session: AsyncSession, email: str) -> None:
    repo = UserRepository(db_session)
    user = await repo.get_by_email(email)
    assert user is not None
    user.role = UserRole.ADMIN
    await db_session.flush()


async def _seed_platform_providers(db_session: AsyncSession) -> None:
    for name, secret, model in (
        ("gemini", "GEMINI_API_KEY", "GEMINI_MODEL"),
        ("llama", "LLAMA_API_KEY", "LLAMA_MODEL"),
        ("mistral", "MISTRAL_API_KEY", "MISTRAL_MODEL"),
    ):
        db_session.add(
            ProviderConfig(
                organization_id=None,
                provider_name=name,
                enabled=True,
                default_model="test-model",
                timeout_seconds=60,
                max_retries=3,
                priority=10,
                max_output_tokens=4096,
                secret_env_key=secret,
                model_env_key=model,
            )
        )
    for operation in LLMOperation:
        db_session.add(
            ProviderRoutingPolicy(
                organization_id=None,
                operation=operation,
                primary_provider="gemini",
                fallback_providers=["llama", "mistral"],
            )
        )
    await db_session.flush()


async def _create_org(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    slug: str,
) -> dict:
    response = await client.post(
        "/api/v1/organizations",
        json={"name": "Test Org", "slug": slug},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


@pytest.mark.asyncio
async def test_admin_provider_configs_and_health(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _seed_platform_providers(db_session)
    user_headers = await _register_and_login(
        client, username="provuser", email="provuser@example.com"
    )

    forbidden = await client.get(
        "/api/v1/admin/providers/configs", headers=user_headers
    )
    assert forbidden.status_code == 403

    admin_headers = await _register_and_login(
        client, username="provadmin", email="provadmin@example.com"
    )
    await _promote_to_admin(db_session, "provadmin@example.com")

    listed = await client.get("/api/v1/admin/providers/configs", headers=admin_headers)
    assert listed.status_code == 200
    assert len(listed.json()["data"]) >= 3

    patched = await client.patch(
        "/api/v1/admin/providers/configs/gemini",
        json={"enabled": False},
        headers=admin_headers,
    )
    assert patched.status_code == 200
    assert patched.json()["data"]["enabled"] is False

    health = await client.get("/api/v1/admin/providers/health", headers=admin_headers)
    assert health.status_code == 200
    names = {item["provider_name"] for item in health.json()["data"]}
    assert "gemini" in names


@pytest.mark.asyncio
async def test_org_owner_provider_allowlist(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _seed_platform_providers(db_session)
    owner_headers = await _register_and_login(
        client, username="orgprov", email="orgprov@example.com"
    )
    org = await _create_org(client, owner_headers, slug="org-prov-team")

    patched = await client.patch(
        f"/api/v1/organizations/{org['id']}/providers/configs/mistral",
        json={"enabled": False},
        headers=owner_headers,
    )
    assert patched.status_code == 200
    assert patched.json()["data"]["organization_id"] == org["id"]


@pytest.mark.asyncio
async def test_usage_and_quota_enforcement(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    headers = await _register_and_login(
        client, username="usageuser", email="usageuser@example.com"
    )
    org = await _create_org(client, headers, slug="usage-team")

    usage_me = await client.get("/api/v1/usage/me", headers=headers)
    assert usage_me.status_code == 200
    assert usage_me.json()["data"]["daily"]["requests"] >= 0

    set_quota = await client.patch(
        f"/api/v1/organizations/{org['id']}/quotas",
        json={
            "daily_request_limit": 0,
            "enforce_quotas": True,
        },
        headers=headers,
    )
    assert set_quota.status_code == 200

    chat = await client.post(
        "/api/v1/chat",
        json={
            "message": "How do I debug CrashLoopBackOff?",
            "organization_id": org["id"],
        },
        headers=headers,
    )
    assert chat.status_code == 429
    assert chat.json()["error"]["code"] == "QUOTA_EXCEEDED"


@pytest.mark.asyncio
async def test_artifact_tags_favorites_archive(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    created = await client.post(
        "/api/v1/artifacts",
        json={
            "name": "Tagged Dockerfile",
            "artifact_type": "dockerfile",
            "content": 'FROM alpine:3.20\nCMD ["sh"]',
        },
        headers=auth_headers,
    )
    assert created.status_code == 200
    artifact_id = created.json()["data"]["id"]

    tagged = await client.post(
        f"/api/v1/artifacts/{artifact_id}/tags",
        json={"name": "production"},
        headers=auth_headers,
    )
    assert tagged.status_code == 200
    assert tagged.json()["data"][0]["name"] == "production"

    favorited = await client.post(
        f"/api/v1/artifacts/{artifact_id}/favorite",
        headers=auth_headers,
    )
    assert favorited.status_code == 200

    listed = await client.get(
        "/api/v1/artifacts",
        params={"favorites_only": True, "tags": ["production"]},
        headers=auth_headers,
    )
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 1

    archived = await client.post(
        f"/api/v1/artifacts/{artifact_id}/archive",
        headers=auth_headers,
    )
    assert archived.status_code == 200
    assert archived.json()["data"]["archived_at"] is not None

    hidden = await client.get("/api/v1/artifacts", headers=auth_headers)
    assert hidden.json()["data"]["total"] == 0

    visible = await client.get(
        "/api/v1/artifacts",
        params={"include_archived": True},
        headers=auth_headers,
    )
    assert visible.json()["data"]["total"] == 1


@pytest.mark.asyncio
async def test_onboarding_get_and_patch(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    initial = await client.get("/api/v1/users/me/onboarding", headers=auth_headers)
    assert initial.status_code == 200
    assert initial.json()["data"]["welcome_dismissed"] is False

    patched = await client.patch(
        "/api/v1/users/me/onboarding",
        json={"welcome_dismissed": True, "first_chat_completed": True},
        headers=auth_headers,
    )
    assert patched.status_code == 200
    data = patched.json()["data"]
    assert data["welcome_dismissed"] is True
    assert data["first_chat_completed"] is True


@pytest.mark.asyncio
async def test_admin_routing_patch(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _seed_platform_providers(db_session)
    admin_headers = await _register_and_login(
        client, username="routingadmin", email="routingadmin@example.com"
    )
    await _promote_to_admin(db_session, "routingadmin@example.com")

    patched = await client.patch(
        "/api/v1/admin/providers/routing/chat",
        json={
            "primary_provider": "llama",
            "fallback_providers": ["mistral", "gemini"],
        },
        headers=admin_headers,
    )
    assert patched.status_code == 200, patched.text
    data = patched.json()["data"]
    assert data["operation"] == "chat"
    assert data["primary_provider"] == "llama"
    assert data["fallback_providers"] == ["mistral", "gemini"]


@pytest.mark.asyncio
async def test_personal_quota_enforcement(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("USAGE_ENFORCE_PERSONAL_QUOTAS", "true")
    monkeypatch.setenv("USAGE_DEFAULT_DAILY_TOKEN_LIMIT", "0")
    get_settings.cache_clear()
    try:
        headers = await _register_and_login(
            client, username="personalquota", email="personalquota@example.com"
        )
        chat = await client.post(
            "/api/v1/chat",
            json={"message": "Why is my pod CrashLoopBackOff?"},
            headers=headers,
        )
        assert chat.status_code == 429
        assert chat.json()["error"]["code"] == "QUOTA_EXCEEDED"
    finally:
        monkeypatch.delenv("USAGE_ENFORCE_PERSONAL_QUOTAS", raising=False)
        monkeypatch.delenv("USAGE_DEFAULT_DAILY_TOKEN_LIMIT", raising=False)
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_email_verification_required_blocks_login(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    email_outbox: list,
) -> None:
    monkeypatch.setenv("EMAIL_VERIFICATION_REQUIRED", "true")
    get_settings.cache_clear()
    try:
        register = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "needverify@example.com",
                "username": "needverify",
                "password": "DevOpsPass123!",
            },
        )
        assert register.status_code == 200, register.text
        assert any("verify" in mail.subject.lower() for mail in email_outbox)

        login = await client.post(
            "/api/v1/auth/login",
            data={"username": "needverify", "password": "DevOpsPass123!"},
        )
        assert login.status_code == 401
    finally:
        monkeypatch.delenv("EMAIL_VERIFICATION_REQUIRED", raising=False)
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_invitation_expired_persists_expired_status(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    owner_headers = await _register_and_login(
        client, username="expireowner", email="expireowner@example.com"
    )
    invitee_headers = await _register_and_login(
        client, username="expireinvitee", email="expireinvitee@example.com"
    )
    org = await _create_org(client, owner_headers, slug="expire-invite-org")

    owner = await UserRepository(db_session).get_by_email("expireowner@example.com")
    assert owner is not None
    invitation = OrganizationInvitation(
        organization_id=UUID(org["id"]),
        email="expireinvitee@example.com",
        role=OrgRole.MEMBER,
        token_hash=hash_secure_token("expired-invite-token"),
        invited_by_user_id=owner.id,
        expires_at=datetime.now(UTC) - timedelta(hours=1),
        status=InvitationStatus.PENDING,
    )
    db_session.add(invitation)
    await db_session.flush()
    await db_session.commit()
    invitation_id = invitation.id

    accept = await client.post(
        "/api/v1/invitations/accept",
        json={"token": "expired-invite-token"},
        headers=invitee_headers,
    )
    assert accept.status_code == 404

    db_session.expire_all()
    result = await db_session.execute(
        select(OrganizationInvitation).where(
            OrganizationInvitation.id == invitation_id
        )
    )
    stored = result.scalar_one()
    assert stored.status == InvitationStatus.EXPIRED


@pytest.mark.asyncio
async def test_dockerfile_generate_via_gateway(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await client.post(
        "/api/v1/generate/dockerfile",
        headers=auth_headers,
        json={
            "language": "python",
            "framework": "fastapi",
            "python_version": "3.12",
            "port": 8000,
            "use_multistage": True,
            "run_as_non_root": True,
        },
    )
    assert response.status_code == 200, response.text
    assert "FROM python" in response.json()["data"]["content"]
