from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LLMOperation(str, enum.Enum):
    CHAT = "chat"
    LOG_ANALYSIS = "log_analysis"
    CONFIGURATION_REVIEW = "configuration_review"
    DOCKERFILE_GENERATION = "dockerfile_generation"
    KUBERNETES = "kubernetes"
    PIPELINE_GENERATION = "pipeline_generation"
    SHELL_COMMAND = "shell_command"


class ProviderConfig(Base):
    __tablename__ = "provider_configs"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "provider_name",
            name="uq_provider_config_org_provider",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    provider_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    default_model: Mapped[str] = mapped_column(String(120), nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    max_output_tokens: Mapped[int] = mapped_column(
        Integer, default=4096, nullable=False
    )
    secret_env_key: Mapped[str] = mapped_column(String(120), nullable=False)
    base_url_env_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    model_env_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class ProviderRoutingPolicy(Base):
    __tablename__ = "provider_routing_policies"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "operation",
            name="uq_provider_routing_org_operation",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    operation: Mapped[LLMOperation] = mapped_column(
        Enum(
            LLMOperation,
            name="llm_operation",
            values_callable=lambda x: [e.value for e in x],
            native_enum=False,
        ),
        nullable=False,
        index=True,
    )
    primary_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    fallback_providers: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
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
