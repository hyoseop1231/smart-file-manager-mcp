"""Tests for ImageProcessor class.

TAG: VIS-M2-01 to VIS-M2-08
SPEC: SPEC-VISION-001
"""

import hashlib
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from smart_file_manager.processors.image_processor import ImageProcessor

from smart_file_manager.core.constants import (
    TARGET_IMAGE_DIMENSION,
    VISION_CACHE_KEY_PREFIX_IMAGE,
    VISION_CACHE_TTL_SECONDS,
)
from smart_file_manager.services.vision_models import (
    ImageAnalysisResult,
    ImageMetadata,
)


class TestImageProcessorInit:
    """Tests for ImageProcessor initialization."""

    def test_init_with_client_only(self) -> None:
        """ImageProcessor should initialize with just an OpenRouterClient."""
        mock_client = MagicMock()
        processor = ImageProcessor(client=mock_client)

        assert processor.client == mock_client
        assert processor.cache is None

    def test_init_with_client_and_cache(self) -> None:
        """ImageProcessor should initialize with client and optional cache."""
        mock_client = MagicMock()
        mock_cache = MagicMock()
        processor = ImageProcessor(client=mock_client, cache=mock_cache)

        assert processor.client == mock_client
        assert processor.cache == mock_cache


class TestImageProcessorValidateFormat:
    """Tests for format validation (VIS-M2-02)."""

    def test_validate_format_jpeg_supported(self) -> None:
        """JPEG format should be valid."""
        mock_client = MagicMock()
        processor = ImageProcessor(client=mock_client)

        assert processor.validate_format(Path("test.jpg")) is True
        assert processor.validate_format(Path("test.jpeg")) is True
        assert processor.validate_format(Path("test.JPEG")) is True

    def test_validate_format_png_supported(self) -> None:
        """PNG format should be valid."""
        mock_client = MagicMock()
        processor = ImageProcessor(client=mock_client)

        assert processor.validate_format(Path("test.png")) is True
        assert processor.validate_format(Path("test.PNG")) is True

    def test_validate_format_gif_supported(self) -> None:
        """GIF format should be valid."""
        mock_client = MagicMock()
        processor = ImageProcessor(client=mock_client)

        assert processor.validate_format(Path("test.gif")) is True

    def test_validate_format_webp_supported(self) -> None:
        """WebP format should be valid."""
        mock_client = MagicMock()
        processor = ImageProcessor(client=mock_client)

        assert processor.validate_format(Path("test.webp")) is True

    def test_validate_format_bmp_supported(self) -> None:
        """BMP format should be valid."""
        mock_client = MagicMock()
        processor = ImageProcessor(client=mock_client)

        assert processor.validate_format(Path("test.bmp")) is True

    def test_validate_format_tiff_not_supported(self) -> None:
        """TIFF format should NOT be valid."""
        mock_client = MagicMock()
        processor = ImageProcessor(client=mock_client)

        assert processor.validate_format(Path("test.tiff")) is False
        assert processor.validate_format(Path("test.tif")) is False

    def test_validate_format_heic_not_supported(self) -> None:
        """HEIC format should NOT be valid."""
        mock_client = MagicMock()
        processor = ImageProcessor(client=mock_client)

        assert processor.validate_format(Path("test.heic")) is False


class TestImageProcessorResizeIfNeeded:
    """Tests for image resizing (VIS-M2-03)."""

    def test_resize_small_image_unchanged(self) -> None:
        """Small images should not be resized."""
        mock_client = MagicMock()
        processor = ImageProcessor(client=mock_client)

        # Create a mock small image (800x600)
        with patch("smart_file_manager.processors.image_processor.Image") as mock_pil:
            mock_img = MagicMock()
            mock_img.size = (800, 600)
            mock_img.mode = "RGB"
            mock_pil.open.return_value.__enter__.return_value = mock_img

            # Small image should return original data
            original_data = b"fake_image_data"
            result = processor.resize_if_needed(original_data)

            # Should not call resize for small images
            mock_img.resize.assert_not_called()

    def test_resize_large_image_resized(self) -> None:
        """Large images should be resized to target dimension."""
        mock_client = MagicMock()
        processor = ImageProcessor(client=mock_client)

        with patch("smart_file_manager.processors.image_processor.Image") as mock_pil:
            mock_img = MagicMock()
            mock_img.size = (8000, 6000)  # Larger than TARGET_IMAGE_DIMENSION
            mock_img.mode = "RGB"

            resized_img = MagicMock()
            mock_img.resize.return_value = resized_img

            mock_pil.open.return_value.__enter__.return_value = mock_img

            original_data = b"fake_large_image_data"
            result = processor.resize_if_needed(original_data, max_size=TARGET_IMAGE_DIMENSION)

            # Should call resize
            mock_img.resize.assert_called_once()

    def test_resize_preserves_aspect_ratio(self) -> None:
        """Resize should preserve aspect ratio."""
        mock_client = MagicMock()
        processor = ImageProcessor(client=mock_client)

        with patch("smart_file_manager.processors.image_processor.Image") as mock_pil:
            mock_img = MagicMock()
            mock_img.size = (8000, 4000)  # 2:1 aspect ratio
            mock_img.mode = "RGB"

            resized_img = MagicMock()
            mock_img.resize.return_value = resized_img

            mock_pil.open.return_value.__enter__.return_value = mock_img

            processor.resize_if_needed(b"data", max_size=4096)

            # Check that resize was called with correct dimensions
            call_args = mock_img.resize.call_args[0][0]
            # Aspect ratio should be preserved (4096, 2048)
            assert call_args[0] / call_args[1] == pytest.approx(2.0, rel=0.1)


class TestImageProcessorExtractMetadata:
    """Tests for EXIF metadata extraction (VIS-M2-04)."""

    def test_extract_metadata_basic(self) -> None:
        """Should extract basic image metadata."""
        mock_client = MagicMock()
        processor = ImageProcessor(client=mock_client)

        with patch("smart_file_manager.processors.image_processor.Image") as mock_pil:
            mock_img = MagicMock()
            mock_img.size = (1920, 1080)
            mock_img.format = "JPEG"
            mock_img.getexif.return_value = {}
            mock_pil.open.return_value.__enter__.return_value = mock_img

            with patch("builtins.open", MagicMock()):
                with patch("pathlib.Path.stat") as mock_stat:
                    mock_stat.return_value.st_size = 1024000

                    metadata = processor.extract_metadata(
                        Path("/test/image.jpg"),
                        content_hash="abc123",
                    )

                    assert metadata.width == 1920
                    assert metadata.height == 1080
                    assert metadata.format == "jpeg"
                    assert metadata.size_bytes == 1024000
                    assert metadata.content_hash == "abc123"

    def test_extract_metadata_with_exif(self) -> None:
        """Should extract EXIF data when present."""
        mock_client = MagicMock()
        processor = ImageProcessor(client=mock_client)

        with patch("smart_file_manager.processors.image_processor.Image") as mock_pil:
            mock_img = MagicMock()
            mock_img.size = (4000, 3000)
            mock_img.format = "JPEG"

            # Mock EXIF data
            mock_exif = MagicMock()
            mock_exif.items.return_value = [(271, "Canon"), (272, "EOS R5")]
            mock_img.getexif.return_value = mock_exif

            mock_pil.open.return_value.__enter__.return_value = mock_img
            mock_pil.ExifTags.TAGS = {271: "Make", 272: "Model"}

            with patch("builtins.open", MagicMock()):
                with patch("pathlib.Path.stat") as mock_stat:
                    mock_stat.return_value.st_size = 5000000

                    metadata = processor.extract_metadata(
                        Path("/test/photo.jpg"),
                        content_hash="xyz789",
                    )

                    assert metadata.exif is not None
                    assert "Make" in metadata.exif
                    assert metadata.exif["Make"] == "Canon"


class TestImageProcessorAnalyze:
    """Tests for image analysis (VIS-M2-05, VIS-M2-06, VIS-M2-07)."""

    @pytest.mark.asyncio
    async def test_analyze_cache_hit(self) -> None:
        """Should return cached result on cache hit (REQ-E-001)."""
        mock_client = MagicMock()
        mock_cache = AsyncMock()

        # Setup cached data
        cached_data = {
            "description": "A cached image description",
            "objects": [],
            "scene": "indoor",
            "text_content": None,
            "tags": ["cached"],
            "dominant_colors": ["white"],
            "quality": "sharp",
            "metadata": {
                "width": 800,
                "height": 600,
                "format": "jpeg",
                "size_bytes": 100000,
                "content_hash": "hash123",
                "exif": None,
            },
            "model_used": "google/gemini-2.0-flash-001",
            "estimated_cost": 0.001,
            "cached": True,
            "processing_time_ms": 50.0,
        }
        mock_cache.get.return_value = cached_data

        processor = ImageProcessor(client=mock_client, cache=mock_cache)

        result = await processor.analyze(
            image_data=b"fake_data",
            content_hash="hash123",
        )

        assert result.cached is True
        assert result.description == "A cached image description"
        mock_cache.get.assert_called_once_with(f"{VISION_CACHE_KEY_PREFIX_IMAGE}hash123")

    @pytest.mark.asyncio
    async def test_analyze_cache_miss_calls_api(self) -> None:
        """Should call API on cache miss (REQ-E-002)."""
        mock_client = AsyncMock()
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None  # Cache miss

        # Setup API response
        mock_response = MagicMock()
        mock_response.content = """{"description": "API result", "objects": [], "scene": "outdoor", "text": null, "tags": ["api"], "dominant_colors": ["blue"], "quality": "sharp"}"""
        mock_response.prompt_tokens = 100
        mock_response.completion_tokens = 50
        mock_response.model_used = "google/gemini-2.0-flash-001"
        mock_client.chat_completion_with_fallback.return_value = mock_response

        processor = ImageProcessor(client=mock_client, cache=mock_cache)

        with patch.object(processor, "_parse_api_response") as mock_parse:
            mock_result = ImageAnalysisResult(
                description="API result",
                objects=[],
                scene="outdoor",
                text_content=None,
                tags=["api"],
                dominant_colors=["blue"],
                quality="sharp",
                metadata=ImageMetadata(
                    width=800,
                    height=600,
                    format="jpeg",
                    size_bytes=100000,
                    content_hash="hash456",
                ),
                model_used="google/gemini-2.0-flash-001",
                estimated_cost=0.001,
                cached=False,
                processing_time_ms=1500.0,
            )
            mock_parse.return_value = mock_result

            with patch.object(processor, "_prepare_image_message") as mock_prep:
                mock_prep.return_value = [{"role": "user", "content": "test"}]

                result = await processor.analyze(
                    image_data=b"fake_data",
                    content_hash="hash456",
                    metadata=ImageMetadata(
                        width=800,
                        height=600,
                        format="jpeg",
                        size_bytes=100000,
                        content_hash="hash456",
                    ),
                )

                mock_client.chat_completion_with_fallback.assert_called_once()
                assert result.cached is False

    @pytest.mark.asyncio
    async def test_analyze_stores_result_in_cache(self) -> None:
        """Should store successful result in cache (REQ-U-002)."""
        mock_client = AsyncMock()
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None

        mock_response = MagicMock()
        mock_response.content = """{"description": "Test", "objects": [], "scene": "test", "text": null, "tags": [], "dominant_colors": [], "quality": "sharp"}"""
        mock_response.prompt_tokens = 100
        mock_response.completion_tokens = 50
        mock_response.model_used = "test-model"
        mock_client.chat_completion_with_fallback.return_value = mock_response

        processor = ImageProcessor(client=mock_client, cache=mock_cache)

        with patch.object(processor, "_parse_api_response") as mock_parse:
            mock_result = ImageAnalysisResult(
                description="Test",
                objects=[],
                scene="test",
                text_content=None,
                tags=[],
                dominant_colors=[],
                quality="sharp",
                metadata=ImageMetadata(
                    width=100,
                    height=100,
                    format="png",
                    size_bytes=1000,
                    content_hash="test_hash",
                ),
                model_used="test-model",
                estimated_cost=0.001,
                cached=False,
                processing_time_ms=100.0,
            )
            mock_parse.return_value = mock_result

            with patch.object(processor, "_prepare_image_message") as mock_prep:
                mock_prep.return_value = [{"role": "user", "content": "test"}]

                await processor.analyze(
                    image_data=b"data",
                    content_hash="test_hash",
                    metadata=ImageMetadata(
                        width=100,
                        height=100,
                        format="png",
                        size_bytes=1000,
                        content_hash="test_hash",
                    ),
                )

                # Verify cache.set was called with correct TTL
                mock_cache.set.assert_called_once()
                call_args = mock_cache.set.call_args
                assert call_args[1].get("ttl") == VISION_CACHE_TTL_SECONDS

    @pytest.mark.asyncio
    async def test_analyze_force_refresh_ignores_cache(self) -> None:
        """Should ignore cache when force_refresh=True (REQ-E-010)."""
        mock_client = AsyncMock()
        mock_cache = AsyncMock()

        # Cache has data but should be ignored
        cached_data = {"description": "Old cached data"}
        mock_cache.get.return_value = cached_data

        mock_response = MagicMock()
        mock_response.content = """{"description": "Fresh API result", "objects": [], "scene": "new", "text": null, "tags": [], "dominant_colors": [], "quality": "sharp"}"""
        mock_response.prompt_tokens = 100
        mock_response.completion_tokens = 50
        mock_response.model_used = "test-model"
        mock_client.chat_completion_with_fallback.return_value = mock_response

        processor = ImageProcessor(client=mock_client, cache=mock_cache)

        with patch.object(processor, "_parse_api_response") as mock_parse:
            mock_result = ImageAnalysisResult(
                description="Fresh API result",
                objects=[],
                scene="new",
                text_content=None,
                tags=[],
                dominant_colors=[],
                quality="sharp",
                metadata=ImageMetadata(
                    width=100,
                    height=100,
                    format="png",
                    size_bytes=1000,
                    content_hash="hash",
                ),
                model_used="test-model",
                estimated_cost=0.001,
                cached=False,
                processing_time_ms=100.0,
            )
            mock_parse.return_value = mock_result

            with patch.object(processor, "_prepare_image_message") as mock_prep:
                mock_prep.return_value = [{"role": "user", "content": "test"}]

                result = await processor.analyze(
                    image_data=b"data",
                    content_hash="hash",
                    force_refresh=True,
                    metadata=ImageMetadata(
                        width=100,
                        height=100,
                        format="png",
                        size_bytes=1000,
                        content_hash="hash",
                    ),
                )

                # Cache.get should not be called when force_refresh=True
                mock_cache.get.assert_not_called()
                assert result.description == "Fresh API result"

    @pytest.mark.asyncio
    async def test_analyze_local_fallback_on_api_failure(self) -> None:
        """Should use local fallback when all API calls fail (REQ-E-005)."""
        mock_client = AsyncMock()
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None

        from smart_file_manager.core.exceptions import ModelUnavailableError

        mock_client.chat_completion_with_fallback.side_effect = ModelUnavailableError(
            "All models failed"
        )

        processor = ImageProcessor(client=mock_client, cache=mock_cache)

        with patch.object(processor, "_local_fallback_analysis") as mock_fallback:
            mock_fallback_result = ImageAnalysisResult(
                description="Local analysis based on metadata",
                objects=[],
                scene="unknown",
                text_content=None,
                tags=["image"],
                dominant_colors=[],
                quality="unknown",
                metadata=ImageMetadata(
                    width=800,
                    height=600,
                    format="jpeg",
                    size_bytes=100000,
                    content_hash="local_hash",
                ),
                model_used="local",
                estimated_cost=0.0,
                cached=False,
                processing_time_ms=10.0,
            )
            mock_fallback.return_value = mock_fallback_result

            with patch.object(processor, "_prepare_image_message") as mock_prep:
                mock_prep.return_value = [{"role": "user", "content": "test"}]

                result = await processor.analyze(
                    image_data=b"data",
                    content_hash="local_hash",
                    metadata=ImageMetadata(
                        width=800,
                        height=600,
                        format="jpeg",
                        size_bytes=100000,
                        content_hash="local_hash",
                    ),
                )

                mock_fallback.assert_called_once()
                assert result.model_used == "local"


class TestImageProcessorLocalFallback:
    """Tests for local fallback analysis (VIS-M2-07)."""

    def test_local_fallback_returns_basic_analysis(self) -> None:
        """Local fallback should return basic metadata-based analysis."""
        mock_client = MagicMock()
        processor = ImageProcessor(client=mock_client)

        metadata = ImageMetadata(
            width=1920,
            height=1080,
            format="jpeg",
            size_bytes=2000000,
            content_hash="fallback_hash",
            exif={"Make": "Canon"},
        )

        result = processor._local_fallback_analysis(
            image_data=b"data",
            metadata=metadata,
        )

        assert result.model_used == "local"
        assert result.estimated_cost == 0.0
        assert result.metadata == metadata
        assert "image" in result.tags or "photo" in result.tags


class TestImageProcessorHelpers:
    """Tests for helper methods."""

    def test_compute_content_hash(self) -> None:
        """Should compute SHA256 hash of image data."""
        mock_client = MagicMock()
        processor = ImageProcessor(client=mock_client)

        data = b"test image data"
        expected_hash = hashlib.sha256(data).hexdigest()

        result = processor.compute_content_hash(data)
        assert result == expected_hash

    def test_prepare_image_message(self) -> None:
        """Should prepare message with base64 encoded image."""
        mock_client = MagicMock()
        processor = ImageProcessor(client=mock_client)

        image_data = b"fake_image_bytes"
        messages = processor._prepare_image_message(image_data, "image/jpeg")

        assert len(messages) > 0
        assert messages[0]["role"] == "user"
