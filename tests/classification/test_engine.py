"""Tests for ClassificationEngine class.

TAG: CLASS-001-M1
SPEC: SPEC-CLASS-001

This module tests:
- Classification priority (user rules > AI > metadata)
- AI-based classification from VisionService results
- Metadata-based classification
- Confidence score calculation
- requires_review flag logic
"""

from pathlib import Path

from smart_file_manager.classification.engine import ClassificationEngine

from smart_file_manager.classification.category_registry import CategoryRegistry
from smart_file_manager.classification.models import (
    FileMetadata,
)
from smart_file_manager.services.vision_models import (
    DetectedObject,
    ImageAnalysisResult,
    ImageMetadata,
    VideoAnalysisResult,
    VideoMetadata,
)


class TestClassificationEngineInit:
    """Tests for ClassificationEngine initialization."""

    def test_init_default(self) -> None:
        """Should initialize with default CategoryRegistry."""
        engine = ClassificationEngine()

        assert engine.category_registry is not None
        assert engine.confidence_threshold == 0.7

    def test_init_custom_registry(self) -> None:
        """Should accept custom CategoryRegistry."""
        registry = CategoryRegistry()
        registry.register_custom_category(
            id="custom_cat",
            name_ko="커스텀",
            name_en="Custom",
            sub_categories=[],
        )

        engine = ClassificationEngine(category_registry=registry)

        assert engine.category_registry.has_category("custom_cat")

    def test_init_custom_confidence_threshold(self) -> None:
        """Should accept custom confidence threshold."""
        engine = ClassificationEngine(confidence_threshold=0.8)

        assert engine.confidence_threshold == 0.8


class TestClassificationEnginePriority:
    """Tests for classification priority (acceptance 3.1)."""

    def test_user_rule_priority_over_ai(self) -> None:
        """User rules should have priority over AI classification."""
        engine = ClassificationEngine()

        # Register a user rule
        engine.register_user_rule(
            pattern="*/screenshots/*",
            category="screenshot",
            sub_category="desktop",
        )

        metadata = FileMetadata(
            file_path=Path("/home/user/screenshots/capture.png"),
            size_bytes=500000,
            extension="png",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hash123",
            exif=None,
        )

        # Even with AI result suggesting "photo", user rule should win
        vision_result = ImageAnalysisResult(
            description="A nature photo",
            objects=[DetectedObject(name="landscape", confidence=0.95)],
            scene="outdoor",
            text_content=None,
            tags=["nature", "landscape"],
            dominant_colors=["green", "blue"],
            quality="sharp",
            metadata=ImageMetadata(
                width=1920,
                height=1080,
                format="png",
                size_bytes=500000,
                content_hash="hash123",
            ),
            model_used="test-model",
            estimated_cost=0.001,
            cached=False,
            processing_time_ms=100.0,
        )

        classification = engine.classify(
            vision_result=vision_result,
            metadata=metadata,
        )

        assert classification.method == "user_rule"
        assert classification.category == "screenshot"
        assert classification.sub_category == "desktop"

    def test_ai_priority_over_metadata_when_no_user_rule(self) -> None:
        """AI should have priority over metadata when no user rule matches."""
        engine = ClassificationEngine()

        metadata = FileMetadata(
            file_path=Path("/home/user/photos/image.jpg"),
            size_bytes=500000,
            extension="jpg",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hash456",
            exif=None,
        )

        vision_result = ImageAnalysisResult(
            description="A portrait photo of a person",
            objects=[DetectedObject(name="person", confidence=0.95)],
            scene="indoor",
            text_content=None,
            tags=["portrait", "person"],
            dominant_colors=["beige"],
            quality="sharp",
            metadata=ImageMetadata(
                width=1920,
                height=1080,
                format="jpeg",
                size_bytes=500000,
                content_hash="hash456",
            ),
            model_used="test-model",
            estimated_cost=0.001,
            cached=False,
            processing_time_ms=100.0,
        )

        classification = engine.classify(
            vision_result=vision_result,
            metadata=metadata,
        )

        assert classification.method == "ai"
        assert classification.category == "photo"

    def test_metadata_fallback_when_no_vision_result(self) -> None:
        """Metadata classification should be used when no vision result."""
        engine = ClassificationEngine()

        metadata = FileMetadata(
            file_path=Path("/home/user/images/photo.jpg"),
            size_bytes=500000,
            extension="jpg",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hash789",
            exif=None,
        )

        classification = engine.classify(
            vision_result=None,
            metadata=metadata,
        )

        assert classification.method == "metadata"


class TestClassificationEngineAIClassification:
    """Tests for AI-based classification."""

    def test_classify_photo_from_person_detection(self) -> None:
        """Should classify as photo when person is detected."""
        engine = ClassificationEngine()

        metadata = FileMetadata(
            file_path=Path("/test/image.jpg"),
            size_bytes=500000,
            extension="jpg",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hashABC",
            exif=None,
        )

        vision_result = ImageAnalysisResult(
            description="Portrait photo",
            objects=[DetectedObject(name="person", confidence=0.9)],
            scene="indoor",
            text_content=None,
            tags=["portrait"],
            dominant_colors=[],
            quality="sharp",
            metadata=ImageMetadata(
                width=800,
                height=600,
                format="jpeg",
                size_bytes=500000,
                content_hash="hashABC",
            ),
            model_used="test-model",
            estimated_cost=0.001,
            cached=False,
            processing_time_ms=100.0,
        )

        classification = engine.classify(
            vision_result=vision_result,
            metadata=metadata,
        )

        assert classification.category == "photo"

    def test_classify_screenshot_from_text_heavy_image(self) -> None:
        """Should classify as screenshot when text content is detected."""
        engine = ClassificationEngine()

        metadata = FileMetadata(
            file_path=Path("/test/capture.png"),
            size_bytes=500000,
            extension="png",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hashDEF",
            exif=None,
        )

        vision_result = ImageAnalysisResult(
            description="Screenshot of a code editor",
            objects=[
                DetectedObject(name="screen", confidence=0.85),
                DetectedObject(name="text", confidence=0.9),
            ],
            scene="desktop",
            text_content="def hello_world():\n    print('Hello')",
            tags=["code", "programming"],
            dominant_colors=["black", "white"],
            quality="sharp",
            metadata=ImageMetadata(
                width=1920,
                height=1080,
                format="png",
                size_bytes=500000,
                content_hash="hashDEF",
            ),
            model_used="test-model",
            estimated_cost=0.001,
            cached=False,
            processing_time_ms=100.0,
        )

        classification = engine.classify(
            vision_result=vision_result,
            metadata=metadata,
        )

        assert classification.category == "screenshot"

    def test_classify_document_from_scan(self) -> None:
        """Should classify as document for scanned documents."""
        engine = ClassificationEngine()

        metadata = FileMetadata(
            file_path=Path("/test/scan.jpg"),
            size_bytes=500000,
            extension="jpg",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hashGHI",
            exif=None,
        )

        vision_result = ImageAnalysisResult(
            description="Scanned document with text",
            objects=[
                DetectedObject(name="document", confidence=0.9),
                DetectedObject(name="paper", confidence=0.85),
            ],
            scene="document",
            text_content="Invoice #12345\nDate: 2026-01-10",
            tags=["document", "invoice", "receipt"],
            dominant_colors=["white", "black"],
            quality="sharp",
            metadata=ImageMetadata(
                width=2480,
                height=3508,
                format="jpeg",
                size_bytes=500000,
                content_hash="hashGHI",
            ),
            model_used="test-model",
            estimated_cost=0.001,
            cached=False,
            processing_time_ms=100.0,
        )

        classification = engine.classify(
            vision_result=vision_result,
            metadata=metadata,
        )

        assert classification.category == "document"

    def test_classify_video_from_video_result(self) -> None:
        """Should classify as video for VideoAnalysisResult."""
        engine = ClassificationEngine()

        metadata = FileMetadata(
            file_path=Path("/test/clip.mp4"),
            size_bytes=5000000,
            extension="mp4",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hashJKL",
            exif=None,
        )

        vision_result = VideoAnalysisResult(
            summary="A short video clip",
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
                content_hash="hashJKL",
            ),
            model_used="test-model",
            total_cost=0.01,
            cached=False,
            processing_time_ms=500.0,
        )

        classification = engine.classify(
            vision_result=vision_result,
            metadata=metadata,
        )

        assert classification.category == "video"


class TestClassificationEngineMetadataClassification:
    """Tests for metadata-based classification."""

    def test_classify_image_by_extension(self) -> None:
        """Should classify image by extension when no vision result."""
        engine = ClassificationEngine()

        metadata = FileMetadata(
            file_path=Path("/test/image.jpg"),
            size_bytes=500000,
            extension="jpg",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hashMNO",
            exif=None,
        )

        classification = engine.classify(
            vision_result=None,
            metadata=metadata,
        )

        # JPEG should default to photo category
        assert classification.category == "photo"
        assert classification.method == "metadata"

    def test_classify_video_by_extension(self) -> None:
        """Should classify video by extension when no vision result."""
        engine = ClassificationEngine()

        metadata = FileMetadata(
            file_path=Path("/test/video.mp4"),
            size_bytes=5000000,
            extension="mp4",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hashPQR",
            exif=None,
        )

        classification = engine.classify(
            vision_result=None,
            metadata=metadata,
        )

        assert classification.category == "video"
        assert classification.method == "metadata"

    def test_classify_other_for_unknown_extension(self) -> None:
        """Should classify as 'other' for unknown extensions."""
        engine = ClassificationEngine()

        metadata = FileMetadata(
            file_path=Path("/test/file.xyz"),
            size_bytes=500000,
            extension="xyz",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hashSTU",
            exif=None,
        )

        classification = engine.classify(
            vision_result=None,
            metadata=metadata,
        )

        assert classification.category == "other"
        assert classification.method == "metadata"


class TestClassificationEngineConfidence:
    """Tests for confidence score calculation (acceptance 3.2)."""

    def test_high_confidence_no_review_required(self) -> None:
        """High confidence should not require review."""
        engine = ClassificationEngine(confidence_threshold=0.7)

        metadata = FileMetadata(
            file_path=Path("/test/photo.jpg"),
            size_bytes=500000,
            extension="jpg",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hashVWX",
            exif=None,
        )

        vision_result = ImageAnalysisResult(
            description="Clear photo",
            objects=[DetectedObject(name="person", confidence=0.95)],
            scene="outdoor",
            text_content=None,
            tags=[],
            dominant_colors=[],
            quality="sharp",
            metadata=ImageMetadata(
                width=800,
                height=600,
                format="jpeg",
                size_bytes=500000,
                content_hash="hashVWX",
            ),
            model_used="test-model",
            estimated_cost=0.001,
            cached=False,
            processing_time_ms=100.0,
        )

        classification = engine.classify(
            vision_result=vision_result,
            metadata=metadata,
        )

        assert classification.confidence >= 0.7
        assert classification.requires_review is False

    def test_low_confidence_requires_review(self) -> None:
        """Low confidence should require review (REQ-E-008)."""
        engine = ClassificationEngine(confidence_threshold=0.7)

        metadata = FileMetadata(
            file_path=Path("/test/ambiguous.jpg"),
            size_bytes=500000,
            extension="jpg",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hashYZ1",
            exif=None,
        )

        vision_result = ImageAnalysisResult(
            description="Unclear image",
            objects=[DetectedObject(name="unknown", confidence=0.3)],
            scene="unknown",
            text_content=None,
            tags=[],
            dominant_colors=[],
            quality="blurry",
            metadata=ImageMetadata(
                width=800,
                height=600,
                format="jpeg",
                size_bytes=500000,
                content_hash="hashYZ1",
            ),
            model_used="test-model",
            estimated_cost=0.001,
            cached=False,
            processing_time_ms=100.0,
        )

        classification = engine.classify(
            vision_result=vision_result,
            metadata=metadata,
        )

        # With very low object confidence, the classification should require review
        assert classification.confidence < 0.5 or classification.requires_review is True

    def test_user_rule_has_high_confidence(self) -> None:
        """User rule match should have high confidence."""
        engine = ClassificationEngine()

        engine.register_user_rule(
            pattern="*/work/*",
            category="document",
            sub_category="scan",
        )

        metadata = FileMetadata(
            file_path=Path("/home/user/work/report.pdf.jpg"),
            size_bytes=500000,
            extension="jpg",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hash234",
            exif=None,
        )

        classification = engine.classify(
            vision_result=None,
            metadata=metadata,
        )

        # User rules should have confidence of 1.0
        assert classification.confidence == 1.0
        assert classification.requires_review is False


class TestClassificationEngineUserRules:
    """Tests for user rule management."""

    def test_register_user_rule(self) -> None:
        """Should register a user rule."""
        engine = ClassificationEngine()

        engine.register_user_rule(
            pattern="*/photos/*",
            category="photo",
            sub_category="portrait",
        )

        rules = engine.get_user_rules()
        assert len(rules) == 1
        assert rules[0]["pattern"] == "*/photos/*"

    def test_register_multiple_user_rules(self) -> None:
        """Should register multiple user rules."""
        engine = ClassificationEngine()

        engine.register_user_rule(pattern="*/photos/*", category="photo")
        engine.register_user_rule(pattern="*/screenshots/*", category="screenshot")
        engine.register_user_rule(pattern="*/documents/*", category="document")

        rules = engine.get_user_rules()
        assert len(rules) == 3

    def test_unregister_user_rule(self) -> None:
        """Should unregister a user rule."""
        engine = ClassificationEngine()

        engine.register_user_rule(pattern="*/photos/*", category="photo")
        engine.register_user_rule(pattern="*/screenshots/*", category="screenshot")

        engine.unregister_user_rule("*/photos/*")

        rules = engine.get_user_rules()
        assert len(rules) == 1
        assert rules[0]["pattern"] == "*/screenshots/*"

    def test_clear_user_rules(self) -> None:
        """Should clear all user rules."""
        engine = ClassificationEngine()

        engine.register_user_rule(pattern="*/photos/*", category="photo")
        engine.register_user_rule(pattern="*/screenshots/*", category="screenshot")

        engine.clear_user_rules()

        rules = engine.get_user_rules()
        assert len(rules) == 0

    def test_user_rule_pattern_matching(self) -> None:
        """Should correctly match file paths with patterns."""
        engine = ClassificationEngine()

        engine.register_user_rule(
            pattern="*/Screenshots/*",
            category="screenshot",
            sub_category="desktop",
        )

        # Matching path
        metadata1 = FileMetadata(
            file_path=Path("/Users/john/Screenshots/capture.png"),
            size_bytes=500000,
            extension="png",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hash567",
            exif=None,
        )

        # Non-matching path
        metadata2 = FileMetadata(
            file_path=Path("/Users/john/Photos/vacation.jpg"),
            size_bytes=500000,
            extension="jpg",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hash890",
            exif=None,
        )

        result1 = engine.classify(vision_result=None, metadata=metadata1)
        result2 = engine.classify(vision_result=None, metadata=metadata2)

        assert result1.method == "user_rule"
        assert result1.category == "screenshot"

        assert result2.method == "metadata"
