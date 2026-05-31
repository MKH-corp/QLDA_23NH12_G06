from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Work & KPI Management API"
    app_environment: str = "development"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/work_kpi_db"
    jwt_secret_key: str = "change-this-secret-in-env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    business_timezone: str = "Asia/Ho_Chi_Minh"
    notification_scheduler_enabled: bool = True
    notification_scheduler_interval_seconds: int = 300
    openai_chat_enabled: bool = True
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.4-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_timeout_seconds: float = 20
    openai_max_output_tokens: int = 500
    cors_allow_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5174,http://127.0.0.1:5174"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.app_environment.lower() in {"production", "prod"} and self.jwt_secret_key == "change-this-secret-in-env":
            raise ValueError("JWT_SECRET_KEY must be configured for production")
        return self


@lru_cache
def get_settings() -> "Settings":
    return Settings()


settings = get_settings()
