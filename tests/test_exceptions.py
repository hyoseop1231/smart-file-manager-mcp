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


# =============================================================================
# TAG-001: API Exception Classes Tests
# =============================================================================


class TestAPIError:
    """Test cases for APIError base exception."""

    def test_api_error_can_be_raised(self) -> None:
        """APIError should be raisable."""
        from smart_file_manager.core.exceptions import APIError

        with pytest.raises(APIError):
            raise APIError()

    def test_api_error_has_default_message(self) -> None:
        """APIError should have a default message."""
        from smart_file_manager.core.exceptions import APIError

        error = APIError()
        assert error.message == "API error occurred"

    def test_api_error_accepts_custom_message(self) -> None:
        """APIError should accept a custom message."""
        from smart_file_manager.core.exceptions import APIError

        error = APIError("Custom API error")
        assert error.message == "Custom API error"

    def test_api_error_inherits_from_base(self) -> None:
        """APIError should inherit from SmartFileManagerError."""
        from smart_file_manager.core.exceptions import APIError

        assert issubclass(APIError, SmartFileManagerError)


class TestAPIConnectionError:
    """Test cases for APIConnectionError."""

    def test_api_connection_error_can_be_raised(self) -> None:
        """APIConnectionError should be raisable."""
        from smart_file_manager.core.exceptions import APIConnectionError

        with pytest.raises(APIConnectionError):
            raise APIConnectionError()

    def test_api_connection_error_has_default_message(self) -> None:
        """APIConnectionError should have a default message."""
        from smart_file_manager.core.exceptions import APIConnectionError

        error = APIConnectionError()
        assert error.message == "Failed to connect to API"

    def test_api_connection_error_accepts_custom_message(self) -> None:
        """APIConnectionError should accept a custom message."""
        from smart_file_manager.core.exceptions import APIConnectionError

        error = APIConnectionError("Connection refused")
        assert error.message == "Connection refused"

    def test_api_connection_error_inherits_from_api_error(self) -> None:
        """APIConnectionError should inherit from APIError."""
        from smart_file_manager.core.exceptions import APIConnectionError, APIError

        assert issubclass(APIConnectionError, APIError)

    def test_api_connection_error_can_be_caught_as_api_error(self) -> None:
        """APIConnectionError should be catchable as APIError."""
        from smart_file_manager.core.exceptions import APIConnectionError, APIError

        with pytest.raises(APIError):
            raise APIConnectionError("Test")


class TestAPITimeoutError:
    """Test cases for APITimeoutError."""

    def test_api_timeout_error_can_be_raised(self) -> None:
        """APITimeoutError should be raisable."""
        from smart_file_manager.core.exceptions import APITimeoutError

        with pytest.raises(APITimeoutError):
            raise APITimeoutError()

    def test_api_timeout_error_has_default_message(self) -> None:
        """APITimeoutError should have a default message."""
        from smart_file_manager.core.exceptions import APITimeoutError

        error = APITimeoutError()
        assert error.message == "API request timed out"

    def test_api_timeout_error_accepts_custom_message(self) -> None:
        """APITimeoutError should accept a custom message."""
        from smart_file_manager.core.exceptions import APITimeoutError

        error = APITimeoutError("Request timed out after 30s")
        assert error.message == "Request timed out after 30s"

    def test_api_timeout_error_inherits_from_api_error(self) -> None:
        """APITimeoutError should inherit from APIError."""
        from smart_file_manager.core.exceptions import APIError, APITimeoutError

        assert issubclass(APITimeoutError, APIError)


class TestAPIResponseError:
    """Test cases for APIResponseError."""

    def test_api_response_error_can_be_raised(self) -> None:
        """APIResponseError should be raisable."""
        from smart_file_manager.core.exceptions import APIResponseError

        with pytest.raises(APIResponseError):
            raise APIResponseError()

    def test_api_response_error_has_default_message(self) -> None:
        """APIResponseError should have a default message."""
        from smart_file_manager.core.exceptions import APIResponseError

        error = APIResponseError()
        assert error.message == "Invalid API response"

    def test_api_response_error_accepts_custom_message_and_status_code(self) -> None:
        """APIResponseError should accept custom message and status code."""
        from smart_file_manager.core.exceptions import APIResponseError

        error = APIResponseError("Bad gateway", status_code=502)
        assert error.message == "Bad gateway"
        assert error.status_code == 502

    def test_api_response_error_inherits_from_api_error(self) -> None:
        """APIResponseError should inherit from APIError."""
        from smart_file_manager.core.exceptions import APIError, APIResponseError

        assert issubclass(APIResponseError, APIError)

    def test_api_response_error_status_code_defaults_to_none(self) -> None:
        """APIResponseError status_code should default to None."""
        from smart_file_manager.core.exceptions import APIResponseError

        error = APIResponseError()
        assert error.status_code is None


class TestRateLimitError:
    """Test cases for RateLimitError."""

    def test_rate_limit_error_can_be_raised(self) -> None:
        """RateLimitError should be raisable."""
        from smart_file_manager.core.exceptions import RateLimitError

        with pytest.raises(RateLimitError):
            raise RateLimitError()

    def test_rate_limit_error_has_default_message(self) -> None:
        """RateLimitError should have a default message."""
        from smart_file_manager.core.exceptions import RateLimitError

        error = RateLimitError()
        assert error.message == "API rate limit exceeded"

    def test_rate_limit_error_accepts_retry_after(self) -> None:
        """RateLimitError should accept retry_after parameter."""
        from smart_file_manager.core.exceptions import RateLimitError

        error = RateLimitError("Rate limited", retry_after=60)
        assert error.message == "Rate limited"
        assert error.retry_after == 60

    def test_rate_limit_error_inherits_from_api_error(self) -> None:
        """RateLimitError should inherit from APIError."""
        from smart_file_manager.core.exceptions import APIError, RateLimitError

        assert issubclass(RateLimitError, APIError)

    def test_rate_limit_error_retry_after_defaults_to_none(self) -> None:
        """RateLimitError retry_after should default to None."""
        from smart_file_manager.core.exceptions import RateLimitError

        error = RateLimitError()
        assert error.retry_after is None


class TestBudgetExceededError:
    """Test cases for BudgetExceededError."""

    def test_budget_exceeded_error_can_be_raised(self) -> None:
        """BudgetExceededError should be raisable."""
        from smart_file_manager.core.exceptions import BudgetExceededError

        with pytest.raises(BudgetExceededError):
            raise BudgetExceededError()

    def test_budget_exceeded_error_has_default_message(self) -> None:
        """BudgetExceededError should have a default message."""
        from smart_file_manager.core.exceptions import BudgetExceededError

        error = BudgetExceededError()
        assert error.message == "Budget limit exceeded"

    def test_budget_exceeded_error_accepts_budget_info(self) -> None:
        """BudgetExceededError should accept budget information."""
        from smart_file_manager.core.exceptions import BudgetExceededError

        error = BudgetExceededError(
            "Daily limit exceeded",
            budget_type="daily",
            limit=1.0,
            current=1.25,
        )
        assert error.message == "Daily limit exceeded"
        assert error.budget_type == "daily"
        assert error.limit == 1.0
        assert error.current == 1.25

    def test_budget_exceeded_error_inherits_from_api_error(self) -> None:
        """BudgetExceededError should inherit from APIError."""
        from smart_file_manager.core.exceptions import APIError, BudgetExceededError

        assert issubclass(BudgetExceededError, APIError)

    def test_budget_exceeded_error_defaults(self) -> None:
        """BudgetExceededError should have sensible defaults."""
        from smart_file_manager.core.exceptions import BudgetExceededError

        error = BudgetExceededError()
        assert error.budget_type is None
        assert error.limit is None
        assert error.current is None


class TestModelUnavailableError:
    """Test cases for ModelUnavailableError."""

    def test_model_unavailable_error_can_be_raised(self) -> None:
        """ModelUnavailableError should be raisable."""
        from smart_file_manager.core.exceptions import ModelUnavailableError

        with pytest.raises(ModelUnavailableError):
            raise ModelUnavailableError()

    def test_model_unavailable_error_has_default_message(self) -> None:
        """ModelUnavailableError should have a default message."""
        from smart_file_manager.core.exceptions import ModelUnavailableError

        error = ModelUnavailableError()
        assert error.message == "Model is unavailable"

    def test_model_unavailable_error_accepts_model_id(self) -> None:
        """ModelUnavailableError should accept model_id parameter."""
        from smart_file_manager.core.exceptions import ModelUnavailableError

        error = ModelUnavailableError("Model offline", model_id="openai/gpt-4")
        assert error.message == "Model offline"
        assert error.model_id == "openai/gpt-4"

    def test_model_unavailable_error_inherits_from_api_error(self) -> None:
        """ModelUnavailableError should inherit from APIError."""
        from smart_file_manager.core.exceptions import APIError, ModelUnavailableError

        assert issubclass(ModelUnavailableError, APIError)

    def test_model_unavailable_error_model_id_defaults_to_none(self) -> None:
        """ModelUnavailableError model_id should default to None."""
        from smart_file_manager.core.exceptions import ModelUnavailableError

        error = ModelUnavailableError()
        assert error.model_id is None
