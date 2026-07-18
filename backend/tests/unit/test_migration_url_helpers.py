"""Unit tests for migration validation URL helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "migrations"))

from _db_url import (  # noqa: E402
    SAFE_MIGRATION_ENVS,
    assert_safe_migration_env,
    normalize_async_url,
    parse_database_url,
    redact_database_url,
    resolve_database_url,
)


def test_redact_database_url_masks_password() -> None:
    url = "postgresql+asyncpg://devops:s3cret@localhost:5432/devops_assistant"
    redacted = redact_database_url(url)
    assert "s3cret" not in redacted
    assert "devops:***@" in redacted
    assert "localhost:5432/devops_assistant" in redacted


def test_normalize_async_url_variants() -> None:
    assert normalize_async_url(
        "postgresql://devops:devops@localhost:5432/db"
    ).startswith("postgresql+asyncpg://")
    assert normalize_async_url(
        "postgresql+psycopg://devops:devops@localhost:5432/db"
    ).startswith("postgresql+asyncpg://")
    assert (
        normalize_async_url("postgresql+asyncpg://devops:devops@localhost:5432/db")
        == "postgresql+asyncpg://devops:devops@localhost:5432/db"
    )


def test_parse_database_url() -> None:
    target = parse_database_url(
        "postgresql+asyncpg://devops:devops@127.0.0.1:5432/devops_assistant"
    )
    assert target.host == "127.0.0.1"
    assert target.port == 5432
    assert target.user == "devops"
    assert target.database == "devops_assistant"
    assert target.driver == "asyncpg"


def test_resolve_database_url_requires_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(SystemExit):
        resolve_database_url(None)


def test_resolve_database_url_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://devops:devops@localhost:5432/devops_assistant",
    )
    assert resolve_database_url(None).startswith("postgresql+asyncpg://")


def test_assert_safe_migration_env_blocks_unmarked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MIGRATION_ENV", raising=False)
    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(SystemExit):
        assert_safe_migration_env(allow_unsafe=False)


def test_assert_safe_migration_env_allows_development(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MIGRATION_ENV", "development")
    assert assert_safe_migration_env() == "development"
    assert SAFE_MIGRATION_ENVS == frozenset({"development", "test", "ci"})


def test_assert_safe_migration_env_allow_unsafe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MIGRATION_ENV", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    assert assert_safe_migration_env(allow_unsafe=True) == "unsafe-allowed"
