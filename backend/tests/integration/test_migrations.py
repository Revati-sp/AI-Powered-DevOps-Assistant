from __future__ import annotations

import subprocess
from pathlib import Path

from app.core.database import Base
from app.models import (
    EmailChangeToken,
    EmailVerificationToken,
    Organization,
    OrganizationInvitation,
    OrganizationQuota,
    PasswordResetToken,
    ProviderConfig,
    RefreshToken,
    UsageEvent,
    UserOnboarding,
)
from sqlalchemy import create_engine, inspect

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_CMD = str(BACKEND_ROOT / ".venv" / "bin" / "alembic")


def test_alembic_has_single_head() -> None:
    result = subprocess.run(
        [ALEMBIC_CMD, "heads"],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    heads = [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip() and "(head)" in line
    ]
    assert len(heads) == 1
    assert "011_user_profile" in heads[0]


def test_refresh_token_and_organization_models_in_metadata() -> None:
    table_names = set(Base.metadata.tables.keys())
    assert RefreshToken.__tablename__ in table_names
    assert Organization.__tablename__ in table_names
    assert PasswordResetToken.__tablename__ in table_names
    assert EmailVerificationToken.__tablename__ in table_names
    assert EmailChangeToken.__tablename__ in table_names
    assert OrganizationInvitation.__tablename__ in table_names
    assert ProviderConfig.__tablename__ in table_names
    assert UsageEvent.__tablename__ in table_names
    assert OrganizationQuota.__tablename__ in table_names
    assert UserOnboarding.__tablename__ in table_names


def test_sqlite_create_all_matches_model_metadata() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    inspector = inspect(engine)
    created_tables = set(inspector.get_table_names())
    assert RefreshToken.__tablename__ in created_tables
    assert Organization.__tablename__ in created_tables
    assert PasswordResetToken.__tablename__ in created_tables
    assert EmailVerificationToken.__tablename__ in created_tables
    assert EmailChangeToken.__tablename__ in created_tables
    assert OrganizationInvitation.__tablename__ in created_tables
    assert ProviderConfig.__tablename__ in created_tables
    assert UsageEvent.__tablename__ in created_tables
    assert OrganizationQuota.__tablename__ in created_tables
    assert UserOnboarding.__tablename__ in created_tables
