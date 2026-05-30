from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Work & KPI Management API"
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> "Settings":
    return Settings()


settings = get_settings()
