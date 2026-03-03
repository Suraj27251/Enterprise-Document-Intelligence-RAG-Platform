"""Application configuration and environment management."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized settings loaded from environment variables."""

    app_name: str = "Enterprise Document Intelligence Platform"
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")
    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")
    embedding_model: str = Field(default="text-embedding-3-small", validation_alias="EMBEDDING_MODEL")
    data_dir: Path = Field(default=Path("data/raw_documents"), validation_alias="DATA_DIR")
    vector_store_dir: Path = Field(default=Path("embeddings/vector_store"), validation_alias="VECTOR_STORE_DIR")
    sentry_dsn: str | None = Field(default=None, validation_alias="SENTRY_DSN")
    auth_secret_key: str = Field(default="dev-secret", validation_alias="AUTH_SECRET_KEY")
    auth_algorithm: str = Field(default="HS256", validation_alias="AUTH_ALGORITHM")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""

    return Settings()
