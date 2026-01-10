"""Tests for TagGenerator class.

TAG: CLASS-001-M2
SPEC: SPEC-CLASS-001

This module tests:
- Tag generation from VisionService results
- Tag generation from metadata
- Tag translation (English to Korean)
- Tag count limits
"""

from pathlib import Path

from smart_file_manager.classification.tag_generator import TagGenerator

from smart_file_manager.classification.models import (
    Classification,
    FileMetadata,
)
from smart_file_manager.services.vision_models import (
    DetectedObject,
    ImageAnalysisResult,
    ImageMetadata,
)


class TestTagGeneratorInit:
    """Tests for TagGenerator initialization."""

    def test_init_default(self) -> None:
        """Should initialize with default settings."""
        generator = TagGenerator()

        assert generator.max_tags == 20
        assert generator._translation_dict is not None

    def test_init_custom_max_tags(self) -> None:
        """Should accept custom max_tags setting."""
        generator = TagGenerator(max_tags=10)

        assert generator.max_tags == 10


class TestTagGeneratorFromVisionResult:
    """Tests for tag generation from VisionService results (acceptance 4.1)."""

    def test_generate_tags_from_objects(self) -> None:
        """Should generate tags from detected objects."""
        generator = TagGenerator()

        vision_result = ImageAnalysisResult(
            description="A person walking near a car in front of a building",
            objects=[
                DetectedObject(name="person", confidence=0.95),
                DetectedObject(name="car", confidence=0.88),
                DetectedObject(name="building", confidence=0.82),
            ],
            scene="outdoor",
            text_content=None,
            tags=["urban", "street"],
            dominant_colors=["gray", "blue"],
            quality="sharp",
            metadata=ImageMetadata(
                width=1920,
                height=1080,
                format="jpeg",
                size_bytes=1000000,
                content_hash="hash123",
            ),
            model_used="test-model",
            estimated_cost=0.001,
            cached=False,
            processing_time_ms=100.0,
        )
        metadata = FileMetadata(
            file_path=Path("/test/photo.jpg"),
            size_bytes=1000000,
            extension="jpg",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hash123",
            exif=None,
        )
        classification = Classification(
            category="photo",
            sub_category="portrait",
            confidence=0.9,
            method="ai",
            requires_review=False,
        )

        tagset = generator.generate_tags(
            vision_result=vision_result,
            metadata=metadata,
            classification=classification,
        )

        assert "person" in tagset.tags_en
        assert "car" in tagset.tags_en
        assert "building" in tagset.tags_en

    def test_generate_tags_from_scene(self) -> None:
        """Should include scene as a tag."""
        generator = TagGenerator()

        vision_result = ImageAnalysisResult(
            description="An outdoor scene",
            objects=[],
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
                content_hash="hash456",
            ),
            model_used="test-model",
            estimated_cost=0.001,
            cached=False,
            processing_time_ms=100.0,
        )
        metadata = FileMetadata(
            file_path=Path("/test/scene.jpg"),
            size_bytes=500000,
            extension="jpg",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hash456",
            exif=None,
        )
        classification = Classification(
            category="photo",
            sub_category="landscape",
            confidence=0.85,
            method="ai",
            requires_review=False,
        )

        tagset = generator.generate_tags(
            vision_result=vision_result,
            metadata=metadata,
            classification=classification,
        )

        assert "outdoor" in tagset.tags_en

    def test_generate_tags_includes_vision_tags(self) -> None:
        """Should include tags from vision result."""
        generator = TagGenerator()

        vision_result = ImageAnalysisResult(
            description="Urban scene",
            objects=[],
            scene="urban",
            text_content=None,
            tags=["street", "city", "traffic"],
            dominant_colors=["gray"],
            quality="sharp",
            metadata=ImageMetadata(
                width=800,
                height=600,
                format="jpeg",
                size_bytes=500000,
                content_hash="hash789",
            ),
            model_used="test-model",
            estimated_cost=0.001,
            cached=False,
            processing_time_ms=100.0,
        )
        metadata = FileMetadata(
            file_path=Path("/test/urban.jpg"),
            size_bytes=500000,
            extension="jpg",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hash789",
            exif=None,
        )
        classification = Classification(
            category="photo",
            sub_category=None,
            confidence=0.8,
            method="ai",
            requires_review=False,
        )

        tagset = generator.generate_tags(
            vision_result=vision_result,
            metadata=metadata,
            classification=classification,
        )

        assert "street" in tagset.tags_en
        assert "city" in tagset.tags_en
        assert "traffic" in tagset.tags_en

    def test_generate_tags_source_breakdown(self) -> None:
        """Should include source breakdown in TagSet."""
        generator = TagGenerator()

        vision_result = ImageAnalysisResult(
            description="A dog in a park",
            objects=[
                DetectedObject(name="dog", confidence=0.9),
            ],
            scene="park",
            text_content=None,
            tags=["nature"],
            dominant_colors=["green"],
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
        metadata = FileMetadata(
            file_path=Path("/test/dog.jpg"),
            size_bytes=500000,
            extension="jpg",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hashABC",
            exif=None,
        )
        classification = Classification(
            category="photo",
            sub_category=None,
            confidence=0.85,
            method="ai",
            requires_review=False,
        )

        tagset = generator.generate_tags(
            vision_result=vision_result,
            metadata=metadata,
            classification=classification,
        )

        assert "objects" in tagset.source_breakdown
        assert "scene" in tagset.source_breakdown
        assert "dog" in tagset.source_breakdown["objects"]


class TestTagGeneratorFromMetadata:
    """Tests for tag generation from file metadata."""

    def test_generate_tags_includes_extension(self) -> None:
        """Should include file extension as tag."""
        generator = TagGenerator()

        metadata = FileMetadata(
            file_path=Path("/test/photo.jpg"),
            size_bytes=500000,
            extension="jpg",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hashDEF",
            exif=None,
        )
        classification = Classification(
            category="photo",
            sub_category=None,
            confidence=0.7,
            method="metadata",
            requires_review=False,
        )

        tagset = generator.generate_tags(
            vision_result=None,
            metadata=metadata,
            classification=classification,
        )

        assert "jpg" in tagset.tags_en

    def test_generate_tags_from_exif_date(self) -> None:
        """Should generate date-based tags from EXIF data."""
        generator = TagGenerator()

        metadata = FileMetadata(
            file_path=Path("/test/photo.jpg"),
            size_bytes=500000,
            extension="jpg",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hashGHI",
            exif={"DateTimeOriginal": "2026:01:10 10:00:00"},
        )
        classification = Classification(
            category="photo",
            sub_category=None,
            confidence=0.7,
            method="metadata",
            requires_review=False,
        )

        tagset = generator.generate_tags(
            vision_result=None,
            metadata=metadata,
            classification=classification,
        )

        assert "2026" in tagset.tags_en
        assert "january" in tagset.tags_en or "January" in tagset.tags_en

    def test_generate_tags_includes_category(self) -> None:
        """Should include category as a tag."""
        generator = TagGenerator()

        metadata = FileMetadata(
            file_path=Path("/test/screenshot.png"),
            size_bytes=500000,
            extension="png",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hashJKL",
            exif=None,
        )
        classification = Classification(
            category="screenshot",
            sub_category="desktop",
            confidence=0.9,
            method="ai",
            requires_review=False,
        )

        tagset = generator.generate_tags(
            vision_result=None,
            metadata=metadata,
            classification=classification,
        )

        assert "screenshot" in tagset.tags_en


class TestTagGeneratorLimits:
    """Tests for tag count limits (REQ-N-007)."""

    def test_max_20_tags(self) -> None:
        """Should limit tags to maximum 20."""
        generator = TagGenerator(max_tags=20)

        # Create vision result with many objects
        objects = [DetectedObject(name=f"object{i}", confidence=0.8) for i in range(30)]

        vision_result = ImageAnalysisResult(
            description="Many objects",
            objects=objects,
            scene="indoor",
            text_content=None,
            tags=[f"tag{i}" for i in range(10)],
            dominant_colors=["red", "blue", "green"],
            quality="sharp",
            metadata=ImageMetadata(
                width=800,
                height=600,
                format="jpeg",
                size_bytes=500000,
                content_hash="hashMNO",
            ),
            model_used="test-model",
            estimated_cost=0.001,
            cached=False,
            processing_time_ms=100.0,
        )
        metadata = FileMetadata(
            file_path=Path("/test/many_objects.jpg"),
            size_bytes=500000,
            extension="jpg",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hashMNO",
            exif=None,
        )
        classification = Classification(
            category="photo",
            sub_category=None,
            confidence=0.8,
            method="ai",
            requires_review=False,
        )

        tagset = generator.generate_tags(
            vision_result=vision_result,
            metadata=metadata,
            classification=classification,
        )

        assert len(tagset.tags_en) <= 20
        assert len(tagset.tags_ko) <= 20

    def test_custom_max_tags(self) -> None:
        """Should respect custom max_tags setting."""
        generator = TagGenerator(max_tags=5)

        objects = [DetectedObject(name=f"object{i}", confidence=0.8) for i in range(10)]

        vision_result = ImageAnalysisResult(
            description="Multiple objects",
            objects=objects,
            scene="indoor",
            text_content=None,
            tags=[],
            dominant_colors=[],
            quality="sharp",
            metadata=ImageMetadata(
                width=800,
                height=600,
                format="jpeg",
                size_bytes=500000,
                content_hash="hashPQR",
            ),
            model_used="test-model",
            estimated_cost=0.001,
            cached=False,
            processing_time_ms=100.0,
        )
        metadata = FileMetadata(
            file_path=Path("/test/limited.jpg"),
            size_bytes=500000,
            extension="jpg",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hashPQR",
            exif=None,
        )
        classification = Classification(
            category="photo",
            sub_category=None,
            confidence=0.8,
            method="ai",
            requires_review=False,
        )

        tagset = generator.generate_tags(
            vision_result=vision_result,
            metadata=metadata,
            classification=classification,
            max_tags=5,
        )

        assert len(tagset.tags_en) <= 5


class TestTagGeneratorTranslation:
    """Tests for tag translation (acceptance 4.2)."""

    def test_translate_basic_tags(self) -> None:
        """Should translate common tags to Korean."""
        generator = TagGenerator()

        tags_en = ["person", "car", "outdoor"]
        tags_ko = generator.translate_tags(tags_en)

        # At least some tags should be translated
        assert len(tags_ko) == 3
        # Verify translation of common terms
        assert any(tag in tags_ko for tag in ["사람", "person"])

    def test_translate_unknown_tag_returns_original(self) -> None:
        """Should return original tag if translation not found."""
        generator = TagGenerator()

        tags_en = ["very_specific_unknown_object_xyz123"]
        tags_ko = generator.translate_tags(tags_en)

        # Unknown tags should be returned as-is
        assert tags_ko == ["very_specific_unknown_object_xyz123"]

    def test_generate_tags_includes_korean(self) -> None:
        """Should generate both English and Korean tags."""
        generator = TagGenerator()

        vision_result = ImageAnalysisResult(
            description="A person outdoors",
            objects=[
                DetectedObject(name="person", confidence=0.9),
            ],
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
                content_hash="hashSTU",
            ),
            model_used="test-model",
            estimated_cost=0.001,
            cached=False,
            processing_time_ms=100.0,
        )
        metadata = FileMetadata(
            file_path=Path("/test/person.jpg"),
            size_bytes=500000,
            extension="jpg",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hashSTU",
            exif=None,
        )
        classification = Classification(
            category="photo",
            sub_category="portrait",
            confidence=0.9,
            method="ai",
            requires_review=False,
        )

        tagset = generator.generate_tags(
            vision_result=vision_result,
            metadata=metadata,
            classification=classification,
        )

        # Both English and Korean tags should be generated
        assert len(tagset.tags_en) > 0
        assert len(tagset.tags_ko) > 0


class TestTagGeneratorDeduplication:
    """Tests for tag deduplication."""

    def test_no_duplicate_tags(self) -> None:
        """Should not include duplicate tags."""
        generator = TagGenerator()

        # Create vision result with duplicate object names
        vision_result = ImageAnalysisResult(
            description="Multiple dogs",
            objects=[
                DetectedObject(name="dog", confidence=0.9),
                DetectedObject(name="dog", confidence=0.85),
                DetectedObject(name="dog", confidence=0.8),
            ],
            scene="outdoor",
            text_content=None,
            tags=["dog", "pet"],  # dog appears again in tags
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
        metadata = FileMetadata(
            file_path=Path("/test/dogs.jpg"),
            size_bytes=500000,
            extension="jpg",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hashVWX",
            exif=None,
        )
        classification = Classification(
            category="photo",
            sub_category=None,
            confidence=0.85,
            method="ai",
            requires_review=False,
        )

        tagset = generator.generate_tags(
            vision_result=vision_result,
            metadata=metadata,
            classification=classification,
        )

        # Count occurrences of "dog"
        dog_count = tagset.tags_en.count("dog")
        assert dog_count == 1, f"Expected 1 'dog' tag, found {dog_count}"

    def test_case_insensitive_deduplication(self) -> None:
        """Should deduplicate tags case-insensitively."""
        generator = TagGenerator()

        vision_result = ImageAnalysisResult(
            description="Cat image",
            objects=[
                DetectedObject(name="Cat", confidence=0.9),
            ],
            scene="indoor",
            text_content=None,
            tags=["cat", "CAT"],
            dominant_colors=[],
            quality="sharp",
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
        metadata = FileMetadata(
            file_path=Path("/test/cat.jpg"),
            size_bytes=500000,
            extension="jpg",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hashYZ1",
            exif=None,
        )
        classification = Classification(
            category="photo",
            sub_category=None,
            confidence=0.85,
            method="ai",
            requires_review=False,
        )

        tagset = generator.generate_tags(
            vision_result=vision_result,
            metadata=metadata,
            classification=classification,
        )

        # Should only have one variant of "cat"
        cat_variants = [t for t in tagset.tags_en if t.lower() == "cat"]
        assert len(cat_variants) == 1
