"""Configuration module for Smart File Manager.

This module provides settings management using pydantic-settings.
Environment variables are loaded and validated at startup.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Valid log levels
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        app_env: Application environment (development, staging, production).
        openrouter_api_key: OpenRouter API key for AI services (required).
        redis_url: Redis connection URL for caching.
        vision_primary_model: Primary vision model for image/video analysis.
        vision_fallback_model: Fallback model when primary fails.
        cache_ttl_seconds: Cache TTL in seconds (default: 24 hours).
        log_level: Logging level for the application.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application environment
    app_env: str = Field(default="development", description="Application environment")

    # OpenRouter API (Required)
    openrouter_api_key: SecretStr = Field(
        ...,
        description="OpenRouter API key for AI services",
    )

    # Redis configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # Vision model configuration
    vision_primary_model: str = Field(
        default="google/gemini-2.0-flash-001",
        description="Primary vision model",
    )
    vision_fallback_model: str = Field(
        default="openai/gpt-4o-mini",
        description="Fallback vision model",
    )

    # Cache configuration
    cache_ttl_seconds: int = Field(
        default=86400,
        ge=1,
        description="Cache TTL in seconds (must be positive)",
    )

    # Logging configuration
    log_level: LogLevel = Field(
        default="INFO",
        description="Logging level",
    )

    @field_validator("cache_ttl_seconds", mode="before")
    @classmethod
    def validate_cache_ttl(cls, v: int | str) -> int:
        """Validate that cache TTL is a positive integer."""
        if isinstance(v, str):
            v = int(v)
        if v < 1:
            raise ValueError("cache_ttl_seconds must be a positive integer")
        return v

    @property
    def is_development(self) -> bool:
        """Check if the application is running in development mode."""
        return self.app_env.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: The application settings.
    """
    return Settings()
