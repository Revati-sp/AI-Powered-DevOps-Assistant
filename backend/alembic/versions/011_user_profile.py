"""add editable user profile and email change tokens

Revision ID: 011_user_profile
Revises: 010_pipeline_shell_routing
Create Date: 2026-07-17 22:10:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011_user_profile"
down_revision: Union[str, None] = "010_pipeline_shell_routing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("display_name", sa.String(length=120)))
    op.add_column("users", sa.Column("timezone", sa.String(length=64)))
    op.add_column("users", sa.Column("job_title", sa.String(length=120)))
    op.add_column("users", sa.Column("avatar_url", sa.String(length=512)))

    op.create_table(
        "email_change_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("new_email", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_ip", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_email_change_tokens_user_id", "email_change_tokens", ["user_id"]
    )
    op.create_index(
        "ix_email_change_tokens_token_hash",
        "email_change_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_email_change_tokens_expires_at", "email_change_tokens", ["expires_at"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_email_change_tokens_expires_at", table_name="email_change_tokens"
    )
    op.drop_index(
        "ix_email_change_tokens_token_hash", table_name="email_change_tokens"
    )
    op.drop_index("ix_email_change_tokens_user_id", table_name="email_change_tokens")
    op.drop_table("email_change_tokens")

    op.drop_column("users", "avatar_url")
    op.drop_column("users", "job_title")
    op.drop_column("users", "timezone")
    op.drop_column("users", "display_name")
