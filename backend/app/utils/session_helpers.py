from __future__ import annotations

from app.models.refresh_token import RefreshToken
from app.schemas.auth import SessionResponse


def truncate_user_agent(user_agent: str | None, *, max_len: int = 80) -> str | None:
    if not user_agent:
        return None
    if len(user_agent) <= max_len:
        return user_agent
    return user_agent[: max_len - 3] + "..."


def refresh_token_to_session(
    record: RefreshToken,
    *,
    current_jti: str | None = None,
) -> SessionResponse:
    return SessionResponse(
        id=record.id,
        created_at=record.issued_at,
        expires_at=record.expires_at,
        revoked=record.revoked_at is not None,
        approx_ip=record.created_ip,
        approx_client=truncate_user_agent(record.created_user_agent),
        is_current=current_jti is not None and record.jti == current_jti,
    )
