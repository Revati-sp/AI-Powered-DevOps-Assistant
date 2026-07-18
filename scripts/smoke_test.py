#!/usr/bin/env python3
"""Full-stack smoke test against a running Compose environment.

Usage:
  python scripts/smoke_test.py
  API_BASE_URL=http://localhost:8000 FRONTEND_BASE_URL=http://localhost:3000 python scripts/smoke_test.py

Exits non-zero on failure. Never logs tokens or passwords.
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")
FRONTEND_BASE = os.environ.get("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/")
TIMEOUT = float(os.environ.get("SMOKE_TIMEOUT_SECONDS", "15"))


class SmokeFailure(Exception):
    pass


def _request(
    method: str,
    url: str,
    *,
    data: dict[str, Any] | None = None,
    form: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    accept: str | None = None,
) -> tuple[int, Any, dict[str, str]]:
    body: bytes | None = None
    req_headers = dict(headers or {})
    if form is not None:
        from urllib.parse import urlencode

        body = urlencode(form).encode()
        req_headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif data is not None:
        body = json.dumps(data).encode()
        req_headers["Content-Type"] = "application/json"
    if accept:
        req_headers["Accept"] = accept
    req = Request(url, data=body, headers=req_headers, method=method)
    try:
        with urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read()
            ctype = resp.headers.get("Content-Type", "")
            parsed: Any
            if "application/json" in ctype:
                parsed = json.loads(raw.decode() or "null")
            else:
                parsed = raw.decode(errors="replace")
            return resp.status, parsed, dict(resp.headers)
    except HTTPError as exc:
        raw = exc.read()
        try:
            parsed = json.loads(raw.decode() or "null")
        except Exception:
            parsed = raw.decode(errors="replace")
        return exc.code, parsed, dict(exc.headers.items())
    except URLError as exc:
        raise SmokeFailure(f"Request failed {method} {url}: {exc}") from exc


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"PASS  {name}")
        return
    msg = f"FAIL  {name}"
    if detail:
        msg = f"{msg}: {detail}"
    raise SmokeFailure(msg)


def main() -> int:
    suffix = uuid.uuid4().hex[:10]
    username = f"smoke_{suffix}"
    email = f"smoke_{suffix}@example.com"
    password = "SmokeTestPass123!"

    print(f"Smoke testing API={API_BASE} frontend={FRONTEND_BASE}")

    status, body, _ = _request("GET", f"{API_BASE}/health")
    check("GET /health", status == 200 and body.get("status") == "ok", str(body))

    status, body, _ = _request("GET", f"{API_BASE}/ready")
    check("GET /ready", status == 200, str(body))

    status, body, headers = _request("GET", f"{API_BASE}/metrics")
    check(
        "GET /metrics",
        status == 200 and ("text/plain" in headers.get("Content-Type", "") or isinstance(body, str)),
        f"status={status}",
    )

    status, body, _ = _request(
        "POST",
        f"{API_BASE}/api/v1/auth/register",
        data={"email": email, "username": username, "password": password},
    )
    check("POST /auth/register", status == 200 and body.get("success") is True, str(body)[:200])

    status, tokens, _ = _request(
        "POST",
        f"{API_BASE}/api/v1/auth/login",
        form={"username": username, "password": password},
    )
    check(
        "POST /auth/login",
        status == 200 and isinstance(tokens, dict) and "access_token" in tokens and "refresh_token" in tokens,
        "login failed",
    )
    access = tokens["access_token"]
    refresh = tokens["refresh_token"]
    auth = {"Authorization": f"Bearer {access}"}

    status, refreshed, _ = _request(
        "POST",
        f"{API_BASE}/api/v1/auth/refresh",
        data={"refresh_token": refresh},
    )
    check(
        "POST /auth/refresh",
        status == 200 and "access_token" in refreshed,
        "refresh failed",
    )
    access = refreshed["access_token"]
    refresh = refreshed["refresh_token"]
    auth = {"Authorization": f"Bearer {access}"}

    status, me, _ = _request("GET", f"{API_BASE}/api/v1/users/me", headers=auth)
    check(
        "GET /users/me",
        status == 200 and me.get("data", {}).get("username") == username,
        str(me)[:200],
    )

    status, org, _ = _request(
        "POST",
        f"{API_BASE}/api/v1/organizations",
        headers=auth,
        data={"name": f"Smoke Org {suffix}", "slug": f"smoke-org-{suffix}"},
    )
    check("POST /organizations", status == 200 and org.get("success") is True, str(org)[:200])
    org_id = org["data"]["id"]

    status, artifact, _ = _request(
        "POST",
        f"{API_BASE}/api/v1/artifacts",
        headers=auth,
        data={
            "name": f"smoke-dockerfile-{suffix}",
            "artifact_type": "dockerfile",
            "content": "FROM python:3.12-slim\n",
            "organization_id": org_id,
        },
    )
    check("POST /artifacts", status == 200 and artifact.get("success") is True, str(artifact)[:200])

    status, review, _ = _request(
        "POST",
        f"{API_BASE}/api/v1/review",
        headers=auth,
        data={
            "type": "dockerfile",
            "content": "FROM python:3.12-slim\nUSER root\n",
            "organization_id": org_id,
        },
    )
    check("POST /review", status == 200, str(review)[:200])

    status, task, _ = _request(
        "POST",
        f"{API_BASE}/api/v1/logs/analyze/async",
        headers=auth,
        data={
            "log_text": "ERROR CrashLoopBackOff back-off restarting failed container\n",
            "organization_id": org_id,
        },
    )
    check(
        "POST /logs/analyze/async",
        status in {200, 202} and (task.get("success") is True or "id" in str(task)),
        str(task)[:200],
    )

    # Streaming chat: expect SSE framing
    status, stream_body, stream_headers = _request(
        "POST",
        f"{API_BASE}/api/v1/chat/stream",
        headers={**auth, "Accept": "text/event-stream"},
        data={"message": "What is CrashLoopBackOff?", "organization_id": org_id},
        accept="text/event-stream",
    )
    stream_ok = status == 200 and (
        "text/event-stream" in stream_headers.get("Content-Type", "")
        or "data:" in str(stream_body)
    )
    check("POST /chat/stream", stream_ok, f"status={status}")

    status, _, _ = _request(
        "POST",
        f"{API_BASE}/api/v1/auth/logout",
        data={"refresh_token": refresh},
    )
    check("POST /auth/logout", status == 200)

    # Frontend availability (best-effort; may be HTML)
    try:
        status, page, _ = _request("GET", FRONTEND_BASE)
        check("GET frontend /", status == 200 and len(str(page)) > 0, f"status={status}")
    except SmokeFailure as exc:
        print(f"WARN  frontend check skipped/failed: {exc}")

    print("Smoke test completed successfully.")
    return 0


if __name__ == "__main__":
    started = time.time()
    try:
        code = main()
    except SmokeFailure as exc:
        print(str(exc), file=sys.stderr)
        code = 1
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL  unexpected error: {exc.__class__.__name__}", file=sys.stderr)
        code = 1
    print(f"Elapsed {time.time() - started:.1f}s")
    raise SystemExit(code)
