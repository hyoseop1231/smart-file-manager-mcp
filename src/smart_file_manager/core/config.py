"""Configuration module for Smart File Manager.

This module provides settings management using pydantic-settings.
Environment variables are loaded and validated at startup.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Valid log levels
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        app_env: Application environment (development, staging, production).
        ollama_base_url: Primary Ollama server URL.
        ollama_fallback_url: Fallback Ollama server URL.
        ollama_vision_model: Vision model for image/video analysis.
        ollama_text_model: Text model for classification and generation.
        ollama_fast_model: Fast model for quick responses.
        ollama_connect_timeout: Connection timeout in seconds.
        ollama_read_timeout: Read timeout in seconds.
        ollama_total_timeout: Total request timeout in seconds.
        redis_url: Redis connection URL for caching.
        cache_ttl_seconds: Cache TTL in seconds (default: 24 hours).
        log_level: Logging level for the application.
        stt_model_size: Whisper model size for STT.
        stt_device: Device for STT inference (auto/cuda/cpu).
        stt_compute_type: Compute type for STT (auto/float16/int8).
        stt_default_language: Default language for STT (None for auto-detect).
        stt_chunk_length_seconds: Chunk length for STT processing.
        stt_enable_vad: Enable Voice Activity Detection for STT.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application environment
    app_env: str = Field(default="development", description="Application environment")

    # ==========================================================================
    # Ollama Configuration
    # ==========================================================================

    ollama_base_url: str = Field(
        default="http://192.168.0.106:11434",
        description="Primary Ollama server URL",
    )

    ollama_fallback_url: str | None = Field(
        default="http://192.168.0.107:11434",
        description="Fallback Ollama server URL",
    )

    # Ollama model configuration
    ollama_vision_model: str = Field(
        default="qwen2.5vl:7b",
        description="Vision model for image/video analysis",
    )

    ollama_text_model: str = Field(
        default="glm-4.7-flash",
        description="Text model for classification and generation",
    )

    ollama_fast_model: str = Field(
        default="qwen2.5:7b",
        description="Fast model for quick responses",
    )

    # Ollama timeout configuration
    ollama_connect_timeout: float = Field(
        default=10.0,
        ge=1.0,
        description="Connection timeout in seconds",
    )

    ollama_read_timeout: float = Field(
        default=120.0,
        ge=10.0,
        description="Read timeout in seconds",
    )

    ollama_total_timeout: float = Field(
        default=180.0,
        ge=30.0,
        description="Total request timeout in seconds",
    )

    # Legacy: OpenRouter API key (optional, for backward compatibility)
    openrouter_api_key: str | None = Field(
        default=None,
        description="OpenRouter API key (deprecated, use Ollama instead)",
    )

    # Redis configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # Vision model configuration (legacy, mapped to Ollama)
    vision_primary_model: str = Field(
        default="qwen2.5vl:7b",
        description="Primary vision model (use ollama_vision_model)",
    )
    vision_fallback_model: str = Field(
        default="qwen2.5vl:7b",
        description="Fallback vision model (use ollama_vision_model)",
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

    # ==========================================================================
    # STT (Speech-to-Text) Configuration (TAG: STT-001, SPEC-STT-001)
    # ==========================================================================

    stt_model_size: str = Field(
        default="large-v3",
        description="Whisper model size (tiny, base, small, medium, large-v3)",
    )

    stt_device: str = Field(
        default="auto",
        description="Device for STT inference (auto, cuda, cpu)",
    )

    stt_compute_type: str = Field(
        default="auto",
        description="Compute type for STT (auto, float16, int8)",
    )

    stt_default_language: str | None = Field(
        default=None,
        description="Default language for STT (None for auto-detect)",
    )

    stt_chunk_length_seconds: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Chunk length in seconds for STT processing",
    )

    stt_enable_vad: bool = Field(
        default=True,
        description="Enable Voice Activity Detection for STT",
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

    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate and normalize log level to uppercase."""
        if isinstance(v, str):
            return v.upper()
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
