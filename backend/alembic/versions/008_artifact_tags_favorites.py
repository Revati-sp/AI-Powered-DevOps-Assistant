"""artifact tags favorites

Revision ID: 008_artifact_tags_favorites
Revises: 007_usage_quotas
Create Date: 2026-07-17 20:20:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008_artifact_tags_favorites"
down_revision: Union[str, None] = "007_usage_quotas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "generated_artifacts",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "artifact_tags",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("color", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "user_id",
            "name",
            name="uq_artifact_tag_scope_name",
        ),
    )
    op.create_index("ix_artifact_tags_organization_id", "artifact_tags", ["organization_id"])
    op.create_index("ix_artifact_tags_user_id", "artifact_tags", ["user_id"])
    op.create_index("ix_artifact_tags_name", "artifact_tags", ["name"])

    op.create_table(
        "artifact_tag_associations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("artifact_id", sa.Uuid(), nullable=False),
        sa.Column("tag_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["artifact_id"], ["generated_artifacts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["tag_id"], ["artifact_tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("artifact_id", "tag_id", name="uq_artifact_tag_association"),
    )
    op.create_index(
        "ix_artifact_tag_associations_artifact_id",
        "artifact_tag_associations",
        ["artifact_id"],
    )
    op.create_index(
        "ix_artifact_tag_associations_tag_id",
        "artifact_tag_associations",
        ["tag_id"],
    )

    op.create_table(
        "artifact_favorites",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("artifact_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["artifact_id"], ["generated_artifacts.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "artifact_id", name="uq_artifact_favorite"),
    )
    op.create_index("ix_artifact_favorites_user_id", "artifact_favorites", ["user_id"])
    op.create_index(
        "ix_artifact_favorites_artifact_id", "artifact_favorites", ["artifact_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_artifact_favorites_artifact_id", table_name="artifact_favorites")
    op.drop_index("ix_artifact_favorites_user_id", table_name="artifact_favorites")
    op.drop_table("artifact_favorites")
    op.drop_index(
        "ix_artifact_tag_associations_tag_id",
        table_name="artifact_tag_associations",
    )
    op.drop_index(
        "ix_artifact_tag_associations_artifact_id",
        table_name="artifact_tag_associations",
    )
    op.drop_table("artifact_tag_associations")
    op.drop_index("ix_artifact_tags_name", table_name="artifact_tags")
    op.drop_index("ix_artifact_tags_user_id", table_name="artifact_tags")
    op.drop_index("ix_artifact_tags_organization_id", table_name="artifact_tags")
    op.drop_table("artifact_tags")
    op.drop_column("generated_artifacts", "archived_at")
