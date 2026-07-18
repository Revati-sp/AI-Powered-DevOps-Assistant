"""Shared helpers for migration validation scripts (URL parse + redaction)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse


_CREDENTIAL_RE = re.compile(r"(://[^:/@]+:)([^@]+)(@)")


def redact_database_url(url: str) -> str:
    """Mask the password segment of a database URL for safe logging."""
    return _CREDENTIAL_RE.sub(r"\1***\3", url)


@dataclass(frozen=True)
class DatabaseTarget:
    url: str
    host: str
    port: int
    user: str
    database: str
    driver: str


def normalize_async_url(url: str) -> str:
    """Ensure SQLAlchemy async URL uses postgresql+asyncpg."""
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql+psycopg://"):
        return "postgresql+asyncpg://" + url.removeprefix("postgresql+psycopg://")
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url.removeprefix("postgresql://")
    return url


def parse_database_url(url: str) -> DatabaseTarget:
    normalized = normalize_async_url(url.strip())
    # urlparse needs a standard scheme for username/password extraction
    parseable = normalized.replace("postgresql+asyncpg://", "postgresql://", 1)
    parsed = urlparse(parseable)
    database = (parsed.path or "/").lstrip("/") or "devops_assistant"
    return DatabaseTarget(
        url=normalized,
        host=parsed.hostname or "localhost",
        port=int(parsed.port or 5432),
        user=parsed.username or "devops",
        database=database,
        driver="asyncpg",
    )


def resolve_database_url(cli_url: str | None = None) -> str:
    raw = cli_url or os.environ.get("DATABASE_URL")
    if not raw:
        raise SystemExit(
            "DATABASE_URL is required (or pass --database-url). "
            "Example: postgresql+asyncpg://devops:devops@localhost:5432/devops_assistant"
        )
    return normalize_async_url(raw)


SAFE_MIGRATION_ENVS = frozenset({"development", "test", "ci"})


def assert_safe_migration_env(*, allow_unsafe: bool = False) -> str:
    """Refuse accidental runs against unmarked environments."""
    env = (os.environ.get("MIGRATION_ENV") or os.environ.get("APP_ENV") or "").lower()
    if allow_unsafe:
        return env or "unsafe-allowed"
    if env not in SAFE_MIGRATION_ENVS:
        raise SystemExit(
            "Refusing to run migration validation without a safe environment marker.\n"
            "Set MIGRATION_ENV=development|test|ci (or APP_ENV to one of those),\n"
            "or pass --allow-unsafe if you intentionally target another database.\n"
            f"Current MIGRATION_ENV/APP_ENV={env!r}"
        )
    return env
