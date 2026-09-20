"""Konfigurasi ai-service menggunakan pydantic-settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pengaturan aplikasi dibaca dari environment variables atau file .env."""

    ai_service_api_key: str = "dev-ai-service-key"
    ai_service_port: int = 8001
    ai_service_env: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Mengembalikan instance singleton Settings."""
    return Settings()
