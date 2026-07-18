"""provider routing

Revision ID: 006_provider_routing
Revises: 005_organization_invitations
Create Date: 2026-07-17 20:00:00.000000

"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_provider_routing"
down_revision: Union[str, None] = "005_organization_invitations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_PROVIDERS = [
    {
        "id": str(uuid.uuid4()),
        "provider_name": "gemini",
        "enabled": True,
        "default_model": "gemini-1.5-flash",
        "timeout_seconds": 60,
        "max_retries": 3,
        "priority": 10,
        "max_output_tokens": 4096,
        "secret_env_key": "GEMINI_API_KEY",
        "base_url_env_key": None,
        "model_env_key": "GEMINI_MODEL",
    },
    {
        "id": str(uuid.uuid4()),
        "provider_name": "llama",
        "enabled": True,
        "default_model": "llama-3.1-8b-instruct",
        "timeout_seconds": 60,
        "max_retries": 3,
        "priority": 20,
        "max_output_tokens": 4096,
        "secret_env_key": "LLAMA_API_KEY",
        "base_url_env_key": "LLAMA_BASE_URL",
        "model_env_key": "LLAMA_MODEL",
    },
    {
        "id": str(uuid.uuid4()),
        "provider_name": "mistral",
        "enabled": True,
        "default_model": "mistral-small-latest",
        "timeout_seconds": 60,
        "max_retries": 3,
        "priority": 30,
        "max_output_tokens": 4096,
        "secret_env_key": "MISTRAL_API_KEY",
        "base_url_env_key": "MISTRAL_BASE_URL",
        "model_env_key": "MISTRAL_MODEL",
    },
]

DEFAULT_ROUTING = [
    ("chat", "gemini", ["llama", "mistral"]),
    ("log_analysis", "gemini", ["llama", "mistral"]),
    ("configuration_review", "gemini", ["llama", "mistral"]),
    ("dockerfile_generation", "gemini", ["llama", "mistral"]),
    ("kubernetes", "gemini", ["llama", "mistral"]),
    ("pipeline_generation", "gemini", ["llama", "mistral"]),
    ("shell_command", "gemini", ["llama", "mistral"]),
]


def upgrade() -> None:
    op.create_table(
        "provider_configs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("provider_name", sa.String(length=50), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("default_model", sa.String(length=120), nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("max_output_tokens", sa.Integer(), nullable=False),
        sa.Column("secret_env_key", sa.String(length=120), nullable=False),
        sa.Column("base_url_env_key", sa.String(length=120), nullable=True),
        sa.Column("model_env_key", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "provider_name",
            name="uq_provider_config_org_provider",
        ),
    )
    op.create_index(
        "ix_provider_configs_organization_id",
        "provider_configs",
        ["organization_id"],
    )
    op.create_index(
        "ix_provider_configs_provider_name",
        "provider_configs",
        ["provider_name"],
    )

    op.create_table(
        "provider_routing_policies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("operation", sa.String(length=50), nullable=False),
        sa.Column("primary_provider", sa.String(length=50), nullable=False),
        sa.Column("fallback_providers", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "operation",
            name="uq_provider_routing_org_operation",
        ),
    )
    op.create_index(
        "ix_provider_routing_policies_organization_id",
        "provider_routing_policies",
        ["organization_id"],
    )
    op.create_index(
        "ix_provider_routing_policies_operation",
        "provider_routing_policies",
        ["operation"],
    )

    provider_configs = sa.table(
        "provider_configs",
        sa.column("id", sa.Uuid()),
        sa.column("organization_id", sa.Uuid()),
        sa.column("provider_name", sa.String()),
        sa.column("enabled", sa.Boolean()),
        sa.column("default_model", sa.String()),
        sa.column("timeout_seconds", sa.Integer()),
        sa.column("max_retries", sa.Integer()),
        sa.column("priority", sa.Integer()),
        sa.column("max_output_tokens", sa.Integer()),
        sa.column("secret_env_key", sa.String()),
        sa.column("base_url_env_key", sa.String()),
        sa.column("model_env_key", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    now = datetime.now(UTC)
    op.bulk_insert(
        provider_configs,
        [
            {
                **row,
                "organization_id": None,
                "created_at": now,
                "updated_at": now,
            }
            for row in DEFAULT_PROVIDERS
        ],
    )

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
    op.bulk_insert(
        routing_policies,
        [
            {
                "id": str(uuid.uuid4()),
                "organization_id": None,
                "operation": operation,
                "primary_provider": primary,
                "fallback_providers": fallbacks,
                "created_at": now,
                "updated_at": now,
            }
            for operation, primary, fallbacks in DEFAULT_ROUTING
        ],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_provider_routing_policies_operation",
        table_name="provider_routing_policies",
    )
    op.drop_index(
        "ix_provider_routing_policies_organization_id",
        table_name="provider_routing_policies",
    )
    op.drop_table("provider_routing_policies")
    op.drop_index("ix_provider_configs_provider_name", table_name="provider_configs")
    op.drop_index("ix_provider_configs_organization_id", table_name="provider_configs")
    op.drop_table("provider_configs")
