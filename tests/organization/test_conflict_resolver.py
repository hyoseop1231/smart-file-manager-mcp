"""Tests for ConflictResolver class.

TAG: ORG-001-T4
SPEC: SPEC-ORG-001

This module contains TDD test cases for the ConflictResolver class
that handles file conflict detection and resolution with various strategies.

REQ-E-002: Target path conflict detection
REQ-S-003: Strategy-based conflict resolution
"""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from smart_file_manager.core.exceptions import ConflictError
from smart_file_manager.organization.conflict_resolver import ConflictResolver
from smart_file_manager.organization.models import (
    Conflict,
    ConflictStrategy,
    OrganizationAction,
)


class TestDetectConflict:
    """Test cases for conflict detection."""

    @pytest.mark.asyncio
    async def test_detect_no_conflict(self, tmp_path: Path) -> None:
        """Test no conflict when target path does not exist."""
        resolver = ConflictResolver()
        target_path = tmp_path / "nonexistent.txt"

        conflict = await resolver.detect_conflict(target_path)

        assert conflict is None

    @pytest.mark.asyncio
    async def test_detect_conflict_file_exists(self, tmp_path: Path) -> None:
        """Test conflict detection when file exists at target path."""
        resolver = ConflictResolver()
        target_path = tmp_path / "existing_file.txt"
        target_path.write_text("existing content")

        conflict = await resolver.detect_conflict(target_path)

        assert conflict is not None
        assert conflict.target_path == target_path
        assert conflict.reason == "File already exists"

    @pytest.mark.asyncio
    async def test_detect_conflict_for_action(self, tmp_path: Path) -> None:
        """Test conflict detection for OrganizationAction."""
        resolver = ConflictResolver()
        source_path = tmp_path / "source.txt"
        target_path = tmp_path / "target.txt"
        source_path.write_text("source content")
        target_path.write_text("target content")

        action = OrganizationAction(
            action="move",
            source_path=source_path,
            target_path=target_path,
            options={},
        )

        conflict = await resolver.detect_conflicts_for_action(action)

        assert conflict is not None
        assert conflict.source_path == source_path
        assert conflict.target_path == target_path


class TestResolveStrategies:
    """Test cases for conflict resolution strategies."""

    @pytest.mark.asyncio
    async def test_resolve_skip_strategy(self, tmp_path: Path) -> None:
        """Test skip strategy returns False for proceed."""
        resolver = ConflictResolver(default_strategy=ConflictStrategy.SKIP)
        target_path = tmp_path / "existing.txt"
        target_path.write_text("content")

        conflict = Conflict(
            source_path=Path("/source/file.txt"),
            target_path=target_path,
            reason="File already exists",
            suggestions=["Skip", "Overwrite"],
        )

        result_path, should_proceed = await resolver.resolve(conflict)

        assert result_path == target_path
        assert should_proceed is False

    @pytest.mark.asyncio
    async def test_resolve_overwrite_strategy(self, tmp_path: Path) -> None:
        """Test overwrite strategy returns True for proceed."""
        resolver = ConflictResolver(default_strategy=ConflictStrategy.OVERWRITE)
        target_path = tmp_path / "existing.txt"
        target_path.write_text("content")

        conflict = Conflict(
            source_path=Path("/source/file.txt"),
            target_path=target_path,
            reason="File already exists",
            suggestions=["Skip", "Overwrite"],
        )

        result_path, should_proceed = await resolver.resolve(conflict)

        assert result_path == target_path
        assert should_proceed is True

    @pytest.mark.asyncio
    async def test_resolve_rename_suffix_strategy(self, tmp_path: Path) -> None:
        """Test rename_suffix strategy returns new path with suffix."""
        resolver = ConflictResolver(default_strategy=ConflictStrategy.RENAME_SUFFIX)
        target_path = tmp_path / "file.txt"
        target_path.write_text("content")

        conflict = Conflict(
            source_path=Path("/source/file.txt"),
            target_path=target_path,
            reason="File already exists",
            suggestions=[],
        )

        result_path, should_proceed = await resolver.resolve(conflict)

        assert result_path != target_path
        assert result_path.parent == target_path.parent
        assert "_1" in result_path.name or "_2" in result_path.name
        assert result_path.suffix == target_path.suffix
        assert should_proceed is True

    @pytest.mark.asyncio
    async def test_resolve_rename_suffix_increments(self, tmp_path: Path) -> None:
        """Test rename_suffix increments counter when multiple files exist."""
        resolver = ConflictResolver(default_strategy=ConflictStrategy.RENAME_SUFFIX)
        target_path = tmp_path / "file.txt"
        target_path.write_text("content")
        (tmp_path / "file_1.txt").write_text("content 1")
        (tmp_path / "file_2.txt").write_text("content 2")

        conflict = Conflict(
            source_path=Path("/source/file.txt"),
            target_path=target_path,
            reason="File already exists",
            suggestions=[],
        )

        result_path, should_proceed = await resolver.resolve(conflict)

        assert result_path == tmp_path / "file_3.txt"
        assert should_proceed is True

    @pytest.mark.asyncio
    async def test_resolve_rename_timestamp_strategy(self, tmp_path: Path) -> None:
        """Test rename_timestamp strategy returns path with timestamp."""
        resolver = ConflictResolver(default_strategy=ConflictStrategy.RENAME_TIMESTAMP)
        target_path = tmp_path / "file.txt"
        target_path.write_text("content")

        conflict = Conflict(
            source_path=Path("/source/file.txt"),
            target_path=target_path,
            reason="File already exists",
            suggestions=[],
        )

        result_path, should_proceed = await resolver.resolve(conflict)

        assert result_path != target_path
        assert result_path.parent == target_path.parent
        # Check timestamp pattern (YYYYMMDD_HHMMSS)
        name_without_ext = result_path.stem
        assert "file_" in name_without_ext
        assert len(name_without_ext) > len("file_")
        assert result_path.suffix == target_path.suffix
        assert should_proceed is True

    @pytest.mark.asyncio
    async def test_resolve_ask_user_with_callback(self, tmp_path: Path) -> None:
        """Test ask_user strategy with callback returns selected strategy result."""
        callback = AsyncMock(return_value=ConflictStrategy.SKIP)
        resolver = ConflictResolver(
            default_strategy=ConflictStrategy.ASK_USER,
            user_prompt_callback=callback,
        )
        target_path = tmp_path / "file.txt"
        target_path.write_text("content")

        conflict = Conflict(
            source_path=Path("/source/file.txt"),
            target_path=target_path,
            reason="File already exists",
            suggestions=[],
        )

        result_path, should_proceed = await resolver.resolve(conflict)

        callback.assert_called_once_with(conflict)
        assert should_proceed is False  # Because callback returned SKIP

    @pytest.mark.asyncio
    async def test_resolve_ask_user_without_callback_raises(self, tmp_path: Path) -> None:
        """Test ask_user strategy without callback raises ConflictError."""
        resolver = ConflictResolver(default_strategy=ConflictStrategy.ASK_USER)
        target_path = tmp_path / "file.txt"
        target_path.write_text("content")

        conflict = Conflict(
            source_path=Path("/source/file.txt"),
            target_path=target_path,
            reason="File already exists",
            suggestions=[],
        )

        with pytest.raises(ConflictError) as exc_info:
            await resolver.resolve(conflict)

        assert "user_prompt_callback" in str(exc_info.value)


class TestGenerateUniqueName:
    """Test cases for unique name generation."""

    def test_generate_unique_name_suffix(self, tmp_path: Path) -> None:
        """Test generating unique name with numeric suffix."""
        resolver = ConflictResolver()
        target_path = tmp_path / "file.txt"
        target_path.write_text("content")

        unique_path = resolver.generate_unique_name(target_path, use_timestamp=False)

        assert unique_path == tmp_path / "file_1.txt"
        assert not unique_path.exists()

    def test_generate_unique_name_timestamp(self, tmp_path: Path) -> None:
        """Test generating unique name with timestamp."""
        resolver = ConflictResolver()
        target_path = tmp_path / "file.txt"
        target_path.write_text("content")

        unique_path = resolver.generate_unique_name(target_path, use_timestamp=True)

        assert unique_path.parent == target_path.parent
        assert unique_path.suffix == target_path.suffix
        # Timestamp format check: file_YYYYMMDD_HHMMSS.txt
        assert unique_path.stem.startswith("file_")
        assert len(unique_path.stem) > len("file_")
        assert not unique_path.exists()

    def test_generate_unique_name_long_filename(self, tmp_path: Path) -> None:
        """Test generating unique name with very long filename."""
        resolver = ConflictResolver()
        # Create a very long filename (close to 255 char limit)
        long_name = "a" * 240 + ".txt"
        target_path = tmp_path / long_name
        target_path.write_text("content")

        unique_path = resolver.generate_unique_name(target_path, use_timestamp=False)

        # Ensure the resulting filename doesn't exceed 255 characters
        assert len(unique_path.name) <= 255
        assert not unique_path.exists()


class TestExtractBaseStem:
    """Test cases for base stem extraction."""

    def test_extract_base_stem_with_suffix(self) -> None:
        """Test extracting base stem removes existing numeric suffix."""
        resolver = ConflictResolver()

        assert resolver._extract_base_stem("file_1") == "file"
        assert resolver._extract_base_stem("document_23") == "document"
        assert resolver._extract_base_stem("report_100") == "report"

    def test_extract_base_stem_without_suffix(self) -> None:
        """Test extracting base stem keeps name without numeric suffix."""
        resolver = ConflictResolver()

        assert resolver._extract_base_stem("file") == "file"
        assert resolver._extract_base_stem("my_document") == "my_document"
        assert resolver._extract_base_stem("report_final") == "report_final"


class TestDefaultStrategyProperty:
    """Test cases for default_strategy property."""

    def test_default_strategy_getter(self) -> None:
        """Test getting default strategy."""
        resolver = ConflictResolver(default_strategy=ConflictStrategy.OVERWRITE)

        assert resolver.default_strategy == ConflictStrategy.OVERWRITE

    def test_default_strategy_setter(self) -> None:
        """Test setting default strategy."""
        resolver = ConflictResolver()

        resolver.default_strategy = ConflictStrategy.RENAME_SUFFIX

        assert resolver.default_strategy == ConflictStrategy.RENAME_SUFFIX

    def test_default_strategy_initial_value(self) -> None:
        """Test initial default strategy is SKIP."""
        resolver = ConflictResolver()

        assert resolver.default_strategy == ConflictStrategy.SKIP


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_resolve_with_explicit_strategy(self, tmp_path: Path) -> None:
        """Test resolving with explicit strategy overrides default."""
        resolver = ConflictResolver(default_strategy=ConflictStrategy.SKIP)
        target_path = tmp_path / "file.txt"
        target_path.write_text("content")

        conflict = Conflict(
            source_path=Path("/source/file.txt"),
            target_path=target_path,
            reason="File already exists",
            suggestions=[],
        )

        result_path, should_proceed = await resolver.resolve(
            conflict, strategy=ConflictStrategy.OVERWRITE
        )

        assert should_proceed is True  # Explicit OVERWRITE overrides default SKIP

    @pytest.mark.asyncio
    async def test_detect_conflict_directory_exists(self, tmp_path: Path) -> None:
        """Test conflict detection when directory exists at target path."""
        resolver = ConflictResolver()
        target_path = tmp_path / "existing_dir"
        target_path.mkdir()

        conflict = await resolver.detect_conflict(target_path)

        assert conflict is not None
        assert conflict.target_path == target_path

    @pytest.mark.asyncio
    async def test_ask_user_returns_ask_user_raises(self, tmp_path: Path) -> None:
        """Test that ask_user returning ASK_USER raises error."""
        callback = AsyncMock(return_value=ConflictStrategy.ASK_USER)
        resolver = ConflictResolver(
            default_strategy=ConflictStrategy.ASK_USER,
            user_prompt_callback=callback,
        )
        target_path = tmp_path / "file.txt"
        target_path.write_text("content")

        conflict = Conflict(
            source_path=Path("/source/file.txt"),
            target_path=target_path,
            reason="File already exists",
            suggestions=[],
        )

        with pytest.raises(ConflictError) as exc_info:
            await resolver.resolve(conflict)

        assert "valid strategy" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_detect_conflicts_for_action_no_target(self, tmp_path: Path) -> None:
        """Test detect_conflicts_for_action returns None when target_path is None."""
        resolver = ConflictResolver()
        source_path = tmp_path / "source.txt"
        source_path.write_text("content")

        action = OrganizationAction(
            action="delete",
            source_path=source_path,
            target_path=None,
            options={},
        )

        conflict = await resolver.detect_conflicts_for_action(action)

        assert conflict is None

    @pytest.mark.asyncio
    async def test_detect_conflicts_for_action_no_conflict(self, tmp_path: Path) -> None:
        """Test detect_conflicts_for_action returns None when no conflict exists."""
        resolver = ConflictResolver()
        source_path = tmp_path / "source.txt"
        target_path = tmp_path / "nonexistent_target.txt"
        source_path.write_text("content")

        action = OrganizationAction(
            action="move",
            source_path=source_path,
            target_path=target_path,
            options={},
        )

        conflict = await resolver.detect_conflicts_for_action(action)

        assert conflict is None

    def test_truncate_stem_when_too_long(self) -> None:
        """Test _truncate_stem correctly truncates long stems."""
        resolver = ConflictResolver()
        long_stem = "a" * 300  # Longer than MAX_FILENAME_LENGTH
        reserved = 10

        truncated = resolver._truncate_stem(long_stem, reserved)

        assert len(truncated) == ConflictResolver.MAX_FILENAME_LENGTH - reserved
        assert truncated == "a" * (255 - 10)
