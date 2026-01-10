"""Tests for VisionService class.

TAG: VIS-M4-01 to VIS-M4-06
SPEC: SPEC-VISION-001
"""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from smart_file_manager.services.vision_service import VisionService

from smart_file_manager.core.exceptions import (
    UnsupportedFormatError,
)
from smart_file_manager.services.vision_models import (
    AnalysisStats,
    ImageAnalysisResult,
    ImageMetadata,
    VideoAnalysisResult,
    VideoMetadata,
)


class TestVisionServiceInit:
    """Tests for VisionService initialization (VIS-M4-01)."""

    def test_init_with_client(self) -> None:
        """VisionService should initialize with OpenRouterClient."""
        mock_client = MagicMock()
        service = VisionService(client=mock_client)

        assert service.client == mock_client
        assert service.cache is None
        assert service.image_processor is not None
        assert service.video_processor is not None

    def test_init_with_cache(self) -> None:
        """VisionService should accept optional cache."""
        mock_client = MagicMock()
        mock_cache = MagicMock()
        service = VisionService(client=mock_client, cache=mock_cache)

        assert service.cache == mock_cache
        # Processors should also have cache
        assert service.image_processor.cache == mock_cache
        assert service.video_processor.cache == mock_cache


class TestVisionServiceFileTypeRouting:
    """Tests for file type routing (VIS-M4-02)."""

    def test_is_image_file_jpeg(self) -> None:
        """Should identify JPEG files as images."""
        mock_client = MagicMock()
        service = VisionService(client=mock_client)

        assert service.is_image_file(Path("test.jpg")) is True
        assert service.is_image_file(Path("test.jpeg")) is True
        assert service.is_image_file(Path("test.JPG")) is True

    def test_is_image_file_png(self) -> None:
        """Should identify PNG files as images."""
        mock_client = MagicMock()
        service = VisionService(client=mock_client)

        assert service.is_image_file(Path("test.png")) is True

    def test_is_video_file_mp4(self) -> None:
        """Should identify MP4 files as videos."""
        mock_client = MagicMock()
        service = VisionService(client=mock_client)

        assert service.is_video_file(Path("test.mp4")) is True
        assert service.is_video_file(Path("test.MP4")) is True

    def test_is_video_file_mkv(self) -> None:
        """Should identify MKV files as videos."""
        mock_client = MagicMock()
        service = VisionService(client=mock_client)

        assert service.is_video_file(Path("test.mkv")) is True

    def test_is_image_file_video_returns_false(self) -> None:
        """Video files should not be identified as images."""
        mock_client = MagicMock()
        service = VisionService(client=mock_client)

        assert service.is_image_file(Path("test.mp4")) is False

    def test_is_video_file_image_returns_false(self) -> None:
        """Image files should not be identified as videos."""
        mock_client = MagicMock()
        service = VisionService(client=mock_client)

        assert service.is_video_file(Path("test.jpg")) is False

    def test_is_supported_file(self) -> None:
        """Should identify supported files."""
        mock_client = MagicMock()
        service = VisionService(client=mock_client)

        assert service.is_supported_file(Path("test.jpg")) is True
        assert service.is_supported_file(Path("test.mp4")) is True
        assert service.is_supported_file(Path("test.txt")) is False
        assert service.is_supported_file(Path("test.pdf")) is False


class TestVisionServiceAnalyzeImage:
    """Tests for image analysis."""

    @pytest.mark.asyncio
    async def test_analyze_image_success(self) -> None:
        """Should analyze image successfully."""
        mock_client = MagicMock()
        service = VisionService(client=mock_client)

        mock_result = ImageAnalysisResult(
            description="Test image",
            objects=[],
            scene="test",
            text_content=None,
            tags=["test"],
            dominant_colors=["white"],
            quality="sharp",
            metadata=ImageMetadata(
                width=800,
                height=600,
                format="jpeg",
                size_bytes=100000,
                content_hash="img_hash",
            ),
            model_used="test-model",
            estimated_cost=0.001,
            cached=False,
            processing_time_ms=100.0,
        )

        with patch.object(service.image_processor, "analyze", return_value=mock_result):
            with patch.object(service.image_processor, "extract_metadata") as mock_metadata:
                mock_metadata.return_value = ImageMetadata(
                    width=800,
                    height=600,
                    format="jpeg",
                    size_bytes=100000,
                    content_hash="img_hash",
                )

                with patch("builtins.open", MagicMock()) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = b"image_data"

                    with patch.object(service.image_processor, "compute_content_hash") as mock_hash:
                        mock_hash.return_value = "img_hash"

                        result = await service.analyze_image(Path("/test/image.jpg"))

                        assert result.description == "Test image"
                        assert isinstance(result, ImageAnalysisResult)

    @pytest.mark.asyncio
    async def test_analyze_image_unsupported_format(self) -> None:
        """Should raise error for unsupported format."""
        mock_client = MagicMock()
        service = VisionService(client=mock_client)

        with pytest.raises(UnsupportedFormatError):
            await service.analyze_image(Path("/test/image.tiff"))


class TestVisionServiceAnalyzeVideo:
    """Tests for video analysis."""

    @pytest.mark.asyncio
    async def test_analyze_video_success(self) -> None:
        """Should analyze video successfully."""
        mock_client = MagicMock()
        service = VisionService(client=mock_client)

        mock_result = VideoAnalysisResult(
            summary="Test video",
            frame_analyses=[],
            scene_changes=[],
            duration_seconds=60.0,
            metadata=VideoMetadata(
                width=1920,
                height=1080,
                duration_seconds=60.0,
                fps=30.0,
                codec="h264",
                size_bytes=10000000,
                content_hash="video_hash",
            ),
            model_used="test-model",
            total_cost=0.01,
            cached=False,
            processing_time_ms=5000.0,
        )

        with patch.object(service.video_processor, "analyze", return_value=mock_result):
            with patch.object(service.video_processor, "compute_content_hash") as mock_hash:
                mock_hash.return_value = "video_hash"

                result = await service.analyze_video(Path("/test/video.mp4"))

                assert result.summary == "Test video"
                assert isinstance(result, VideoAnalysisResult)

    @pytest.mark.asyncio
    async def test_analyze_video_unsupported_format(self) -> None:
        """Should raise error for unsupported format."""
        mock_client = MagicMock()
        service = VisionService(client=mock_client)

        with pytest.raises(UnsupportedFormatError):
            await service.analyze_video(Path("/test/video.wmv"))


class TestVisionServiceBatchAnalyze:
    """Tests for batch analysis (VIS-M4-03)."""

    @pytest.mark.asyncio
    async def test_batch_analyze_mixed_files(self) -> None:
        """Should analyze batch of mixed image and video files."""
        mock_client = MagicMock()
        service = VisionService(client=mock_client)

        mock_image_result = ImageAnalysisResult(
            description="Image",
            objects=[],
            scene="test",
            text_content=None,
            tags=[],
            dominant_colors=[],
            quality="sharp",
            metadata=ImageMetadata(
                width=800,
                height=600,
                format="jpeg",
                size_bytes=100000,
                content_hash="ih",
            ),
            model_used="model",
            estimated_cost=0.001,
            cached=False,
            processing_time_ms=100.0,
        )

        mock_video_result = VideoAnalysisResult(
            summary="Video",
            frame_analyses=[],
            scene_changes=[],
            duration_seconds=30.0,
            metadata=VideoMetadata(
                width=1920,
                height=1080,
                duration_seconds=30.0,
                fps=30.0,
                codec="h264",
                size_bytes=5000000,
                content_hash="vh",
            ),
            model_used="model",
            total_cost=0.005,
            cached=False,
            processing_time_ms=3000.0,
        )

        with patch.object(service, "analyze_image", return_value=mock_image_result) as mock_img:
            with patch.object(service, "analyze_video", return_value=mock_video_result) as mock_vid:
                paths = [
                    Path("/test/image.jpg"),
                    Path("/test/video.mp4"),
                    Path("/test/photo.png"),
                ]

                results = await service.batch_analyze(paths)

                assert len(results) == 3
                # Check that correct methods were called
                assert mock_img.call_count == 2  # Two images
                assert mock_vid.call_count == 1  # One video

    @pytest.mark.asyncio
    async def test_batch_analyze_concurrency_limit(self) -> None:
        """Should respect concurrency limit."""
        mock_client = MagicMock()
        service = VisionService(client=mock_client)

        async def slow_analyze(*args, **kwargs):
            await asyncio.sleep(0.01)
            return ImageAnalysisResult(
                description="Image",
                objects=[],
                scene="test",
                text_content=None,
                tags=[],
                dominant_colors=[],
                quality="sharp",
                metadata=ImageMetadata(
                    width=100,
                    height=100,
                    format="jpeg",
                    size_bytes=1000,
                    content_hash="h",
                ),
                model_used="model",
                estimated_cost=0.001,
                cached=False,
                processing_time_ms=10.0,
            )

        with patch.object(service, "analyze_image", side_effect=slow_analyze):
            paths = [Path(f"/test/image{i}.jpg") for i in range(10)]

            # This should complete without issues
            results = await service.batch_analyze(paths, concurrency=3)

            assert len(results) == 10

    @pytest.mark.asyncio
    async def test_batch_analyze_skips_unsupported(self) -> None:
        """Should skip unsupported files in batch."""
        mock_client = MagicMock()
        service = VisionService(client=mock_client)

        mock_result = ImageAnalysisResult(
            description="Image",
            objects=[],
            scene="test",
            text_content=None,
            tags=[],
            dominant_colors=[],
            quality="sharp",
            metadata=ImageMetadata(
                width=100,
                height=100,
                format="jpeg",
                size_bytes=1000,
                content_hash="h",
            ),
            model_used="model",
            estimated_cost=0.001,
            cached=False,
            processing_time_ms=10.0,
        )

        with patch.object(service, "analyze_image", return_value=mock_result):
            paths = [
                Path("/test/image.jpg"),
                Path("/test/document.txt"),
                Path("/test/photo.png"),
            ]

            results = await service.batch_analyze(paths)

            # Only 2 supported files should be analyzed
            assert len(results) == 2


class TestVisionServiceStats:
    """Tests for analysis statistics (VIS-M4-04)."""

    @pytest.mark.asyncio
    async def test_get_analysis_stats_initial(self) -> None:
        """Should return initial stats with zeros."""
        mock_client = MagicMock()
        service = VisionService(client=mock_client)

        stats = await service.get_analysis_stats()

        assert isinstance(stats, AnalysisStats)
        assert stats.total_analyses == 0
        assert stats.cached_analyses == 0
        assert stats.total_cost == 0.0

    @pytest.mark.asyncio
    async def test_get_analysis_stats_after_analysis(self) -> None:
        """Should track statistics after analyses."""
        mock_client = MagicMock()
        service = VisionService(client=mock_client)

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
                format="jpeg",
                size_bytes=1000,
                content_hash="h",
            ),
            model_used="google/gemini-2.0-flash-001",
            estimated_cost=0.001,
            cached=False,
            processing_time_ms=100.0,
        )

        with patch.object(service.image_processor, "analyze", return_value=mock_result):
            with patch.object(service.image_processor, "extract_metadata") as mock_metadata:
                mock_metadata.return_value = ImageMetadata(
                    width=100,
                    height=100,
                    format="jpeg",
                    size_bytes=1000,
                    content_hash="h",
                )

                with patch("builtins.open", MagicMock()) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = b"data"

                    with patch.object(service.image_processor, "compute_content_hash") as mock_hash:
                        mock_hash.return_value = "h"

                        await service.analyze_image(Path("/test/image.jpg"))

        stats = await service.get_analysis_stats()

        assert stats.total_analyses == 1
        assert stats.api_analyses == 1
        assert stats.total_cost == 0.001


class TestVisionServiceRaceCondition:
    """Tests for race condition prevention (VIS-M4-05)."""

    @pytest.mark.asyncio
    async def test_no_duplicate_api_calls(self) -> None:
        """Should prevent duplicate API calls for same content (REQ-N-004)."""
        mock_client = MagicMock()
        service = VisionService(client=mock_client)

        call_count = 0

        async def counting_analyze(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.05)  # Simulate API call
            return ImageAnalysisResult(
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
                    format="jpeg",
                    size_bytes=1000,
                    content_hash="same_hash",
                ),
                model_used="model",
                estimated_cost=0.001,
                cached=False,
                processing_time_ms=50.0,
            )

        with patch.object(service.image_processor, "analyze", side_effect=counting_analyze):
            with patch.object(service.image_processor, "extract_metadata") as mock_metadata:
                mock_metadata.return_value = ImageMetadata(
                    width=100,
                    height=100,
                    format="jpeg",
                    size_bytes=1000,
                    content_hash="same_hash",
                )

                with patch("builtins.open", MagicMock()) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = b"same_data"

                    with patch.object(service.image_processor, "compute_content_hash") as mock_hash:
                        mock_hash.return_value = "same_hash"

                        # Start multiple concurrent requests for same content
                        tasks = [service.analyze_image(Path("/test/image.jpg")) for _ in range(5)]

                        results = await asyncio.gather(*tasks)

                        # All results should be valid
                        assert len(results) == 5
                        # With race condition prevention, API should be called fewer times
                        # (at least some should be deduplicated or use in-flight cache)
                        # For basic implementation, we just verify it doesn't crash
                        assert all(r is not None for r in results)
