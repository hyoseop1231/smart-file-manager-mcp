"""Tests for OrganizationPlanner class.

TAG: CLASS-001-M3
SPEC: SPEC-CLASS-001

This module tests:
- Organization plan generation based on classification
- Path template generation
- Date-based organization
- Batch organization plans
"""

from pathlib import Path

import pytest
from smart_file_manager.classification.organization_planner import (
    OrganizationPlanner,
)

from smart_file_manager.classification.models import (
    Classification,
    ClassificationResult,
    FileMetadata,
    OrganizationPlan,
    TagSet,
)
from smart_file_manager.core.exceptions import OrganizationPlanError


class TestOrganizationPlannerInit:
    """Tests for OrganizationPlanner initialization."""

    def test_init_default(self) -> None:
        """Should initialize with default settings."""
        planner = OrganizationPlanner()

        assert planner.base_path == Path.home()

    def test_init_custom_base_path(self) -> None:
        """Should accept custom base path."""
        planner = OrganizationPlanner(base_path=Path("/custom/base"))

        assert planner.base_path == Path("/custom/base")


class TestOrganizationPlannerScreenshots:
    """Tests for screenshot organization (acceptance 6.1)."""

    def test_screenshot_organization_by_date(self) -> None:
        """Should organize screenshots by date."""
        planner = OrganizationPlanner(base_path=Path("/home/user"))

        classification_result = ClassificationResult(
            file_path=Path("/downloads/capture.png"),
            content_hash="hash123",
            classification=Classification(
                category="screenshot",
                sub_category="desktop",
                confidence=0.9,
                method="ai",
                requires_review=False,
            ),
            tags=TagSet(tags_en=[], tags_ko=[], source_breakdown={}),
            organization_plan=None,
            vision_result=None,
            metadata=FileMetadata(
                file_path=Path("/downloads/capture.png"),
                size_bytes=500000,
                extension="png",
                created_at="2026-01-10T10:00:00",
                modified_at="2026-01-10T10:00:00",
                content_hash="hash123",
                exif={"DateTimeOriginal": "2026:01:10 10:00:00"},
            ),
            processing_time_ms=100.0,
            cached=False,
        )

        plan = planner.create_plan(
            file_path=classification_result.file_path,
            classification=classification_result,
        )

        assert plan.action == "move"
        assert "Screenshots" in str(plan.target_path)
        assert "2026" in str(plan.target_path)
        assert "01" in str(plan.target_path)
        assert plan.confidence > 0.8

    def test_screenshot_organization_reason(self) -> None:
        """Should include reason for screenshot organization."""
        planner = OrganizationPlanner(base_path=Path("/home/user"))

        classification_result = ClassificationResult(
            file_path=Path("/downloads/screen.png"),
            content_hash="hash456",
            classification=Classification(
                category="screenshot",
                sub_category="desktop",
                confidence=0.9,
                method="ai",
                requires_review=False,
            ),
            tags=TagSet(tags_en=[], tags_ko=[], source_breakdown={}),
            organization_plan=None,
            vision_result=None,
            metadata=FileMetadata(
                file_path=Path("/downloads/screen.png"),
                size_bytes=500000,
                extension="png",
                created_at="2026-01-10T10:00:00",
                modified_at="2026-01-10T10:00:00",
                content_hash="hash456",
                exif=None,
            ),
            processing_time_ms=100.0,
            cached=False,
        )

        plan = planner.create_plan(
            file_path=classification_result.file_path,
            classification=classification_result,
        )

        assert "screenshot" in plan.reason.lower() or "Screenshot" in plan.reason


class TestOrganizationPlannerPhotos:
    """Tests for photo organization."""

    def test_photo_organization_by_exif_date(self) -> None:
        """Should organize photos by EXIF date."""
        planner = OrganizationPlanner(base_path=Path("/home/user"))

        classification_result = ClassificationResult(
            file_path=Path("/downloads/photo.jpg"),
            content_hash="hash789",
            classification=Classification(
                category="photo",
                sub_category="portrait",
                confidence=0.9,
                method="ai",
                requires_review=False,
            ),
            tags=TagSet(tags_en=[], tags_ko=[], source_breakdown={}),
            organization_plan=None,
            vision_result=None,
            metadata=FileMetadata(
                file_path=Path("/downloads/photo.jpg"),
                size_bytes=500000,
                extension="jpg",
                created_at="2026-01-10T10:00:00",
                modified_at="2026-01-10T10:00:00",
                content_hash="hash789",
                exif={"DateTimeOriginal": "2026:01:10 10:00:00"},
            ),
            processing_time_ms=100.0,
            cached=False,
        )

        plan = planner.create_plan(
            file_path=classification_result.file_path,
            classification=classification_result,
        )

        assert plan.action == "move"
        assert "Photos" in str(plan.target_path)
        assert "2026" in str(plan.target_path)
        assert "01" in str(plan.target_path)

    def test_photo_organization_without_exif(self) -> None:
        """Should organize photos without EXIF using file modified date."""
        planner = OrganizationPlanner(base_path=Path("/home/user"))

        classification_result = ClassificationResult(
            file_path=Path("/downloads/image.jpg"),
            content_hash="hashABC",
            classification=Classification(
                category="photo",
                sub_category="landscape",
                confidence=0.85,
                method="ai",
                requires_review=False,
            ),
            tags=TagSet(tags_en=[], tags_ko=[], source_breakdown={}),
            organization_plan=None,
            vision_result=None,
            metadata=FileMetadata(
                file_path=Path("/downloads/image.jpg"),
                size_bytes=500000,
                extension="jpg",
                created_at="2026-03-15T14:00:00",
                modified_at="2026-03-15T14:00:00",
                content_hash="hashABC",
                exif=None,
            ),
            processing_time_ms=100.0,
            cached=False,
        )

        plan = planner.create_plan(
            file_path=classification_result.file_path,
            classification=classification_result,
        )

        assert plan.action == "move"
        assert "Photos" in str(plan.target_path)


class TestOrganizationPlannerDocuments:
    """Tests for document organization."""

    def test_document_organization(self) -> None:
        """Should organize documents to Documents folder."""
        planner = OrganizationPlanner(base_path=Path("/home/user"))

        classification_result = ClassificationResult(
            file_path=Path("/downloads/scan.jpg"),
            content_hash="hashDEF",
            classification=Classification(
                category="document",
                sub_category="scan",
                confidence=0.9,
                method="ai",
                requires_review=False,
            ),
            tags=TagSet(tags_en=[], tags_ko=[], source_breakdown={}),
            organization_plan=None,
            vision_result=None,
            metadata=FileMetadata(
                file_path=Path("/downloads/scan.jpg"),
                size_bytes=500000,
                extension="jpg",
                created_at="2026-01-10T10:00:00",
                modified_at="2026-01-10T10:00:00",
                content_hash="hashDEF",
                exif=None,
            ),
            processing_time_ms=100.0,
            cached=False,
        )

        plan = planner.create_plan(
            file_path=classification_result.file_path,
            classification=classification_result,
        )

        assert plan.action == "move"
        assert "Documents" in str(plan.target_path) or "Scans" in str(plan.target_path)


class TestOrganizationPlannerVideos:
    """Tests for video organization."""

    def test_video_organization(self) -> None:
        """Should organize videos to Videos folder."""
        planner = OrganizationPlanner(base_path=Path("/home/user"))

        classification_result = ClassificationResult(
            file_path=Path("/downloads/video.mp4"),
            content_hash="hashGHI",
            classification=Classification(
                category="video",
                sub_category="clip",
                confidence=0.9,
                method="ai",
                requires_review=False,
            ),
            tags=TagSet(tags_en=[], tags_ko=[], source_breakdown={}),
            organization_plan=None,
            vision_result=None,
            metadata=FileMetadata(
                file_path=Path("/downloads/video.mp4"),
                size_bytes=5000000,
                extension="mp4",
                created_at="2026-01-10T10:00:00",
                modified_at="2026-01-10T10:00:00",
                content_hash="hashGHI",
                exif=None,
            ),
            processing_time_ms=100.0,
            cached=False,
        )

        plan = planner.create_plan(
            file_path=classification_result.file_path,
            classification=classification_result,
        )

        assert plan.action == "move"
        assert "Videos" in str(plan.target_path)


class TestOrganizationPlannerErrors:
    """Tests for error handling."""

    def test_missing_classification_raises_error(self) -> None:
        """Should raise error when classification is missing."""
        planner = OrganizationPlanner()

        with pytest.raises(OrganizationPlanError):
            planner.create_plan(
                file_path=Path("/test/file.jpg"),
                classification=None,  # type: ignore
            )

    def test_other_category_no_plan(self) -> None:
        """Should handle 'other' category gracefully."""
        planner = OrganizationPlanner(base_path=Path("/home/user"))

        classification_result = ClassificationResult(
            file_path=Path("/downloads/unknown.xyz"),
            content_hash="hashJKL",
            classification=Classification(
                category="other",
                sub_category=None,
                confidence=0.3,
                method="metadata",
                requires_review=True,
            ),
            tags=TagSet(tags_en=[], tags_ko=[], source_breakdown={}),
            organization_plan=None,
            vision_result=None,
            metadata=FileMetadata(
                file_path=Path("/downloads/unknown.xyz"),
                size_bytes=500000,
                extension="xyz",
                created_at="2026-01-10T10:00:00",
                modified_at="2026-01-10T10:00:00",
                content_hash="hashJKL",
                exif=None,
            ),
            processing_time_ms=100.0,
            cached=False,
        )

        plan = planner.create_plan(
            file_path=classification_result.file_path,
            classification=classification_result,
        )

        # Should still generate a plan, but with lower confidence
        assert plan.confidence < 0.7


class TestOrganizationPlannerBatch:
    """Tests for batch organization plans."""

    def test_batch_plan_creation(self) -> None:
        """Should create batch organization plan."""
        planner = OrganizationPlanner(base_path=Path("/home/user"))

        results = [
            ClassificationResult(
                file_path=Path(f"/downloads/photo{i}.jpg"),
                content_hash=f"hash{i}",
                classification=Classification(
                    category="photo",
                    sub_category="portrait",
                    confidence=0.9,
                    method="ai",
                    requires_review=False,
                ),
                tags=TagSet(tags_en=[], tags_ko=[], source_breakdown={}),
                organization_plan=None,
                vision_result=None,
                metadata=FileMetadata(
                    file_path=Path(f"/downloads/photo{i}.jpg"),
                    size_bytes=500000,
                    extension="jpg",
                    created_at="2026-01-10T10:00:00",
                    modified_at="2026-01-10T10:00:00",
                    content_hash=f"hash{i}",
                    exif={"DateTimeOriginal": "2026:01:10 10:00:00"},
                ),
                processing_time_ms=100.0,
                cached=False,
            )
            for i in range(5)
        ]

        batch_plan = planner.create_batch_plan(results)

        assert batch_plan.total_files == 5
        assert len(batch_plan.plans) == 5
        assert all(isinstance(p, OrganizationPlan) for p in batch_plan.plans)

    def test_batch_plan_with_mixed_categories(self) -> None:
        """Should handle batch with mixed categories."""
        planner = OrganizationPlanner(base_path=Path("/home/user"))

        results = [
            ClassificationResult(
                file_path=Path("/downloads/photo.jpg"),
                content_hash="hash1",
                classification=Classification(
                    category="photo",
                    sub_category=None,
                    confidence=0.9,
                    method="ai",
                    requires_review=False,
                ),
                tags=TagSet(tags_en=[], tags_ko=[], source_breakdown={}),
                organization_plan=None,
                vision_result=None,
                metadata=FileMetadata(
                    file_path=Path("/downloads/photo.jpg"),
                    size_bytes=500000,
                    extension="jpg",
                    created_at="2026-01-10T10:00:00",
                    modified_at="2026-01-10T10:00:00",
                    content_hash="hash1",
                    exif=None,
                ),
                processing_time_ms=100.0,
                cached=False,
            ),
            ClassificationResult(
                file_path=Path("/downloads/screenshot.png"),
                content_hash="hash2",
                classification=Classification(
                    category="screenshot",
                    sub_category="desktop",
                    confidence=0.9,
                    method="ai",
                    requires_review=False,
                ),
                tags=TagSet(tags_en=[], tags_ko=[], source_breakdown={}),
                organization_plan=None,
                vision_result=None,
                metadata=FileMetadata(
                    file_path=Path("/downloads/screenshot.png"),
                    size_bytes=500000,
                    extension="png",
                    created_at="2026-01-10T10:00:00",
                    modified_at="2026-01-10T10:00:00",
                    content_hash="hash2",
                    exif=None,
                ),
                processing_time_ms=100.0,
                cached=False,
            ),
        ]

        batch_plan = planner.create_batch_plan(results)

        assert batch_plan.total_files == 2
        # Should have plans for different destinations
        target_paths = {str(p.target_path) for p in batch_plan.plans}
        assert len(target_paths) == 2  # Different destinations


class TestOrganizationPlannerPreserveFilename:
    """Tests for filename preservation."""

    def test_preserves_original_filename(self) -> None:
        """Should preserve the original filename in target path."""
        planner = OrganizationPlanner(base_path=Path("/home/user"))

        original_filename = "my_special_photo_2026.jpg"
        classification_result = ClassificationResult(
            file_path=Path(f"/downloads/{original_filename}"),
            content_hash="hashMNO",
            classification=Classification(
                category="photo",
                sub_category=None,
                confidence=0.9,
                method="ai",
                requires_review=False,
            ),
            tags=TagSet(tags_en=[], tags_ko=[], source_breakdown={}),
            organization_plan=None,
            vision_result=None,
            metadata=FileMetadata(
                file_path=Path(f"/downloads/{original_filename}"),
                size_bytes=500000,
                extension="jpg",
                created_at="2026-01-10T10:00:00",
                modified_at="2026-01-10T10:00:00",
                content_hash="hashMNO",
                exif=None,
            ),
            processing_time_ms=100.0,
            cached=False,
        )

        plan = planner.create_plan(
            file_path=classification_result.file_path,
            classification=classification_result,
        )

        assert plan.target_path.name == original_filename
