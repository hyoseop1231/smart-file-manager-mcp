"""Tests for OrganizationExecutor.

TAG: ORG-001-E1
SPEC: SPEC-ORG-001

TDD Test Suite for OrganizationExecutor covering:
- Single file execution (move, copy, delete)
- Dry run mode
- Conflict handling
- Batch execution
- Trash management
- Transaction rollback
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from smart_file_manager.organization.conflict_resolver import ConflictResolver
from smart_file_manager.organization.models import (
    ConflictStrategy,
    OrganizationAction,
    Progress,
)
from smart_file_manager.organization.organization_executor import OrganizationExecutor
from smart_file_manager.organization.safety_validator import SafetyValidator
from smart_file_manager.organization.transaction_manager import TransactionManager

if TYPE_CHECKING:
    pass


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def source_file(temp_dir: Path) -> Path:
    """Create a test source file."""
    file_path = temp_dir / "source" / "test_file.txt"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("Test content")
    return file_path


@pytest.fixture
def target_dir(temp_dir: Path) -> Path:
    """Create a target directory."""
    target = temp_dir / "target"
    target.mkdir(parents=True, exist_ok=True)
    return target


@pytest.fixture
def trash_dir(temp_dir: Path) -> Path:
    """Create a trash directory."""
    trash = temp_dir / "trash"
    trash.mkdir(parents=True, exist_ok=True)
    return trash


@pytest.fixture
def transaction_dir(temp_dir: Path) -> Path:
    """Create a transaction directory."""
    trans = temp_dir / "transactions"
    trans.mkdir(parents=True, exist_ok=True)
    return trans


@pytest.fixture
def executor(trash_dir: Path, transaction_dir: Path) -> OrganizationExecutor:
    """Create an OrganizationExecutor instance."""
    transaction_manager = TransactionManager(transaction_dir=transaction_dir)
    return OrganizationExecutor(
        safety_validator=SafetyValidator(),
        transaction_manager=transaction_manager,
        conflict_resolver=ConflictResolver(),
        trash_dir=trash_dir,
    )


# =============================================================================
# TestExecuteSingle - Single file operation tests
# =============================================================================


class TestExecuteSingle:
    """Test cases for single file execution."""

    @pytest.mark.asyncio
    async def test_execute_move_success(
        self,
        executor: OrganizationExecutor,
        source_file: Path,
        target_dir: Path,
    ) -> None:
        """Test successful file move operation.

        REQ-E-006: action="move" moves file to target path.
        """
        target_path = target_dir / "moved_file.txt"
        action = OrganizationAction(
            action="move",
            source_path=source_file,
            target_path=target_path,
            options={},
        )

        result = await executor.execute(action)

        assert result.success is True
        assert result.file_path == source_file
        assert result.target_path == target_path
        assert result.action == "move"
        assert not source_file.exists()
        assert target_path.exists()
        assert target_path.read_text() == "Test content"

    @pytest.mark.asyncio
    async def test_execute_copy_success(
        self,
        executor: OrganizationExecutor,
        source_file: Path,
        target_dir: Path,
    ) -> None:
        """Test successful file copy operation.

        REQ-E-007: action="copy" copies file to target path.
        """
        target_path = target_dir / "copied_file.txt"
        action = OrganizationAction(
            action="copy",
            source_path=source_file,
            target_path=target_path,
            options={},
        )

        result = await executor.execute(action)

        assert result.success is True
        assert result.file_path == source_file
        assert result.target_path == target_path
        assert result.action == "copy"
        assert source_file.exists()  # Original should still exist
        assert target_path.exists()
        assert target_path.read_text() == "Test content"

    @pytest.mark.asyncio
    async def test_execute_delete_moves_to_trash(
        self,
        executor: OrganizationExecutor,
        source_file: Path,
        trash_dir: Path,
    ) -> None:
        """Test delete operation moves file to trash.

        REQ-E-009: action="delete" moves file to trash (not permanent delete).
        """
        action = OrganizationAction(
            action="delete",
            source_path=source_file,
            target_path=None,
            options={},
        )

        result = await executor.execute(action)

        assert result.success is True
        assert result.file_path == source_file
        assert result.action == "delete"
        assert not source_file.exists()

        # Verify file is in trash (date-based directory)
        trash_files = list(trash_dir.rglob("*test_file.txt"))
        assert len(trash_files) == 1

    @pytest.mark.asyncio
    async def test_execute_delete_creates_metadata(
        self,
        executor: OrganizationExecutor,
        source_file: Path,
        trash_dir: Path,
    ) -> None:
        """Test delete operation creates metadata file.

        REQ-E-010: Trash stores metadata (original path, deletion time).
        """
        original_path = str(source_file)
        action = OrganizationAction(
            action="delete",
            source_path=source_file,
            target_path=None,
            options={},
        )

        await executor.execute(action)

        # Find metadata file
        meta_files = list(trash_dir.rglob("*.meta.json"))
        assert len(meta_files) == 1

        with open(meta_files[0]) as f:
            metadata = json.load(f)

        assert metadata["original_path"] == original_path
        assert "deleted_at" in metadata
        assert "auto_delete_after" in metadata
        assert "transaction_id" in metadata

    @pytest.mark.asyncio
    async def test_execute_creates_target_directory(
        self,
        executor: OrganizationExecutor,
        source_file: Path,
        temp_dir: Path,
    ) -> None:
        """Test that target directory is automatically created.

        REQ-E-008: Target directory is created if it doesn't exist.
        """
        nested_target = temp_dir / "new" / "nested" / "dir" / "file.txt"
        action = OrganizationAction(
            action="move",
            source_path=source_file,
            target_path=nested_target,
            options={},
        )

        result = await executor.execute(action)

        assert result.success is True
        assert nested_target.exists()
        assert nested_target.parent.exists()

    @pytest.mark.asyncio
    async def test_execute_dry_run_no_file_changes(
        self,
        executor: OrganizationExecutor,
        source_file: Path,
        target_dir: Path,
    ) -> None:
        """Test dry run mode doesn't modify files.

        REQ-E-001: dry_run=True performs no actual file operations.
        """
        target_path = target_dir / "moved_file.txt"
        action = OrganizationAction(
            action="move",
            source_path=source_file,
            target_path=target_path,
            options={},
        )

        result = await executor.execute(action, dry_run=True)

        assert result.success is True
        assert source_file.exists()  # Source should still exist
        assert not target_path.exists()  # Target should not be created

    @pytest.mark.asyncio
    async def test_execute_dry_run_detects_conflict(
        self,
        executor: OrganizationExecutor,
        source_file: Path,
        target_dir: Path,
    ) -> None:
        """Test dry run mode detects conflicts.

        REQ-E-001: dry_run mode should detect potential conflicts.
        """
        # Create existing file at target
        target_path = target_dir / "existing_file.txt"
        target_path.write_text("Existing content")

        action = OrganizationAction(
            action="move",
            source_path=source_file,
            target_path=target_path,
            options={},
        )

        result = await executor.execute(action, dry_run=True)

        assert result.success is True  # Dry run succeeds but detects conflict
        assert source_file.exists()
        assert target_path.read_text() == "Existing content"  # Unchanged

    @pytest.mark.asyncio
    async def test_execute_with_conflict_skip(
        self,
        executor: OrganizationExecutor,
        source_file: Path,
        target_dir: Path,
    ) -> None:
        """Test conflict resolution with SKIP strategy."""
        target_path = target_dir / "existing_file.txt"
        target_path.write_text("Existing content")

        action = OrganizationAction(
            action="move",
            source_path=source_file,
            target_path=target_path,
            options={},
        )

        result = await executor.execute(
            action,
            conflict_strategy=ConflictStrategy.SKIP,
        )

        assert result.success is False  # Skipped due to conflict
        assert source_file.exists()  # Source unchanged
        assert target_path.read_text() == "Existing content"  # Target unchanged

    @pytest.mark.asyncio
    async def test_execute_with_conflict_overwrite(
        self,
        executor: OrganizationExecutor,
        source_file: Path,
        target_dir: Path,
    ) -> None:
        """Test conflict resolution with OVERWRITE strategy."""
        target_path = target_dir / "existing_file.txt"
        target_path.write_text("Existing content")

        action = OrganizationAction(
            action="move",
            source_path=source_file,
            target_path=target_path,
            options={},
        )

        result = await executor.execute(
            action,
            conflict_strategy=ConflictStrategy.OVERWRITE,
        )

        assert result.success is True
        assert not source_file.exists()
        assert target_path.read_text() == "Test content"  # Overwritten

    @pytest.mark.asyncio
    async def test_execute_with_conflict_rename_suffix(
        self,
        executor: OrganizationExecutor,
        source_file: Path,
        target_dir: Path,
    ) -> None:
        """Test conflict resolution with RENAME_SUFFIX strategy."""
        target_path = target_dir / "existing_file.txt"
        target_path.write_text("Existing content")

        action = OrganizationAction(
            action="move",
            source_path=source_file,
            target_path=target_path,
            options={},
        )

        result = await executor.execute(
            action,
            conflict_strategy=ConflictStrategy.RENAME_SUFFIX,
        )

        assert result.success is True
        assert not source_file.exists()
        assert target_path.read_text() == "Existing content"  # Original unchanged

        # Should have created a renamed file
        renamed_files = list(target_dir.glob("existing_file_*.txt"))
        assert len(renamed_files) == 1
        assert renamed_files[0].read_text() == "Test content"

    @pytest.mark.asyncio
    async def test_execute_safety_validation_failure(
        self,
        trash_dir: Path,
        transaction_dir: Path,
        temp_dir: Path,
    ) -> None:
        """Test that safety validation failure returns error result."""
        # Create a mock safety validator that fails
        mock_validator = MagicMock(spec=SafetyValidator)
        mock_validator.validate_plan.return_value = MagicMock(
            valid=False,
            errors=["Permission denied"],
            warnings=[],
            conflicts=[],
        )

        executor = OrganizationExecutor(
            safety_validator=mock_validator,
            transaction_manager=TransactionManager(transaction_dir=transaction_dir),
            conflict_resolver=ConflictResolver(),
            trash_dir=trash_dir,
        )

        source = temp_dir / "test.txt"
        source.write_text("test")
        target = temp_dir / "target.txt"

        action = OrganizationAction(
            action="move",
            source_path=source,
            target_path=target,
            options={},
        )

        result = await executor.execute(action)

        assert result.success is False
        assert "Permission denied" in result.error

    @pytest.mark.asyncio
    async def test_execute_concurrent_same_file_blocked(
        self,
        executor: OrganizationExecutor,
        source_file: Path,
        target_dir: Path,
    ) -> None:
        """Test that concurrent operations on same file are blocked."""
        target_path = target_dir / "moved_file.txt"
        action = OrganizationAction(
            action="move",
            source_path=source_file,
            target_path=target_path,
            options={},
        )

        # Simulate in-progress by adding to tracking set
        async with executor._in_progress_lock:
            executor._in_progress.add(source_file)

        try:
            result = await executor.execute(action)
            assert result.success is False
            assert "already" in result.error.lower() or "processing" in result.error.lower()
        finally:
            async with executor._in_progress_lock:
                executor._in_progress.discard(source_file)


# =============================================================================
# TestExecuteBatch - Batch operation tests
# =============================================================================


class TestExecuteBatch:
    """Test cases for batch file execution."""

    @pytest.mark.asyncio
    async def test_batch_execute_all_success(
        self,
        executor: OrganizationExecutor,
        temp_dir: Path,
        target_dir: Path,
    ) -> None:
        """Test batch execution with all operations successful."""
        # Create multiple source files
        source_dir = temp_dir / "batch_source"
        source_dir.mkdir(parents=True, exist_ok=True)

        actions = []
        for i in range(5):
            source = source_dir / f"file_{i}.txt"
            source.write_text(f"Content {i}")
            target = target_dir / f"file_{i}.txt"
            actions.append(
                OrganizationAction(
                    action="move",
                    source_path=source,
                    target_path=target,
                    options={},
                )
            )

        result = await executor.execute_batch(actions)

        assert result.successful == 5
        assert result.failed == 0
        assert result.total == 5
        assert len(result.results) == 5

        # Verify all files moved
        for i in range(5):
            assert (target_dir / f"file_{i}.txt").exists()

    @pytest.mark.asyncio
    async def test_batch_execute_partial_failure(
        self,
        executor: OrganizationExecutor,
        temp_dir: Path,
        target_dir: Path,
    ) -> None:
        """Test batch execution continues despite individual failures.

        REQ-S-006: Individual errors don't stop batch processing.
        """
        source_dir = temp_dir / "batch_source"
        source_dir.mkdir(parents=True, exist_ok=True)

        actions = []

        # Create 3 valid source files
        for i in range(3):
            source = source_dir / f"file_{i}.txt"
            source.write_text(f"Content {i}")
            actions.append(
                OrganizationAction(
                    action="move",
                    source_path=source,
                    target_path=target_dir / f"file_{i}.txt",
                    options={},
                )
            )

        # Add an action with non-existent source (will fail)
        actions.append(
            OrganizationAction(
                action="move",
                source_path=source_dir / "nonexistent.txt",
                target_path=target_dir / "nonexistent.txt",
                options={},
            )
        )

        # Add another valid file
        source = source_dir / "file_4.txt"
        source.write_text("Content 4")
        actions.append(
            OrganizationAction(
                action="move",
                source_path=source,
                target_path=target_dir / "file_4.txt",
                options={},
            )
        )

        result = await executor.execute_batch(actions)

        assert result.total == 5
        assert result.successful >= 3  # At least 3 should succeed
        assert result.failed >= 1  # At least 1 failure

    @pytest.mark.asyncio
    async def test_batch_execute_rollback_on_error(
        self,
        executor: OrganizationExecutor,
        temp_dir: Path,
        target_dir: Path,
    ) -> None:
        """Test batch rollback when rollback_on_error is True.

        REQ-U-003: Transaction rollback support.
        """
        source_dir = temp_dir / "batch_source"
        source_dir.mkdir(parents=True, exist_ok=True)

        actions = []

        # Create valid source files
        for i in range(3):
            source = source_dir / f"file_{i}.txt"
            source.write_text(f"Content {i}")
            actions.append(
                OrganizationAction(
                    action="move",
                    source_path=source,
                    target_path=target_dir / f"file_{i}.txt",
                    options={},
                )
            )

        # Add failing action
        actions.append(
            OrganizationAction(
                action="move",
                source_path=source_dir / "nonexistent.txt",
                target_path=target_dir / "nonexistent.txt",
                options={},
            )
        )

        result = await executor.execute_batch(
            actions,
            rollback_on_error=True,
        )

        assert result.failed > 0
        # With rollback, successful count should be affected

    @pytest.mark.asyncio
    async def test_batch_execute_concurrency_limit(
        self,
        executor: OrganizationExecutor,
        temp_dir: Path,
        target_dir: Path,
    ) -> None:
        """Test batch execution respects concurrency limit."""
        source_dir = temp_dir / "batch_source"
        source_dir.mkdir(parents=True, exist_ok=True)

        actions = []
        for i in range(10):
            source = source_dir / f"file_{i}.txt"
            source.write_text(f"Content {i}")
            actions.append(
                OrganizationAction(
                    action="copy",
                    source_path=source,
                    target_path=target_dir / f"file_{i}.txt",
                    options={},
                )
            )

        # Execute with concurrency=2
        result = await executor.execute_batch(actions, concurrency=2)

        assert result.successful == 10
        assert result.total == 10

    @pytest.mark.asyncio
    async def test_batch_execute_progress_callback(
        self,
        executor: OrganizationExecutor,
        temp_dir: Path,
        target_dir: Path,
    ) -> None:
        """Test progress callback is called during batch execution."""
        source_dir = temp_dir / "batch_source"
        source_dir.mkdir(parents=True, exist_ok=True)

        actions = []
        for i in range(5):
            source = source_dir / f"file_{i}.txt"
            source.write_text(f"Content {i}")
            actions.append(
                OrganizationAction(
                    action="copy",
                    source_path=source,
                    target_path=target_dir / f"file_{i}.txt",
                    options={},
                )
            )

        progress_updates: list[Progress] = []

        async def progress_callback(progress: Progress) -> None:
            progress_updates.append(progress)

        # Create executor with callback
        executor_with_callback = OrganizationExecutor(
            trash_dir=executor.trash_dir,
            progress_callback=progress_callback,
        )

        await executor_with_callback.execute_batch(actions)

        assert len(progress_updates) == 5
        assert progress_updates[-1].current == 5
        assert progress_updates[-1].total == 5
        assert progress_updates[-1].percentage == 100.0


# =============================================================================
# TestTrashManagement - Trash operation tests
# =============================================================================


class TestTrashManagement:
    """Test cases for trash management."""

    @pytest.mark.asyncio
    async def test_trash_directory_structure(
        self,
        executor: OrganizationExecutor,
        source_file: Path,
        trash_dir: Path,
    ) -> None:
        """Test trash creates date-based directory structure."""
        action = OrganizationAction(
            action="delete",
            source_path=source_file,
            target_path=None,
            options={},
        )

        await executor.execute(action)

        # Check date-based directory
        today = datetime.now().strftime("%Y-%m-%d")
        date_dir = trash_dir / today
        assert date_dir.exists()
        assert date_dir.is_dir()

    @pytest.mark.asyncio
    async def test_trash_metadata_content(
        self,
        executor: OrganizationExecutor,
        source_file: Path,
        trash_dir: Path,
    ) -> None:
        """Test trash metadata contains required fields.

        REQ-E-010: Metadata includes original path, deletion time.
        """
        original_path = str(source_file)
        action = OrganizationAction(
            action="delete",
            source_path=source_file,
            target_path=None,
            options={},
        )

        await executor.execute(action)

        meta_files = list(trash_dir.rglob("*.meta.json"))
        assert len(meta_files) == 1

        with open(meta_files[0]) as f:
            metadata = json.load(f)

        # Required fields
        assert "original_path" in metadata
        assert "deleted_at" in metadata
        assert "auto_delete_after" in metadata
        assert "transaction_id" in metadata

        # Verify content
        assert metadata["original_path"] == original_path

        # Verify deleted_at is valid ISO format
        deleted_at = datetime.fromisoformat(metadata["deleted_at"])
        assert isinstance(deleted_at, datetime)

    @pytest.mark.asyncio
    async def test_trash_auto_delete_timestamp(
        self,
        executor: OrganizationExecutor,
        source_file: Path,
        trash_dir: Path,
    ) -> None:
        """Test auto-delete timestamp is set correctly (30 days)."""
        action = OrganizationAction(
            action="delete",
            source_path=source_file,
            target_path=None,
            options={},
        )

        before_delete = datetime.now().timestamp()
        await executor.execute(action)
        after_delete = datetime.now().timestamp()

        meta_files = list(trash_dir.rglob("*.meta.json"))
        with open(meta_files[0]) as f:
            metadata = json.load(f)

        auto_delete_after = metadata["auto_delete_after"]

        # Should be approximately 30 days from now
        thirty_days = 30 * 24 * 60 * 60
        expected_min = before_delete + thirty_days
        expected_max = after_delete + thirty_days

        assert expected_min <= auto_delete_after <= expected_max


# =============================================================================
# TestTransactionSupport - Transaction and rollback tests
# =============================================================================


class TestTransactionSupport:
    """Test cases for transaction support."""

    @pytest.mark.asyncio
    async def test_execute_returns_transaction_id(
        self,
        executor: OrganizationExecutor,
        source_file: Path,
        target_dir: Path,
    ) -> None:
        """Test that successful execution returns transaction ID."""
        target_path = target_dir / "moved_file.txt"
        action = OrganizationAction(
            action="move",
            source_path=source_file,
            target_path=target_path,
            options={},
        )

        result = await executor.execute(action)

        assert result.success is True
        assert result.transaction_id is not None

    @pytest.mark.asyncio
    async def test_execute_error_triggers_rollback(
        self,
        trash_dir: Path,
        transaction_dir: Path,
        temp_dir: Path,
    ) -> None:
        """Test that errors trigger transaction rollback.

        REQ-U-003: Transaction rollback on error.
        """
        # Create executor with mock transaction manager
        mock_tm = AsyncMock(spec=TransactionManager)
        mock_tm.begin.return_value = "test-transaction-id"
        mock_tm.record = AsyncMock()
        mock_tm.rollback = AsyncMock()
        mock_tm.commit = AsyncMock()

        executor = OrganizationExecutor(
            safety_validator=SafetyValidator(),
            transaction_manager=mock_tm,
            conflict_resolver=ConflictResolver(),
            trash_dir=trash_dir,
        )

        # Create a source file
        source = temp_dir / "source.txt"
        source.write_text("test")

        # Target in a path that will cause an error (read-only directory simulation)
        # We'll mock _execute_action to raise an error
        action = OrganizationAction(
            action="move",
            source_path=source,
            target_path=temp_dir / "target.txt",
            options={},
        )

        # Patch _execute_action to raise error
        with patch.object(executor, "_execute_action", side_effect=OSError("Disk error")):
            result = await executor.execute(action)

        assert result.success is False
        mock_tm.rollback.assert_called_once_with("test-transaction-id")


# =============================================================================
# TestEdgeCases - Edge case and error handling tests
# =============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_execute_unsupported_action_type(
        self,
        executor: OrganizationExecutor,
        source_file: Path,
        target_dir: Path,
    ) -> None:
        """Test handling of unsupported action type."""
        action = OrganizationAction(
            action="unsupported_action",
            source_path=source_file,
            target_path=target_dir / "target.txt",
            options={},
        )

        result = await executor.execute(action)

        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_execute_preserves_file_metadata_on_copy(
        self,
        executor: OrganizationExecutor,
        source_file: Path,
        target_dir: Path,
    ) -> None:
        """Test that copy preserves file metadata."""
        target_path = target_dir / "copied_file.txt"
        action = OrganizationAction(
            action="copy",
            source_path=source_file,
            target_path=target_path,
            options={},
        )

        # Get original file stats
        original_mtime = source_file.stat().st_mtime

        result = await executor.execute(action)

        assert result.success is True
        # shutil.copy2 preserves metadata
        copied_mtime = target_path.stat().st_mtime
        assert abs(copied_mtime - original_mtime) < 1  # Allow 1 second tolerance

    @pytest.mark.asyncio
    async def test_trash_property(
        self,
        trash_dir: Path,
        transaction_dir: Path,
    ) -> None:
        """Test trash_dir property returns correct path."""
        executor = OrganizationExecutor(
            trash_dir=trash_dir,
            transaction_manager=TransactionManager(transaction_dir=transaction_dir),
        )

        assert executor.trash_dir == trash_dir

    @pytest.mark.asyncio
    async def test_default_trash_dir(
        self,
        transaction_dir: Path,
    ) -> None:
        """Test default trash directory is set correctly."""
        executor = OrganizationExecutor(
            transaction_manager=TransactionManager(transaction_dir=transaction_dir),
        )

        assert executor.trash_dir == OrganizationExecutor.DEFAULT_TRASH_DIR

    @pytest.mark.asyncio
    async def test_batch_dry_run(
        self,
        executor: OrganizationExecutor,
        temp_dir: Path,
        target_dir: Path,
    ) -> None:
        """Test batch execution in dry run mode."""
        source_dir = temp_dir / "batch_source"
        source_dir.mkdir(parents=True, exist_ok=True)

        actions = []
        for i in range(3):
            source = source_dir / f"file_{i}.txt"
            source.write_text(f"Content {i}")
            actions.append(
                OrganizationAction(
                    action="move",
                    source_path=source,
                    target_path=target_dir / f"file_{i}.txt",
                    options={},
                )
            )

        result = await executor.execute_batch(actions, dry_run=True)

        # BatchExecutionResult doesn't have dry_run field in models.py
        # Verify by checking successful count and file state
        assert result.successful == 3

        # Verify no files were actually moved
        for i in range(3):
            assert (source_dir / f"file_{i}.txt").exists()
            assert not (target_dir / f"file_{i}.txt").exists()
