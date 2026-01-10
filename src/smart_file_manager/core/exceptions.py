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


# =============================================================================
# Classification Exception Classes (TAG: CLASS-001, SPEC-CLASS-001)
# =============================================================================


class ClassificationError(SmartFileManagerError):
    """Base exception for classification-related errors.

    This exception is raised when there is a general classification error.
    All classification-specific exceptions should inherit from this class.
    """

    def __init__(self, message: str = "Classification error") -> None:
        """Initialize the exception with a message.

        Args:
            message: The error message describing the classification issue.
        """
        super().__init__(message)


class CategoryNotFoundError(ClassificationError):
    """Exception raised when a category is not found.

    This exception is raised when the requested category does not exist
    in the CategoryRegistry.
    """

    def __init__(
        self,
        message: str = "Category not found",
        category_id: str | None = None,
    ) -> None:
        """Initialize the exception with category information.

        Args:
            message: The error message describing the issue.
            category_id: The identifier of the category that was not found.
        """
        self.category_id = category_id
        if category_id:
            message = f"Category not found: {category_id}"
        super().__init__(message)


class InvalidCategoryNameError(ClassificationError):
    """Exception raised when a category name is invalid.

    This exception is raised when the category name contains invalid
    characters or violates naming rules.
    """

    def __init__(
        self,
        message: str = "Invalid category name",
        category_id: str | None = None,
    ) -> None:
        """Initialize the exception with category information.

        Args:
            message: The error message describing the issue.
            category_id: The invalid category identifier.
        """
        self.category_id = category_id
        super().__init__(message)


class ClassificationFailedError(ClassificationError):
    """Exception raised when classification fails.

    This exception is raised when file classification fails
    after trying all available methods.
    """

    def __init__(
        self,
        message: str = "Classification failed",
        file_path: str | None = None,
    ) -> None:
        """Initialize the exception with file information.

        Args:
            message: The error message describing the failure.
            file_path: The path to the file that failed classification.
        """
        self.file_path = file_path
        super().__init__(message)


class OrganizationPlanError(ClassificationError):
    """Exception raised when organization plan generation fails.

    This exception is raised when the system cannot generate
    a valid organization plan for a file.
    """

    def __init__(
        self,
        message: str = "Organization plan generation failed",
        file_path: str | None = None,
    ) -> None:
        """Initialize the exception with file information.

        Args:
            message: The error message describing the failure.
            file_path: The path to the file that failed plan generation.
        """
        self.file_path = file_path
        super().__init__(message)


# =============================================================================
# STT Exception Classes (TAG: STT-001, SPEC-STT-001)
# =============================================================================


class STTError(SmartFileManagerError):
    """Base exception for STT (Speech-to-Text) errors.

    This exception is raised when there is a general STT error.
    All STT-specific exceptions should inherit from this class.
    """

    def __init__(self, message: str = "STT error occurred") -> None:
        """Initialize the exception with a message.

        Args:
            message: The error message describing the STT issue.
        """
        super().__init__(message)


class UnsupportedAudioFormatError(STTError):
    """Exception raised when audio format is not supported.

    This exception is raised when the input audio file format is not
    in the list of supported formats for STT processing.
    """

    def __init__(
        self,
        message: str = "Unsupported audio format",
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
        self.supported_formats = supported_formats or []
        super().__init__(message)


class AudioProcessingError(STTError):
    """Exception raised when audio processing fails.

    This exception is raised when an audio file cannot be processed
    due to corruption, encoding issues, or other processing errors.
    """

    def __init__(
        self,
        message: str = "Audio processing error",
        audio_path: str | None = None,
    ) -> None:
        """Initialize the exception with audio information.

        Args:
            message: The error message describing the processing issue.
            audio_path: The path to the audio file that failed processing.
        """
        self.audio_path = audio_path
        super().__init__(message)


class ModelLoadError(STTError):
    """Exception raised when STT model fails to load.

    This exception is raised when the Faster-Whisper model
    cannot be loaded due to missing files, memory issues, etc.
    """

    def __init__(
        self,
        message: str = "Failed to load STT model",
        model_name: str | None = None,
    ) -> None:
        """Initialize the exception with model information.

        Args:
            message: The error message describing the load failure.
            model_name: The name of the model that failed to load.
        """
        self.model_name = model_name
        super().__init__(message)


class TranscriptionError(STTError):
    """Exception raised when transcription fails.

    This exception is raised when the STT transcription process
    fails after the model has been loaded.
    """

    def __init__(
        self,
        message: str = "Transcription failed",
        audio_path: str | None = None,
        reason: str | None = None,
    ) -> None:
        """Initialize the exception with transcription failure information.

        Args:
            message: The error message describing the failure.
            audio_path: The path to the audio file that failed transcription.
            reason: The reason for the transcription failure.
        """
        self.audio_path = audio_path
        self.reason = reason
        super().__init__(message)


class AudioTooLongError(STTError):
    """Exception raised when audio exceeds maximum duration (REQ-N-001).

    This exception is raised when the audio file duration exceeds
    the configured maximum (default: 2 hours / 7200 seconds).
    """

    def __init__(
        self,
        message: str = "Audio file exceeds maximum duration",
        duration_seconds: float | None = None,
        max_duration_seconds: float | None = None,
    ) -> None:
        """Initialize the exception with duration information.

        Args:
            message: The error message describing the duration issue.
            duration_seconds: The actual duration of the audio file.
            max_duration_seconds: The maximum allowed duration.
        """
        self.duration_seconds = duration_seconds
        self.max_duration_seconds = max_duration_seconds
        super().__init__(message)


class FileTooLargeError(STTError):
    """Exception raised when file size exceeds maximum limit (REQ-N-002).

    This exception is raised when the audio file size exceeds
    the configured maximum (default: 100MB).
    """

    def __init__(
        self,
        message: str = "File size exceeds maximum limit",
        file_size_bytes: int | None = None,
        max_size_bytes: int | None = None,
    ) -> None:
        """Initialize the exception with size information.

        Args:
            message: The error message describing the size issue.
            file_size_bytes: The actual size of the file in bytes.
            max_size_bytes: The maximum allowed size in bytes.
        """
        self.file_size_bytes = file_size_bytes
        self.max_size_bytes = max_size_bytes
        super().__init__(message)


# =============================================================================
# Organization Exception Classes (TAG: ORG-001, SPEC-ORG-001)
# =============================================================================


class OrganizationError(SmartFileManagerError):
    """Base exception for file organization errors.

    This exception is raised when there is a general organization error.
    All organization-specific exceptions should inherit from this class.
    """

    def __init__(self, message: str = "Organization error occurred") -> None:
        """Initialize the exception with a message.

        Args:
            message: The error message describing the organization issue.
        """
        super().__init__(message)


class SafetyValidationError(OrganizationError):
    """Exception raised when safety validation fails.

    This exception is raised when a safety check fails, such as
    attempting to modify protected paths, insufficient disk space,
    or missing permissions.
    """

    def __init__(
        self,
        message: str = "Safety validation failed",
        validation_type: str | None = None,
        details: str | None = None,
    ) -> None:
        """Initialize the exception with validation information.

        Args:
            message: The error message describing the validation failure.
            validation_type: Type of validation that failed
                (protected_path, disk_space, permissions).
            details: Additional details about the failure.
        """
        self.validation_type = validation_type
        self.details = details
        super().__init__(message)


class ConflictError(OrganizationError):
    """Exception raised when a file conflict cannot be resolved.

    This exception is raised when a target file already exists
    and the conflict strategy cannot resolve it automatically.
    """

    def __init__(
        self,
        message: str = "File conflict could not be resolved",
        source_path: str | None = None,
        target_path: str | None = None,
    ) -> None:
        """Initialize the exception with conflict information.

        Args:
            message: The error message describing the conflict.
            source_path: Path of the source file.
            target_path: Path of the target file.
        """
        self.source_path = source_path
        self.target_path = target_path
        super().__init__(message)


class TransactionError(OrganizationError):
    """Exception raised when a transaction fails.

    This exception is raised when a file organization transaction
    cannot be completed or saved.
    """

    def __init__(
        self,
        message: str = "Transaction failed",
        transaction_id: str | None = None,
    ) -> None:
        """Initialize the exception with transaction information.

        Args:
            message: The error message describing the transaction failure.
            transaction_id: The ID of the failed transaction.
        """
        self.transaction_id = transaction_id
        super().__init__(message)


class RollbackError(OrganizationError):
    """Exception raised when a rollback operation fails.

    This exception is raised when attempting to roll back
    a file organization transaction fails.
    """

    def __init__(
        self,
        message: str = "Rollback failed",
        transaction_id: str | None = None,
        partial_rollback: bool = False,
    ) -> None:
        """Initialize the exception with rollback information.

        Args:
            message: The error message describing the rollback failure.
            transaction_id: The ID of the transaction being rolled back.
            partial_rollback: Whether the rollback was partially completed.
        """
        self.transaction_id = transaction_id
        self.partial_rollback = partial_rollback
        super().__init__(message)


class ExecutionError(OrganizationError):
    """Exception raised when file operation execution fails.

    This exception is raised when a file operation (move, copy, delete)
    fails during execution.
    """

    def __init__(
        self,
        message: str = "File operation failed",
        operation: str | None = None,
        file_path: str | None = None,
    ) -> None:
        """Initialize the exception with execution information.

        Args:
            message: The error message describing the execution failure.
            operation: The operation that failed (move, copy, delete).
            file_path: The path of the file that caused the failure.
        """
        self.operation = operation
        self.file_path = file_path
        super().__init__(message)


class ProtectedPathError(OrganizationError):
    """Exception raised when attempting to modify a protected path.

    This exception is raised when an operation attempts to
    modify files in a protected system directory.
    """

    def __init__(
        self,
        message: str = "Cannot modify protected path",
        protected_path: str | None = None,
    ) -> None:
        """Initialize the exception with path information.

        Args:
            message: The error message describing the protection issue.
            protected_path: The protected path that was accessed.
        """
        self.protected_path = protected_path
        super().__init__(message)


class InsufficientSpaceError(OrganizationError):
    """Exception raised when there is not enough disk space.

    This exception is raised when a file operation cannot be
    completed due to insufficient disk space.
    """

    def __init__(
        self,
        message: str = "Insufficient disk space",
        required_bytes: int | None = None,
        available_bytes: int | None = None,
    ) -> None:
        """Initialize the exception with space information.

        Args:
            message: The error message describing the space issue.
            required_bytes: The number of bytes required for the operation.
            available_bytes: The number of bytes currently available.
        """
        self.required_bytes = required_bytes
        self.available_bytes = available_bytes
        super().__init__(message)
