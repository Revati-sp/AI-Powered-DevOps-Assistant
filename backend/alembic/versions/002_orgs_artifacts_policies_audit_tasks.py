"""organizations artifacts policies audit tasks

Revision ID: 002_orgs_artifacts
Revises: 001_initial
Create Date: 2026-07-17 16:00:00.000000

"""

from __future__ import annotations

import hashlib
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_orgs_artifacts"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)
    op.create_index("ix_organizations_created_by", "organizations", ["created_by"])

    op.create_table(
        "organization_members",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id", "user_id", name="uq_org_member"
        ),
    )
    op.create_index(
        "ix_organization_members_organization_id",
        "organization_members",
        ["organization_id"],
    )
    op.create_index(
        "ix_organization_members_user_id", "organization_members", ["user_id"]
    )
    op.create_index("ix_organization_members_role", "organization_members", ["role"])

    op.add_column(
        "conversations",
        sa.Column("organization_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_conversations_organization_id",
        "conversations",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_conversations_organization_id", "conversations", ["organization_id"]
    )

    op.add_column(
        "analyses",
        sa.Column("organization_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_analyses_organization_id",
        "analyses",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_analyses_organization_id", "analyses", ["organization_id"])

    op.add_column(
        "generated_artifacts",
        sa.Column("organization_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "generated_artifacts",
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.add_column(
        "generated_artifacts",
        sa.Column("current_version_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "generated_artifacts",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "generated_artifacts",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_generated_artifacts_organization_id",
        "generated_artifacts",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_generated_artifacts_organization_id",
        "generated_artifacts",
        ["organization_id"],
    )

    op.execute(
        sa.text(
            "UPDATE generated_artifacts SET updated_at = created_at "
            "WHERE updated_at IS NULL"
        )
    )
    op.alter_column(
        "generated_artifacts",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )

    op.create_table(
        "artifact_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("artifact_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["artifact_id"], ["generated_artifacts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "artifact_id", "version_number", name="uq_artifact_version"
        ),
    )
    op.create_index(
        "ix_artifact_versions_artifact_id", "artifact_versions", ["artifact_id"]
    )
    op.create_index(
        "ix_artifact_versions_created_by", "artifact_versions", ["created_by"]
    )

    connection = op.get_bind()
    artifacts = connection.execute(
        sa.text(
            "SELECT id, user_id, content, metadata_json, created_at "
            "FROM generated_artifacts"
        )
    ).fetchall()
    for artifact in artifacts:
        version_id = uuid.uuid4()
        content_hash = hashlib.sha256(artifact.content.encode("utf-8")).hexdigest()
        connection.execute(
            sa.text(
                "INSERT INTO artifact_versions "
                "(id, artifact_id, version_number, content, content_hash, "
                "metadata_json, created_by, created_at) "
                "VALUES (:id, :artifact_id, 1, :content, :content_hash, "
                ":metadata_json, :created_by, :created_at)"
            ),
            {
                "id": version_id,
                "artifact_id": artifact.id,
                "content": artifact.content,
                "content_hash": content_hash,
                "metadata_json": artifact.metadata_json,
                "created_by": artifact.user_id,
                "created_at": artifact.created_at,
            },
        )
        connection.execute(
            sa.text(
                "UPDATE generated_artifacts SET current_version_id = :version_id "
                "WHERE id = :artifact_id"
            ),
            {"version_id": version_id, "artifact_id": artifact.id},
        )

    op.create_foreign_key(
        "fk_artifact_current_version",
        "generated_artifacts",
        "artifact_versions",
        ["current_version_id"],
        ["id"],
        ondelete="SET NULL",
        use_alter=True,
    )

    op.create_table(
        "policy_packs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_policy_packs_organization_id", "policy_packs", ["organization_id"]
    )
    op.create_index("ix_policy_packs_is_active", "policy_packs", ["is_active"])

    op.create_table(
        "policy_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("policy_pack_id", sa.Uuid(), nullable=False),
        sa.Column("rule_key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("configuration_json", sa.JSON(), nullable=False),
        sa.Column("remediation", sa.Text(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["policy_pack_id"], ["policy_packs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_policy_rules_policy_pack_id", "policy_rules", ["policy_pack_id"]
    )
    op.create_index("ix_policy_rules_rule_key", "policy_rules", ["rule_key"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=True),
        sa.Column("request_id", sa.String(length=100), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_audit_events_organization_id", "audit_events", ["organization_id"]
    )
    op.create_index(
        "ix_audit_events_actor_user_id", "audit_events", ["actor_user_id"]
    )
    op.create_index("ix_audit_events_action", "audit_events", ["action"])
    op.create_index(
        "ix_audit_events_resource_type", "audit_events", ["resource_type"]
    )
    op.create_index("ix_audit_events_resource_id", "audit_events", ["resource_id"])
    op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"])

    op.create_table(
        "background_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("celery_task_id", sa.String(length=255), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("task_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("celery_task_id"),
    )
    op.create_index("ix_background_tasks_user_id", "background_tasks", ["user_id"])
    op.create_index(
        "ix_background_tasks_organization_id",
        "background_tasks",
        ["organization_id"],
    )
    op.create_index("ix_background_tasks_status", "background_tasks", ["status"])
    op.create_index(
        "ix_background_tasks_task_type", "background_tasks", ["task_type"]
    )
    op.create_index(
        "ix_background_tasks_created_at", "background_tasks", ["created_at"]
    )
    op.create_index(
        "ix_background_tasks_idempotency_key",
        "background_tasks",
        ["idempotency_key"],
    )


def downgrade() -> None:
    op.drop_table("background_tasks")
    op.drop_table("audit_events")
    op.drop_table("policy_rules")
    op.drop_table("policy_packs")
    op.drop_constraint(
        "fk_artifact_current_version", "generated_artifacts", type_="foreignkey"
    )
    op.drop_table("artifact_versions")
    op.drop_index(
        "ix_generated_artifacts_organization_id", table_name="generated_artifacts"
    )
    op.drop_constraint(
        "fk_generated_artifacts_organization_id",
        "generated_artifacts",
        type_="foreignkey",
    )
    op.drop_column("generated_artifacts", "deleted_at")
    op.drop_column("generated_artifacts", "updated_at")
    op.drop_column("generated_artifacts", "current_version_id")
    op.drop_column("generated_artifacts", "description")
    op.drop_column("generated_artifacts", "organization_id")
    op.drop_index("ix_analyses_organization_id", table_name="analyses")
    op.drop_constraint("fk_analyses_organization_id", "analyses", type_="foreignkey")
    op.drop_column("analyses", "organization_id")
    op.drop_index("ix_conversations_organization_id", table_name="conversations")
    op.drop_constraint(
        "fk_conversations_organization_id", "conversations", type_="foreignkey"
    )
    op.drop_column("conversations", "organization_id")
    op.drop_table("organization_members")
    op.drop_table("organizations")
