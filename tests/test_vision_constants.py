"""Tests for Vision-related constants.

TAG: VIS-M1-02
SPEC: SPEC-VISION-001
"""



class TestVisionSupportedFormats:
    """Tests for supported image and video formats."""

    def test_supported_image_formats_defined(self) -> None:
        """SUPPORTED_IMAGE_FORMATS should be defined."""
        from smart_file_manager.core.constants import SUPPORTED_IMAGE_FORMATS

        assert isinstance(SUPPORTED_IMAGE_FORMATS, frozenset)
        assert len(SUPPORTED_IMAGE_FORMATS) > 0

    def test_supported_image_formats_contains_required_types(self) -> None:
        """SUPPORTED_IMAGE_FORMATS should contain JPEG, PNG, GIF, WebP, BMP."""
        from smart_file_manager.core.constants import SUPPORTED_IMAGE_FORMATS

        required_formats = {"jpeg", "jpg", "png", "gif", "webp", "bmp"}
        for fmt in required_formats:
            assert fmt in SUPPORTED_IMAGE_FORMATS, f"{fmt} should be supported"

    def test_supported_video_formats_defined(self) -> None:
        """SUPPORTED_VIDEO_FORMATS should be defined."""
        from smart_file_manager.core.constants import SUPPORTED_VIDEO_FORMATS

        assert isinstance(SUPPORTED_VIDEO_FORMATS, frozenset)
        assert len(SUPPORTED_VIDEO_FORMATS) > 0

    def test_supported_video_formats_contains_required_types(self) -> None:
        """SUPPORTED_VIDEO_FORMATS should contain MP4, MKV, AVI, MOV, WebM."""
        from smart_file_manager.core.constants import SUPPORTED_VIDEO_FORMATS

        required_formats = {"mp4", "mkv", "avi", "mov", "webm"}
        for fmt in required_formats:
            assert fmt in SUPPORTED_VIDEO_FORMATS, f"{fmt} should be supported"


class TestVisionMimeTypes:
    """Tests for MIME type mappings."""

    def test_image_mime_types_defined(self) -> None:
        """IMAGE_MIME_TYPES should be defined."""
        from smart_file_manager.core.constants import IMAGE_MIME_TYPES

        assert isinstance(IMAGE_MIME_TYPES, dict)
        assert len(IMAGE_MIME_TYPES) > 0

    def test_image_mime_types_correct_mapping(self) -> None:
        """IMAGE_MIME_TYPES should have correct MIME type mappings."""
        from smart_file_manager.core.constants import IMAGE_MIME_TYPES

        expected_mappings = {
            "jpeg": "image/jpeg",
            "jpg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp",
            "bmp": "image/bmp",
        }
        for ext, mime in expected_mappings.items():
            assert IMAGE_MIME_TYPES.get(ext) == mime, f"{ext} should map to {mime}"

    def test_video_mime_types_defined(self) -> None:
        """VIDEO_MIME_TYPES should be defined."""
        from smart_file_manager.core.constants import VIDEO_MIME_TYPES

        assert isinstance(VIDEO_MIME_TYPES, dict)
        assert len(VIDEO_MIME_TYPES) > 0

    def test_video_mime_types_correct_mapping(self) -> None:
        """VIDEO_MIME_TYPES should have correct MIME type mappings."""
        from smart_file_manager.core.constants import VIDEO_MIME_TYPES

        expected_mappings = {
            "mp4": "video/mp4",
            "mkv": "video/x-matroska",
            "avi": "video/x-msvideo",
            "mov": "video/quicktime",
            "webm": "video/webm",
        }
        for ext, mime in expected_mappings.items():
            assert VIDEO_MIME_TYPES.get(ext) == mime, f"{ext} should map to {mime}"


class TestVisionSizeLimits:
    """Tests for size limit constants."""

    def test_max_image_size_defined(self) -> None:
        """MAX_IMAGE_SIZE_BYTES should be defined as 20MB."""
        from smart_file_manager.core.constants import MAX_IMAGE_SIZE_BYTES

        assert MAX_IMAGE_SIZE_BYTES == 20 * 1024 * 1024  # 20MB

    def test_max_image_dimension_defined(self) -> None:
        """MAX_IMAGE_DIMENSION should be defined as 8192px."""
        from smart_file_manager.core.constants import MAX_IMAGE_DIMENSION

        assert MAX_IMAGE_DIMENSION == 8192

    def test_target_image_dimension_defined(self) -> None:
        """TARGET_IMAGE_DIMENSION should be defined as 4096px for resizing."""
        from smart_file_manager.core.constants import TARGET_IMAGE_DIMENSION

        assert TARGET_IMAGE_DIMENSION == 4096

    def test_max_video_size_defined(self) -> None:
        """MAX_VIDEO_SIZE_BYTES should be defined as 500MB."""
        from smart_file_manager.core.constants import MAX_VIDEO_SIZE_BYTES

        assert MAX_VIDEO_SIZE_BYTES == 500 * 1024 * 1024  # 500MB

    def test_max_video_duration_defined(self) -> None:
        """MAX_VIDEO_DURATION_SECONDS should be defined as 30 minutes."""
        from smart_file_manager.core.constants import MAX_VIDEO_DURATION_SECONDS

        assert MAX_VIDEO_DURATION_SECONDS == 30 * 60  # 30 minutes


class TestVisionCacheSettings:
    """Tests for cache-related constants."""

    def test_vision_cache_ttl_defined(self) -> None:
        """VISION_CACHE_TTL_SECONDS should be defined as 7 days."""
        from smart_file_manager.core.constants import VISION_CACHE_TTL_SECONDS

        assert VISION_CACHE_TTL_SECONDS == 7 * 24 * 60 * 60  # 7 days

    def test_vision_cache_key_prefix_image(self) -> None:
        """VISION_CACHE_KEY_PREFIX_IMAGE should be defined."""
        from smart_file_manager.core.constants import VISION_CACHE_KEY_PREFIX_IMAGE

        assert VISION_CACHE_KEY_PREFIX_IMAGE == "vision:image:"

    def test_vision_cache_key_prefix_video(self) -> None:
        """VISION_CACHE_KEY_PREFIX_VIDEO should be defined."""
        from smart_file_manager.core.constants import VISION_CACHE_KEY_PREFIX_VIDEO

        assert VISION_CACHE_KEY_PREFIX_VIDEO == "vision:video:"

    def test_vision_cache_key_prefix_frame(self) -> None:
        """VISION_CACHE_KEY_PREFIX_FRAME should be defined."""
        from smart_file_manager.core.constants import VISION_CACHE_KEY_PREFIX_FRAME

        assert VISION_CACHE_KEY_PREFIX_FRAME == "vision:frame:"


class TestVideoKeyframeSettings:
    """Tests for video keyframe extraction settings."""

    def test_keyframe_intervals_defined(self) -> None:
        """KEYFRAME_INTERVALS should be defined with duration thresholds."""
        from smart_file_manager.core.constants import KEYFRAME_INTERVALS

        assert isinstance(KEYFRAME_INTERVALS, dict)
        # Should have entries for different video durations
        assert len(KEYFRAME_INTERVALS) >= 4

    def test_keyframe_intervals_correct_values(self) -> None:
        """KEYFRAME_INTERVALS should have correct interval values."""
        from smart_file_manager.core.constants import KEYFRAME_INTERVALS

        # Format: (max_duration_seconds, interval_seconds, max_frames)
        expected = {
            60: (5, 12),  # 0-60 seconds: 5s interval, max 12 frames
            300: (15, 20),  # 1-5 minutes: 15s interval, max 20 frames
            600: (30, 20),  # 5-10 minutes: 30s interval, max 20 frames
            1800: (60, 30),  # 10-30 minutes: 60s interval, max 30 frames
        }
        for duration, (interval, max_frames) in expected.items():
            assert KEYFRAME_INTERVALS.get(duration) == (interval, max_frames)

    def test_max_representative_frames_defined(self) -> None:
        """MAX_REPRESENTATIVE_FRAMES should be defined as 5."""
        from smart_file_manager.core.constants import MAX_REPRESENTATIVE_FRAMES

        assert MAX_REPRESENTATIVE_FRAMES == 5


class TestVisionAnalysisPrompt:
    """Tests for analysis prompt template."""

    def test_image_analysis_prompt_defined(self) -> None:
        """IMAGE_ANALYSIS_PROMPT should be defined."""
        from smart_file_manager.core.constants import IMAGE_ANALYSIS_PROMPT

        assert isinstance(IMAGE_ANALYSIS_PROMPT, str)
        assert len(IMAGE_ANALYSIS_PROMPT) > 100  # Should be a substantial prompt

    def test_image_analysis_prompt_requests_json(self) -> None:
        """IMAGE_ANALYSIS_PROMPT should request JSON output."""
        from smart_file_manager.core.constants import IMAGE_ANALYSIS_PROMPT

        assert "JSON" in IMAGE_ANALYSIS_PROMPT

    def test_image_analysis_prompt_includes_required_fields(self) -> None:
        """IMAGE_ANALYSIS_PROMPT should request required analysis fields."""
        from smart_file_manager.core.constants import IMAGE_ANALYSIS_PROMPT

        required_fields = ["description", "objects", "scene", "text", "tags"]
        for field in required_fields:
            assert field in IMAGE_ANALYSIS_PROMPT, f"Prompt should request {field}"
