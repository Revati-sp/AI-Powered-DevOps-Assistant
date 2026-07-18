#!/usr/bin/env python3
"""Seed local/dev databases with deterministic dummy data for UI demos.

Idempotent: skips when demo.owner@example.com already exists.
See docs/dummy-data.md for accounts and sample content.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Allow `python scripts/seed_dummy_data.py` from backend/
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models import (  # noqa: F401 — register mappers
    Analysis,
    AnalysisStatus,
    AnalysisType,
    ArtifactType,
    ArtifactVersion,
    AuditEvent,
    BackgroundTask,
    Conversation,
    GeneratedArtifact,
    Message,
    MessageRole,
    Organization,
    OrganizationMember,
    OrganizationQuota,
    OrgRole,
    PolicyPack,
    PolicyRule,
    TaskStatus,
    UsageEvent,
    User,
    UserOnboarding,
    UserRole,
)

DEMO_PASSWORD = "DummyPass123!"
OWNER_EMAIL = "demo.owner@example.com"


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


async def _user_exists(session, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def seed(*, force: bool = False) -> None:
    async with AsyncSessionLocal() as session:
        existing = await _user_exists(session, OWNER_EMAIL)
        if existing and not force:
            print(
                f"Dummy data already present ({OWNER_EMAIL}). "
                "Re-run with --force to insert another copy (not recommended)."
            )
            return

        now = datetime.now(UTC)
        password_hash = hash_password(DEMO_PASSWORD)

        users_spec = [
            {
                "email": OWNER_EMAIL,
                "username": "demo_owner",
                "display_name": "Dana Owner",
                "job_title": "Platform Lead",
                "role": UserRole.USER,
                "onboarding_complete": True,
            },
            {
                "email": "demo.admin@example.com",
                "username": "demo_admin",
                "display_name": "Alex Admin",
                "job_title": "DevOps Admin",
                "role": UserRole.USER,
                "onboarding_complete": True,
            },
            {
                "email": "demo.member@example.com",
                "username": "demo_member",
                "display_name": "Morgan Member",
                "job_title": "SRE",
                "role": UserRole.USER,
                "onboarding_complete": False,
            },
            {
                "email": "demo.viewer@example.com",
                "username": "demo_viewer",
                "display_name": "Riley Viewer",
                "job_title": "Observer",
                "role": UserRole.USER,
                "onboarding_complete": False,
            },
            {
                "email": "demo.personal@example.com",
                "username": "demo_personal",
                "display_name": "Pat Personal",
                "job_title": "Engineer",
                "role": UserRole.USER,
                "onboarding_complete": False,
            },
        ]

        users: dict[str, User] = {}
        for spec in users_spec:
            if force:
                prior = await _user_exists(session, spec["email"])
                if prior:
                    # Force mode still skips existing emails to avoid unique violations.
                    users[spec["email"]] = prior
                    continue

            user = User(
                id=uuid.uuid4(),
                email=spec["email"],
                username=spec["username"],
                hashed_password=password_hash,
                role=spec["role"],
                is_active=True,
                email_verified_at=now,
                display_name=spec["display_name"],
                timezone="UTC",
                job_title=spec["job_title"],
            )
            session.add(user)
            users[spec["email"]] = user

            complete = bool(spec["onboarding_complete"])
            session.add(
                UserOnboarding(
                    user_id=user.id,
                    welcome_dismissed=complete,
                    profile_completed=complete,
                    first_chat_completed=complete,
                    first_artifact_created=complete,
                    organization_created=complete
                    and spec["email"] != "demo.personal@example.com",
                    invite_team_completed=complete
                    and spec["email"] == OWNER_EMAIL,
                    tour_completed=complete,
                    onboarding_completed=complete,
                )
            )

        await session.flush()

        owner = users[OWNER_EMAIL]
        admin = users["demo.admin@example.com"]
        member = users["demo.member@example.com"]
        viewer = users["demo.viewer@example.com"]

        org = Organization(
            id=uuid.uuid4(),
            name="Acme Platform",
            slug="acme-platform",
            created_by=owner.id,
        )
        session.add(org)
        await session.flush()

        for user, role in (
            (owner, OrgRole.OWNER),
            (admin, OrgRole.ADMIN),
            (member, OrgRole.MEMBER),
            (viewer, OrgRole.VIEWER),
        ):
            session.add(
                OrganizationMember(
                    organization_id=org.id,
                    user_id=user.id,
                    role=role,
                )
            )

        session.add(
            OrganizationQuota(
                organization_id=org.id,
                daily_token_limit=100_000,
                daily_request_limit=500,
                monthly_token_limit=2_000_000,
                monthly_request_limit=10_000,
                enforce_quotas=False,
            )
        )

        pack = PolicyPack(
            id=uuid.uuid4(),
            organization_id=org.id,
            name="Baseline Security Pack",
            description="Starter rules for Dockerfiles and CI pipelines.",
            is_active=True,
            version=1,
            created_by=owner.id,
        )
        session.add(pack)
        await session.flush()
        session.add_all(
            [
                PolicyRule(
                    policy_pack_id=pack.id,
                    rule_key="dockerfile_no_latest",
                    name="Disallow :latest tags",
                    description="Container images must use pinned digests or versions.",
                    resource_type="dockerfile",
                    severity="high",
                    configuration_json={"forbid_tag": "latest"},
                    remediation="Pin image tags or digests explicitly.",
                    is_enabled=True,
                ),
                PolicyRule(
                    policy_pack_id=pack.id,
                    rule_key="ci_no_curl_pipe_bash",
                    name="No curl|bash in CI",
                    description="Piping remote scripts into a shell is risky.",
                    resource_type="github-actions",
                    severity="critical",
                    configuration_json={},
                    remediation="Vendor install scripts or use package managers.",
                    is_enabled=True,
                ),
            ]
        )

        dockerfile = """FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
USER nobody
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        artifact = GeneratedArtifact(
            id=uuid.uuid4(),
            user_id=owner.id,
            organization_id=org.id,
            artifact_type=ArtifactType.DOCKERFILE,
            name="api-service.Dockerfile",
            description="Sample production Dockerfile for the API service.",
            content=dockerfile,
            metadata_json={"source": "dummy-seed", "language": "dockerfile"},
        )
        session.add(artifact)
        await session.flush()
        version = ArtifactVersion(
            id=uuid.uuid4(),
            artifact_id=artifact.id,
            version_number=1,
            content=dockerfile,
            content_hash=_hash(dockerfile),
            metadata_json={"note": "Initial seeded version"},
            created_by=owner.id,
        )
        session.add(version)
        await session.flush()
        artifact.current_version_id = version.id

        conversation = Conversation(
            id=uuid.uuid4(),
            user_id=owner.id,
            organization_id=org.id,
            title="CrashLoopBackOff triage",
            provider="gemini",
        )
        session.add(conversation)
        await session.flush()
        session.add_all(
            [
                Message(
                    conversation_id=conversation.id,
                    role=MessageRole.USER,
                    content="Pod api-0 is CrashLoopBackOff after the last deploy. What should I check first?",
                    created_at=now - timedelta(hours=2),
                ),
                Message(
                    conversation_id=conversation.id,
                    role=MessageRole.ASSISTANT,
                    content=(
                        "Start with `kubectl describe pod api-0` and recent container logs. "
                        "Look for OOMKilled, missing ConfigMaps, or failing readiness probes."
                    ),
                    created_at=now - timedelta(hours=2) + timedelta(minutes=1),
                ),
            ]
        )

        session.add(
            Analysis(
                user_id=owner.id,
                organization_id=org.id,
                analysis_type=AnalysisType.LOG,
                input_preview="Error: connect ECONNREFUSED 10.0.0.12:5432\n...",
                status=AnalysisStatus.COMPLETED,
                result_json={
                    "summary": "Application cannot reach Postgres on 10.0.0.12:5432.",
                    "findings": [
                        {
                            "severity": "high",
                            "title": "Database connection refused",
                            "detail": "Verify service DNS, NetworkPolicy, and DB readiness.",
                        }
                    ],
                },
                created_at=now - timedelta(days=1),
            )
        )
        session.add(
            Analysis(
                user_id=owner.id,
                organization_id=org.id,
                analysis_type=AnalysisType.REVIEW,
                input_preview="FROM python:3.12\nUSER root\n...",
                status=AnalysisStatus.COMPLETED,
                result_json={
                    "summary": "Dockerfile review completed with policy findings.",
                    "findings": [
                        {
                            "severity": "critical",
                            "title": "Running as root",
                            "detail": "Add a non-root USER instruction.",
                        },
                        {
                            "severity": "high",
                            "title": "Unpinned base image",
                            "detail": "Pin python:3.12 to a digest.",
                        },
                        {
                            "severity": "medium",
                            "title": "Missing HEALTHCHECK",
                            "detail": "Consider adding a container health check.",
                        },
                    ],
                },
                created_at=now - timedelta(hours=5),
            )
        )

        session.add_all(
            [
                BackgroundTask(
                    user_id=owner.id,
                    organization_id=org.id,
                    task_type="analyze_logs",
                    status=TaskStatus.SUCCEEDED,
                    progress=100,
                    result_json={"summary": "Log analysis finished"},
                    created_at=now - timedelta(hours=3),
                    started_at=now - timedelta(hours=3),
                    completed_at=now - timedelta(hours=3) + timedelta(minutes=2),
                ),
                BackgroundTask(
                    user_id=member.id,
                    organization_id=org.id,
                    task_type="analyze_logs",
                    status=TaskStatus.FAILED,
                    progress=40,
                    error_code="LLM_TIMEOUT",
                    error_message="Provider timed out (seeded failure).",
                    created_at=now - timedelta(hours=1),
                    started_at=now - timedelta(hours=1),
                    completed_at=now - timedelta(minutes=50),
                ),
                BackgroundTask(
                    user_id=owner.id,
                    organization_id=org.id,
                    task_type="analyze_logs",
                    status=TaskStatus.QUEUED,
                    progress=0,
                    created_at=now - timedelta(minutes=10),
                ),
            ]
        )

        for offset_hours, operation in (
            (1, "chat"),
            (5, "review"),
            (26, "generate"),
            (30, "chat"),
        ):
            session.add(
                UsageEvent(
                    user_id=owner.id,
                    organization_id=org.id,
                    operation=operation,
                    provider="gemini",
                    model="gemini-1.5-flash",
                    input_tokens=400 + offset_hours,
                    output_tokens=200 + offset_hours,
                    total_tokens=600 + offset_hours * 2,
                    is_estimated=True,
                    created_at=now - timedelta(hours=offset_hours),
                )
            )

        session.add_all(
            [
                AuditEvent(
                    actor_user_id=owner.id,
                    organization_id=org.id,
                    action="organization.created",
                    resource_type="organization",
                    resource_id=org.id,
                    request_id="seed-audit-1",
                    metadata_json={"source": "dummy-seed"},
                    created_at=now - timedelta(days=2),
                ),
                AuditEvent(
                    actor_user_id=admin.id,
                    organization_id=org.id,
                    action="policy_pack.created",
                    resource_type="policy_pack",
                    resource_id=pack.id,
                    request_id="seed-audit-2",
                    metadata_json={"name": pack.name},
                    created_at=now - timedelta(days=1),
                ),
            ]
        )

        # Personal workspace sample for demo.personal
        personal = users["demo.personal@example.com"]
        personal_conv = Conversation(
            id=uuid.uuid4(),
            user_id=personal.id,
            organization_id=None,
            title="Personal: generate a Kubernetes probe",
            provider="gemini",
        )
        session.add(personal_conv)
        await session.flush()
        session.add(
            Message(
                conversation_id=personal_conv.id,
                role=MessageRole.USER,
                content="Draft a readinessProbe for a Next.js service on port 3000.",
            )
        )

        await session.commit()

        print("Dummy data seeded successfully.")
        print(f"  Organization : Acme Platform (slug=acme-platform)")
        print(f"  Password     : {DEMO_PASSWORD}")
        print("  Accounts     :")
        for spec in users_spec:
            print(f"    - {spec['email']} ({spec['username']})")
        print("Details: docs/dummy-data.md")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed dummy demo data")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Attempt seed even if owner exists (still skips duplicate emails)",
    )
    args = parser.parse_args()
    asyncio.run(seed(force=args.force))


if __name__ == "__main__":
    main()
