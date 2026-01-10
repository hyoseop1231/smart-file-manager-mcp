"""Tests for custom exceptions module."""

import pytest

from smart_file_manager.core.exceptions import (
    CacheConnectionError,
    CacheError,
    ConfigurationError,
    SmartFileManagerError,
)


class TestSmartFileManagerError:
    """Test cases for SmartFileManagerError base exception."""

    def test_base_exception_can_be_raised(self) -> None:
        """SmartFileManagerError should be raisable."""
        with pytest.raises(SmartFileManagerError):
            raise SmartFileManagerError()

    def test_base_exception_has_default_message(self) -> None:
        """SmartFileManagerError should have a default message."""
        error = SmartFileManagerError()
        assert error.message == "An error occurred in Smart File Manager"
        assert str(error) == "An error occurred in Smart File Manager"

    def test_base_exception_accepts_custom_message(self) -> None:
        """SmartFileManagerError should accept a custom message."""
        error = SmartFileManagerError("Custom error message")
        assert error.message == "Custom error message"
        assert str(error) == "Custom error message"

    def test_base_exception_inherits_from_exception(self) -> None:
        """SmartFileManagerError should inherit from Exception."""
        assert issubclass(SmartFileManagerError, Exception)


class TestConfigurationError:
    """Test cases for ConfigurationError."""

    def test_configuration_error_can_be_raised(self) -> None:
        """ConfigurationError should be raisable."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError()

    def test_configuration_error_has_default_message(self) -> None:
        """ConfigurationError should have a default message."""
        error = ConfigurationError()
        assert error.message == "Configuration error"

    def test_configuration_error_accepts_custom_message(self) -> None:
        """ConfigurationError should accept a custom message."""
        error = ConfigurationError("Missing API key")
        assert error.message == "Missing API key"

    def test_configuration_error_inherits_from_base(self) -> None:
        """ConfigurationError should inherit from SmartFileManagerError."""
        assert issubclass(ConfigurationError, SmartFileManagerError)

    def test_configuration_error_can_be_caught_as_base(self) -> None:
        """ConfigurationError should be catchable as SmartFileManagerError."""
        with pytest.raises(SmartFileManagerError):
            raise ConfigurationError("Test")


class TestCacheError:
    """Test cases for CacheError."""

    def test_cache_error_can_be_raised(self) -> None:
        """CacheError should be raisable."""
        with pytest.raises(CacheError):
            raise CacheError()

    def test_cache_error_has_default_message(self) -> None:
        """CacheError should have a default message."""
        error = CacheError()
        assert error.message == "Cache error"

    def test_cache_error_accepts_custom_message(self) -> None:
        """CacheError should accept a custom message."""
        error = CacheError("Cache write failed")
        assert error.message == "Cache write failed"

    def test_cache_error_inherits_from_base(self) -> None:
        """CacheError should inherit from SmartFileManagerError."""
        assert issubclass(CacheError, SmartFileManagerError)


class TestCacheConnectionError:
    """Test cases for CacheConnectionError."""

    def test_cache_connection_error_can_be_raised(self) -> None:
        """CacheConnectionError should be raisable."""
        with pytest.raises(CacheConnectionError):
            raise CacheConnectionError()

    def test_cache_connection_error_has_default_message(self) -> None:
        """CacheConnectionError should have a default message."""
        error = CacheConnectionError()
        assert error.message == "Failed to connect to cache"

    def test_cache_connection_error_accepts_custom_message(self) -> None:
        """CacheConnectionError should accept a custom message."""
        error = CacheConnectionError("Redis connection refused")
        assert error.message == "Redis connection refused"

    def test_cache_connection_error_inherits_from_cache_error(self) -> None:
        """CacheConnectionError should inherit from CacheError."""
        assert issubclass(CacheConnectionError, CacheError)

    def test_cache_connection_error_can_be_caught_as_cache_error(self) -> None:
        """CacheConnectionError should be catchable as CacheError."""
        with pytest.raises(CacheError):
            raise CacheConnectionError("Test")

    def test_cache_connection_error_can_be_caught_as_base(self) -> None:
        """CacheConnectionError should be catchable as SmartFileManagerError."""
        with pytest.raises(SmartFileManagerError):
            raise CacheConnectionError("Test")
