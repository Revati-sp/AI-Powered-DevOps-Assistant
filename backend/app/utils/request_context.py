from __future__ import annotations

import uuid

from fastapi import Request

from app.services.audit_service import AuditRequestContext
from app.utils.client_ip import resolve_client_ip


def build_audit_context(request: Request | None) -> AuditRequestContext:
    if request is None:
        return AuditRequestContext()
    request_id = getattr(request.state, "request_id", None) or request.headers.get(
        "x-request-id"
    )
    if not request_id:
        request_id = str(uuid.uuid4())
    return AuditRequestContext(
        request_id=request_id,
        ip_address=resolve_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
