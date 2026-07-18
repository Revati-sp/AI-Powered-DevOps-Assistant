from __future__ import annotations

import subprocess
from pathlib import Path

from app.core.database import Base
from app.models import Organization, RefreshToken
from sqlalchemy import create_engine, inspect

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def test_alembic_has_single_head() -> None:
    result = subprocess.run(
        ["alembic", "heads"],
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


def test_refresh_token_and_organization_models_in_metadata() -> None:
    table_names = set(Base.metadata.tables.keys())
    assert RefreshToken.__tablename__ in table_names
    assert Organization.__tablename__ in table_names


def test_sqlite_create_all_matches_model_metadata() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    inspector = inspect(engine)
    created_tables = set(inspector.get_table_names())
    assert RefreshToken.__tablename__ in created_tables
    assert Organization.__tablename__ in created_tables
