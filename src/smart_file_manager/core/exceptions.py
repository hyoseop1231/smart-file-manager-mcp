"""Custom exceptions for Smart File Manager.

This module defines the exception hierarchy for the application.
All custom exceptions inherit from SmartFileManagerError.
"""


class SmartFileManagerError(Exception):
    """Base exception for Smart File Manager.

    All custom exceptions in this application should inherit from this class.
    """

    def __init__(self, message: str = "An error occurred in Smart File Manager") -> None:
        """Initialize the exception with a message.

        Args:
            message: The error message.
        """
        self.message = message
        super().__init__(self.message)


class ConfigurationError(SmartFileManagerError):
    """Exception raised for configuration errors.

    This exception is raised when there is an issue with the application
    configuration, such as missing or invalid environment variables.
    """

    def __init__(self, message: str = "Configuration error") -> None:
        """Initialize the exception with a message.

        Args:
            message: The error message describing the configuration issue.
        """
        super().__init__(message)


class CacheError(SmartFileManagerError):
    """Base exception for cache-related errors.

    This exception is raised when there is a general cache error.
    """

    def __init__(self, message: str = "Cache error") -> None:
        """Initialize the exception with a message.

        Args:
            message: The error message describing the cache issue.
        """
        super().__init__(message)


class CacheConnectionError(CacheError):
    """Exception raised when cache connection fails.

    This exception is raised when the application cannot connect
    to the cache backend (e.g., Redis).
    """

    def __init__(self, message: str = "Failed to connect to cache") -> None:
        """Initialize the exception with a message.

        Args:
            message: The error message describing the connection issue.
        """
        super().__init__(message)


# =============================================================================
# API Exception Classes (TAG-001: SPEC-API-001)
# =============================================================================


class APIError(SmartFileManagerError):
    """Base exception for API-related errors.

    This exception is raised when there is a general API error.
    All API-specific exceptions should inherit from this class.
    """

    def __init__(self, message: str = "API error occurred") -> None:
        """Initialize the exception with a message.

        Args:
            message: The error message describing the API issue.
        """
        super().__init__(message)


class APIConnectionError(APIError):
    """Exception raised when API connection fails.

    This exception is raised when the application cannot connect
    to an external API (e.g., OpenRouter).
    """

    def __init__(self, message: str = "Failed to connect to API") -> None:
        """Initialize the exception with a message.

        Args:
            message: The error message describing the connection issue.
        """
        super().__init__(message)


class APITimeoutError(APIError):
    """Exception raised when API request times out.

    This exception is raised when an API request exceeds the
    configured timeout duration.
    """

    def __init__(self, message: str = "API request timed out") -> None:
        """Initialize the exception with a message.

        Args:
            message: The error message describing the timeout issue.
        """
        super().__init__(message)


class APIResponseError(APIError):
    """Exception raised when API returns an invalid response.

    This exception is raised when the API response cannot be parsed
    or contains unexpected data.
    """

    def __init__(
        self,
        message: str = "Invalid API response",
        status_code: int | None = None,
    ) -> None:
        """Initialize the exception with a message and optional status code.

        Args:
            message: The error message describing the response issue.
            status_code: The HTTP status code from the API response.
        """
        self.status_code = status_code
        super().__init__(message)


class RateLimitError(APIError):
    """Exception raised when API rate limit is exceeded.

    This exception is raised when the API returns a 429 status code
    indicating too many requests.
    """

    def __init__(
        self,
        message: str = "API rate limit exceeded",
        retry_after: int | None = None,
    ) -> None:
        """Initialize the exception with a message and optional retry delay.

        Args:
            message: The error message describing the rate limit issue.
            retry_after: The number of seconds to wait before retrying.
        """
        self.retry_after = retry_after
        super().__init__(message)


class BudgetExceededError(APIError):
    """Exception raised when budget limit is exceeded.

    This exception is raised when the daily or monthly API cost
    budget has been exceeded.
    """

    def __init__(
        self,
        message: str = "Budget limit exceeded",
        budget_type: str | None = None,
        limit: float | None = None,
        current: float | None = None,
    ) -> None:
        """Initialize the exception with budget information.

        Args:
            message: The error message describing the budget issue.
            budget_type: The type of budget exceeded (daily, monthly).
            limit: The budget limit that was exceeded.
            current: The current spending amount.
        """
        self.budget_type = budget_type
        self.limit = limit
        self.current = current
        super().__init__(message)


class ModelUnavailableError(APIError):
    """Exception raised when a model is unavailable.

    This exception is raised when the requested AI model
    is offline, deprecated, or otherwise unavailable.
    """

    def __init__(
        self,
        message: str = "Model is unavailable",
        model_id: str | None = None,
    ) -> None:
        """Initialize the exception with model information.

        Args:
            message: The error message describing the availability issue.
            model_id: The identifier of the unavailable model.
        """
        self.model_id = model_id
        super().__init__(message)
