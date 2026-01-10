"""Tests for Vision data models.

TAG: VIS-M1-03
SPEC: SPEC-VISION-001
"""




class TestImageMetadata:
    """Tests for ImageMetadata dataclass."""

    def test_image_metadata_creation(self) -> None:
        """ImageMetadata should be creatable with required fields."""
        from smart_file_manager.services.vision_models import ImageMetadata

        metadata = ImageMetadata(
            width=1920,
            height=1080,
            format="jpeg",
            size_bytes=1024000,
            content_hash="abc123def456",
        )
        assert metadata.width == 1920
        assert metadata.height == 1080
        assert metadata.format == "jpeg"
        assert metadata.size_bytes == 1024000
        assert metadata.content_hash == "abc123def456"

    def test_image_metadata_optional_exif(self) -> None:
        """ImageMetadata should accept optional exif data."""
        from smart_file_manager.services.vision_models import ImageMetadata

        exif_data = {"Make": "Canon", "Model": "EOS R5"}
        metadata = ImageMetadata(
            width=1920,
            height=1080,
            format="jpeg",
            size_bytes=1024000,
            content_hash="abc123",
            exif=exif_data,
        )
        assert metadata.exif == exif_data

    def test_image_metadata_exif_default_none(self) -> None:
        """ImageMetadata.exif should default to None."""
        from smart_file_manager.services.vision_models import ImageMetadata

        metadata = ImageMetadata(
            width=800,
            height=600,
            format="png",
            size_bytes=500000,
            content_hash="xyz789",
        )
        assert metadata.exif is None


class TestVideoMetadata:
    """Tests for VideoMetadata dataclass."""

    def test_video_metadata_creation(self) -> None:
        """VideoMetadata should be creatable with required fields."""
        from smart_file_manager.services.vision_models import VideoMetadata

        metadata = VideoMetadata(
            width=1920,
            height=1080,
            duration_seconds=120.5,
            fps=30.0,
            codec="h264",
            size_bytes=50000000,
            content_hash="video_hash_123",
        )
        assert metadata.width == 1920
        assert metadata.height == 1080
        assert metadata.duration_seconds == 120.5
        assert metadata.fps == 30.0
        assert metadata.codec == "h264"
        assert metadata.size_bytes == 50000000
        assert metadata.content_hash == "video_hash_123"


class TestDetectedObject:
    """Tests for DetectedObject dataclass."""

    def test_detected_object_creation(self) -> None:
        """DetectedObject should be creatable with required fields."""
        from smart_file_manager.services.vision_models import DetectedObject

        obj = DetectedObject(
            name="car",
            confidence=0.95,
        )
        assert obj.name == "car"
        assert obj.confidence == 0.95

    def test_detected_object_with_bounding_box(self) -> None:
        """DetectedObject should accept optional bounding_box."""
        from smart_file_manager.services.vision_models import (
            BoundingBox,
            DetectedObject,
        )

        bbox = BoundingBox(x=100, y=200, width=300, height=400)
        obj = DetectedObject(
            name="person",
            confidence=0.88,
            bounding_box=bbox,
        )
        assert obj.bounding_box is not None
        assert obj.bounding_box.x == 100
        assert obj.bounding_box.y == 200

    def test_detected_object_bounding_box_default_none(self) -> None:
        """DetectedObject.bounding_box should default to None."""
        from smart_file_manager.services.vision_models import DetectedObject

        obj = DetectedObject(name="tree", confidence=0.75)
        assert obj.bounding_box is None


class TestBoundingBox:
    """Tests for BoundingBox dataclass."""

    def test_bounding_box_creation(self) -> None:
        """BoundingBox should be creatable with required fields."""
        from smart_file_manager.services.vision_models import BoundingBox

        bbox = BoundingBox(x=10, y=20, width=100, height=150)
        assert bbox.x == 10
        assert bbox.y == 20
        assert bbox.width == 100
        assert bbox.height == 150


class TestImageAnalysisResult:
    """Tests for ImageAnalysisResult dataclass."""

    def test_image_analysis_result_creation(self) -> None:
        """ImageAnalysisResult should be creatable with all fields."""
        from smart_file_manager.services.vision_models import (
            DetectedObject,
            ImageAnalysisResult,
            ImageMetadata,
        )

        metadata = ImageMetadata(
            width=1920,
            height=1080,
            format="jpeg",
            size_bytes=1024000,
            content_hash="abc123",
        )
        objects = [DetectedObject(name="car", confidence=0.95)]

        result = ImageAnalysisResult(
            description="A red car parked on a street",
            objects=objects,
            scene="urban",
            text_content="ABC-123",
            tags=["car", "street", "urban"],
            dominant_colors=["red", "gray", "black"],
            quality="sharp",
            metadata=metadata,
            model_used="google/gemini-2.0-flash-001",
            estimated_cost=0.001,
            cached=False,
            processing_time_ms=1500.0,
        )

        assert result.description == "A red car parked on a street"
        assert len(result.objects) == 1
        assert result.scene == "urban"
        assert result.text_content == "ABC-123"
        assert result.tags == ["car", "street", "urban"]
        assert result.dominant_colors == ["red", "gray", "black"]
        assert result.quality == "sharp"
        assert result.model_used == "google/gemini-2.0-flash-001"
        assert result.estimated_cost == 0.001
        assert result.cached is False
        assert result.processing_time_ms == 1500.0

    def test_image_analysis_result_text_content_optional(self) -> None:
        """ImageAnalysisResult.text_content should be optional (None)."""
        from smart_file_manager.services.vision_models import (
            ImageAnalysisResult,
            ImageMetadata,
        )

        metadata = ImageMetadata(
            width=800,
            height=600,
            format="png",
            size_bytes=500000,
            content_hash="xyz",
        )

        result = ImageAnalysisResult(
            description="A sunset over mountains",
            objects=[],
            scene="nature",
            text_content=None,
            tags=["sunset", "mountains"],
            dominant_colors=["orange", "purple"],
            quality="sharp",
            metadata=metadata,
            model_used="google/gemini-2.0-flash-001",
            estimated_cost=0.001,
            cached=True,
            processing_time_ms=50.0,
        )
        assert result.text_content is None

    def test_image_analysis_result_to_dict(self) -> None:
        """ImageAnalysisResult should be convertible to dict."""
        from smart_file_manager.services.vision_models import (
            ImageAnalysisResult,
            ImageMetadata,
        )

        metadata = ImageMetadata(
            width=800,
            height=600,
            format="png",
            size_bytes=500000,
            content_hash="xyz",
        )

        result = ImageAnalysisResult(
            description="Test image",
            objects=[],
            scene="indoor",
            text_content=None,
            tags=["test"],
            dominant_colors=["white"],
            quality="sharp",
            metadata=metadata,
            model_used="test-model",
            estimated_cost=0.001,
            cached=False,
            processing_time_ms=100.0,
        )

        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict["description"] == "Test image"
        assert result_dict["scene"] == "indoor"

    def test_image_analysis_result_from_dict(self) -> None:
        """ImageAnalysisResult should be creatable from dict (for cache deserialization)."""
        from smart_file_manager.services.vision_models import ImageAnalysisResult

        data = {
            "description": "A landscape photo",
            "objects": [{"name": "tree", "confidence": 0.9, "bounding_box": None}],
            "scene": "nature",
            "text_content": None,
            "tags": ["landscape", "nature"],
            "dominant_colors": ["green", "blue"],
            "quality": "sharp",
            "metadata": {
                "width": 1920,
                "height": 1080,
                "format": "jpeg",
                "size_bytes": 2000000,
                "content_hash": "hash123",
                "exif": None,
            },
            "model_used": "google/gemini-2.0-flash-001",
            "estimated_cost": 0.002,
            "cached": True,
            "processing_time_ms": 1200.0,
        }

        result = ImageAnalysisResult.from_dict(data)
        assert result.description == "A landscape photo"
        assert result.scene == "nature"
        assert result.cached is True


class TestFrameAnalysisResult:
    """Tests for FrameAnalysisResult dataclass."""

    def test_frame_analysis_result_creation(self) -> None:
        """FrameAnalysisResult should include frame_index and timestamp."""
        from smart_file_manager.services.vision_models import (
            FrameAnalysisResult,
            ImageAnalysisResult,
            ImageMetadata,
        )

        metadata = ImageMetadata(
            width=1920,
            height=1080,
            format="jpeg",
            size_bytes=100000,
            content_hash="frame_hash",
        )

        image_result = ImageAnalysisResult(
            description="Frame showing a person walking",
            objects=[],
            scene="outdoor",
            text_content=None,
            tags=["person", "walking"],
            dominant_colors=["gray"],
            quality="sharp",
            metadata=metadata,
            model_used="test-model",
            estimated_cost=0.001,
            cached=False,
            processing_time_ms=100.0,
        )

        frame_result = FrameAnalysisResult(
            frame_index=5,
            timestamp_seconds=15.0,
            analysis=image_result,
        )

        assert frame_result.frame_index == 5
        assert frame_result.timestamp_seconds == 15.0
        assert frame_result.analysis.description == "Frame showing a person walking"


class TestSceneChange:
    """Tests for SceneChange dataclass."""

    def test_scene_change_creation(self) -> None:
        """SceneChange should be creatable with timestamp and descriptions."""
        from smart_file_manager.services.vision_models import SceneChange

        scene_change = SceneChange(
            timestamp_seconds=30.5,
            from_scene="indoor",
            to_scene="outdoor",
        )
        assert scene_change.timestamp_seconds == 30.5
        assert scene_change.from_scene == "indoor"
        assert scene_change.to_scene == "outdoor"


class TestVideoAnalysisResult:
    """Tests for VideoAnalysisResult dataclass."""

    def test_video_analysis_result_creation(self) -> None:
        """VideoAnalysisResult should be creatable with all fields."""
        from smart_file_manager.services.vision_models import (
            VideoAnalysisResult,
            VideoMetadata,
        )

        metadata = VideoMetadata(
            width=1920,
            height=1080,
            duration_seconds=120.0,
            fps=30.0,
            codec="h264",
            size_bytes=50000000,
            content_hash="video_hash",
        )

        result = VideoAnalysisResult(
            summary="A video showing traffic in an urban area",
            frame_analyses=[],
            scene_changes=[],
            duration_seconds=120.0,
            metadata=metadata,
            model_used="google/gemini-2.0-flash-001",
            total_cost=0.01,
            cached=False,
            processing_time_ms=15000.0,
        )

        assert result.summary == "A video showing traffic in an urban area"
        assert result.duration_seconds == 120.0
        assert result.total_cost == 0.01
        assert result.cached is False

    def test_video_analysis_result_to_dict(self) -> None:
        """VideoAnalysisResult should be convertible to dict."""
        from smart_file_manager.services.vision_models import (
            VideoAnalysisResult,
            VideoMetadata,
        )

        metadata = VideoMetadata(
            width=1280,
            height=720,
            duration_seconds=60.0,
            fps=24.0,
            codec="h264",
            size_bytes=10000000,
            content_hash="vh",
        )

        result = VideoAnalysisResult(
            summary="Test video",
            frame_analyses=[],
            scene_changes=[],
            duration_seconds=60.0,
            metadata=metadata,
            model_used="test-model",
            total_cost=0.005,
            cached=False,
            processing_time_ms=5000.0,
        )

        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict["summary"] == "Test video"

    def test_video_analysis_result_from_dict(self) -> None:
        """VideoAnalysisResult should be creatable from dict."""
        from smart_file_manager.services.vision_models import VideoAnalysisResult

        data = {
            "summary": "A video summary",
            "frame_analyses": [],
            "scene_changes": [],
            "duration_seconds": 90.0,
            "metadata": {
                "width": 1920,
                "height": 1080,
                "duration_seconds": 90.0,
                "fps": 30.0,
                "codec": "h264",
                "size_bytes": 20000000,
                "content_hash": "vhash",
            },
            "model_used": "google/gemini-2.0-flash-001",
            "total_cost": 0.008,
            "cached": True,
            "processing_time_ms": 10000.0,
        }

        result = VideoAnalysisResult.from_dict(data)
        assert result.summary == "A video summary"
        assert result.cached is True


class TestAnalysisStats:
    """Tests for AnalysisStats dataclass."""

    def test_analysis_stats_creation(self) -> None:
        """AnalysisStats should be creatable with all statistics."""
        from smart_file_manager.services.vision_models import AnalysisStats

        stats = AnalysisStats(
            total_analyses=100,
            cached_analyses=60,
            api_analyses=40,
            total_cost=0.50,
            average_processing_time_ms=1200.0,
            models_used={"google/gemini-2.0-flash-001": 35, "qwen/qwen2.5-vl-32b-instruct": 5},
        )

        assert stats.total_analyses == 100
        assert stats.cached_analyses == 60
        assert stats.api_analyses == 40
        assert stats.total_cost == 0.50
        assert stats.average_processing_time_ms == 1200.0
        assert "google/gemini-2.0-flash-001" in stats.models_used

    def test_analysis_stats_cache_hit_rate(self) -> None:
        """AnalysisStats should calculate cache_hit_rate property."""
        from smart_file_manager.services.vision_models import AnalysisStats

        stats = AnalysisStats(
            total_analyses=100,
            cached_analyses=75,
            api_analyses=25,
            total_cost=0.25,
            average_processing_time_ms=800.0,
            models_used={},
        )

        assert stats.cache_hit_rate == 0.75

    def test_analysis_stats_cache_hit_rate_zero_analyses(self) -> None:
        """AnalysisStats.cache_hit_rate should return 0 when no analyses."""
        from smart_file_manager.services.vision_models import AnalysisStats

        stats = AnalysisStats(
            total_analyses=0,
            cached_analyses=0,
            api_analyses=0,
            total_cost=0.0,
            average_processing_time_ms=0.0,
            models_used={},
        )

        assert stats.cache_hit_rate == 0.0
