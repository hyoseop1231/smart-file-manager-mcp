"""Tests for CategoryRegistry class.

TAG: CLASS-001-M1
SPEC: SPEC-CLASS-001

This module tests:
- Default category loading
- Category retrieval
- Custom category registration
- Category validation
"""

import pytest
from smart_file_manager.classification.category_registry import (
    Category,
    CategoryRegistry,
)

from smart_file_manager.core.exceptions import (
    CategoryNotFoundError,
    InvalidCategoryNameError,
)


class TestCategory:
    """Tests for Category dataclass."""

    def test_category_creation(self) -> None:
        """Should create Category with all fields."""
        category = Category(
            id="photo",
            name_ko="사진",
            name_en="Photo",
            sub_categories=["portrait", "landscape", "macro", "aerial"],
            is_custom=False,
        )

        assert category.id == "photo"
        assert category.name_ko == "사진"
        assert category.name_en == "Photo"
        assert len(category.sub_categories) == 4
        assert category.is_custom is False

    def test_category_custom(self) -> None:
        """Should mark custom category correctly."""
        category = Category(
            id="work_docs",
            name_ko="업무 문서",
            name_en="Work Documents",
            sub_categories=[],
            is_custom=True,
        )

        assert category.is_custom is True

    def test_category_to_dict(self) -> None:
        """Should serialize Category to dictionary."""
        category = Category(
            id="screenshot",
            name_ko="스크린샷",
            name_en="Screenshot",
            sub_categories=["desktop", "mobile"],
            is_custom=False,
        )

        result = category.to_dict()

        assert result["id"] == "screenshot"
        assert result["name_ko"] == "스크린샷"
        assert result["sub_categories"] == ["desktop", "mobile"]


class TestCategoryRegistryDefaultCategories:
    """Tests for default categories (REQ-U-003, acceptance 5.1)."""

    def test_registry_has_eight_default_categories(self) -> None:
        """Should have 8 default categories."""
        registry = CategoryRegistry()

        categories = registry.get_all_categories()

        assert len(categories) == 8

    def test_registry_contains_photo_category(self) -> None:
        """Should contain photo category with sub-categories."""
        registry = CategoryRegistry()

        photo = registry.get_category("photo")

        assert photo.id == "photo"
        assert photo.name_ko == "사진"
        assert photo.name_en == "Photo"
        assert "portrait" in photo.sub_categories
        assert "landscape" in photo.sub_categories
        assert "macro" in photo.sub_categories
        assert "aerial" in photo.sub_categories

    def test_registry_contains_screenshot_category(self) -> None:
        """Should contain screenshot category with sub-categories."""
        registry = CategoryRegistry()

        screenshot = registry.get_category("screenshot")

        assert screenshot.id == "screenshot"
        assert screenshot.name_ko == "스크린샷"
        assert screenshot.name_en == "Screenshot"
        assert "desktop" in screenshot.sub_categories
        assert "mobile" in screenshot.sub_categories
        assert "web" in screenshot.sub_categories
        assert "game" in screenshot.sub_categories

    def test_registry_contains_document_category(self) -> None:
        """Should contain document category with sub-categories."""
        registry = CategoryRegistry()

        document = registry.get_category("document")

        assert document.id == "document"
        assert document.name_ko == "문서"
        assert document.name_en == "Document"
        assert "scan" in document.sub_categories
        assert "receipt" in document.sub_categories
        assert "id_card" in document.sub_categories
        assert "form" in document.sub_categories

    def test_registry_contains_artwork_category(self) -> None:
        """Should contain artwork category with sub-categories."""
        registry = CategoryRegistry()

        artwork = registry.get_category("artwork")

        assert artwork.id == "artwork"
        assert artwork.name_ko == "아트워크"
        assert artwork.name_en == "Artwork"
        assert "illustration" in artwork.sub_categories
        assert "painting" in artwork.sub_categories
        assert "digital_art" in artwork.sub_categories

    def test_registry_contains_meme_category(self) -> None:
        """Should contain meme category with sub-categories."""
        registry = CategoryRegistry()

        meme = registry.get_category("meme")

        assert meme.id == "meme"
        assert meme.name_ko == "밈"
        assert meme.name_en == "Meme"
        assert "reaction" in meme.sub_categories
        assert "text_meme" in meme.sub_categories
        assert "comic" in meme.sub_categories

    def test_registry_contains_product_category(self) -> None:
        """Should contain product category with sub-categories."""
        registry = CategoryRegistry()

        product = registry.get_category("product")

        assert product.id == "product"
        assert product.name_ko == "제품"
        assert product.name_en == "Product"
        assert "electronics" in product.sub_categories
        assert "fashion" in product.sub_categories
        assert "food" in product.sub_categories

    def test_registry_contains_video_category(self) -> None:
        """Should contain video category with sub-categories."""
        registry = CategoryRegistry()

        video = registry.get_category("video")

        assert video.id == "video"
        assert video.name_ko == "비디오"
        assert video.name_en == "Video"
        assert "clip" in video.sub_categories
        assert "movie" in video.sub_categories
        assert "recording" in video.sub_categories
        assert "tutorial" in video.sub_categories

    def test_registry_contains_other_category(self) -> None:
        """Should contain other category without sub-categories."""
        registry = CategoryRegistry()

        other = registry.get_category("other")

        assert other.id == "other"
        assert other.name_ko == "기타"
        assert other.name_en == "Other"
        assert other.sub_categories == []

    def test_registry_default_categories_not_custom(self) -> None:
        """Default categories should not be marked as custom."""
        registry = CategoryRegistry()

        for category in registry.get_all_categories():
            assert category.is_custom is False


class TestCategoryRegistryLookup:
    """Tests for category lookup operations."""

    def test_get_category_by_id(self) -> None:
        """Should retrieve category by ID."""
        registry = CategoryRegistry()

        category = registry.get_category("photo")

        assert category.id == "photo"

    def test_get_nonexistent_category_raises_error(self) -> None:
        """Should raise CategoryNotFoundError for nonexistent category."""
        registry = CategoryRegistry()

        with pytest.raises(CategoryNotFoundError) as exc_info:
            registry.get_category("nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_has_category_true(self) -> None:
        """Should return True for existing category."""
        registry = CategoryRegistry()

        assert registry.has_category("photo") is True
        assert registry.has_category("screenshot") is True

    def test_has_category_false(self) -> None:
        """Should return False for nonexistent category."""
        registry = CategoryRegistry()

        assert registry.has_category("nonexistent") is False

    def test_get_category_ids(self) -> None:
        """Should return all category IDs."""
        registry = CategoryRegistry()

        ids = registry.get_category_ids()

        assert "photo" in ids
        assert "screenshot" in ids
        assert "document" in ids
        assert "artwork" in ids
        assert "meme" in ids
        assert "product" in ids
        assert "video" in ids
        assert "other" in ids


class TestCategoryRegistryCustomCategories:
    """Tests for custom category registration (acceptance 5.2)."""

    def test_register_custom_category(self) -> None:
        """Should register custom category successfully."""
        registry = CategoryRegistry()

        registry.register_custom_category(
            id="work_document",
            name_ko="업무 문서",
            name_en="Work Document",
            sub_categories=["report", "presentation"],
        )

        category = registry.get_category("work_document")
        assert category.id == "work_document"
        assert category.name_ko == "업무 문서"
        assert category.is_custom is True

    def test_custom_category_in_all_categories(self) -> None:
        """Custom category should appear in all categories list."""
        registry = CategoryRegistry()

        registry.register_custom_category(
            id="custom_test",
            name_ko="테스트",
            name_en="Test",
            sub_categories=[],
        )

        all_categories = registry.get_all_categories()
        custom_ids = [c.id for c in all_categories if c.is_custom]

        assert "custom_test" in custom_ids

    def test_register_invalid_category_name_special_chars(self) -> None:
        """Should reject category name with special characters (REQ-N-006)."""
        registry = CategoryRegistry()

        with pytest.raises(InvalidCategoryNameError):
            registry.register_custom_category(
                id="invalid@name!",
                name_ko="잘못된 이름",
                name_en="Invalid Name",
                sub_categories=[],
            )

    def test_register_invalid_category_name_spaces(self) -> None:
        """Should reject category name with spaces."""
        registry = CategoryRegistry()

        with pytest.raises(InvalidCategoryNameError):
            registry.register_custom_category(
                id="invalid name",
                name_ko="잘못된 이름",
                name_en="Invalid Name",
                sub_categories=[],
            )

    def test_valid_category_name_with_hyphen(self) -> None:
        """Should accept category name with hyphen."""
        registry = CategoryRegistry()

        registry.register_custom_category(
            id="work-docs",
            name_ko="업무 문서",
            name_en="Work Docs",
            sub_categories=[],
        )

        assert registry.has_category("work-docs") is True

    def test_valid_category_name_with_underscore(self) -> None:
        """Should accept category name with underscore."""
        registry = CategoryRegistry()

        registry.register_custom_category(
            id="work_docs",
            name_ko="업무 문서",
            name_en="Work Docs",
            sub_categories=[],
        )

        assert registry.has_category("work_docs") is True

    def test_valid_category_name_with_numbers(self) -> None:
        """Should accept category name with numbers."""
        registry = CategoryRegistry()

        registry.register_custom_category(
            id="category123",
            name_ko="카테고리123",
            name_en="Category123",
            sub_categories=[],
        )

        assert registry.has_category("category123") is True

    def test_cannot_override_default_category(self) -> None:
        """Should not allow overriding default categories."""
        registry = CategoryRegistry()

        with pytest.raises(InvalidCategoryNameError):
            registry.register_custom_category(
                id="photo",  # Existing default category
                name_ko="사진 재정의",
                name_en="Redefined Photo",
                sub_categories=[],
            )

    def test_unregister_custom_category(self) -> None:
        """Should unregister custom category."""
        registry = CategoryRegistry()

        registry.register_custom_category(
            id="temp_category",
            name_ko="임시",
            name_en="Temporary",
            sub_categories=[],
        )
        assert registry.has_category("temp_category") is True

        registry.unregister_custom_category("temp_category")
        assert registry.has_category("temp_category") is False

    def test_cannot_unregister_default_category(self) -> None:
        """Should not allow unregistering default categories."""
        registry = CategoryRegistry()

        with pytest.raises(InvalidCategoryNameError):
            registry.unregister_custom_category("photo")


class TestCategoryRegistryValidation:
    """Tests for category validation."""

    def test_is_valid_sub_category_true(self) -> None:
        """Should return True for valid sub-category."""
        registry = CategoryRegistry()

        assert registry.is_valid_sub_category("photo", "portrait") is True
        assert registry.is_valid_sub_category("screenshot", "desktop") is True

    def test_is_valid_sub_category_false(self) -> None:
        """Should return False for invalid sub-category."""
        registry = CategoryRegistry()

        assert registry.is_valid_sub_category("photo", "desktop") is False
        assert registry.is_valid_sub_category("screenshot", "portrait") is False

    def test_is_valid_sub_category_nonexistent_category(self) -> None:
        """Should return False for nonexistent category."""
        registry = CategoryRegistry()

        assert registry.is_valid_sub_category("nonexistent", "any") is False

    def test_get_custom_categories_only(self) -> None:
        """Should return only custom categories."""
        registry = CategoryRegistry()

        registry.register_custom_category(
            id="custom1",
            name_ko="커스텀1",
            name_en="Custom1",
            sub_categories=[],
        )
        registry.register_custom_category(
            id="custom2",
            name_ko="커스텀2",
            name_en="Custom2",
            sub_categories=[],
        )

        custom_categories = registry.get_custom_categories()

        assert len(custom_categories) == 2
        assert all(c.is_custom for c in custom_categories)

    def test_get_default_categories_only(self) -> None:
        """Should return only default categories."""
        registry = CategoryRegistry()

        registry.register_custom_category(
            id="custom1",
            name_ko="커스텀1",
            name_en="Custom1",
            sub_categories=[],
        )

        default_categories = registry.get_default_categories()

        assert len(default_categories) == 8
        assert all(not c.is_custom for c in default_categories)
