"""Tests for VideoProcessor class.

TAG: VIS-M3-01 to VIS-M3-08
SPEC: SPEC-VISION-001
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from smart_file_manager.processors.video_processor import VideoProcessor

from smart_file_manager.core.constants import (
    VISION_CACHE_TTL_SECONDS,
)
from smart_file_manager.core.exceptions import (
    DependencyError,
)
from smart_file_manager.services.vision_models import (
    ImageAnalysisResult,
    ImageMetadata,
    VideoMetadata,
)


class TestVideoProcessorInit:
    """Tests for VideoProcessor initialization (VIS-M3-01)."""

    def test_init_with_image_processor(self) -> None:
        """VideoProcessor should initialize with an ImageProcessor."""
        mock_image_processor = MagicMock()
        processor = VideoProcessor(image_processor=mock_image_processor)

        assert processor.image_processor == mock_image_processor
        assert processor.cache is None

    def test_init_with_cache(self) -> None:
        """VideoProcessor should accept optional cache."""
        mock_image_processor = MagicMock()
        mock_cache = MagicMock()
        processor = VideoProcessor(
            image_processor=mock_image_processor,
            cache=mock_cache,
        )

        assert processor.cache == mock_cache


class TestVideoProcessorValidateFormat:
    """Tests for video format validation."""

    def test_validate_format_mp4_supported(self) -> None:
        """MP4 format should be valid."""
        mock_image_processor = MagicMock()
        processor = VideoProcessor(image_processor=mock_image_processor)

        assert processor.validate_format(Path("test.mp4")) is True
        assert processor.validate_format(Path("test.MP4")) is True

    def test_validate_format_mkv_supported(self) -> None:
        """MKV format should be valid."""
        mock_image_processor = MagicMock()
        processor = VideoProcessor(image_processor=mock_image_processor)

        assert processor.validate_format(Path("test.mkv")) is True

    def test_validate_format_avi_supported(self) -> None:
        """AVI format should be valid."""
        mock_image_processor = MagicMock()
        processor = VideoProcessor(image_processor=mock_image_processor)

        assert processor.validate_format(Path("test.avi")) is True

    def test_validate_format_mov_supported(self) -> None:
        """MOV format should be valid."""
        mock_image_processor = MagicMock()
        processor = VideoProcessor(image_processor=mock_image_processor)

        assert processor.validate_format(Path("test.mov")) is True

    def test_validate_format_webm_supported(self) -> None:
        """WebM format should be valid."""
        mock_image_processor = MagicMock()
        processor = VideoProcessor(image_processor=mock_image_processor)

        assert processor.validate_format(Path("test.webm")) is True

    def test_validate_format_wmv_not_supported(self) -> None:
        """WMV format should NOT be valid."""
        mock_image_processor = MagicMock()
        processor = VideoProcessor(image_processor=mock_image_processor)

        assert processor.validate_format(Path("test.wmv")) is False


class TestVideoProcessorCheckFfmpeg:
    """Tests for FFmpeg dependency check (VIS-M3-07)."""

    def test_check_ffmpeg_available(self) -> None:
        """Should return True when FFmpeg is available."""
        mock_image_processor = MagicMock()
        processor = VideoProcessor(image_processor=mock_image_processor)

        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            assert processor.check_ffmpeg_available() is True

    def test_check_ffmpeg_not_available(self) -> None:
        """Should return False when FFmpeg is not available."""
        mock_image_processor = MagicMock()
        processor = VideoProcessor(image_processor=mock_image_processor)

        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            assert processor.check_ffmpeg_available() is False


class TestVideoProcessorExtractKeyframes:
    """Tests for keyframe extraction (VIS-M3-02)."""

    def test_extract_keyframes_calls_ffmpeg(self) -> None:
        """Should call FFmpeg to extract keyframes."""
        mock_image_processor = MagicMock()
        processor = VideoProcessor(image_processor=mock_image_processor)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            with patch("pathlib.Path.glob") as mock_glob:
                # Mock extracted frames
                mock_glob.return_value = [
                    Path("/tmp/frame_001.jpg"),
                    Path("/tmp/frame_002.jpg"),
                ]

                with patch("builtins.open", MagicMock()) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = b"frame_data"

                    frames = processor.extract_keyframes(
                        video_path=Path("/test/video.mp4"),
                        interval=5.0,
                        output_dir=Path("/tmp"),
                    )

                    mock_run.assert_called_once()
                    # FFmpeg should be called with correct arguments
                    call_args = mock_run.call_args[0][0]
                    assert "ffmpeg" in call_args[0]

    def test_extract_keyframes_raises_on_ffmpeg_missing(self) -> None:
        """Should raise DependencyError when FFmpeg is not available."""
        mock_image_processor = MagicMock()
        processor = VideoProcessor(image_processor=mock_image_processor)

        with patch.object(processor, "check_ffmpeg_available", return_value=False):
            with pytest.raises(DependencyError) as exc_info:
                processor.extract_keyframes(
                    video_path=Path("/test/video.mp4"),
                    interval=5.0,
                    output_dir=Path("/tmp"),
                )

            assert exc_info.value.dependency_name == "ffmpeg"


class TestVideoProcessorSelectRepresentativeFrames:
    """Tests for representative frame selection (VIS-M3-03)."""

    def test_select_representative_frames_max_count(self) -> None:
        """Should select up to max_count representative frames."""
        mock_image_processor = MagicMock()
        processor = VideoProcessor(image_processor=mock_image_processor)

        frames = [b"frame1", b"frame2", b"frame3", b"frame4", b"frame5", b"frame6"]

        selected = processor.select_representative_frames(
            frames=frames,
            max_count=3,
        )

        assert len(selected) == 3

    def test_select_representative_frames_fewer_than_max(self) -> None:
        """Should return all frames if fewer than max_count."""
        mock_image_processor = MagicMock()
        processor = VideoProcessor(image_processor=mock_image_processor)

        frames = [b"frame1", b"frame2"]

        selected = processor.select_representative_frames(
            frames=frames,
            max_count=5,
        )

        assert len(selected) == 2

    def test_select_representative_frames_empty(self) -> None:
        """Should handle empty frames list."""
        mock_image_processor = MagicMock()
        processor = VideoProcessor(image_processor=mock_image_processor)

        selected = processor.select_representative_frames(
            frames=[],
            max_count=5,
        )

        assert len(selected) == 0


class TestVideoProcessorGetMetadata:
    """Tests for video metadata extraction (VIS-M3-04)."""

    def test_get_video_metadata(self) -> None:
        """Should extract video metadata using FFprobe."""
        mock_image_processor = MagicMock()
        processor = VideoProcessor(image_processor=mock_image_processor)

        ffprobe_output = {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "30/1",
                    "codec_name": "h264",
                }
            ],
            "format": {
                "duration": "120.5",
                "size": "50000000",
            },
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=str(ffprobe_output).replace("'", '"'),
            )

            with patch("json.loads") as mock_json:
                mock_json.return_value = ffprobe_output

                metadata = processor.get_video_metadata(
                    video_path=Path("/test/video.mp4"),
                    content_hash="video_hash_123",
                )

                assert metadata.width == 1920
                assert metadata.height == 1080
                assert metadata.duration_seconds == 120.5
                assert metadata.fps == 30.0
                assert metadata.codec == "h264"
                assert metadata.content_hash == "video_hash_123"


class TestVideoProcessorCalculateInterval:
    """Tests for keyframe interval calculation."""

    def test_calculate_interval_short_video(self) -> None:
        """Short videos should have 5s interval."""
        mock_image_processor = MagicMock()
        processor = VideoProcessor(image_processor=mock_image_processor)

        interval, max_frames = processor.calculate_keyframe_interval(duration_seconds=30)
        assert interval == 5
        assert max_frames == 12

    def test_calculate_interval_medium_video(self) -> None:
        """Medium videos (1-5 min) should have 15s interval."""
        mock_image_processor = MagicMock()
        processor = VideoProcessor(image_processor=mock_image_processor)

        interval, max_frames = processor.calculate_keyframe_interval(duration_seconds=180)
        assert interval == 15
        assert max_frames == 20

    def test_calculate_interval_long_video(self) -> None:
        """Long videos (5-10 min) should have 30s interval."""
        mock_image_processor = MagicMock()
        processor = VideoProcessor(image_processor=mock_image_processor)

        interval, max_frames = processor.calculate_keyframe_interval(duration_seconds=420)
        assert interval == 30
        assert max_frames == 20

    def test_calculate_interval_very_long_video(self) -> None:
        """Very long videos (10+ min) should have 60s interval."""
        mock_image_processor = MagicMock()
        processor = VideoProcessor(image_processor=mock_image_processor)

        interval, max_frames = processor.calculate_keyframe_interval(duration_seconds=900)
        assert interval == 60
        assert max_frames == 30


class TestVideoProcessorAnalyze:
    """Tests for video analysis (VIS-M3-05, VIS-M3-06)."""

    @pytest.mark.asyncio
    async def test_analyze_cache_hit(self) -> None:
        """Should return cached result on cache hit."""
        mock_image_processor = MagicMock()
        mock_cache = AsyncMock()

        cached_data = {
            "summary": "Cached video summary",
            "frame_analyses": [],
            "scene_changes": [],
            "duration_seconds": 60.0,
            "metadata": {
                "width": 1920,
                "height": 1080,
                "duration_seconds": 60.0,
                "fps": 30.0,
                "codec": "h264",
                "size_bytes": 10000000,
                "content_hash": "cached_hash",
            },
            "model_used": "google/gemini-2.0-flash-001",
            "total_cost": 0.01,
            "cached": True,
            "processing_time_ms": 50.0,
        }
        mock_cache.get.return_value = cached_data

        processor = VideoProcessor(
            image_processor=mock_image_processor,
            cache=mock_cache,
        )

        result = await processor.analyze(
            video_path=Path("/test/video.mp4"),
            content_hash="cached_hash",
        )

        assert result.cached is True
        assert result.summary == "Cached video summary"

    @pytest.mark.asyncio
    async def test_analyze_extracts_and_processes_frames(self) -> None:
        """Should extract keyframes and analyze each."""
        mock_image_processor = AsyncMock()
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None

        # Mock frame analysis result
        mock_frame_result = ImageAnalysisResult(
            description="Frame description",
            objects=[],
            scene="outdoor",
            text_content=None,
            tags=["frame"],
            dominant_colors=["blue"],
            quality="sharp",
            metadata=ImageMetadata(
                width=1920,
                height=1080,
                format="jpeg",
                size_bytes=100000,
                content_hash="frame_hash",
            ),
            model_used="test-model",
            estimated_cost=0.001,
            cached=False,
            processing_time_ms=100.0,
        )
        mock_image_processor.analyze.return_value = mock_frame_result

        processor = VideoProcessor(
            image_processor=mock_image_processor,
            cache=mock_cache,
        )

        with patch.object(processor, "check_ffmpeg_available", return_value=True):
            with patch.object(processor, "get_video_metadata") as mock_metadata:
                mock_metadata.return_value = VideoMetadata(
                    width=1920,
                    height=1080,
                    duration_seconds=30.0,
                    fps=30.0,
                    codec="h264",
                    size_bytes=5000000,
                    content_hash="test_video_hash",
                )

                with patch.object(processor, "extract_keyframes") as mock_extract:
                    mock_extract.return_value = [b"frame1", b"frame2"]

                    with patch.object(processor, "select_representative_frames") as mock_select:
                        mock_select.return_value = [b"frame1", b"frame2"]

                        result = await processor.analyze(
                            video_path=Path("/test/video.mp4"),
                            content_hash="test_video_hash",
                        )

                        assert len(result.frame_analyses) == 2
                        assert mock_image_processor.analyze.call_count == 2

    @pytest.mark.asyncio
    async def test_analyze_raises_dependency_error(self) -> None:
        """Should raise DependencyError when FFmpeg is missing."""
        mock_image_processor = MagicMock()
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None

        processor = VideoProcessor(
            image_processor=mock_image_processor,
            cache=mock_cache,
        )

        with patch.object(processor, "check_ffmpeg_available", return_value=False):
            with pytest.raises(DependencyError) as exc_info:
                await processor.analyze(
                    video_path=Path("/test/video.mp4"),
                    content_hash="test_hash",
                )

            assert exc_info.value.dependency_name == "ffmpeg"

    @pytest.mark.asyncio
    async def test_analyze_stores_result_in_cache(self) -> None:
        """Should store successful result in cache."""
        mock_image_processor = AsyncMock()
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None

        mock_frame_result = ImageAnalysisResult(
            description="Frame",
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
                size_bytes=50000,
                content_hash="fh",
            ),
            model_used="model",
            estimated_cost=0.001,
            cached=False,
            processing_time_ms=50.0,
        )
        mock_image_processor.analyze.return_value = mock_frame_result

        processor = VideoProcessor(
            image_processor=mock_image_processor,
            cache=mock_cache,
        )

        with patch.object(processor, "check_ffmpeg_available", return_value=True):
            with patch.object(processor, "get_video_metadata") as mock_metadata:
                mock_metadata.return_value = VideoMetadata(
                    width=800,
                    height=600,
                    duration_seconds=10.0,
                    fps=24.0,
                    codec="h264",
                    size_bytes=1000000,
                    content_hash="vh",
                )

                with patch.object(processor, "extract_keyframes") as mock_extract:
                    mock_extract.return_value = [b"frame"]

                    with patch.object(processor, "select_representative_frames") as mock_select:
                        mock_select.return_value = [b"frame"]

                        await processor.analyze(
                            video_path=Path("/test/video.mp4"),
                            content_hash="vh",
                        )

                        mock_cache.set.assert_called_once()
                        call_args = mock_cache.set.call_args
                        assert call_args[1].get("ttl") == VISION_CACHE_TTL_SECONDS


class TestVideoProcessorHelpers:
    """Tests for helper methods."""

    def test_compute_content_hash(self) -> None:
        """Should compute SHA256 hash of video file."""
        mock_image_processor = MagicMock()
        processor = VideoProcessor(image_processor=mock_image_processor)

        with patch("builtins.open", MagicMock()) as mock_open:
            mock_file = MagicMock()
            mock_file.__enter__.return_value.read.side_effect = [b"chunk1", b"chunk2", b""]
            mock_open.return_value = mock_file

            result = processor.compute_content_hash(Path("/test/video.mp4"))

            # Should return a valid hash string
            assert isinstance(result, str)
            assert len(result) == 64  # SHA256 hex digest length
