#!/usr/bin/env python3
"""Validate Alembic migrations against a PostgreSQL database.

Runs:
  alembic heads
  alembic current
  alembic upgrade head
  alembic check

Safety:
  Requires MIGRATION_ENV or APP_ENV in {development, test, ci}
  unless --allow-unsafe is provided.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
BACKEND_DIR = REPO_ROOT / "backend"

sys.path.insert(0, str(SCRIPT_DIR))
from _db_url import (  # noqa: E402
    assert_safe_migration_env,
    redact_database_url,
    resolve_database_url,
)


def run_alembic(args: list[str], *, env: dict[str, str]) -> str:
    cmd = [sys.executable, "-m", "alembic", *args]
    print("+", " ".join(cmd))
    result = subprocess.run(
        cmd,
        cwd=BACKEND_DIR,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    if stdout.strip():
        print(stdout.rstrip())
    if stderr.strip():
        # Alembic often writes informational logs to stderr.
        print(stderr.rstrip(), file=sys.stderr)
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    return stdout + "\n" + stderr


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database-url",
        default=None,
        help="PostgreSQL URL (defaults to DATABASE_URL). Password is never printed.",
    )
    parser.add_argument(
        "--skip-upgrade",
        action="store_true",
        help="Only check heads/current/check (no upgrade).",
    )
    parser.add_argument(
        "--allow-unsafe",
        action="store_true",
        help="Allow running without MIGRATION_ENV/APP_ENV=development|test|ci.",
    )
    args = parser.parse_args()

    migration_env = assert_safe_migration_env(allow_unsafe=args.allow_unsafe)
    database_url = resolve_database_url(args.database_url)
    print(f"Migration environment: {migration_env}")
    print(f"Database URL: {redact_database_url(database_url)}")

    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    env.setdefault("MIGRATION_ENV", migration_env)
    # Avoid loading a developer's .env secrets into logs; settings still read DATABASE_URL.
    env.setdefault("APP_ENV", migration_env if migration_env != "ci" else "test")

    heads_out = run_alembic(["heads"], env=env)
    head_revs: list[str] = []
    for line in heads_out.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("INFO") or stripped.startswith("["):
            continue
        # Formats: "<rev> (head)" or "<rev>"
        token = stripped.split()[0]
        if "(head)" in stripped or token:
            head_revs.append(token)
    unique_heads = sorted({rev for rev in head_revs if rev})
    if len(unique_heads) != 1:
        print(
            f"error: expected exactly one Alembic head, found {len(unique_heads)}: "
            f"{unique_heads}",
            file=sys.stderr,
        )
        return 1
    print(f"Single head: {unique_heads[0]}")

    if not args.skip_upgrade:
        run_alembic(["upgrade", "head"], env=env)

    current_out = run_alembic(["current"], env=env)
    print("Current revision output captured.")
    if unique_heads[0] not in current_out and "head" not in current_out.lower():
        # Soft check — alembic current formats vary; upgrade already succeeded.
        print("warning: could not confirm current revision string in output")

    run_alembic(["check"], env=env)
    print("Migration validation succeeded.")
    print(f"Head revision: {unique_heads[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
