"""pipeline and shell routing seeds

Revision ID: 010_pipeline_shell_routing
Revises: 009_onboarding
Create Date: 2026-07-17 21:00:00.000000

"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010_pipeline_shell_routing"
down_revision: Union[str, None] = "009_onboarding"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_ROUTING = [
    ("pipeline_generation", "gemini", ["llama", "mistral"]),
    ("shell_command", "gemini", ["llama", "mistral"]),
]


def upgrade() -> None:
    connection = op.get_bind()
    existing = connection.execute(
        sa.text(
            "SELECT operation FROM provider_routing_policies "
            "WHERE organization_id IS NULL "
            "AND operation IN ('pipeline_generation', 'shell_command')"
        )
    ).fetchall()
    existing_ops = {row[0] for row in existing}

    routing_policies = sa.table(
        "provider_routing_policies",
        sa.column("id", sa.Uuid()),
        sa.column("organization_id", sa.Uuid()),
        sa.column("operation", sa.String()),
        sa.column("primary_provider", sa.String()),
        sa.column("fallback_providers", sa.JSON()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    now = datetime.now(UTC)
    rows = [
        {
            "id": str(uuid.uuid4()),
            "organization_id": None,
            "operation": operation,
            "primary_provider": primary,
            "fallback_providers": fallbacks,
            "created_at": now,
            "updated_at": now,
        }
        for operation, primary, fallbacks in NEW_ROUTING
        if operation not in existing_ops
    ]
    if rows:
        op.bulk_insert(routing_policies, rows)


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM provider_routing_policies "
            "WHERE organization_id IS NULL "
            "AND operation IN ('pipeline_generation', 'shell_command')"
        )
    )
