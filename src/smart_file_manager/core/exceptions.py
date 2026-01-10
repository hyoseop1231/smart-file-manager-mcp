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
