from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_onboarding import UserOnboarding


class UserOnboardingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_for_user(self, user_id: UUID) -> UserOnboarding | None:
        result = await self.session.execute(
            select(UserOnboarding).where(UserOnboarding.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: UUID) -> UserOnboarding:
        onboarding = await self.get_for_user(user_id)
        if onboarding is not None:
            return onboarding
        onboarding = UserOnboarding(user_id=user_id)
        self.session.add(onboarding)
        await self.session.flush()
        await self.session.refresh(onboarding)
        return onboarding

    async def update(
        self,
        user_id: UUID,
        *,
        welcome_dismissed: bool | None = None,
        profile_completed: bool | None = None,
        first_chat_completed: bool | None = None,
        first_artifact_created: bool | None = None,
        organization_created: bool | None = None,
        invite_team_completed: bool | None = None,
        tour_completed: bool | None = None,
        onboarding_completed: bool | None = None,
    ) -> UserOnboarding:
        onboarding = await self.get_or_create(user_id)
        fields = {
            "welcome_dismissed": welcome_dismissed,
            "profile_completed": profile_completed,
            "first_chat_completed": first_chat_completed,
            "first_artifact_created": first_artifact_created,
            "organization_created": organization_created,
            "invite_team_completed": invite_team_completed,
            "tour_completed": tour_completed,
            "onboarding_completed": onboarding_completed,
        }
        for key, value in fields.items():
            if value is not None:
                setattr(onboarding, key, value)
        onboarding.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(onboarding)
        return onboarding
