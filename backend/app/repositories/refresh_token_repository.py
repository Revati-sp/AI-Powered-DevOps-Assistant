from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: UUID,
        family_id: UUID,
        token_hash: str,
        jti: str,
        expires_at: datetime,
        created_ip: str | None = None,
        created_user_agent: str | None = None,
    ) -> RefreshToken:
        record = RefreshToken(
            user_id=user_id,
            family_id=family_id,
            token_hash=token_hash,
            jti=jti,
            expires_at=expires_at,
            created_ip=created_ip,
            created_user_agent=created_user_agent,
        )
        self.session.add(record)
        await self.session.flush()
        await self.session.refresh(record)
        return record

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        )
        return result.scalar_one_or_none()

    async def get_by_jti_for_update(self, jti: str) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.jti == jti).with_for_update()
        )
        return result.scalar_one_or_none()

    async def revoke_token(
        self,
        token_id: UUID,
        *,
        reason: str,
    ) -> RefreshToken | None:
        record = await self.session.get(RefreshToken, token_id)
        if record is None or record.revoked_at is not None:
            return record
        record.revoked_at = datetime.now(UTC)
        record.revoked_reason = reason
        await self.session.flush()
        return record

    async def revoke_family(self, family_id: UUID, *, reason: str) -> int:
        now = datetime.now(UTC)
        result = await self.session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.family_id == family_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now, revoked_reason=reason)
        )
        await self.session.flush()
        return int(cast(CursorResult[Any], result).rowcount or 0)

    async def revoke_all_for_user(self, user_id: UUID, *, reason: str) -> int:
        now = datetime.now(UTC)
        result = await self.session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now, revoked_reason=reason)
        )
        await self.session.flush()
        return int(cast(CursorResult[Any], result).rowcount or 0)

    async def revoke_all_except_jti(
        self, user_id: UUID, *, keep_jti: str, reason: str
    ) -> int:
        now = datetime.now(UTC)
        result = await self.session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.jti != keep_jti,
            )
            .values(revoked_at=now, revoked_reason=reason)
        )
        await self.session.flush()
        return int(cast(CursorResult[Any], result).rowcount or 0)

    async def list_for_user(self, user_id: UUID) -> list[RefreshToken]:
        result = await self.session.execute(
            select(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .order_by(RefreshToken.issued_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id_for_user(
        self, token_id: UUID, user_id: UUID
    ) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.id == token_id,
                RefreshToken.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_jti_for_user(self, jti: str, user_id: UUID) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.jti == jti,
                RefreshToken.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()
