"""Classification engine for file classification.

TAG: CLASS-001-M1
SPEC: SPEC-CLASS-001

This module provides the ClassificationEngine class for hybrid
classification using user rules, AI analysis, and metadata rules.
"""

import fnmatch
from dataclasses import dataclass
from typing import Any

from smart_file_manager.classification.category_registry import CategoryRegistry
from smart_file_manager.classification.models import (
    Classification,
    FileMetadata,
)
from smart_file_manager.services.vision_models import (
    ImageAnalysisResult,
    VideoAnalysisResult,
)

# Extension to category mapping for metadata-based classification
EXTENSION_CATEGORY_MAP: dict[str, str] = {
    # Image formats -> photo
    "jpg": "photo",
    "jpeg": "photo",
    "png": "photo",
    "gif": "photo",
    "webp": "photo",
    "bmp": "photo",
    "tiff": "photo",
    "heic": "photo",
    "heif": "photo",
    # Video formats -> video
    "mp4": "video",
    "mkv": "video",
    "avi": "video",
    "mov": "video",
    "webm": "video",
    "wmv": "video",
    "flv": "video",
    "m4v": "video",
}

# Scene keywords that suggest specific categories
SCENE_CATEGORY_HINTS: dict[str, str] = {
    "desktop": "screenshot",
    "screen": "screenshot",
    "code": "screenshot",
    "terminal": "screenshot",
    "browser": "screenshot",
    "document": "document",
    "scan": "document",
    "receipt": "document",
    "invoice": "document",
    "form": "document",
    "art": "artwork",
    "illustration": "artwork",
    "painting": "artwork",
    "digital_art": "artwork",
    "drawing": "artwork",
    "meme": "meme",
    "comic": "meme",
    "product": "product",
    "electronics": "product",
    "fashion": "product",
}

# Object keywords that suggest specific categories
OBJECT_CATEGORY_HINTS: dict[str, str] = {
    "person": "photo",
    "people": "photo",
    "face": "photo",
    "portrait": "photo",
    "landscape": "photo",
    "nature": "photo",
    "animal": "photo",
    "screen": "screenshot",
    "text": "screenshot",
    "code": "screenshot",
    "window": "screenshot",
    "document": "document",
    "paper": "document",
    "receipt": "document",
    "id_card": "document",
}


@dataclass
class UserRule:
    """A user-defined classification rule.

    Attributes:
        pattern: File path pattern for matching (supports wildcards).
        category: Target category ID.
        sub_category: Optional target sub-category ID.
    """

    pattern: str
    category: str
    sub_category: str | None = None


class ClassificationEngine:
    """Engine for classifying files using hybrid approach.

    This engine classifies files using a priority-based approach:
    1. User-defined rules (highest priority)
    2. AI-based classification from VisionService results
    3. Metadata-based rules (lowest priority)

    Attributes:
        category_registry: Registry for category validation.
        confidence_threshold: Threshold for requires_review flag.
        _user_rules: List of user-defined classification rules.
    """

    def __init__(
        self,
        category_registry: CategoryRegistry | None = None,
        confidence_threshold: float = 0.7,
    ) -> None:
        """Initialize the ClassificationEngine.

        Args:
            category_registry: Optional custom category registry.
            confidence_threshold: Confidence threshold for review flag.
        """
        self.category_registry = category_registry or CategoryRegistry()
        self.confidence_threshold = confidence_threshold
        self._user_rules: list[UserRule] = []

    def classify(
        self,
        vision_result: ImageAnalysisResult | VideoAnalysisResult | None,
        metadata: FileMetadata,
    ) -> Classification:
        """Classify a file using the priority-based approach.

        Args:
            vision_result: Optional VisionService analysis result.
            metadata: File metadata.

        Returns:
            Classification result with category, confidence, and method.
        """
        # Priority 1: User rules
        user_classification = self._apply_user_rules(metadata)
        if user_classification is not None:
            return user_classification

        # Priority 2: AI classification
        if vision_result is not None:
            ai_classification = self._apply_ai_classification(vision_result, metadata)
            return ai_classification

        # Priority 3: Metadata rules
        return self._apply_metadata_rules(metadata)

    def _apply_user_rules(self, metadata: FileMetadata) -> Classification | None:
        """Apply user-defined classification rules.

        Args:
            metadata: File metadata.

        Returns:
            Classification if a rule matches, None otherwise.
        """
        file_path_str = str(metadata.file_path)

        for rule in self._user_rules:
            if fnmatch.fnmatch(file_path_str, rule.pattern):
                return Classification(
                    category=rule.category,
                    sub_category=rule.sub_category,
                    confidence=1.0,  # User rules have full confidence
                    method="user_rule",
                    requires_review=False,
                )

        return None

    def _apply_ai_classification(
        self,
        vision_result: ImageAnalysisResult | VideoAnalysisResult,
        metadata: FileMetadata,
    ) -> Classification:
        """Apply AI-based classification from VisionService results.

        Args:
            vision_result: VisionService analysis result.
            metadata: File metadata.

        Returns:
            Classification based on AI analysis.
        """
        # Handle VideoAnalysisResult
        if isinstance(vision_result, VideoAnalysisResult):
            return Classification(
                category="video",
                sub_category=self._detect_video_sub_category(vision_result),
                confidence=0.9,
                method="ai",
                requires_review=False,
            )

        # Handle ImageAnalysisResult
        category, sub_category, confidence = self._analyze_image_result(vision_result)

        requires_review = confidence < self.confidence_threshold

        return Classification(
            category=category,
            sub_category=sub_category,
            confidence=confidence,
            method="ai",
            requires_review=requires_review,
        )

    def _analyze_image_result(
        self,
        result: ImageAnalysisResult,
    ) -> tuple[str, str | None, float]:
        """Analyze ImageAnalysisResult to determine category.

        Args:
            result: ImageAnalysisResult from VisionService.

        Returns:
            Tuple of (category, sub_category, confidence).
        """
        category_scores: dict[str, float] = {}
        sub_category: str | None = None

        # Check for screenshot indicators
        if self._is_screenshot(result):
            category_scores["screenshot"] = 0.9
            sub_category = self._detect_screenshot_sub_category(result)

        # Check for document indicators
        if self._is_document(result):
            category_scores["document"] = max(category_scores.get("document", 0), 0.85)
            sub_category = self._detect_document_sub_category(result)

        # Check scene hints
        if result.scene:
            scene_lower = result.scene.lower()
            if scene_lower in SCENE_CATEGORY_HINTS:
                hint_category = SCENE_CATEGORY_HINTS[scene_lower]
                category_scores[hint_category] = max(category_scores.get(hint_category, 0), 0.75)

        # Check object hints
        for obj in result.objects:
            obj_name = obj.name.lower()
            if obj_name in OBJECT_CATEGORY_HINTS:
                hint_category = OBJECT_CATEGORY_HINTS[obj_name]
                # Weight by object confidence
                score = 0.6 + (obj.confidence * 0.3)
                category_scores[hint_category] = max(category_scores.get(hint_category, 0), score)

        # Check tags for additional hints
        for tag in result.tags:
            tag_lower = tag.lower()
            if tag_lower in SCENE_CATEGORY_HINTS:
                hint_category = SCENE_CATEGORY_HINTS[tag_lower]
                category_scores[hint_category] = max(category_scores.get(hint_category, 0), 0.6)

        # Determine best category
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)  # type: ignore
            confidence = category_scores[best_category]
        else:
            # Default to photo for images with no clear category
            best_category = "photo"
            confidence = 0.5

        # Detect sub-category if not already set
        if sub_category is None and best_category == "photo":
            sub_category = self._detect_photo_sub_category(result)

        return best_category, sub_category, confidence

    def _is_screenshot(self, result: ImageAnalysisResult) -> bool:
        """Check if image is likely a screenshot.

        Args:
            result: ImageAnalysisResult.

        Returns:
            True if likely a screenshot.
        """
        # Check scene
        if result.scene and result.scene.lower() in ["desktop", "screen", "code"]:
            return True

        # Check for text content (common in screenshots)
        if result.text_content and len(result.text_content) > 50:
            return True

        # Check for screen/code-related objects
        screen_keywords = {"screen", "text", "code", "window", "button", "menu"}
        for obj in result.objects:
            if obj.name.lower() in screen_keywords and obj.confidence > 0.7:
                return True

        # Check tags
        screenshot_tags = {"code", "programming", "terminal", "screenshot", "desktop"}
        if any(tag.lower() in screenshot_tags for tag in result.tags):
            return True

        return False

    def _is_document(self, result: ImageAnalysisResult) -> bool:
        """Check if image is likely a document.

        Args:
            result: ImageAnalysisResult.

        Returns:
            True if likely a document.
        """
        # Check scene
        if result.scene and result.scene.lower() in ["document", "scan", "paper"]:
            return True

        # Check for document-related objects
        doc_keywords = {"document", "paper", "receipt", "invoice", "form", "id_card"}
        for obj in result.objects:
            if obj.name.lower() in doc_keywords and obj.confidence > 0.7:
                return True

        # Check tags
        doc_tags = {"document", "invoice", "receipt", "scan", "form", "paper"}
        if any(tag.lower() in doc_tags for tag in result.tags):
            return True

        return False

    def _detect_screenshot_sub_category(
        self,
        result: ImageAnalysisResult,
    ) -> str | None:
        """Detect sub-category for screenshots.

        Args:
            result: ImageAnalysisResult.

        Returns:
            Sub-category or None.
        """
        scene_lower = result.scene.lower() if result.scene else ""
        tags_lower = [t.lower() for t in result.tags]

        if "mobile" in scene_lower or "mobile" in tags_lower:
            return "mobile"
        if "game" in scene_lower or "game" in tags_lower:
            return "game"
        if "web" in scene_lower or "browser" in scene_lower:
            return "web"

        return "desktop"

    def _detect_document_sub_category(
        self,
        result: ImageAnalysisResult,
    ) -> str | None:
        """Detect sub-category for documents.

        Args:
            result: ImageAnalysisResult.

        Returns:
            Sub-category or None.
        """
        tags_lower = [t.lower() for t in result.tags]
        objects_lower = [o.name.lower() for o in result.objects]

        if "receipt" in tags_lower or "receipt" in objects_lower:
            return "receipt"
        if "id_card" in tags_lower or "id_card" in objects_lower:
            return "id_card"
        if "form" in tags_lower or "form" in objects_lower:
            return "form"

        return "scan"

    def _detect_photo_sub_category(
        self,
        result: ImageAnalysisResult,
    ) -> str | None:
        """Detect sub-category for photos.

        Args:
            result: ImageAnalysisResult.

        Returns:
            Sub-category or None.
        """
        objects_lower = [o.name.lower() for o in result.objects]
        tags_lower = [t.lower() for t in result.tags]

        # Portrait detection
        if "person" in objects_lower or "face" in objects_lower:
            return "portrait"

        # Landscape detection
        if result.scene and result.scene.lower() in ["outdoor", "nature", "landscape"]:
            return "landscape"
        if any(t in tags_lower for t in ["landscape", "nature", "outdoor"]):
            return "landscape"

        # Macro detection
        if "macro" in tags_lower:
            return "macro"

        # Aerial detection
        if "aerial" in tags_lower or "drone" in tags_lower:
            return "aerial"

        return None

    def _detect_video_sub_category(
        self,
        result: VideoAnalysisResult,
    ) -> str | None:
        """Detect sub-category for videos.

        Args:
            result: VideoAnalysisResult.

        Returns:
            Sub-category or None.
        """
        # Short videos are clips
        if result.duration_seconds < 60:
            return "clip"

        # Long videos are movies
        if result.duration_seconds > 3600:
            return "movie"

        return "recording"

    def _apply_metadata_rules(self, metadata: FileMetadata) -> Classification:
        """Apply metadata-based classification rules.

        Args:
            metadata: File metadata.

        Returns:
            Classification based on file metadata.
        """
        extension = metadata.extension.lower()

        # Look up category by extension
        category = EXTENSION_CATEGORY_MAP.get(extension, "other")

        # Lower confidence for metadata-only classification
        confidence = 0.6 if category != "other" else 0.3

        return Classification(
            category=category,
            sub_category=None,
            confidence=confidence,
            method="metadata",
            requires_review=confidence < self.confidence_threshold,
        )

    def register_user_rule(
        self,
        pattern: str,
        category: str,
        sub_category: str | None = None,
    ) -> None:
        """Register a user-defined classification rule.

        Args:
            pattern: File path pattern (supports wildcards).
            category: Target category ID.
            sub_category: Optional target sub-category ID.
        """
        rule = UserRule(
            pattern=pattern,
            category=category,
            sub_category=sub_category,
        )
        self._user_rules.append(rule)

    def unregister_user_rule(self, pattern: str) -> None:
        """Unregister a user-defined classification rule.

        Args:
            pattern: The pattern to remove.
        """
        self._user_rules = [r for r in self._user_rules if r.pattern != pattern]

    def clear_user_rules(self) -> None:
        """Remove all user-defined rules."""
        self._user_rules = []

    def get_user_rules(self) -> list[dict[str, Any]]:
        """Get all user-defined rules as dictionaries.

        Returns:
            List of rule dictionaries.
        """
        return [
            {
                "pattern": r.pattern,
                "category": r.category,
                "sub_category": r.sub_category,
            }
            for r in self._user_rules
        ]
