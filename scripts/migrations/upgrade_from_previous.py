#!/usr/bin/env python3
"""Upgrade-from-previous-revision smoke test on a temporary database.

Workflow:
  1. Connect as admin URL (or DATABASE_URL) and create a temporary database
  2. alembic upgrade <previous>
  3. Insert representative rows compatible with that revision
  4. alembic upgrade head
  5. Verify rows still readable
  6. Drop temporary database

Requires PostgreSQL. Safe by default: requires MIGRATION_ENV=development|test|ci
and creates a uniquely named database (never mutates devops_assistant unless forced).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import sys
import uuid
from pathlib import Path
from urllib.parse import urlparse, urlunparse

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
BACKEND_DIR = REPO_ROOT / "backend"

sys.path.insert(0, str(SCRIPT_DIR))
from _db_url import (  # noqa: E402
    assert_safe_migration_env,
    normalize_async_url,
    redact_database_url,
    resolve_database_url,
)


def _admin_url(database_url: str, database: str = "postgres") -> str:
    parseable = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    parsed = urlparse(parseable)
    replaced = parsed._replace(path=f"/{database}")
    return normalize_async_url(urlunparse(replaced))


def _with_database(database_url: str, database: str) -> str:
    return _admin_url(database_url, database)


async def _exec_sql(database_url: str, sql: str) -> None:
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(database_url, isolation_level="AUTOCOMMIT")
    try:
        async with engine.connect() as conn:
            await conn.exec_driver_sql(sql)
    finally:
        await engine.dispose()


async def _fetch_one(database_url: str, sql: str) -> tuple[object, ...]:
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(database_url)
    try:
        async with engine.connect() as conn:
            result = await conn.exec_driver_sql(sql)
            row = result.one()
            return tuple(row)
    finally:
        await engine.dispose()


def _run_alembic(args: list[str], database_url: str) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    cmd = [sys.executable, "-m", "alembic", *args]
    print("+", " ".join(cmd), f"(db={redact_database_url(database_url)})")
    subprocess.run(cmd, cwd=BACKEND_DIR, env=env, check=True)


def _list_revisions() -> list[str]:
    # Walk migration filenames for ordered revision chain by down_revision links via alembic.
    env = os.environ.copy()
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "history", "--verbose"],
        cwd=BACKEND_DIR,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    revs: list[str] = []
    for line in result.stdout.splitlines():
        if line.startswith("Rev:"):
            # Rev: 011_user_profile (head)
            token = line.split(":", 1)[1].strip().split()[0]
            revs.append(token)
    # history prints newest first
    return list(reversed(revs))


async def _seed_compatible_data(database_url: str) -> None:
    # Minimal rows that exist since 001_initial_schema.
    await _exec_sql(
        database_url,
        """
        INSERT INTO users (id, email, username, hashed_password, role, is_active, created_at, updated_at)
        VALUES (
          '11111111-1111-1111-1111-111111111111',
          'migration-smoke@example.com',
          'migration_smoke',
          'not-a-real-hash',
          'user',
          true,
          NOW(),
          NOW()
        )
        ON CONFLICT (email) DO NOTHING
        """,
    )


async def _verify_data(database_url: str) -> None:
    row = await _fetch_one(
        database_url,
        "SELECT email FROM users WHERE username = 'migration_smoke'",
    )
    if row[0] != "migration-smoke@example.com":
        raise SystemExit(f"unexpected user email after upgrade: {row[0]!r}")


async def run(database_url: str, *, keep_db: bool) -> None:
    revisions = _list_revisions()
    if len(revisions) < 2:
        print("Only one revision present; skipping previous->head data upgrade test.")
        return

    previous = revisions[-2]
    head = revisions[-1]
    temp_db = f"devops_migrate_{uuid.uuid4().hex[:10]}"
    admin_url = _admin_url(database_url, "postgres")
    temp_url = _with_database(database_url, temp_db)

    print(f"Creating temporary database {temp_db}")
    print(f"Admin URL: {redact_database_url(admin_url)}")
    await _exec_sql(admin_url, f'CREATE DATABASE "{temp_db}"')

    try:
        print(f"Upgrading temporary database to previous revision: {previous}")
        _run_alembic(["upgrade", previous], temp_url)
        print("Inserting representative data")
        await _seed_compatible_data(temp_url)
        print(f"Upgrading temporary database to head: {head}")
        _run_alembic(["upgrade", "head"], temp_url)
        print("Verifying data survived upgrade")
        await _verify_data(temp_url)
        print("Existing-data upgrade succeeded.")
    finally:
        if keep_db:
            print(f"Keeping temporary database {temp_db} (--keep-db)")
        else:
            print(f"Dropping temporary database {temp_db}")
            await _exec_sql(admin_url, f'DROP DATABASE IF EXISTS "{temp_db}" WITH (FORCE)')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=None)
    parser.add_argument("--allow-unsafe", action="store_true")
    parser.add_argument(
        "--keep-db",
        action="store_true",
        help="Do not drop the temporary database (debug only).",
    )
    args = parser.parse_args()
    assert_safe_migration_env(allow_unsafe=args.allow_unsafe)
    database_url = resolve_database_url(args.database_url)
    asyncio.run(run(database_url, keep_db=args.keep_db))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
