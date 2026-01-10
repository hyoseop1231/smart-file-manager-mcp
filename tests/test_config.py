"""Tests for configuration module.

RED Phase: These tests should fail initially as config.py is not implemented yet.
"""

import os
from unittest.mock import patch

import pytest
from pydantic import SecretStr, ValidationError


class TestSettings:
    """Test cases for Settings class."""

    def test_settings_loads_required_openrouter_api_key(self) -> None:
        """Settings should require OPENROUTER_API_KEY."""
        from smart_file_manager.core.config import Settings

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-v1-test-key"}, clear=True):
            settings = Settings()
            assert settings.openrouter_api_key is not None
            assert isinstance(settings.openrouter_api_key, SecretStr)

    def test_settings_raises_error_when_api_key_missing(self) -> None:
        """Settings should raise ValidationError when OPENROUTER_API_KEY is missing."""
        from smart_file_manager.core.config import Settings

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "openrouter_api_key" in str(exc_info.value).lower()

    def test_settings_has_default_app_env(self) -> None:
        """Settings should have default APP_ENV as 'development'."""
        from smart_file_manager.core.config import Settings

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-v1-test-key"}, clear=True):
            settings = Settings()
            assert settings.app_env == "development"

    def test_settings_has_default_redis_url(self) -> None:
        """Settings should have default REDIS_URL."""
        from smart_file_manager.core.config import Settings

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-v1-test-key"}, clear=True):
            settings = Settings()
            assert settings.redis_url == "redis://localhost:6379/0"

    def test_settings_has_default_vision_models(self) -> None:
        """Settings should have default vision model configurations."""
        from smart_file_manager.core.config import Settings

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-v1-test-key"}, clear=True):
            settings = Settings()
            assert settings.vision_primary_model == "google/gemini-2.0-flash-001"
            assert settings.vision_fallback_model == "openai/gpt-4o-mini"

    def test_settings_has_default_cache_ttl(self) -> None:
        """Settings should have default CACHE_TTL_SECONDS as 86400 (24 hours)."""
        from smart_file_manager.core.config import Settings

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-v1-test-key"}, clear=True):
            settings = Settings()
            assert settings.cache_ttl_seconds == 86400

    def test_settings_has_default_log_level(self) -> None:
        """Settings should have default LOG_LEVEL as 'INFO'."""
        from smart_file_manager.core.config import Settings

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-v1-test-key"}, clear=True):
            settings = Settings()
            assert settings.log_level == "INFO"

    def test_settings_can_override_defaults_from_env(self) -> None:
        """Settings should allow overriding defaults from environment variables."""
        from smart_file_manager.core.config import Settings

        env_vars = {
            "OPENROUTER_API_KEY": "sk-or-v1-custom-key",
            "APP_ENV": "production",
            "REDIS_URL": "redis://custom-host:6380/1",
            "VISION_PRIMARY_MODEL": "custom/model",
            "CACHE_TTL_SECONDS": "3600",
            "LOG_LEVEL": "DEBUG",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert settings.app_env == "production"
            assert settings.redis_url == "redis://custom-host:6380/1"
            assert settings.vision_primary_model == "custom/model"
            assert settings.cache_ttl_seconds == 3600
            assert settings.log_level == "DEBUG"

    def test_settings_api_key_is_secret_str(self) -> None:
        """API key should be SecretStr to prevent accidental logging."""
        from smart_file_manager.core.config import Settings

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-v1-secret"}, clear=True):
            settings = Settings()
            # SecretStr should not reveal value in string representation
            assert "sk-or-v1-secret" not in str(settings.openrouter_api_key)
            assert "sk-or-v1-secret" not in repr(settings.openrouter_api_key)
            # But should allow access via get_secret_value()
            assert settings.openrouter_api_key.get_secret_value() == "sk-or-v1-secret"

    def test_settings_cache_ttl_must_be_positive(self) -> None:
        """CACHE_TTL_SECONDS must be a positive integer."""
        from smart_file_manager.core.config import Settings

        with patch.dict(
            os.environ,
            {"OPENROUTER_API_KEY": "sk-or-v1-test", "CACHE_TTL_SECONDS": "-100"},
            clear=True,
        ):
            with pytest.raises(ValidationError):
                Settings()

    def test_settings_log_level_must_be_valid(self) -> None:
        """LOG_LEVEL must be a valid logging level."""
        from smart_file_manager.core.config import Settings

        with patch.dict(
            os.environ,
            {"OPENROUTER_API_KEY": "sk-or-v1-test", "LOG_LEVEL": "INVALID"},
            clear=True,
        ):
            with pytest.raises(ValidationError):
                Settings()


class TestGetSettings:
    """Test cases for get_settings function."""

    def test_get_settings_returns_settings_instance(self) -> None:
        """get_settings should return a Settings instance."""
        from smart_file_manager.core.config import Settings, get_settings

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-v1-test"}, clear=True):
            settings = get_settings()
            assert isinstance(settings, Settings)

    def test_get_settings_returns_cached_instance(self) -> None:
        """get_settings should return the same cached instance."""
        from smart_file_manager.core.config import get_settings

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-v1-test"}, clear=True):
            settings1 = get_settings()
            settings2 = get_settings()
            assert settings1 is settings2


class TestSettingsIsDevelopment:
    """Test cases for is_development property."""

    def test_is_development_true_for_development_env(self) -> None:
        """is_development should return True for development environment."""
        from smart_file_manager.core.config import Settings

        with patch.dict(
            os.environ,
            {"OPENROUTER_API_KEY": "sk-or-v1-test", "APP_ENV": "development"},
            clear=True,
        ):
            settings = Settings()
            assert settings.is_development is True

    def test_is_development_false_for_production_env(self) -> None:
        """is_development should return False for production environment."""
        from smart_file_manager.core.config import Settings

        with patch.dict(
            os.environ,
            {"OPENROUTER_API_KEY": "sk-or-v1-test", "APP_ENV": "production"},
            clear=True,
        ):
            settings = Settings()
            assert settings.is_development is False
