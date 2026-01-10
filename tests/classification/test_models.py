"""Tests for Classification data models.

TAG: CLASS-001-M1
SPEC: SPEC-CLASS-001

This module tests:
- Classification dataclass
- TagSet dataclass
- ClassificationResult dataclass
- OrganizationPlan dataclass
"""

from pathlib import Path

from smart_file_manager.classification.models import (
    Classification,
    ClassificationResult,
    FileMetadata,
    OrganizationPlan,
    TagSet,
)


class TestClassification:
    """Tests for Classification dataclass."""

    def test_classification_creation(self) -> None:
        """Should create Classification with required fields."""
        classification = Classification(
            category="photo",
            sub_category="portrait",
            confidence=0.85,
            method="ai",
            requires_review=False,
        )

        assert classification.category == "photo"
        assert classification.sub_category == "portrait"
        assert classification.confidence == 0.85
        assert classification.method == "ai"
        assert classification.requires_review is False

    def test_classification_without_sub_category(self) -> None:
        """Should create Classification without sub_category."""
        classification = Classification(
            category="other",
            sub_category=None,
            confidence=0.5,
            method="metadata",
            requires_review=True,
        )

        assert classification.sub_category is None
        assert classification.requires_review is True

    def test_classification_method_values(self) -> None:
        """Should accept valid method values."""
        for method in ["user_rule", "ai", "metadata"]:
            classification = Classification(
                category="photo",
                sub_category=None,
                confidence=0.7,
                method=method,
                requires_review=False,
            )
            assert classification.method == method

    def test_classification_confidence_bounds(self) -> None:
        """Confidence should be between 0.0 and 1.0."""
        # Valid bounds
        low = Classification(
            category="photo",
            sub_category=None,
            confidence=0.0,
            method="metadata",
            requires_review=True,
        )
        high = Classification(
            category="photo",
            sub_category=None,
            confidence=1.0,
            method="user_rule",
            requires_review=False,
        )

        assert low.confidence == 0.0
        assert high.confidence == 1.0

    def test_classification_to_dict(self) -> None:
        """Should serialize Classification to dictionary."""
        classification = Classification(
            category="screenshot",
            sub_category="desktop",
            confidence=0.92,
            method="ai",
            requires_review=False,
        )

        result = classification.to_dict()

        assert result["category"] == "screenshot"
        assert result["sub_category"] == "desktop"
        assert result["confidence"] == 0.92
        assert result["method"] == "ai"
        assert result["requires_review"] is False

    def test_classification_from_dict(self) -> None:
        """Should deserialize Classification from dictionary."""
        data = {
            "category": "document",
            "sub_category": "scan",
            "confidence": 0.88,
            "method": "user_rule",
            "requires_review": False,
        }

        classification = Classification.from_dict(data)

        assert classification.category == "document"
        assert classification.sub_category == "scan"
        assert classification.confidence == 0.88


class TestTagSet:
    """Tests for TagSet dataclass."""

    def test_tagset_creation(self) -> None:
        """Should create TagSet with English and Korean tags."""
        tagset = TagSet(
            tags_en=["person", "outdoor", "nature"],
            tags_ko=["사람", "야외", "자연"],
            source_breakdown={
                "objects": ["person"],
                "scene": ["outdoor", "nature"],
            },
        )

        assert tagset.tags_en == ["person", "outdoor", "nature"]
        assert tagset.tags_ko == ["사람", "야외", "자연"]
        assert "objects" in tagset.source_breakdown

    def test_tagset_empty(self) -> None:
        """Should allow empty tag lists."""
        tagset = TagSet(
            tags_en=[],
            tags_ko=[],
            source_breakdown={},
        )

        assert tagset.tags_en == []
        assert tagset.tags_ko == []

    def test_tagset_to_dict(self) -> None:
        """Should serialize TagSet to dictionary."""
        tagset = TagSet(
            tags_en=["car", "road"],
            tags_ko=["자동차", "도로"],
            source_breakdown={"objects": ["car"], "scene": ["road"]},
        )

        result = tagset.to_dict()

        assert result["tags_en"] == ["car", "road"]
        assert result["tags_ko"] == ["자동차", "도로"]
        assert "source_breakdown" in result

    def test_tagset_from_dict(self) -> None:
        """Should deserialize TagSet from dictionary."""
        data = {
            "tags_en": ["building", "city"],
            "tags_ko": ["건물", "도시"],
            "source_breakdown": {"objects": ["building"], "scene": ["city"]},
        }

        tagset = TagSet.from_dict(data)

        assert tagset.tags_en == ["building", "city"]
        assert tagset.tags_ko == ["건물", "도시"]


class TestFileMetadata:
    """Tests for FileMetadata dataclass."""

    def test_file_metadata_creation(self) -> None:
        """Should create FileMetadata with required fields."""
        metadata = FileMetadata(
            file_path=Path("/test/image.jpg"),
            size_bytes=1024000,
            extension="jpg",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T11:00:00",
            content_hash="abc123",
            exif={"DateTimeOriginal": "2026:01:10 10:00:00"},
        )

        assert metadata.file_path == Path("/test/image.jpg")
        assert metadata.size_bytes == 1024000
        assert metadata.extension == "jpg"
        assert metadata.content_hash == "abc123"
        assert "DateTimeOriginal" in metadata.exif

    def test_file_metadata_without_exif(self) -> None:
        """Should create FileMetadata without EXIF data."""
        metadata = FileMetadata(
            file_path=Path("/test/file.png"),
            size_bytes=512000,
            extension="png",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T11:00:00",
            content_hash="def456",
            exif=None,
        )

        assert metadata.exif is None


class TestOrganizationPlan:
    """Tests for OrganizationPlan dataclass."""

    def test_organization_plan_creation(self) -> None:
        """Should create OrganizationPlan with required fields."""
        plan = OrganizationPlan(
            action="move",
            source_path=Path("/downloads/image.jpg"),
            target_path=Path("/Photos/2026/01/image.jpg"),
            reason="Screenshot detected, organizing by date",
            confidence=0.9,
        )

        assert plan.action == "move"
        assert plan.source_path == Path("/downloads/image.jpg")
        assert plan.target_path == Path("/Photos/2026/01/image.jpg")
        assert plan.confidence == 0.9

    def test_organization_plan_actions(self) -> None:
        """Should accept valid action values."""
        for action in ["move", "copy", "delete", "group"]:
            plan = OrganizationPlan(
                action=action,
                source_path=Path("/src/file.jpg"),
                target_path=Path("/dst/file.jpg"),
                reason="Test",
                confidence=0.8,
            )
            assert plan.action == action

    def test_organization_plan_to_dict(self) -> None:
        """Should serialize OrganizationPlan to dictionary."""
        plan = OrganizationPlan(
            action="move",
            source_path=Path("/src/photo.jpg"),
            target_path=Path("/dst/photo.jpg"),
            reason="Photo detected",
            confidence=0.85,
        )

        result = plan.to_dict()

        assert result["action"] == "move"
        assert result["source_path"] == "/src/photo.jpg"
        assert result["target_path"] == "/dst/photo.jpg"


class TestClassificationResult:
    """Tests for ClassificationResult dataclass."""

    def test_classification_result_creation(self) -> None:
        """Should create ClassificationResult with all fields."""
        classification = Classification(
            category="photo",
            sub_category="portrait",
            confidence=0.9,
            method="ai",
            requires_review=False,
        )
        tags = TagSet(
            tags_en=["person"],
            tags_ko=["사람"],
            source_breakdown={"objects": ["person"]},
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
        plan = OrganizationPlan(
            action="move",
            source_path=Path("/test/photo.jpg"),
            target_path=Path("/Photos/photo.jpg"),
            reason="Photo detected",
            confidence=0.85,
        )

        result = ClassificationResult(
            file_path=Path("/test/photo.jpg"),
            content_hash="hash123",
            classification=classification,
            tags=tags,
            organization_plan=plan,
            vision_result=None,
            metadata=metadata,
            processing_time_ms=150.5,
            cached=False,
        )

        assert result.file_path == Path("/test/photo.jpg")
        assert result.classification.category == "photo"
        assert result.tags.tags_en == ["person"]
        assert result.processing_time_ms == 150.5
        assert result.cached is False

    def test_classification_result_without_plan(self) -> None:
        """Should create ClassificationResult without organization plan."""
        classification = Classification(
            category="other",
            sub_category=None,
            confidence=0.5,
            method="metadata",
            requires_review=True,
        )
        tags = TagSet(tags_en=[], tags_ko=[], source_breakdown={})
        metadata = FileMetadata(
            file_path=Path("/test/file.jpg"),
            size_bytes=500000,
            extension="jpg",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hash456",
            exif=None,
        )

        result = ClassificationResult(
            file_path=Path("/test/file.jpg"),
            content_hash="hash456",
            classification=classification,
            tags=tags,
            organization_plan=None,
            vision_result=None,
            metadata=metadata,
            processing_time_ms=50.0,
            cached=True,
        )

        assert result.organization_plan is None
        assert result.cached is True

    def test_classification_result_to_dict(self) -> None:
        """Should serialize ClassificationResult to dictionary."""
        classification = Classification(
            category="screenshot",
            sub_category="desktop",
            confidence=0.95,
            method="ai",
            requires_review=False,
        )
        tags = TagSet(
            tags_en=["screen", "text"],
            tags_ko=["화면", "텍스트"],
            source_breakdown={"objects": ["screen", "text"]},
        )
        metadata = FileMetadata(
            file_path=Path("/test/screenshot.png"),
            size_bytes=800000,
            extension="png",
            created_at="2026-01-10T10:00:00",
            modified_at="2026-01-10T10:00:00",
            content_hash="hash789",
            exif=None,
        )

        result = ClassificationResult(
            file_path=Path("/test/screenshot.png"),
            content_hash="hash789",
            classification=classification,
            tags=tags,
            organization_plan=None,
            vision_result=None,
            metadata=metadata,
            processing_time_ms=100.0,
            cached=False,
        )

        data = result.to_dict()

        assert data["file_path"] == "/test/screenshot.png"
        assert data["content_hash"] == "hash789"
        assert data["classification"]["category"] == "screenshot"
        assert data["tags"]["tags_en"] == ["screen", "text"]
        assert data["processing_time_ms"] == 100.0

    def test_classification_result_from_dict(self) -> None:
        """Should deserialize ClassificationResult from dictionary."""
        data = {
            "file_path": "/test/image.jpg",
            "content_hash": "hashABC",
            "classification": {
                "category": "photo",
                "sub_category": "landscape",
                "confidence": 0.88,
                "method": "ai",
                "requires_review": False,
            },
            "tags": {
                "tags_en": ["mountain", "sky"],
                "tags_ko": ["산", "하늘"],
                "source_breakdown": {"scene": ["mountain", "sky"]},
            },
            "organization_plan": None,
            "vision_result": None,
            "metadata": {
                "file_path": "/test/image.jpg",
                "size_bytes": 1200000,
                "extension": "jpg",
                "created_at": "2026-01-10T10:00:00",
                "modified_at": "2026-01-10T10:00:00",
                "content_hash": "hashABC",
                "exif": None,
            },
            "processing_time_ms": 200.0,
            "cached": True,
        }

        result = ClassificationResult.from_dict(data)

        assert result.file_path == Path("/test/image.jpg")
        assert result.classification.category == "photo"
        assert result.classification.sub_category == "landscape"
        assert result.cached is True
