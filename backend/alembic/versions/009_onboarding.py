"""onboarding

Revision ID: 009_onboarding
Revises: 008_artifact_tags_favorites
Create Date: 2026-07-17 20:30:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009_onboarding"
down_revision: Union[str, None] = "008_artifact_tags_favorites"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_onboarding",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("welcome_dismissed", sa.Boolean(), nullable=False),
        sa.Column("profile_completed", sa.Boolean(), nullable=False),
        sa.Column("first_chat_completed", sa.Boolean(), nullable=False),
        sa.Column("first_artifact_created", sa.Boolean(), nullable=False),
        sa.Column("organization_created", sa.Boolean(), nullable=False),
        sa.Column("invite_team_completed", sa.Boolean(), nullable=False),
        sa.Column("tour_completed", sa.Boolean(), nullable=False),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("user_onboarding")
