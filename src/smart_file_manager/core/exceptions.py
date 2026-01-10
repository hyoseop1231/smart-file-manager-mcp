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


# =============================================================================
# Vision Exception Classes (TAG: VIS-M1-01, SPEC-VISION-001)
# =============================================================================


class VisionError(SmartFileManagerError):
    """Base exception for Vision analysis errors.

    This exception is raised when there is a general vision analysis error.
    All vision-specific exceptions should inherit from this class.
    """

    def __init__(self, message: str = "Vision analysis error") -> None:
        """Initialize the exception with a message.

        Args:
            message: The error message describing the vision issue.
        """
        super().__init__(message)


class ImageProcessingError(VisionError):
    """Exception raised when image processing fails.

    This exception is raised when an image cannot be processed
    due to format issues, size limits, or processing errors.
    """

    def __init__(
        self,
        message: str = "Image processing error",
        image_path: str | None = None,
    ) -> None:
        """Initialize the exception with image information.

        Args:
            message: The error message describing the processing issue.
            image_path: The path to the image that failed processing.
        """
        self.image_path = image_path
        super().__init__(message)


class VideoProcessingError(VisionError):
    """Exception raised when video processing fails.

    This exception is raised when a video cannot be processed
    due to format issues, codec problems, or processing errors.
    """

    def __init__(
        self,
        message: str = "Video processing error",
        video_path: str | None = None,
    ) -> None:
        """Initialize the exception with video information.

        Args:
            message: The error message describing the processing issue.
            video_path: The path to the video that failed processing.
        """
        self.video_path = video_path
        super().__init__(message)


class UnsupportedFormatError(VisionError):
    """Exception raised when file format is not supported.

    This exception is raised when the input file format is not
    in the list of supported formats for vision analysis.
    """

    def __init__(
        self,
        message: str = "Unsupported file format",
        format: str | None = None,
        supported_formats: list[str] | None = None,
    ) -> None:
        """Initialize the exception with format information.

        Args:
            message: The error message describing the format issue.
            format: The unsupported format that was encountered.
            supported_formats: List of formats that are supported.
        """
        self.format = format
        self.supported_formats = supported_formats
        super().__init__(message)


class CorruptedFileError(VisionError):
    """Exception raised when file is corrupted or cannot be decoded.

    This exception is raised when a file cannot be opened or decoded
    due to corruption or invalid data.
    """

    def __init__(
        self,
        message: str = "File is corrupted or cannot be decoded",
        file_path: str | None = None,
    ) -> None:
        """Initialize the exception with file information.

        Args:
            message: The error message describing the corruption issue.
            file_path: The path to the corrupted file.
        """
        self.file_path = file_path
        super().__init__(message)


class DependencyError(VisionError):
    """Exception raised when a required dependency is not available.

    This exception is raised when a system dependency (e.g., FFmpeg)
    is required but not installed or accessible.
    """

    def __init__(
        self,
        message: str = "Required dependency not available",
        dependency_name: str | None = None,
    ) -> None:
        """Initialize the exception with dependency information.

        Args:
            message: The error message describing the dependency issue.
            dependency_name: The name of the missing dependency.
        """
        self.dependency_name = dependency_name
        super().__init__(message)


class AnalysisFailedError(VisionError):
    """Exception raised when analysis fails after all fallbacks.

    This exception is raised when vision analysis fails even after
    trying all available fallback options.
    """

    def __init__(
        self,
        message: str = "Analysis failed after all fallbacks",
        attempts: int | None = None,
        last_error: Exception | None = None,
    ) -> None:
        """Initialize the exception with analysis failure information.

        Args:
            message: The error message describing the failure.
            attempts: Number of attempts made before failure.
            last_error: The last error that occurred during attempts.
        """
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(message)
