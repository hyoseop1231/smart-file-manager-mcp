"""Category registry for file classification.

TAG: CLASS-001-M1
SPEC: SPEC-CLASS-001

This module provides the CategoryRegistry class for managing
predefined and custom file categories.
"""

import re
from dataclasses import dataclass, field
from typing import Any

from smart_file_manager.core.exceptions import (
    CategoryNotFoundError,
    InvalidCategoryNameError,
)

# Valid category ID pattern: alphanumeric, hyphens, underscores only
VALID_CATEGORY_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


@dataclass
class Category:
    """A file category definition.

    Attributes:
        id: Unique category identifier.
        name_ko: Korean display name.
        name_en: English display name.
        sub_categories: List of sub-category IDs.
        is_custom: Whether this is a user-defined category.
    """

    id: str
    name_ko: str
    name_en: str
    sub_categories: list[str] = field(default_factory=list)
    is_custom: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the category.
        """
        return {
            "id": self.id,
            "name_ko": self.name_ko,
            "name_en": self.name_en,
            "sub_categories": self.sub_categories,
            "is_custom": self.is_custom,
        }


# Default categories as defined in SPEC-CLASS-001
DEFAULT_CATEGORIES: list[Category] = [
    Category(
        id="photo",
        name_ko="사진",
        name_en="Photo",
        sub_categories=["portrait", "landscape", "macro", "aerial"],
        is_custom=False,
    ),
    Category(
        id="screenshot",
        name_ko="스크린샷",
        name_en="Screenshot",
        sub_categories=["desktop", "mobile", "web", "game"],
        is_custom=False,
    ),
    Category(
        id="document",
        name_ko="문서",
        name_en="Document",
        sub_categories=["scan", "receipt", "id_card", "form"],
        is_custom=False,
    ),
    Category(
        id="artwork",
        name_ko="아트워크",
        name_en="Artwork",
        sub_categories=["illustration", "painting", "digital_art"],
        is_custom=False,
    ),
    Category(
        id="meme",
        name_ko="밈",
        name_en="Meme",
        sub_categories=["reaction", "text_meme", "comic"],
        is_custom=False,
    ),
    Category(
        id="product",
        name_ko="제품",
        name_en="Product",
        sub_categories=["electronics", "fashion", "food"],
        is_custom=False,
    ),
    Category(
        id="video",
        name_ko="비디오",
        name_en="Video",
        sub_categories=["clip", "movie", "recording", "tutorial"],
        is_custom=False,
    ),
    Category(
        id="other",
        name_ko="기타",
        name_en="Other",
        sub_categories=[],
        is_custom=False,
    ),
]


class CategoryRegistry:
    """Registry for managing file categories.

    This class provides methods for retrieving, registering, and
    validating file categories. It includes 8 default categories
    and supports custom user-defined categories.

    Attributes:
        _categories: Internal dictionary mapping category IDs to Category objects.
        _default_ids: Set of default category IDs (cannot be overridden).
    """

    def __init__(self) -> None:
        """Initialize the CategoryRegistry with default categories."""
        self._categories: dict[str, Category] = {}
        self._default_ids: set[str] = set()

        # Load default categories
        for category in DEFAULT_CATEGORIES:
            self._categories[category.id] = category
            self._default_ids.add(category.id)

    def get_category(self, category_id: str) -> Category:
        """Get a category by ID.

        Args:
            category_id: The category identifier.

        Returns:
            The Category object.

        Raises:
            CategoryNotFoundError: If the category does not exist.
        """
        if category_id not in self._categories:
            raise CategoryNotFoundError(category_id=category_id)
        return self._categories[category_id]

    def has_category(self, category_id: str) -> bool:
        """Check if a category exists.

        Args:
            category_id: The category identifier.

        Returns:
            True if the category exists, False otherwise.
        """
        return category_id in self._categories

    def get_all_categories(self) -> list[Category]:
        """Get all registered categories.

        Returns:
            List of all Category objects.
        """
        return list(self._categories.values())

    def get_category_ids(self) -> list[str]:
        """Get all category IDs.

        Returns:
            List of all category identifiers.
        """
        return list(self._categories.keys())

    def get_default_categories(self) -> list[Category]:
        """Get only default (non-custom) categories.

        Returns:
            List of default Category objects.
        """
        return [c for c in self._categories.values() if not c.is_custom]

    def get_custom_categories(self) -> list[Category]:
        """Get only custom (user-defined) categories.

        Returns:
            List of custom Category objects.
        """
        return [c for c in self._categories.values() if c.is_custom]

    def register_custom_category(
        self,
        id: str,
        name_ko: str,
        name_en: str,
        sub_categories: list[str] | None = None,
    ) -> Category:
        """Register a new custom category.

        Args:
            id: Unique category identifier (alphanumeric, hyphens, underscores).
            name_ko: Korean display name.
            name_en: English display name.
            sub_categories: Optional list of sub-category IDs.

        Returns:
            The newly created Category object.

        Raises:
            InvalidCategoryNameError: If the ID is invalid or already exists as default.
        """
        # Validate category ID format
        if not VALID_CATEGORY_ID_PATTERN.match(id):
            raise InvalidCategoryNameError(
                message=f"Invalid category ID format: {id}. "
                "Only alphanumeric characters, hyphens, and underscores are allowed.",
                category_id=id,
            )

        # Check if trying to override a default category
        if id in self._default_ids:
            raise InvalidCategoryNameError(
                message=f"Cannot override default category: {id}",
                category_id=id,
            )

        # Create and register the category
        category = Category(
            id=id,
            name_ko=name_ko,
            name_en=name_en,
            sub_categories=sub_categories or [],
            is_custom=True,
        )
        self._categories[id] = category
        return category

    def unregister_custom_category(self, category_id: str) -> None:
        """Unregister a custom category.

        Args:
            category_id: The category identifier to remove.

        Raises:
            InvalidCategoryNameError: If trying to unregister a default category.
            CategoryNotFoundError: If the category does not exist.
        """
        if category_id in self._default_ids:
            raise InvalidCategoryNameError(
                message=f"Cannot unregister default category: {category_id}",
                category_id=category_id,
            )

        if category_id not in self._categories:
            raise CategoryNotFoundError(category_id=category_id)

        del self._categories[category_id]

    def is_valid_sub_category(self, category_id: str, sub_category: str) -> bool:
        """Check if a sub-category is valid for a given category.

        Args:
            category_id: The parent category identifier.
            sub_category: The sub-category to validate.

        Returns:
            True if the sub-category is valid, False otherwise.
        """
        if category_id not in self._categories:
            return False

        category = self._categories[category_id]
        return sub_category in category.sub_categories
