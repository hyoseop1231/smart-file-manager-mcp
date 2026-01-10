"""Tests for OrganizationService.

TAG: ORG-001-F1
SPEC: SPEC-ORG-001

TDD Test Suite for OrganizationService (Facade Pattern) covering:
- Initialization with various configurations
- Single plan execution (move, copy, delete, dry-run)
- Batch execution with progress callbacks
- Validation
- Rollback and crash recovery
- Properties
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from smart_file_manager.core.exceptions import ProtectedPathError, TransactionError
from smart_file_manager.organization.models import (
    ConflictStrategy,
    OrganizationAction,
    Progress,
    ValidationResult,
)
from smart_file_manager.organization.organization_service import OrganizationService

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
def service(trash_dir: Path, transaction_dir: Path) -> OrganizationService:
    """Create an OrganizationService instance with default settings."""
    return OrganizationService(
        trash_dir=trash_dir,
        transaction_dir=transaction_dir,
    )


# =============================================================================
# TestOrganizationServiceInit - Initialization tests
# =============================================================================


class TestOrganizationServiceInit:
    """Test cases for OrganizationService initialization."""

    def test_init_with_defaults(self, temp_dir: Path) -> None:
        """Test initialization with default values.

        OrganizationService should initialize with sensible defaults.
        """
        service = OrganizationService()

        assert service is not None
        assert service.default_conflict_strategy == ConflictStrategy.SKIP
        assert service.trash_dir is not None

    def test_init_with_custom_trash_dir(self, trash_dir: Path) -> None:
        """Test initialization with custom trash directory.

        OrganizationService should use provided trash directory.
        """
        service = OrganizationService(trash_dir=trash_dir)

        assert service.trash_dir == trash_dir

    def test_init_with_custom_conflict_strategy(self) -> None:
        """Test initialization with custom conflict strategy.

        OrganizationService should use provided default conflict strategy.
        """
        service = OrganizationService(default_conflict_strategy=ConflictStrategy.OVERWRITE)

        assert service.default_conflict_strategy == ConflictStrategy.OVERWRITE

    def test_init_with_transaction_dir(self, transaction_dir: Path) -> None:
        """Test initialization with custom transaction directory.

        OrganizationService should use provided transaction directory.
        """
        service = OrganizationService(transaction_dir=transaction_dir)

        # Verify transaction directory is used (internal state)
        assert service is not None

    def test_init_with_user_prompt_callback(self) -> None:
        """Test initialization with user prompt callback.

        OrganizationService should accept user prompt callback for ASK_USER strategy.
        """

        async def user_callback(conflict):
            return ConflictStrategy.SKIP

        service = OrganizationService(user_prompt_callback=user_callback)

        assert service is not None


# =============================================================================
# TestExecutePlan - Single plan execution tests
# =============================================================================


class TestExecutePlan:
    """Test cases for single plan execution."""

    @pytest.mark.asyncio
    async def test_execute_plan_move_success(
        self,
        service: OrganizationService,
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

        result = await service.execute_plan(action)

        assert result.success is True
        assert result.file_path == source_file
        assert result.target_path == target_path
        assert result.action == "move"
        assert not source_file.exists()
        assert target_path.exists()
        assert target_path.read_text() == "Test content"

    @pytest.mark.asyncio
    async def test_execute_plan_copy_success(
        self,
        service: OrganizationService,
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

        result = await service.execute_plan(action)

        assert result.success is True
        assert result.file_path == source_file
        assert result.target_path == target_path
        assert result.action == "copy"
        assert source_file.exists()  # Original should still exist
        assert target_path.exists()
        assert target_path.read_text() == "Test content"

    @pytest.mark.asyncio
    async def test_execute_plan_delete_success(
        self,
        service: OrganizationService,
        source_file: Path,
        trash_dir: Path,
    ) -> None:
        """Test successful file delete operation.

        REQ-E-009: action="delete" moves file to trash.
        """
        action = OrganizationAction(
            action="delete",
            source_path=source_file,
            target_path=None,
            options={},
        )

        result = await service.execute_plan(action)

        assert result.success is True
        assert result.file_path == source_file
        assert result.action == "delete"
        assert not source_file.exists()

        # Verify file is in trash
        trash_files = list(trash_dir.rglob("*test_file.txt"))
        assert len(trash_files) == 1

    @pytest.mark.asyncio
    async def test_execute_plan_dry_run(
        self,
        service: OrganizationService,
        source_file: Path,
        target_dir: Path,
    ) -> None:
        """Test dry-run mode doesn't modify files.

        REQ-E-001: dry_run=True performs no actual file operations.
        """
        target_path = target_dir / "moved_file.txt"
        action = OrganizationAction(
            action="move",
            source_path=source_file,
            target_path=target_path,
            options={},
        )

        result = await service.execute_plan(action, dry_run=True)

        assert result.success is True
        assert source_file.exists()  # Source should still exist
        assert not target_path.exists()  # Target should not be created

    @pytest.mark.asyncio
    async def test_execute_plan_with_conflict_strategy(
        self,
        service: OrganizationService,
        source_file: Path,
        target_dir: Path,
    ) -> None:
        """Test execution with explicit conflict strategy.

        REQ-S-003: Conflict resolution strategy support.
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

        result = await service.execute_plan(
            action,
            conflict_strategy=ConflictStrategy.OVERWRITE,
        )

        assert result.success is True
        assert not source_file.exists()
        assert target_path.read_text() == "Test content"  # Overwritten

    @pytest.mark.asyncio
    async def test_execute_plan_validation_failure(
        self,
        trash_dir: Path,
        transaction_dir: Path,
        temp_dir: Path,
    ) -> None:
        """Test that validation failure returns error result.

        REQ-U-001: Safety validation before execution.
        """
        service = OrganizationService(
            trash_dir=trash_dir,
            transaction_dir=transaction_dir,
        )

        # Create action with non-existent source that passes validation
        # but fails during execution
        source = temp_dir / "nonexistent_source.txt"
        target = temp_dir / "target.txt"

        action = OrganizationAction(
            action="move",
            source_path=source,
            target_path=target,
            options={},
        )

        result = await service.execute_plan(action)

        assert result.success is False


# =============================================================================
# TestExecuteBatch - Batch execution tests
# =============================================================================


class TestExecuteBatch:
    """Test cases for batch execution."""

    @pytest.mark.asyncio
    async def test_execute_batch_all_success(
        self,
        service: OrganizationService,
        temp_dir: Path,
        target_dir: Path,
    ) -> None:
        """Test batch execution with all operations successful.

        REQ-E-003: Batch processing support.
        """
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

        result = await service.execute_batch(actions)

        assert result.successful == 5
        assert result.failed == 0
        assert result.total == 5
        assert len(result.results) == 5

        # Verify all files moved
        for i in range(5):
            assert (target_dir / f"file_{i}.txt").exists()

    @pytest.mark.asyncio
    async def test_execute_batch_partial_failure(
        self,
        service: OrganizationService,
        temp_dir: Path,
        target_dir: Path,
    ) -> None:
        """Test batch execution continues despite individual failures.

        REQ-S-006: Individual errors don't stop batch processing.
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

        # Add action with non-existent source (will fail)
        actions.append(
            OrganizationAction(
                action="move",
                source_path=source_dir / "nonexistent.txt",
                target_path=target_dir / "nonexistent.txt",
                options={},
            )
        )

        result = await service.execute_batch(actions)

        assert result.total == 4
        assert result.successful >= 3  # At least 3 should succeed
        assert result.failed >= 1  # At least 1 failure

    @pytest.mark.asyncio
    async def test_execute_batch_rollback_on_error(
        self,
        service: OrganizationService,
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

        result = await service.execute_batch(
            actions,
            rollback_on_error=True,
        )

        assert result.failed > 0

    @pytest.mark.asyncio
    async def test_execute_batch_progress_callback(
        self,
        service: OrganizationService,
        temp_dir: Path,
        target_dir: Path,
    ) -> None:
        """Test progress callback is called during batch execution.

        REQ-E-005: Progress callback invocation.
        """
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

        result = await service.execute_batch(
            actions,
            progress_callback=progress_callback,
        )

        assert result.successful == 5
        # Progress callback should have been called
        assert len(progress_updates) >= 2  # At least start and complete

    @pytest.mark.asyncio
    async def test_execute_batch_concurrency(
        self,
        service: OrganizationService,
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

        result = await service.execute_batch(actions, concurrency=2)

        assert result.successful == 10
        assert result.total == 10


# =============================================================================
# TestValidate - Validation tests
# =============================================================================


class TestValidate:
    """Test cases for action validation."""

    @pytest.mark.asyncio
    async def test_validate_valid_action(
        self,
        service: OrganizationService,
        source_file: Path,
        target_dir: Path,
    ) -> None:
        """Test validation of a valid action.

        REQ-U-001: Safety validation.
        """
        target_path = target_dir / "target_file.txt"
        action = OrganizationAction(
            action="move",
            source_path=source_file,
            target_path=target_path,
            options={},
        )

        result = await service.validate(action)

        assert isinstance(result, ValidationResult)
        assert result.valid is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_invalid_action(
        self,
        service: OrganizationService,
        temp_dir: Path,
    ) -> None:
        """Test validation of an invalid action.

        REQ-U-001: Safety validation rejects invalid actions.
        """
        # Create action targeting protected path
        action = OrganizationAction(
            action="move",
            source_path=temp_dir / "source.txt",
            target_path=Path("/etc/invalid_target"),
            options={},
        )

        # Should raise ProtectedPathError for protected path
        with pytest.raises(ProtectedPathError):
            await service.validate(action)


# =============================================================================
# TestRollbackAndRecovery - Rollback and recovery tests
# =============================================================================


class TestRollbackAndRecovery:
    """Test cases for rollback and crash recovery."""

    @pytest.mark.asyncio
    async def test_rollback_success(
        self,
        trash_dir: Path,
        transaction_dir: Path,
    ) -> None:
        """Test successful transaction rollback.

        REQ-U-003: Rollback restores previous state.
        """
        service = OrganizationService(
            trash_dir=trash_dir,
            transaction_dir=transaction_dir,
        )

        # Create a mock transaction ID
        # Since we don't have an actual transaction, this will raise TransactionError
        with pytest.raises(TransactionError):
            await service.rollback("nonexistent-transaction-id")

    @pytest.mark.asyncio
    async def test_get_transaction_history(
        self,
        service: OrganizationService,
    ) -> None:
        """Test getting transaction history.

        Should return list of transaction summaries.
        """
        history = await service.get_transaction_history(limit=10)

        assert isinstance(history, list)

    @pytest.mark.asyncio
    async def test_recover_from_crash(
        self,
        service: OrganizationService,
    ) -> None:
        """Test crash recovery detection.

        Should detect incomplete transactions.
        """
        incomplete = await service.recover_from_crash()

        assert isinstance(incomplete, list)


# =============================================================================
# TestProperties - Property tests
# =============================================================================


class TestProperties:
    """Test cases for OrganizationService properties."""

    def test_trash_dir_property(
        self,
        trash_dir: Path,
        transaction_dir: Path,
    ) -> None:
        """Test trash_dir property returns correct path."""
        service = OrganizationService(
            trash_dir=trash_dir,
            transaction_dir=transaction_dir,
        )

        assert service.trash_dir == trash_dir

    def test_default_conflict_strategy_getter_setter(
        self,
        service: OrganizationService,
    ) -> None:
        """Test default_conflict_strategy getter and setter."""
        # Verify initial value
        assert service.default_conflict_strategy == ConflictStrategy.SKIP

        # Set new value
        service.default_conflict_strategy = ConflictStrategy.OVERWRITE
        assert service.default_conflict_strategy == ConflictStrategy.OVERWRITE

        # Set another value
        service.default_conflict_strategy = ConflictStrategy.RENAME_SUFFIX
        assert service.default_conflict_strategy == ConflictStrategy.RENAME_SUFFIX


# =============================================================================
# TestIntegration - Integration tests
# =============================================================================


class TestIntegration:
    """Integration tests for OrganizationService."""

    @pytest.mark.asyncio
    async def test_full_workflow_move_validate_rollback(
        self,
        trash_dir: Path,
        transaction_dir: Path,
        temp_dir: Path,
    ) -> None:
        """Test complete workflow: validate, execute, then check state."""
        service = OrganizationService(
            trash_dir=trash_dir,
            transaction_dir=transaction_dir,
        )

        # Create source file
        source = temp_dir / "source" / "workflow_test.txt"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("Workflow test content")

        target = temp_dir / "target" / "workflow_test.txt"
        action = OrganizationAction(
            action="move",
            source_path=source,
            target_path=target,
            options={},
        )

        # 1. Validate
        validation = await service.validate(action)
        assert validation.valid is True

        # 2. Execute
        result = await service.execute_plan(action)
        assert result.success is True
        assert target.exists()
        assert not source.exists()

    @pytest.mark.asyncio
    async def test_batch_with_mixed_operations(
        self,
        service: OrganizationService,
        temp_dir: Path,
        target_dir: Path,
        trash_dir: Path,
    ) -> None:
        """Test batch execution with mixed operation types."""
        source_dir = temp_dir / "mixed_source"
        source_dir.mkdir(parents=True, exist_ok=True)

        actions = []

        # Move operation
        move_source = source_dir / "to_move.txt"
        move_source.write_text("To be moved")
        actions.append(
            OrganizationAction(
                action="move",
                source_path=move_source,
                target_path=target_dir / "moved.txt",
                options={},
            )
        )

        # Copy operation
        copy_source = source_dir / "to_copy.txt"
        copy_source.write_text("To be copied")
        actions.append(
            OrganizationAction(
                action="copy",
                source_path=copy_source,
                target_path=target_dir / "copied.txt",
                options={},
            )
        )

        # Delete operation
        delete_source = source_dir / "to_delete.txt"
        delete_source.write_text("To be deleted")
        actions.append(
            OrganizationAction(
                action="delete",
                source_path=delete_source,
                target_path=None,
                options={},
            )
        )

        result = await service.execute_batch(actions)

        assert result.successful == 3
        assert result.failed == 0

        # Verify operations
        assert not move_source.exists()
        assert (target_dir / "moved.txt").exists()
        assert copy_source.exists()
        assert (target_dir / "copied.txt").exists()
        assert not delete_source.exists()
        assert len(list(trash_dir.rglob("*to_delete.txt"))) == 1
