from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_change_token import EmailChangeToken


class EmailChangeTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: UUID,
        token_hash: str,
        new_email: str,
        expires_at: datetime,
        created_ip: str | None = None,
    ) -> EmailChangeToken:
        record = EmailChangeToken(
            user_id=user_id,
            token_hash=token_hash,
            new_email=new_email,
            expires_at=expires_at,
            created_ip=created_ip,
        )
        self.session.add(record)
        await self.session.flush()
        await self.session.refresh(record)
        return record

    async def get_by_hash_for_update(self, token_hash: str) -> EmailChangeToken | None:
        result = await self.session.execute(
            select(EmailChangeToken)
            .where(EmailChangeToken.token_hash == token_hash)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def invalidate_unused_for_user(self, user_id: UUID) -> int:
        now = datetime.now(UTC)
        result = await self.session.execute(
            select(EmailChangeToken).where(
                EmailChangeToken.user_id == user_id,
                EmailChangeToken.used_at.is_(None),
            )
        )
        tokens = list(result.scalars().all())
        for token in tokens:
            token.used_at = now
        if tokens:
            await self.session.flush()
        return len(tokens)
