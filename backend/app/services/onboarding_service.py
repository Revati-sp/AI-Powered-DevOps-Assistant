from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.user_onboarding import UserOnboarding
from app.repositories.user_onboarding_repository import UserOnboardingRepository

_ONBOARDING_FLAGS = frozenset(
    {
        "welcome_dismissed",
        "profile_completed",
        "first_chat_completed",
        "first_artifact_created",
        "organization_created",
        "invite_team_completed",
        "tour_completed",
        "onboarding_completed",
    }
)


class OnboardingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = UserOnboardingRepository(session)

    async def get_onboarding(self, user: User) -> UserOnboarding:
        return await self.repo.get_or_create(user.id)

    async def mark_flag(self, user_id: UUID, **flags: bool) -> None:
        """Set onboarding flags to True when not already True; ignore False values."""
        true_flags = {
            key: True
            for key, value in flags.items()
            if key in _ONBOARDING_FLAGS and value is True
        }
        if not true_flags:
            return
        onboarding = await self.repo.get_or_create(user_id)
        changed = False
        for key in true_flags:
            if not getattr(onboarding, key):
                setattr(onboarding, key, True)
                changed = True
        if changed:
            onboarding.updated_at = datetime.now(UTC)
            await self.session.flush()

    async def patch_onboarding(
        self,
        user: User,
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
        return await self.repo.update(
            user.id,
            welcome_dismissed=welcome_dismissed,
            profile_completed=profile_completed,
            first_chat_completed=first_chat_completed,
            first_artifact_created=first_artifact_created,
            organization_created=organization_created,
            invite_team_completed=invite_team_completed,
            tour_completed=tour_completed,
            onboarding_completed=onboarding_completed,
        )
