from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import ORMModel


class UserOnboardingResponse(ORMModel):
    user_id: UUID
    welcome_dismissed: bool
    profile_completed: bool
    first_chat_completed: bool
    first_artifact_created: bool
    organization_created: bool
    invite_team_completed: bool
    tour_completed: bool
    onboarding_completed: bool
    created_at: datetime
    updated_at: datetime


class UserOnboardingPatchRequest(BaseModel):
    welcome_dismissed: bool | None = None
    profile_completed: bool | None = None
    first_chat_completed: bool | None = None
    first_artifact_created: bool | None = None
    organization_created: bool | None = None
    invite_team_completed: bool | None = None
    tour_completed: bool | None = None
    onboarding_completed: bool | None = None
