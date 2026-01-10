"""Tests for Vision-related exception classes.

TAG: VIS-M1-01
SPEC: SPEC-VISION-001
"""


from smart_file_manager.core.exceptions import (
    AnalysisFailedError,
    CorruptedFileError,
    DependencyError,
    ImageProcessingError,
    SmartFileManagerError,
    UnsupportedFormatError,
    VideoProcessingError,
    VisionError,
)


class TestVisionError:
    """Tests for VisionError base exception."""

    def test_vision_error_inherits_from_base(self) -> None:
        """VisionError should inherit from SmartFileManagerError."""
        error = VisionError("Vision error occurred")
        assert isinstance(error, SmartFileManagerError)

    def test_vision_error_default_message(self) -> None:
        """VisionError should have a default message."""
        error = VisionError()
        assert error.message == "Vision analysis error"

    def test_vision_error_custom_message(self) -> None:
        """VisionError should accept custom message."""
        error = VisionError("Custom vision error")
        assert error.message == "Custom vision error"
        assert str(error) == "Custom vision error"


class TestImageProcessingError:
    """Tests for ImageProcessingError exception."""

    def test_image_processing_error_inherits_from_vision_error(self) -> None:
        """ImageProcessingError should inherit from VisionError."""
        error = ImageProcessingError("Image processing failed")
        assert isinstance(error, VisionError)

    def test_image_processing_error_default_message(self) -> None:
        """ImageProcessingError should have a default message."""
        error = ImageProcessingError()
        assert error.message == "Image processing error"

    def test_image_processing_error_with_image_path(self) -> None:
        """ImageProcessingError should accept image_path attribute."""
        error = ImageProcessingError("Processing failed", image_path="/path/to/image.jpg")
        assert error.image_path == "/path/to/image.jpg"


class TestVideoProcessingError:
    """Tests for VideoProcessingError exception."""

    def test_video_processing_error_inherits_from_vision_error(self) -> None:
        """VideoProcessingError should inherit from VisionError."""
        error = VideoProcessingError("Video processing failed")
        assert isinstance(error, VisionError)

    def test_video_processing_error_default_message(self) -> None:
        """VideoProcessingError should have a default message."""
        error = VideoProcessingError()
        assert error.message == "Video processing error"

    def test_video_processing_error_with_video_path(self) -> None:
        """VideoProcessingError should accept video_path attribute."""
        error = VideoProcessingError("Processing failed", video_path="/path/to/video.mp4")
        assert error.video_path == "/path/to/video.mp4"


class TestUnsupportedFormatError:
    """Tests for UnsupportedFormatError exception."""

    def test_unsupported_format_error_inherits_from_vision_error(self) -> None:
        """UnsupportedFormatError should inherit from VisionError."""
        error = UnsupportedFormatError("Format not supported")
        assert isinstance(error, VisionError)

    def test_unsupported_format_error_default_message(self) -> None:
        """UnsupportedFormatError should have a default message."""
        error = UnsupportedFormatError()
        assert error.message == "Unsupported file format"

    def test_unsupported_format_error_with_format_info(self) -> None:
        """UnsupportedFormatError should accept format and supported_formats."""
        error = UnsupportedFormatError(
            "TIFF not supported",
            format="tiff",
            supported_formats=["jpeg", "png", "gif", "webp", "bmp"],
        )
        assert error.format == "tiff"
        assert error.supported_formats == ["jpeg", "png", "gif", "webp", "bmp"]


class TestCorruptedFileError:
    """Tests for CorruptedFileError exception."""

    def test_corrupted_file_error_inherits_from_vision_error(self) -> None:
        """CorruptedFileError should inherit from VisionError."""
        error = CorruptedFileError("File is corrupted")
        assert isinstance(error, VisionError)

    def test_corrupted_file_error_default_message(self) -> None:
        """CorruptedFileError should have a default message."""
        error = CorruptedFileError()
        assert error.message == "File is corrupted or cannot be decoded"

    def test_corrupted_file_error_with_file_path(self) -> None:
        """CorruptedFileError should accept file_path attribute."""
        error = CorruptedFileError("Cannot decode image", file_path="/path/to/corrupted.jpg")
        assert error.file_path == "/path/to/corrupted.jpg"


class TestDependencyError:
    """Tests for DependencyError exception."""

    def test_dependency_error_inherits_from_vision_error(self) -> None:
        """DependencyError should inherit from VisionError."""
        error = DependencyError("FFmpeg not found")
        assert isinstance(error, VisionError)

    def test_dependency_error_default_message(self) -> None:
        """DependencyError should have a default message."""
        error = DependencyError()
        assert error.message == "Required dependency not available"

    def test_dependency_error_with_dependency_name(self) -> None:
        """DependencyError should accept dependency_name attribute."""
        error = DependencyError(
            "FFmpeg is required for video processing",
            dependency_name="ffmpeg",
        )
        assert error.dependency_name == "ffmpeg"


class TestAnalysisFailedError:
    """Tests for AnalysisFailedError exception."""

    def test_analysis_failed_error_inherits_from_vision_error(self) -> None:
        """AnalysisFailedError should inherit from VisionError."""
        error = AnalysisFailedError("All fallbacks exhausted")
        assert isinstance(error, VisionError)

    def test_analysis_failed_error_default_message(self) -> None:
        """AnalysisFailedError should have a default message."""
        error = AnalysisFailedError()
        assert error.message == "Analysis failed after all fallbacks"

    def test_analysis_failed_error_with_attempts(self) -> None:
        """AnalysisFailedError should accept attempts and last_error."""
        original_error = Exception("API timeout")
        error = AnalysisFailedError(
            "All models failed",
            attempts=3,
            last_error=original_error,
        )
        assert error.attempts == 3
        assert error.last_error == original_error
