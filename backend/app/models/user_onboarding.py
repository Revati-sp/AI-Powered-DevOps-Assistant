from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserOnboarding(Base):
    __tablename__ = "user_onboarding"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    welcome_dismissed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    profile_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    first_chat_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    first_artifact_created: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    organization_created: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    invite_team_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    tour_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    user: Mapped[User] = relationship("User", back_populates="onboarding")
