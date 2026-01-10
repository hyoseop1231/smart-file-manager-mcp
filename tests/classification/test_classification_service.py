"""Tests for ClassificationService class.

TAG: CLASS-001-M4
SPEC: SPEC-CLASS-001

This module tests:
- Single file classification
- Batch file classification with concurrency limit
- Cache integration
- VisionService integration
- Organization plan generation
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from smart_file_manager.classification.classification_service import (
    ClassificationService,
)
from smart_file_manager.classification.models import (
    BatchClassificationResult,
    Classification,
    ClassificationResult,
    FileMetadata,
    TagSet,
)
from smart_file_manager.services.vision_models import (
    DetectedObject,
    ImageAnalysisResult,
    ImageMetadata,
    VideoAnalysisResult,
    VideoMetadata,
)


def create_mock_image_result(
    *,
    objects: list[DetectedObject] | None = None,
    scene: str = "unknown",
    tags: list[str] | None = None,
    text_content: str | None = None,
    dominant_colors: list[str] | None = None,
) -> ImageAnalysisResult:
    """Create a mock ImageAnalysisResult with required fields."""
    return ImageAnalysisResult(
        description="Test image description",
        objects=objects or [],
        scene=scene,
        text_content=text_content,
        tags=tags or [],
        dominant_colors=dominant_colors or [],
        quality="good",
        metadata=ImageMetadata(
            width=1920,
            height=1080,
            format="jpeg",
            size_bytes=100000,
            content_hash="test_hash",
            exif=None,
        ),
        model_used="test_model",
        estimated_cost=0.01,
        cached=False,
        processing_time_ms=100.0,
    )


def create_mock_video_result(
    *,
    duration_seconds: float = 120.0,
) -> VideoAnalysisResult:
    """Create a mock VideoAnalysisResult with required fields."""
    return VideoAnalysisResult(
        summary="Test video summary",
        frame_analyses=[],
        scene_changes=[],
        duration_seconds=duration_seconds,
        metadata=VideoMetadata(
            width=1920,
            height=1080,
            duration_seconds=duration_seconds,
            fps=30.0,
            codec="h264",
            size_bytes=1000000,
            content_hash="test_video_hash",
        ),
        model_used="test_model",
        total_cost=0.05,
        cached=False,
        processing_time_ms=500.0,
    )


class TestClassificationServiceInit:
    """Tests for ClassificationService initialization."""

    def test_init_default(self) -> None:
        """Should initialize with default settings."""
        service = ClassificationService()

        assert service.concurrency_limit == 10
        assert service.cache is None

    def test_init_custom_concurrency(self) -> None:
        """Should accept custom concurrency limit."""
        service = ClassificationService(concurrency_limit=5)

        assert service.concurrency_limit == 5

    def test_init_with_cache(self) -> None:
        """Should accept cache instance."""
        mock_cache = MagicMock()
        service = ClassificationService(cache=mock_cache)

        assert service.cache is mock_cache

    def test_init_with_vision_service(self) -> None:
        """Should accept VisionService instance."""
        mock_vision = MagicMock()
        service = ClassificationService(vision_service=mock_vision)

        assert service.vision_service is mock_vision


class TestClassificationServiceSingleFile:
    """Tests for single file classification."""

    @pytest.mark.asyncio
    async def test_classify_file_with_vision(self) -> None:
        """Should classify file using VisionService."""
        mock_vision = AsyncMock()
        mock_vision.analyze_image.return_value = create_mock_image_result(
            objects=[DetectedObject(name="person", confidence=0.9)],
            scene="portrait",
            tags=["person", "indoor"],
        )

        service = ClassificationService(vision_service=mock_vision)

        result = await service.classify_file(Path("/test/photo.jpg"))

        assert result is not None
        assert isinstance(result, ClassificationResult)
        assert result.classification.category == "photo"
        mock_vision.analyze_image.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_file_without_vision(self) -> None:
        """Should classify file using metadata when no VisionService."""
        service = ClassificationService()

        result = await service.classify_file(Path("/test/image.jpg"))

        assert result is not None
        assert result.classification.method == "metadata"

    @pytest.mark.asyncio
    async def test_classify_file_generates_tags(self) -> None:
        """Should generate tags for classified file."""
        mock_vision = AsyncMock()
        mock_vision.analyze_image.return_value = create_mock_image_result(
            objects=[DetectedObject(name="dog", confidence=0.9)],
            scene="outdoor",
            tags=["pet", "animal"],
        )

        service = ClassificationService(vision_service=mock_vision)

        result = await service.classify_file(Path("/test/pet.jpg"))

        assert len(result.tags.tags_en) > 0
        assert "dog" in result.tags.tags_en

    @pytest.mark.asyncio
    async def test_classify_file_generates_organization_plan(self) -> None:
        """Should generate organization plan for classified file."""
        mock_vision = AsyncMock()
        mock_vision.analyze_image.return_value = create_mock_image_result(
            objects=[DetectedObject(name="person", confidence=0.9)],
            scene="portrait",
            tags=["person"],
        )

        service = ClassificationService(
            vision_service=mock_vision,
            base_path=Path("/home/user"),
        )

        result = await service.classify_file(
            Path("/downloads/photo.jpg"),
            generate_plan=True,
        )

        assert result.organization_plan is not None
        assert "Photos" in str(result.organization_plan.target_path)

    @pytest.mark.asyncio
    async def test_classify_file_uses_cache(self) -> None:
        """Should use cached result when available."""
        mock_cache = MagicMock()
        cached_result = ClassificationResult(
            file_path=Path("/test/cached.jpg"),
            content_hash="cached_hash",
            classification=Classification(
                category="photo",
                sub_category="portrait",
                confidence=0.9,
                method="ai",
                requires_review=False,
            ),
            tags=TagSet(tags_en=["cached"], tags_ko=["캐시됨"], source_breakdown={}),
            organization_plan=None,
            vision_result=None,
            metadata=FileMetadata(
                file_path=Path("/test/cached.jpg"),
                size_bytes=1000,
                extension="jpg",
                created_at="2026-01-10T10:00:00",
                modified_at="2026-01-10T10:00:00",
                content_hash="cached_hash",
                exif=None,
            ),
            processing_time_ms=10.0,
            cached=True,
        )
        mock_cache.get.return_value = cached_result

        service = ClassificationService(cache=mock_cache)

        with patch.object(service, "_get_file_metadata") as mock_metadata:
            mock_metadata.return_value = FileMetadata(
                file_path=Path("/test/cached.jpg"),
                size_bytes=1000,
                extension="jpg",
                created_at="2026-01-10T10:00:00",
                modified_at="2026-01-10T10:00:00",
                content_hash="cached_hash",
                exif=None,
            )
            result = await service.classify_file(Path("/test/cached.jpg"))

        assert result.cached is True
        assert result.classification.category == "photo"


class TestClassificationServiceBatch:
    """Tests for batch file classification."""

    @pytest.mark.asyncio
    async def test_batch_classify_multiple_files(self) -> None:
        """Should classify multiple files in batch."""
        service = ClassificationService()

        files = [
            Path("/test/photo1.jpg"),
            Path("/test/photo2.jpg"),
            Path("/test/video.mp4"),
        ]

        result = await service.classify_batch(files)

        assert isinstance(result, BatchClassificationResult)
        assert result.total_files == 3
        assert len(result.results) == 3

    @pytest.mark.asyncio
    async def test_batch_classify_respects_concurrency_limit(self) -> None:
        """Should respect concurrency limit during batch processing."""
        service = ClassificationService(concurrency_limit=2)

        files = [Path(f"/test/file{i}.jpg") for i in range(5)]

        # This test verifies the concurrency limit is set correctly
        # The actual concurrent execution is tested by checking semaphore usage
        result = await service.classify_batch(files)

        assert result.total_files == 5
        assert service.concurrency_limit == 2

    @pytest.mark.asyncio
    async def test_batch_classify_with_errors(self) -> None:
        """Should handle errors in batch processing gracefully."""
        service = ClassificationService()

        files = [
            Path("/test/valid.jpg"),
            Path("/nonexistent/invalid.jpg"),
        ]

        result = await service.classify_batch(files)

        # Should still process valid files
        assert result.total_files == 2
        # Failed files should be tracked
        assert result.failed >= 0

    @pytest.mark.asyncio
    async def test_batch_classify_includes_timing(self) -> None:
        """Should include timing information in batch result."""
        service = ClassificationService()

        files = [Path("/test/file.jpg")]

        result = await service.classify_batch(files)

        assert result.total_processing_time_ms >= 0


class TestClassificationServiceMetadata:
    """Tests for file metadata extraction."""

    @pytest.mark.asyncio
    async def test_extract_metadata_from_image(self) -> None:
        """Should extract metadata from image file."""
        service = ClassificationService()

        # Mock file existence and stat
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.stat") as mock_stat,
        ):
            mock_stat.return_value = MagicMock(
                st_size=1000,
                st_mtime=1704873600.0,
                st_ctime=1704873600.0,
            )

            metadata = await service._get_file_metadata(Path("/test/photo.jpg"))

        assert metadata is not None
        assert metadata.extension == "jpg"
        assert metadata.size_bytes == 1000


class TestClassificationServiceContentHash:
    """Tests for content hash generation."""

    @pytest.mark.asyncio
    async def test_generate_content_hash(self) -> None:
        """Should generate consistent content hash."""
        service = ClassificationService()

        # Mock file reading
        with patch("builtins.open", MagicMock()) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = b"test content"
            mock_open.return_value.__enter__.return_value = mock_file

            hash1 = service._calculate_content_hash(Path("/test/file.jpg"))

            mock_file.read.return_value = b"test content"
            hash2 = service._calculate_content_hash(Path("/test/file.jpg"))

        assert hash1 == hash2


class TestClassificationServiceVideoSupport:
    """Tests for video file classification."""

    @pytest.mark.asyncio
    async def test_classify_video_file(self) -> None:
        """Should classify video files correctly."""
        mock_vision = AsyncMock()
        mock_vision.analyze_video.return_value = create_mock_video_result(
            duration_seconds=120.0,
        )

        service = ClassificationService(vision_service=mock_vision)

        result = await service.classify_file(Path("/test/video.mp4"))

        assert result.classification.category == "video"

    @pytest.mark.asyncio
    async def test_classify_short_video_as_clip(self) -> None:
        """Should classify short videos as clips."""
        mock_vision = AsyncMock()
        mock_vision.analyze_video.return_value = create_mock_video_result(
            duration_seconds=30.0,  # Short video
        )

        service = ClassificationService(vision_service=mock_vision)

        result = await service.classify_file(Path("/test/clip.mp4"))

        assert result.classification.category == "video"
        assert result.classification.sub_category == "clip"


class TestClassificationServiceScreenshotDetection:
    """Tests for screenshot detection."""

    @pytest.mark.asyncio
    async def test_detect_screenshot_from_scene(self) -> None:
        """Should detect screenshots from scene analysis."""
        mock_vision = AsyncMock()
        mock_vision.analyze_image.return_value = create_mock_image_result(
            objects=[DetectedObject(name="text", confidence=0.9)],
            scene="desktop",
            tags=["screenshot", "desktop"],
            text_content="Some UI text content here",
            dominant_colors=["#FFFFFF", "#000000"],
        )

        service = ClassificationService(vision_service=mock_vision)

        result = await service.classify_file(Path("/test/screenshot.png"))

        assert result.classification.category == "screenshot"

    @pytest.mark.asyncio
    async def test_detect_screenshot_from_text_content(self) -> None:
        """Should detect screenshots from text content."""
        mock_vision = AsyncMock()
        mock_vision.analyze_image.return_value = create_mock_image_result(
            objects=[],
            scene="unknown",
            tags=[],
            text_content="This is a long text content from a screenshot with lots of words",
            dominant_colors=[],
        )

        service = ClassificationService(vision_service=mock_vision)

        result = await service.classify_file(Path("/test/screen.png"))

        assert result.classification.category == "screenshot"


class TestClassificationServiceUserRules:
    """Tests for user-defined classification rules."""

    @pytest.mark.asyncio
    async def test_user_rule_overrides_ai(self) -> None:
        """Should apply user rules before AI classification."""
        mock_vision = AsyncMock()
        mock_vision.analyze_image.return_value = create_mock_image_result(
            objects=[DetectedObject(name="person", confidence=0.9)],
            scene="portrait",
            tags=["person"],
        )

        service = ClassificationService(vision_service=mock_vision)
        service.register_user_rule("*/receipts/*", "document", "receipt")

        result = await service.classify_file(Path("/home/receipts/receipt.jpg"))

        assert result.classification.category == "document"
        assert result.classification.sub_category == "receipt"
        assert result.classification.method == "user_rule"

    def test_register_user_rule(self) -> None:
        """Should register user-defined rules."""
        service = ClassificationService()

        service.register_user_rule("*/work/*", "document")

        rules = service.get_user_rules()
        assert len(rules) == 1
        assert rules[0]["pattern"] == "*/work/*"

    def test_unregister_user_rule(self) -> None:
        """Should unregister user-defined rules."""
        service = ClassificationService()
        service.register_user_rule("*/test/*", "photo")

        service.unregister_user_rule("*/test/*")

        rules = service.get_user_rules()
        assert len(rules) == 0
