from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

KNOWN_WEAK_SECRETS = frozenset(
    {
        "change-me",
        "change-me-to-a-long-random-secret",
        "change-me-to-a-long-random-pepper",
        "secret",
        "test-secret-key-123456",
        "test-secret-key-123456789012345678",
        "dev-refresh-pepper-default",
    }
)

SAFE_JWT_ALGORITHMS = frozenset({"HS256"})


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AI-Powered DevOps Assistant"
    app_env: Literal["development", "staging", "production", "test"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    secret_key: str = Field(min_length=16)
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14
    refresh_token_pepper: str = Field(
        default="dev-refresh-pepper-default",
        min_length=16,
    )
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "ai-powered-devops-assistant"
    jwt_audience: str = "ai-powered-devops-assistant-api"
    jwt_clock_skew_seconds: int = 30
    password_min_length: int = 12
    password_max_length: int = 128
    password_bcrypt_rounds: int = 12
    password_reject_common: bool = True

    email_enabled: bool = False
    email_verification_required: bool = False
    # smtp | console — console is for local/dev only; blocked in staging/production.
    email_provider: Literal["smtp", "console"] = "smtp"
    email_from_name: str = "AI-Powered DevOps Assistant"
    email_from_address: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_use_tls: bool = True
    email_request_timeout_seconds: int = 30
    email_max_retries: int = 2
    email_log_bodies: bool = False
    password_reset_token_minutes: int = 60
    email_verification_token_minutes: int = 1440
    invitation_expire_hours: int = 168
    frontend_base_url: str = "http://localhost:3000"
    # Optional alias used in deploy docs; wins over frontend_base_url when set.
    app_public_url: str = ""

    database_url: str = (
        "postgresql+asyncpg://devops:devops@localhost:5432/devops_assistant"
    )
    log_format: Literal["text", "json"] = "text"
    log_service_name: str = "api"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    celery_task_soft_time_limit_seconds: int = 540
    celery_task_time_limit_seconds: int = 600
    celery_result_expires_seconds: int = 3600
    celery_max_retries: int = 3
    background_task_retention_days: int = 30

    otel_enabled: bool = False
    otel_service_name: str = "ai-powered-devops-assistant"
    otel_exporter_otlp_endpoint: str = ""
    otel_exporter_otlp_headers: str = ""
    otel_traces_sample_ratio: float = 0.1
    otel_log_correlation: bool = True
    otel_export_timeout_seconds: int = 10

    metrics_enabled: bool = True
    metrics_require_auth: bool = False
    metrics_allowed_ips: str = ""

    provider_circuit_redis_prefix: str = "devops-assistant:circuit-breaker"
    provider_circuit_failure_threshold: int = 5
    provider_circuit_recovery_seconds: int = 60
    provider_circuit_state_ttl_seconds: int = 3600
    usage_default_daily_token_limit: int | None = None
    usage_default_monthly_token_limit: int | None = None
    usage_enforce_personal_quotas: bool = False

    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    llm_provider: str = "gemini"
    llm_timeout_seconds: int = 60
    llm_request_timeout_seconds: int = 60
    llm_max_retries: int = 3
    chat_history_limit: int = 10

    llama_api_key: str = ""
    llama_base_url: str = "https://api.llama.com/compat/v1"
    llama_model: str = "llama-3.1-8b-instruct"

    mistral_api_key: str = ""
    mistral_base_url: str = "https://api.mistral.ai/v1"
    mistral_model: str = "mistral-small-latest"

    allow_insecure_llm_http: bool = False
    allow_private_llm_networks: bool = False
    allowed_llm_hosts: str = ""

    sse_heartbeat_interval_seconds: float = 15.0

    rate_limit_enabled: bool = True
    rate_limit_auth_per_minute: int = 10
    rate_limit_api_per_minute: int = 120
    rate_limit_llm_per_minute: int = 20
    rate_limit_stream_per_minute: int = 10
    rate_limit_upload_per_minute: int = 10
    rate_limit_redis_prefix: str = "devops-assistant:rate-limit"
    rate_limit_fail_open: bool = True
    trusted_proxy_count: int = 0
    trusted_proxy_ips: str = ""

    allowed_origins: str = "http://localhost:3000,http://localhost:8000"
    max_upload_size_mb: int = 5
    max_request_body_mb: int = 10
    max_json_body_size_bytes: int = 10_485_760
    max_log_text_size_bytes: int = 5_242_880
    max_log_lines: int = 100_000
    max_filename_length: int = 255
    max_artifact_content_size_bytes: int = 1_000_000
    block_artifact_save_on_critical_policy_failure: bool = True

    docs_enabled: bool = True
    openapi_enabled: bool = True

    security_headers_enabled: bool = True
    hsts_enabled: bool = True
    hsts_max_age_seconds: int = 31_536_000
    hsts_include_subdomains: bool = True
    hsts_preload: bool = False

    @field_validator(
        "usage_default_daily_token_limit",
        "usage_default_monthly_token_limit",
        mode="before",
    )
    @classmethod
    def empty_optional_int(cls, value: object) -> object:
        if value == "" or value is None:
            return None
        return value

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """Accept managed-provider URLs (postgresql://) for async SQLAlchemy."""
        normalized = value.strip()
        if normalized.startswith("postgres://"):
            normalized = "postgresql://" + normalized.removeprefix("postgres://")
        if normalized.startswith("postgresql://"):
            normalized = "postgresql+asyncpg://" + normalized.removeprefix(
                "postgresql://"
            )
        return normalized

    @field_validator("jwt_algorithm")
    @classmethod
    def validate_jwt_algorithm(cls, value: str) -> str:
        if value not in SAFE_JWT_ALGORITHMS:
            allowed = ", ".join(sorted(SAFE_JWT_ALGORITHMS))
            raise ValueError(f"jwt_algorithm must be one of: {allowed}")
        return value

    @model_validator(mode="after")
    def validate_password_settings(self) -> Self:
        if self.password_min_length < 12:
            raise ValueError("password_min_length must be at least 12")
        if self.password_max_length < self.password_min_length:
            raise ValueError("password_max_length must be >= password_min_length")
        if self.password_bcrypt_rounds < 4:
            raise ValueError("password_bcrypt_rounds must be at least 4")
        return self

    @property
    def cors_origins(self) -> list[str]:
        return [
            item.strip() for item in self.allowed_origins.split(",") if item.strip()
        ]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_deployed_env(self) -> bool:
        return self.app_env in ("staging", "production")

    @property
    def public_frontend_url(self) -> str:
        base = self.app_public_url or self.frontend_base_url
        return base.rstrip("/")

    @property
    def effective_from_email(self) -> str:
        return (self.email_from_address or self.smtp_from_email).strip()

    @property
    def effective_llm_timeout(self) -> int:
        return self.llm_request_timeout_seconds or self.llm_timeout_seconds

    @property
    def metrics_allowed_ip_list(self) -> list[str]:
        return [
            item.strip() for item in self.metrics_allowed_ips.split(",") if item.strip()
        ]

    @property
    def trusted_proxy_ip_list(self) -> list[str]:
        return [
            item.strip() for item in self.trusted_proxy_ips.split(",") if item.strip()
        ]

    @property
    def allowed_llm_host_list(self) -> list[str]:
        return [
            item.strip().lower()
            for item in self.allowed_llm_hosts.split(",")
            if item.strip()
        ]

    @model_validator(mode="after")
    def validate_cors_in_production(self) -> Self:
        if self.is_deployed_env and "*" in self.cors_origins:
            raise ValueError(
                "CORS misconfiguration: wildcard origin is not allowed in "
                f"{self.app_env} when credentials are enabled"
            )
        return self

    def validate_production_secrets(self) -> None:
        """Validate secrets and email delivery for staging and production."""
        if not self.is_deployed_env:
            return

        secret_key_normalized = self.secret_key.strip().lower()
        if (
            len(self.secret_key) < 32
            or secret_key_normalized in KNOWN_WEAK_SECRETS
            or self.secret_key in KNOWN_WEAK_SECRETS
        ):
            raise ValueError(
                "SECRET_KEY must be at least 32 characters and not a known default "
                f"value in {self.app_env}."
            )

        pepper_normalized = self.refresh_token_pepper.strip().lower()
        if (
            len(self.refresh_token_pepper) < 32
            or pepper_normalized in KNOWN_WEAK_SECRETS
            or self.refresh_token_pepper in KNOWN_WEAK_SECRETS
        ):
            raise ValueError(
                "REFRESH_TOKEN_PEPPER must be at least 32 characters and not a known "
                f"default value in {self.app_env}."
            )

        if self.email_enabled and self.email_provider == "console":
            raise ValueError(
                "EMAIL_PROVIDER=console is not allowed in staging or production. "
                "Configure SMTP (e.g. Postmark) instead."
            )

        if self.email_enabled and self.email_provider == "smtp":
            if not self.smtp_host or not self.effective_from_email:
                raise ValueError(
                    "EMAIL_ENABLED requires SMTP_HOST and "
                    "EMAIL_FROM_ADDRESS (or SMTP_FROM_EMAIL) in staging/production."
                )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
