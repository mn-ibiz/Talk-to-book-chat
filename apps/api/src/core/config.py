"""Application configuration management."""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

# Project root is 3 levels up from this file: src/core/config.py
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Database
    database_url: str = Field(
        default="sqlite:///./test.db",
        alias="DATABASE_URL"
    )

    # JWT Authentication
    jwt_secret_key: str = Field(
        default="test-secret-key-change-in-production",
        alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(
        default=60,
        alias="JWT_EXPIRATION_MINUTES"
    )

    # LLM
    anthropic_api_key: str = Field(
        default="",
        alias="ANTHROPIC_API_KEY"
    )

    class Config:
        """Pydantic configuration."""
        env_file = str(PROJECT_ROOT / ".env")
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()
