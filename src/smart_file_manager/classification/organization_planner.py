"""Organization planner for file classification.

TAG: CLASS-001-M3
SPEC: SPEC-CLASS-001

This module provides the OrganizationPlanner class for generating
organization plans based on classification results.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from smart_file_manager.classification.models import (
    ClassificationResult,
    OrganizationPlan,
)
from smart_file_manager.core.exceptions import OrganizationPlanError


@dataclass
class BatchOrganizationPlan:
    """A batch of organization plans.

    Attributes:
        plans: List of individual organization plans.
        total_files: Total number of files in the batch.
    """

    plans: list[OrganizationPlan]
    total_files: int


# Category to folder mapping
CATEGORY_FOLDER_MAP: dict[str, str] = {
    "photo": "Photos",
    "screenshot": "Screenshots",
    "document": "Documents",
    "artwork": "Artwork",
    "meme": "Memes",
    "product": "Products",
    "video": "Videos",
    "other": "Other",
}

# Sub-category specific folder overrides
SUB_CATEGORY_FOLDER_MAP: dict[str, str] = {
    "scan": "Scans",
    "receipt": "Receipts",
    "id_card": "ID_Cards",
}


class OrganizationPlanner:
    """Planner for generating file organization recommendations.

    This class creates organization plans based on classification results,
    suggesting target paths for files based on their categories and metadata.

    Attributes:
        base_path: Base directory for file organization.
    """

    def __init__(self, base_path: Path | None = None) -> None:
        """Initialize the OrganizationPlanner.

        Args:
            base_path: Base directory for organization. Defaults to home directory.
        """
        self.base_path = base_path or Path.home()

    def create_plan(
        self,
        file_path: Path,
        classification: ClassificationResult,
    ) -> OrganizationPlan:
        """Create an organization plan for a classified file.

        Args:
            file_path: Path to the source file.
            classification: Classification result for the file.

        Returns:
            OrganizationPlan with recommended action and target path.

        Raises:
            OrganizationPlanError: If classification is None or invalid.
        """
        if classification is None:
            raise OrganizationPlanError("Classification result is required")

        # Extract classification data
        category = classification.classification.category
        sub_category = classification.classification.sub_category
        confidence = classification.classification.confidence
        metadata = classification.metadata

        # Determine target folder based on category
        target_folder = self._get_target_folder(category, sub_category)

        # Get date for organization
        date_str = self._extract_date(metadata)
        year, month = self._parse_date(date_str)

        # Build target path: base_path/CategoryFolder/YYYY/MM/filename
        target_path = self.base_path / target_folder / year / month / file_path.name

        # Calculate plan confidence (lower for 'other' category)
        plan_confidence = self._calculate_confidence(category, confidence)

        # Generate reason
        reason = self._generate_reason(category, sub_category)

        return OrganizationPlan(
            source_path=file_path,
            target_path=target_path,
            action="move",
            reason=reason,
            confidence=plan_confidence,
        )

    def create_batch_plan(
        self,
        results: list[ClassificationResult],
    ) -> BatchOrganizationPlan:
        """Create organization plans for multiple classified files.

        Args:
            results: List of classification results.

        Returns:
            BatchOrganizationPlan containing all individual plans.
        """
        plans: list[OrganizationPlan] = []

        for result in results:
            plan = self.create_plan(
                file_path=result.file_path,
                classification=result,
            )
            plans.append(plan)

        return BatchOrganizationPlan(
            plans=plans,
            total_files=len(results),
        )

    def _get_target_folder(
        self,
        category: str,
        sub_category: str | None,
    ) -> str:
        """Get the target folder name for a category.

        Args:
            category: File category.
            sub_category: Optional sub-category.

        Returns:
            Folder name for the category.
        """
        # Check sub-category specific folders first
        if sub_category and sub_category in SUB_CATEGORY_FOLDER_MAP:
            return SUB_CATEGORY_FOLDER_MAP[sub_category]

        # Fall back to category folder
        return CATEGORY_FOLDER_MAP.get(category, "Other")

    def _extract_date(self, metadata) -> str:
        """Extract date from metadata.

        Args:
            metadata: FileMetadata object.

        Returns:
            Date string in ISO format or from EXIF.
        """
        # Try EXIF DateTimeOriginal first
        if metadata.exif and "DateTimeOriginal" in metadata.exif:
            return metadata.exif["DateTimeOriginal"]

        # Fall back to modified_at
        return metadata.modified_at

    def _parse_date(self, date_str: str) -> tuple[str, str]:
        """Parse date string to extract year and month.

        Args:
            date_str: Date string (EXIF format or ISO format).

        Returns:
            Tuple of (year, month) as strings.
        """
        try:
            # Try EXIF format: "YYYY:MM:DD HH:MM:SS"
            if ":" in date_str and " " in date_str:
                date_part = date_str.split(" ")[0]
                parts = date_part.split(":")
                if len(parts) >= 2:
                    return parts[0], parts[1]

            # Try ISO format: "YYYY-MM-DDTHH:MM:SS"
            if "T" in date_str:
                date_part = date_str.split("T")[0]
                parts = date_part.split("-")
                if len(parts) >= 2:
                    return parts[0], parts[1]

            # Try simple ISO date: "YYYY-MM-DD..."
            if "-" in date_str:
                parts = date_str.split("-")
                if len(parts) >= 2:
                    return parts[0], parts[1]

        except (ValueError, IndexError):
            pass

        # Default to current date
        now = datetime.now()
        return str(now.year), f"{now.month:02d}"

    def _calculate_confidence(
        self,
        category: str,
        classification_confidence: float,
    ) -> float:
        """Calculate organization plan confidence.

        Args:
            category: File category.
            classification_confidence: Confidence from classification.

        Returns:
            Adjusted confidence for organization plan.
        """
        # Lower confidence for 'other' category
        if category == "other":
            return min(classification_confidence * 0.5, 0.5)

        # Slightly adjust confidence based on category clarity
        return min(classification_confidence * 0.95, 0.99)

    def _generate_reason(
        self,
        category: str,
        sub_category: str | None,
    ) -> str:
        """Generate human-readable reason for organization.

        Args:
            category: File category.
            sub_category: Optional sub-category.

        Returns:
            Reason string for the organization plan.
        """
        category_display = category.replace("_", " ").title()

        if sub_category:
            sub_display = sub_category.replace("_", " ").title()
            return f"{category_display} ({sub_display}) detected - organizing by date"

        return f"{category_display} detected - organizing by date"
