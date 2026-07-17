from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    jwt_algorithm: str = "HS256"

    database_url: str = (
        "postgresql+asyncpg://devops:devops@localhost:5432/devops_assistant"
    )
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    llm_provider: str = "gemini"
    llm_timeout_seconds: int = 60
    chat_history_limit: int = 10

    allowed_origins: str = "http://localhost:3000,http://localhost:8000"
    max_upload_size_mb: int = 5
    max_request_body_mb: int = 10

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


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
