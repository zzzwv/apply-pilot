from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "Job Tracker API"
    environment: str = "development"
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/job_tracker",
        validation_alias=AliasChoices("JOB_TRACKER_DATABASE_URL", "DATABASE_URL"),
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias=AliasChoices("JOB_TRACKER_REDIS_URL", "REDIS_URL"),
    )
    jwt_secret_key: str = Field(
        validation_alias=AliasChoices("JOB_TRACKER_JWT_SECRET_KEY", "JWT_SECRET")
    )
    frontend_origins: str = Field(
        default="http://localhost:5173",
        validation_alias=AliasChoices(
            "JOB_TRACKER_FRONTEND_ORIGINS",
            "FRONTEND_ORIGIN",
            "FRONTEND_ORIGINS",
        ),
    )
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    log_level: str = "INFO"
    kimi_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "JOB_TRACKER_KIMI_API_KEY",
            "KIMI_API_KEY",
            "MOONSHOT_API_KEY",
        ),
    )
    kimi_base_url: str = "https://api.moonshot.cn/v1"
    kimi_model: str = "kimi-k2.5"
    kimi_web_search_formula: str = "moonshot/web-search:latest"
    kimi_search_enabled: bool = True
    kimi_search_timeout_seconds: int = 8
    company_intelligence_cache_ttl_seconds: int = 86_400
    company_intelligence_rate_limit_max_requests: int = 10
    company_intelligence_rate_limit_window_seconds: int = 60

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_prefix="JOB_TRACKER_",
        extra="ignore",
    )

    @field_validator("database_url")
    @classmethod
    def use_asyncpg_database_driver(cls, value: str) -> str:
        if value.startswith("postgres://"):
            return f"postgresql+asyncpg://{value.removeprefix('postgres://')}"
        if value.startswith("postgresql://"):
            return f"postgresql+asyncpg://{value.removeprefix('postgresql://')}"
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.frontend_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
