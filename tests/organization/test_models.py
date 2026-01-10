"""Tests for organization models.

TAG: ORG-001-T1
SPEC: SPEC-ORG-001

This module contains test cases for all organization dataclasses
including ConflictStrategy, ExecutionResult, BatchExecutionResult,
ValidationResult, TransactionEntry, Progress, RollbackResult,
Conflict, and OrganizationAction.
"""

from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest


class TestConflictStrategy:
    """Test cases for ConflictStrategy enum."""

    def test_conflict_strategy_values(self) -> None:
        """Test all 5 conflict strategy values exist."""
        from smart_file_manager.organization.models import ConflictStrategy

        assert hasattr(ConflictStrategy, "SKIP")
        assert hasattr(ConflictStrategy, "OVERWRITE")
        assert hasattr(ConflictStrategy, "RENAME_SUFFIX")
        assert hasattr(ConflictStrategy, "RENAME_TIMESTAMP")
        assert hasattr(ConflictStrategy, "ASK_USER")
        # Verify we have exactly 5 strategies
        assert len(ConflictStrategy) == 5

    def test_conflict_strategy_default(self) -> None:
        """Test default strategy is skip."""
        from smart_file_manager.organization.models import ConflictStrategy

        # SKIP should be the first (default) option
        assert ConflictStrategy.SKIP.value == "skip"

    def test_conflict_strategy_string_values(self) -> None:
        """Test each strategy has correct string value."""
        from smart_file_manager.organization.models import ConflictStrategy

        assert ConflictStrategy.SKIP.value == "skip"
        assert ConflictStrategy.OVERWRITE.value == "overwrite"
        assert ConflictStrategy.RENAME_SUFFIX.value == "rename_suffix"
        assert ConflictStrategy.RENAME_TIMESTAMP.value == "rename_timestamp"
        assert ConflictStrategy.ASK_USER.value == "ask_user"


class TestExecutionResult:
    """Test cases for ExecutionResult dataclass."""

    def test_execution_result_success(self) -> None:
        """Test successful execution result creation."""
        from smart_file_manager.organization.models import ExecutionResult

        transaction_id = uuid4()
        result = ExecutionResult(
            success=True,
            file_path=Path("/source/file.txt"),
            target_path=Path("/target/file.txt"),
            action="move",
            processing_time_ms=150.5,
            error=None,
            transaction_id=transaction_id,
        )

        assert result.success is True
        assert result.file_path == Path("/source/file.txt")
        assert result.target_path == Path("/target/file.txt")
        assert result.action == "move"
        assert result.processing_time_ms == 150.5
        assert result.error is None
        assert result.transaction_id == transaction_id

    def test_execution_result_failure(self) -> None:
        """Test failed execution result with error."""
        from smart_file_manager.organization.models import ExecutionResult

        transaction_id = uuid4()
        result = ExecutionResult(
            success=False,
            file_path=Path("/source/file.txt"),
            target_path=Path("/target/file.txt"),
            action="move",
            processing_time_ms=50.0,
            error="Permission denied",
            transaction_id=transaction_id,
        )

        assert result.success is False
        assert result.error == "Permission denied"

    def test_execution_result_has_processing_time(self) -> None:
        """Test processing time is included."""
        from smart_file_manager.organization.models import ExecutionResult

        result = ExecutionResult(
            success=True,
            file_path=Path("/source/file.txt"),
            target_path=Path("/target/file.txt"),
            action="copy",
            processing_time_ms=250.75,
            error=None,
            transaction_id=uuid4(),
        )

        assert isinstance(result.processing_time_ms, float)
        assert result.processing_time_ms > 0

    def test_execution_result_has_transaction_id(self) -> None:
        """Test transaction ID is valid UUID."""
        from smart_file_manager.organization.models import ExecutionResult

        transaction_id = uuid4()
        result = ExecutionResult(
            success=True,
            file_path=Path("/source/file.txt"),
            target_path=Path("/target/file.txt"),
            action="move",
            processing_time_ms=100.0,
            error=None,
            transaction_id=transaction_id,
        )

        assert isinstance(result.transaction_id, UUID)

    def test_execution_result_immutable(self) -> None:
        """Test ExecutionResult is immutable (frozen dataclass)."""
        from smart_file_manager.organization.models import ExecutionResult

        result = ExecutionResult(
            success=True,
            file_path=Path("/source/file.txt"),
            target_path=Path("/target/file.txt"),
            action="move",
            processing_time_ms=100.0,
            error=None,
            transaction_id=uuid4(),
        )

        with pytest.raises(AttributeError):
            result.success = False  # type: ignore[misc]


class TestBatchExecutionResult:
    """Test cases for BatchExecutionResult dataclass."""

    def test_batch_result_counts(self) -> None:
        """Test successful/failed counts."""
        from smart_file_manager.organization.models import (
            BatchExecutionResult,
            ExecutionResult,
        )

        transaction_id = uuid4()
        results = [
            ExecutionResult(
                success=True,
                file_path=Path("/source/file1.txt"),
                target_path=Path("/target/file1.txt"),
                action="move",
                processing_time_ms=100.0,
                error=None,
                transaction_id=transaction_id,
            ),
            ExecutionResult(
                success=False,
                file_path=Path("/source/file2.txt"),
                target_path=Path("/target/file2.txt"),
                action="move",
                processing_time_ms=50.0,
                error="Failed",
                transaction_id=transaction_id,
            ),
        ]

        batch = BatchExecutionResult(
            successful=1,
            failed=1,
            total=2,
            results=results,
            transaction_id=transaction_id,
        )

        assert batch.successful == 1
        assert batch.failed == 1
        assert batch.total == 2

    def test_batch_result_total_matches_sum(self) -> None:
        """Test total equals successful + failed."""
        from smart_file_manager.organization.models import BatchExecutionResult

        transaction_id = uuid4()
        batch = BatchExecutionResult(
            successful=5,
            failed=3,
            total=8,
            results=[],
            transaction_id=transaction_id,
        )

        assert batch.total == batch.successful + batch.failed

    def test_batch_result_has_transaction_id(self) -> None:
        """Test batch result has valid transaction ID."""
        from smart_file_manager.organization.models import BatchExecutionResult

        transaction_id = uuid4()
        batch = BatchExecutionResult(
            successful=1,
            failed=0,
            total=1,
            results=[],
            transaction_id=transaction_id,
        )

        assert isinstance(batch.transaction_id, UUID)


class TestValidationResult:
    """Test cases for ValidationResult dataclass."""

    def test_validation_result_valid(self) -> None:
        """Test valid result has no errors."""
        from smart_file_manager.organization.models import ValidationResult

        result = ValidationResult(
            valid=True,
            conflicts=[],
            errors=[],
            warnings=[],
        )

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validation_result_invalid(self) -> None:
        """Test invalid result has errors."""
        from smart_file_manager.organization.models import ValidationResult

        result = ValidationResult(
            valid=False,
            conflicts=[],
            errors=["Target path already exists", "Permission denied"],
            warnings=["File is large"],
        )

        assert result.valid is False
        assert len(result.errors) == 2
        assert "Target path already exists" in result.errors

    def test_validation_result_with_conflicts(self) -> None:
        """Test validation result with conflicts."""
        from smart_file_manager.organization.models import Conflict, ValidationResult

        conflict = Conflict(
            source_path=Path("/source/file.txt"),
            target_path=Path("/target/file.txt"),
            reason="File already exists",
            suggestions=["Rename file", "Overwrite"],
        )

        result = ValidationResult(
            valid=False,
            conflicts=[conflict],
            errors=[],
            warnings=[],
        )

        assert len(result.conflicts) == 1
        assert result.conflicts[0].reason == "File already exists"


class TestTransactionEntry:
    """Test cases for TransactionEntry dataclass."""

    def test_transaction_entry_creation(self) -> None:
        """Test transaction entry creation with all fields."""
        from smart_file_manager.organization.models import TransactionEntry

        entry_id = str(uuid4())
        timestamp = datetime.now()

        entry = TransactionEntry(
            id=entry_id,
            action="move",
            source_path=Path("/source/file.txt"),
            target_path=Path("/target/file.txt"),
            backup_path=Path("/backup/file.txt.bak"),
            timestamp=timestamp,
            status="completed",
            metadata={"original_size": 1024},
        )

        assert entry.id == entry_id
        assert entry.action == "move"
        assert entry.source_path == Path("/source/file.txt")
        assert entry.target_path == Path("/target/file.txt")
        assert entry.backup_path == Path("/backup/file.txt.bak")
        assert entry.timestamp == timestamp
        assert entry.status == "completed"
        assert entry.metadata == {"original_size": 1024}

    def test_transaction_entry_pending_status(self) -> None:
        """Test transaction entry with pending status."""
        from smart_file_manager.organization.models import TransactionEntry

        entry = TransactionEntry(
            id=str(uuid4()),
            action="copy",
            source_path=Path("/source/file.txt"),
            target_path=Path("/target/file.txt"),
            backup_path=None,
            timestamp=datetime.now(),
            status="pending",
            metadata={},
        )

        assert entry.status == "pending"

    def test_transaction_entry_failed_status(self) -> None:
        """Test transaction entry with failed status."""
        from smart_file_manager.organization.models import TransactionEntry

        entry = TransactionEntry(
            id=str(uuid4()),
            action="delete",
            source_path=Path("/source/file.txt"),
            target_path=None,
            backup_path=Path("/backup/file.txt.bak"),
            timestamp=datetime.now(),
            status="failed",
            metadata={},
        )

        assert entry.status == "failed"


class TestProgress:
    """Test cases for Progress dataclass."""

    def test_progress_creation(self) -> None:
        """Test progress creation with all fields."""
        from smart_file_manager.organization.models import Progress

        progress = Progress(
            current=50,
            total=100,
            percentage=50.0,
            current_file="/processing/file.txt",
            eta_seconds=120.5,
            elapsed_seconds=60.0,
        )

        assert progress.current == 50
        assert progress.total == 100
        assert progress.percentage == 50.0
        assert progress.current_file == "/processing/file.txt"
        assert progress.eta_seconds == 120.5
        assert progress.elapsed_seconds == 60.0

    def test_progress_initial_state(self) -> None:
        """Test progress at initial state."""
        from smart_file_manager.organization.models import Progress

        progress = Progress(
            current=0,
            total=100,
            percentage=0.0,
            current_file="",
            eta_seconds=None,
            elapsed_seconds=0.0,
        )

        assert progress.current == 0
        assert progress.percentage == 0.0
        assert progress.current_file == ""
        assert progress.elapsed_seconds == 0.0

    def test_progress_completed_state(self) -> None:
        """Test progress at completed state."""
        from smart_file_manager.organization.models import Progress

        progress = Progress(
            current=100,
            total=100,
            percentage=100.0,
            current_file="",
            eta_seconds=0.0,
            elapsed_seconds=120.0,
        )

        assert progress.current == progress.total
        assert progress.percentage == 100.0
        assert progress.elapsed_seconds == 120.0


class TestRollbackResult:
    """Test cases for RollbackResult dataclass."""

    def test_rollback_result_success(self) -> None:
        """Test successful rollback result."""
        from smart_file_manager.organization.models import RollbackResult

        transaction_id = str(uuid4())
        result = RollbackResult(
            success=True,
            restored_files=2,
            failed_restorations=[],
            transaction_id=transaction_id,
        )

        assert result.success is True
        assert result.restored_files == 2
        assert len(result.failed_restorations) == 0

    def test_rollback_result_partial_failure(self) -> None:
        """Test partial rollback failure."""
        from smart_file_manager.organization.models import RollbackResult

        transaction_id = str(uuid4())
        result = RollbackResult(
            success=False,
            restored_files=1,
            failed_restorations=[
                {
                    "entry_id": "entry-1",
                    "source_path": "/file2.txt",
                    "error": "File not found",
                }
            ],
            transaction_id=transaction_id,
        )

        assert result.success is False
        assert result.restored_files == 1
        assert len(result.failed_restorations) == 1

    def test_rollback_result_has_transaction_id(self) -> None:
        """Test rollback result has transaction ID."""
        from smart_file_manager.organization.models import RollbackResult

        transaction_id = str(uuid4())
        result = RollbackResult(
            success=True,
            restored_files=0,
            failed_restorations=[],
            transaction_id=transaction_id,
        )

        assert isinstance(result.transaction_id, str)


class TestConflict:
    """Test cases for Conflict dataclass."""

    def test_conflict_creation(self) -> None:
        """Test conflict creation with all fields."""
        from smart_file_manager.organization.models import Conflict

        conflict = Conflict(
            source_path=Path("/source/file.txt"),
            target_path=Path("/target/file.txt"),
            reason="File already exists at target location",
            suggestions=["Rename", "Overwrite", "Skip"],
        )

        assert conflict.source_path == Path("/source/file.txt")
        assert conflict.target_path == Path("/target/file.txt")
        assert conflict.reason == "File already exists at target location"
        assert len(conflict.suggestions) == 3

    def test_conflict_without_suggestions(self) -> None:
        """Test conflict can be created with empty suggestions."""
        from smart_file_manager.organization.models import Conflict

        conflict = Conflict(
            source_path=Path("/source/file.txt"),
            target_path=Path("/target/file.txt"),
            reason="Permission denied",
            suggestions=[],
        )

        assert len(conflict.suggestions) == 0


class TestOrganizationAction:
    """Test cases for OrganizationAction dataclass."""

    def test_organization_action_move(self) -> None:
        """Test move action creation."""
        from smart_file_manager.organization.models import OrganizationAction

        action = OrganizationAction(
            action="move",
            source_path=Path("/source/file.txt"),
            target_path=Path("/target/file.txt"),
            options={"conflict_strategy": "skip"},
        )

        assert action.action == "move"
        assert action.source_path == Path("/source/file.txt")
        assert action.target_path == Path("/target/file.txt")
        assert action.options["conflict_strategy"] == "skip"

    def test_organization_action_copy(self) -> None:
        """Test copy action creation."""
        from smart_file_manager.organization.models import OrganizationAction

        action = OrganizationAction(
            action="copy",
            source_path=Path("/source/file.txt"),
            target_path=Path("/backup/file.txt"),
            options={},
        )

        assert action.action == "copy"

    def test_organization_action_delete(self) -> None:
        """Test delete action creation."""
        from smart_file_manager.organization.models import OrganizationAction

        action = OrganizationAction(
            action="delete",
            source_path=Path("/source/file.txt"),
            target_path=None,
            options={"confirm": True},
        )

        assert action.action == "delete"
        assert action.target_path is None
        assert action.options["confirm"] is True

    def test_organization_action_immutable(self) -> None:
        """Test OrganizationAction is immutable (frozen dataclass)."""
        from smart_file_manager.organization.models import OrganizationAction

        action = OrganizationAction(
            action="move",
            source_path=Path("/source/file.txt"),
            target_path=Path("/target/file.txt"),
            options={},
        )

        with pytest.raises(AttributeError):
            action.action = "copy"  # type: ignore[misc]
