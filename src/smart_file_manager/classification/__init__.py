"""Classification module for Smart File Manager.

TAG: CLASS-001
SPEC: SPEC-CLASS-001

This module provides AI-based file classification services including:
- CategoryRegistry: Category management with predefined and custom categories
- ClassificationEngine: Hybrid classification (user rules > AI > metadata)
- TagGenerator: Automatic tag generation from VisionService results
- OrganizationPlanner: File organization recommendations
- ClassificationService: Main service coordinating all classification components
"""

from smart_file_manager.classification.category_registry import CategoryRegistry
from smart_file_manager.classification.classification_service import (
    ClassificationService,
)
from smart_file_manager.classification.engine import ClassificationEngine
from smart_file_manager.classification.models import (
    BatchClassificationResult,
    Classification,
    ClassificationResult,
    FileMetadata,
    OrganizationPlan,
    TagSet,
)
from smart_file_manager.classification.organization_planner import (
    BatchOrganizationPlan,
    OrganizationPlanner,
)
from smart_file_manager.classification.tag_generator import TagGenerator

__all__ = [
    "BatchClassificationResult",
    "BatchOrganizationPlan",
    "CategoryRegistry",
    "Classification",
    "ClassificationEngine",
    "ClassificationResult",
    "ClassificationService",
    "FileMetadata",
    "OrganizationPlan",
    "OrganizationPlanner",
    "TagGenerator",
    "TagSet",
]
