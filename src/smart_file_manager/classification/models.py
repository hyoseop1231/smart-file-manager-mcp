"""Classification data models.

TAG: CLASS-001-M1
SPEC: SPEC-CLASS-001

This module defines dataclasses for classification results,
including Classification, TagSet, FileMetadata, OrganizationPlan,
and ClassificationResult.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Classification:
    """Classification result for a file.

    Attributes:
        category: Primary category ID (e.g., photo, screenshot).
        sub_category: Optional sub-category ID (e.g., portrait, desktop).
        confidence: Confidence score between 0.0 and 1.0.
        method: Classification method used (user_rule, ai, metadata).
        requires_review: Whether manual review is recommended.
    """

    category: str
    sub_category: str | None
    confidence: float
    method: str
    requires_review: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the classification.
        """
        return {
            "category": self.category,
            "sub_category": self.sub_category,
            "confidence": self.confidence,
            "method": self.method,
            "requires_review": self.requires_review,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Classification":
        """Create an instance from a dictionary.

        Args:
            data: Dictionary containing the classification data.

        Returns:
            Classification instance.
        """
        return cls(
            category=data["category"],
            sub_category=data.get("sub_category"),
            confidence=data["confidence"],
            method=data["method"],
            requires_review=data.get("requires_review", False),
        )


@dataclass
class TagSet:
    """Set of tags for a file in multiple languages.

    Attributes:
        tags_en: List of English tags.
        tags_ko: List of Korean tags.
        source_breakdown: Dictionary mapping source type to tags.
    """

    tags_en: list[str]
    tags_ko: list[str]
    source_breakdown: dict[str, list[str]]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the tag set.
        """
        return {
            "tags_en": self.tags_en,
            "tags_ko": self.tags_ko,
            "source_breakdown": self.source_breakdown,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TagSet":
        """Create an instance from a dictionary.

        Args:
            data: Dictionary containing the tag set data.

        Returns:
            TagSet instance.
        """
        return cls(
            tags_en=data.get("tags_en", []),
            tags_ko=data.get("tags_ko", []),
            source_breakdown=data.get("source_breakdown", {}),
        )


@dataclass
class FileMetadata:
    """Metadata for a file.

    Attributes:
        file_path: Path to the file.
        size_bytes: File size in bytes.
        extension: File extension without dot.
        created_at: Creation timestamp as ISO string.
        modified_at: Modification timestamp as ISO string.
        content_hash: SHA256 hash of file content.
        exif: Optional EXIF metadata dictionary.
    """

    file_path: Path
    size_bytes: int
    extension: str
    created_at: str
    modified_at: str
    content_hash: str
    exif: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the metadata.
        """
        return {
            "file_path": str(self.file_path),
            "size_bytes": self.size_bytes,
            "extension": self.extension,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "content_hash": self.content_hash,
            "exif": self.exif,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileMetadata":
        """Create an instance from a dictionary.

        Args:
            data: Dictionary containing the metadata.

        Returns:
            FileMetadata instance.
        """
        return cls(
            file_path=Path(data["file_path"]),
            size_bytes=data["size_bytes"],
            extension=data["extension"],
            created_at=data["created_at"],
            modified_at=data["modified_at"],
            content_hash=data["content_hash"],
            exif=data.get("exif"),
        )


@dataclass
class OrganizationPlan:
    """Organization plan for a file.

    Attributes:
        action: Action to take (move, copy, delete, group).
        source_path: Original file path.
        target_path: Recommended target path.
        reason: Reason for the recommendation.
        confidence: Confidence score for the recommendation.
    """

    action: str
    source_path: Path
    target_path: Path
    reason: str
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the plan.
        """
        return {
            "action": self.action,
            "source_path": str(self.source_path),
            "target_path": str(self.target_path),
            "reason": self.reason,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OrganizationPlan":
        """Create an instance from a dictionary.

        Args:
            data: Dictionary containing the plan data.

        Returns:
            OrganizationPlan instance.
        """
        return cls(
            action=data["action"],
            source_path=Path(data["source_path"]),
            target_path=Path(data["target_path"]),
            reason=data["reason"],
            confidence=data["confidence"],
        )


@dataclass
class ClassificationResult:
    """Complete classification result for a file.

    Attributes:
        file_path: Path to the classified file.
        content_hash: SHA256 hash of file content.
        classification: Classification details.
        tags: Generated tags.
        organization_plan: Optional organization recommendation.
        vision_result: Optional vision analysis result.
        metadata: File metadata.
        processing_time_ms: Processing time in milliseconds.
        cached: Whether result was from cache.
    """

    file_path: Path
    content_hash: str
    classification: Classification
    tags: TagSet
    organization_plan: OrganizationPlan | None
    vision_result: Any  # ImageAnalysisResult | VideoAnalysisResult | None
    metadata: FileMetadata
    processing_time_ms: float
    cached: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the result.
        """
        return {
            "file_path": str(self.file_path),
            "content_hash": self.content_hash,
            "classification": self.classification.to_dict(),
            "tags": self.tags.to_dict(),
            "organization_plan": (
                self.organization_plan.to_dict() if self.organization_plan else None
            ),
            "vision_result": (
                self.vision_result.to_dict()
                if self.vision_result and hasattr(self.vision_result, "to_dict")
                else None
            ),
            "metadata": self.metadata.to_dict(),
            "processing_time_ms": self.processing_time_ms,
            "cached": self.cached,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClassificationResult":
        """Create an instance from a dictionary.

        Args:
            data: Dictionary containing the result data.

        Returns:
            ClassificationResult instance.
        """
        return cls(
            file_path=Path(data["file_path"]),
            content_hash=data["content_hash"],
            classification=Classification.from_dict(data["classification"]),
            tags=TagSet.from_dict(data["tags"]),
            organization_plan=(
                OrganizationPlan.from_dict(data["organization_plan"])
                if data.get("organization_plan")
                else None
            ),
            vision_result=data.get("vision_result"),
            metadata=FileMetadata.from_dict(data["metadata"]),
            processing_time_ms=data["processing_time_ms"],
            cached=data["cached"],
        )


@dataclass
class BatchClassificationResult:
    """Result of batch classification operation.

    Attributes:
        total_files: Total number of files processed.
        successful: Number of successfully classified files.
        failed: Number of failed classifications.
        results: List of successful classification results.
        errors: List of errors that occurred.
        organization_plan: Optional batch organization plan.
        total_processing_time_ms: Total processing time in milliseconds.
    """

    total_files: int
    successful: int
    failed: int
    results: list[ClassificationResult]
    errors: list[Exception]
    organization_plan: Any | None  # BatchOrganizationPlan | None
    total_processing_time_ms: float
