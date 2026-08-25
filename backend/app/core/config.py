from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "Job Tracker API"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/job_tracker"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
