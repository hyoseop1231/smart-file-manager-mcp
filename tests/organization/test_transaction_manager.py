"""Tests for TransactionManager.

TAG: ORG-001-T1
SPEC: SPEC-ORG-001

This module contains comprehensive tests for the TransactionManager class,
covering transaction lifecycle, rollback operations, and crash recovery.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

import pytest

from smart_file_manager.core.exceptions import TransactionError
from smart_file_manager.organization.models import RollbackResult, TransactionEntry
from smart_file_manager.organization.transaction_manager import TransactionManager


class TestTransactionManagerInit:
    """Tests for TransactionManager initialization."""

    def test_default_transaction_dir_created(self, tmp_path: Path) -> None:
        """Test that the default transaction directory is created on init."""
        custom_dir = tmp_path / "transactions"
        manager = TransactionManager(transaction_dir=custom_dir)

        assert custom_dir.exists()
        assert custom_dir.is_dir()
        assert manager._transaction_dir == custom_dir

    def test_custom_transaction_dir(self, tmp_path: Path) -> None:
        """Test initialization with custom transaction directory."""
        custom_dir = tmp_path / "custom_transactions"
        manager = TransactionManager(transaction_dir=custom_dir)

        assert manager._transaction_dir == custom_dir
        assert custom_dir.exists()

    def test_creates_directory_if_not_exists(self, tmp_path: Path) -> None:
        """Test that nested directories are created if they don't exist."""
        nested_dir = tmp_path / "level1" / "level2" / "transactions"
        manager = TransactionManager(transaction_dir=nested_dir)

        assert nested_dir.exists()
        assert manager._transaction_dir == nested_dir


class TestBegin:
    """Tests for transaction begin operations."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> TransactionManager:
        """Create a TransactionManager instance for testing."""
        return TransactionManager(transaction_dir=tmp_path / "transactions")

    @pytest.mark.asyncio
    async def test_begin_returns_uuid(self, manager: TransactionManager) -> None:
        """Test that begin() returns a valid UUID string."""
        transaction_id = await manager.begin()

        # Verify it's a valid UUID
        uuid.UUID(transaction_id)
        assert isinstance(transaction_id, str)
        assert len(transaction_id) == 36  # UUID format: 8-4-4-4-12

    @pytest.mark.asyncio
    async def test_begin_creates_empty_entry_list(self, manager: TransactionManager) -> None:
        """Test that begin() creates an empty entry list for the transaction."""
        transaction_id = await manager.begin()

        assert transaction_id in manager._active_transactions
        assert manager._active_transactions[transaction_id] == []

    @pytest.mark.asyncio
    async def test_multiple_transactions_independent(self, manager: TransactionManager) -> None:
        """Test that multiple transactions are independent."""
        tx1 = await manager.begin()
        tx2 = await manager.begin()

        assert tx1 != tx2
        assert tx1 in manager._active_transactions
        assert tx2 in manager._active_transactions
        assert manager._active_transactions[tx1] is not manager._active_transactions[tx2]


class TestRecord:
    """Tests for transaction record operations."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> TransactionManager:
        """Create a TransactionManager instance for testing."""
        return TransactionManager(transaction_dir=tmp_path / "transactions")

    @pytest.mark.asyncio
    async def test_record_creates_entry(self, manager: TransactionManager, tmp_path: Path) -> None:
        """Test that record() creates a TransactionEntry."""
        transaction_id = await manager.begin()
        source = tmp_path / "source.txt"
        target = tmp_path / "target.txt"

        entry = await manager.record(
            transaction_id=transaction_id,
            action="move",
            source_path=source,
            target_path=target,
        )

        assert isinstance(entry, TransactionEntry)
        assert entry.action == "move"
        assert entry.source_path == source
        assert entry.target_path == target
        assert entry.status == "pending"

    @pytest.mark.asyncio
    async def test_record_persists_to_disk(
        self, manager: TransactionManager, tmp_path: Path
    ) -> None:
        """Test that record() persists the transaction log to disk."""
        transaction_id = await manager.begin()
        source = tmp_path / "source.txt"
        target = tmp_path / "target.txt"

        await manager.record(
            transaction_id=transaction_id,
            action="move",
            source_path=source,
            target_path=target,
        )

        log_path = manager._transaction_dir / f"{transaction_id}.json"
        assert log_path.exists()

        with open(log_path) as f:
            data = json.load(f)
        assert data["transaction_id"] == transaction_id
        assert len(data["entries"]) == 1

    @pytest.mark.asyncio
    async def test_record_invalid_transaction_raises_error(
        self, manager: TransactionManager, tmp_path: Path
    ) -> None:
        """Test that record() raises TransactionError for invalid transaction ID."""
        with pytest.raises(TransactionError) as exc_info:
            await manager.record(
                transaction_id="invalid-transaction-id",
                action="move",
                source_path=tmp_path / "source.txt",
                target_path=tmp_path / "target.txt",
            )

        assert "Transaction not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_record_with_backup_path(
        self, manager: TransactionManager, tmp_path: Path
    ) -> None:
        """Test that record() correctly stores backup_path."""
        transaction_id = await manager.begin()
        source = tmp_path / "source.txt"
        target = tmp_path / "target.txt"
        backup = tmp_path / "backup" / "source.txt.bak"

        entry = await manager.record(
            transaction_id=transaction_id,
            action="move",
            source_path=source,
            target_path=target,
            backup_path=backup,
        )

        assert entry.backup_path == backup

    @pytest.mark.asyncio
    async def test_record_with_metadata(self, manager: TransactionManager, tmp_path: Path) -> None:
        """Test that record() correctly stores metadata."""
        transaction_id = await manager.begin()
        source = tmp_path / "source.txt"
        metadata = {"original_size": 1024, "file_type": "text/plain"}

        entry = await manager.record(
            transaction_id=transaction_id,
            action="delete",
            source_path=source,
            metadata=metadata,
        )

        assert entry.metadata == metadata
        assert entry.metadata["original_size"] == 1024


class TestCommit:
    """Tests for transaction commit operations."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> TransactionManager:
        """Create a TransactionManager instance for testing."""
        return TransactionManager(transaction_dir=tmp_path / "transactions")

    @pytest.mark.asyncio
    async def test_commit_marks_completed(
        self, manager: TransactionManager, tmp_path: Path
    ) -> None:
        """Test that commit() creates a completed log file."""
        transaction_id = await manager.begin()
        await manager.record(
            transaction_id=transaction_id,
            action="move",
            source_path=tmp_path / "source.txt",
            target_path=tmp_path / "target.txt",
        )

        await manager.commit(transaction_id)

        completed_log = manager._transaction_dir / f"{transaction_id}_completed.json"
        assert completed_log.exists()

        with open(completed_log) as f:
            data = json.load(f)
        assert "completed_at" in data

    @pytest.mark.asyncio
    async def test_commit_removes_from_active(
        self, manager: TransactionManager, tmp_path: Path
    ) -> None:
        """Test that commit() removes transaction from active transactions."""
        transaction_id = await manager.begin()
        await manager.record(
            transaction_id=transaction_id,
            action="move",
            source_path=tmp_path / "source.txt",
            target_path=tmp_path / "target.txt",
        )

        await manager.commit(transaction_id)

        assert transaction_id not in manager._active_transactions

    @pytest.mark.asyncio
    async def test_commit_invalid_transaction_raises_error(
        self, manager: TransactionManager
    ) -> None:
        """Test that commit() raises TransactionError for invalid transaction ID."""
        with pytest.raises(TransactionError) as exc_info:
            await manager.commit("invalid-transaction-id")

        assert "Transaction not found" in str(exc_info.value)


class TestRollback:
    """Tests for transaction rollback operations."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> TransactionManager:
        """Create a TransactionManager instance for testing."""
        return TransactionManager(transaction_dir=tmp_path / "transactions")

    @pytest.mark.asyncio
    async def test_rollback_reverses_move(
        self, manager: TransactionManager, tmp_path: Path
    ) -> None:
        """Test that rollback() reverses a move operation."""
        # Setup: create source file and backup
        source = tmp_path / "source.txt"
        target = tmp_path / "target.txt"
        backup = tmp_path / "backup" / "source.txt.bak"
        backup.parent.mkdir(parents=True, exist_ok=True)

        # Create backup file (simulating what would happen during move)
        backup.write_text("original content")

        # Record the move operation
        transaction_id = await manager.begin()
        await manager.record(
            transaction_id=transaction_id,
            action="move",
            source_path=source,
            target_path=target,
            backup_path=backup,
        )

        # Rollback
        result = await manager.rollback(transaction_id)

        assert result.success is True
        assert result.restored_files == 1
        assert source.exists()
        assert source.read_text() == "original content"

    @pytest.mark.asyncio
    async def test_rollback_removes_copied_file(
        self, manager: TransactionManager, tmp_path: Path
    ) -> None:
        """Test that rollback() removes a copied file."""
        source = tmp_path / "source.txt"
        target = tmp_path / "target.txt"

        # Create target file (simulating a copy operation)
        source.write_text("source content")
        target.write_text("copied content")

        transaction_id = await manager.begin()
        await manager.record(
            transaction_id=transaction_id,
            action="copy",
            source_path=source,
            target_path=target,
        )

        result = await manager.rollback(transaction_id)

        assert result.success is True
        assert result.restored_files == 1
        assert not target.exists()

    @pytest.mark.asyncio
    async def test_rollback_restores_deleted_file(
        self, manager: TransactionManager, tmp_path: Path
    ) -> None:
        """Test that rollback() restores a deleted file from backup."""
        source = tmp_path / "source.txt"
        backup = tmp_path / "backup" / "source.txt.bak"
        backup.parent.mkdir(parents=True, exist_ok=True)

        # Create backup (simulating what happens during delete)
        backup.write_text("deleted content")

        transaction_id = await manager.begin()
        await manager.record(
            transaction_id=transaction_id,
            action="delete",
            source_path=source,
            backup_path=backup,
        )

        result = await manager.rollback(transaction_id)

        assert result.success is True
        assert result.restored_files == 1
        assert source.exists()
        assert source.read_text() == "deleted content"

    @pytest.mark.asyncio
    async def test_rollback_returns_result(
        self, manager: TransactionManager, tmp_path: Path
    ) -> None:
        """Test that rollback() returns a proper RollbackResult."""
        transaction_id = await manager.begin()
        backup = tmp_path / "backup.txt"
        backup.write_text("content")

        await manager.record(
            transaction_id=transaction_id,
            action="move",
            source_path=tmp_path / "source.txt",
            target_path=tmp_path / "target.txt",
            backup_path=backup,
        )

        result = await manager.rollback(transaction_id)

        assert isinstance(result, RollbackResult)
        assert result.transaction_id == transaction_id
        assert isinstance(result.restored_files, int)
        assert isinstance(result.failed_restorations, list)

    @pytest.mark.asyncio
    async def test_rollback_handles_missing_backup(
        self, manager: TransactionManager, tmp_path: Path
    ) -> None:
        """Test that rollback() handles missing backup files gracefully."""
        transaction_id = await manager.begin()
        missing_backup = tmp_path / "nonexistent_backup.txt"

        await manager.record(
            transaction_id=transaction_id,
            action="move",
            source_path=tmp_path / "source.txt",
            target_path=tmp_path / "target.txt",
            backup_path=missing_backup,
        )

        result = await manager.rollback(transaction_id)

        # Should handle gracefully, not raise exception
        assert isinstance(result, RollbackResult)
        # Missing backup means nothing to restore, but no failure either
        assert result.restored_files == 0


class TestRecoverFromCrash:
    """Tests for crash recovery operations."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> TransactionManager:
        """Create a TransactionManager instance for testing."""
        return TransactionManager(transaction_dir=tmp_path / "transactions")

    @pytest.mark.asyncio
    async def test_finds_incomplete_transactions(self, manager: TransactionManager) -> None:
        """Test that recover_from_crash() finds incomplete transaction logs."""
        # Create an incomplete transaction log file
        incomplete_log = manager._transaction_dir / "incomplete-tx-id.json"
        incomplete_log.write_text(json.dumps({"transaction_id": "incomplete-tx-id", "entries": []}))

        recovered = await manager.recover_from_crash()

        assert "incomplete-tx-id" in recovered

    @pytest.mark.asyncio
    async def test_ignores_completed_transactions(self, manager: TransactionManager) -> None:
        """Test that recover_from_crash() ignores completed transaction logs."""
        # Create a completed transaction log file
        completed_log = manager._transaction_dir / "completed-tx-id_completed.json"
        completed_log.write_text(
            json.dumps(
                {
                    "transaction_id": "completed-tx-id",
                    "entries": [],
                    "completed_at": datetime.now().isoformat(),
                }
            )
        )

        recovered = await manager.recover_from_crash()

        assert "completed-tx-id" not in recovered
        assert "completed-tx-id_completed" not in recovered


class TestGetTransactionHistory:
    """Tests for transaction history retrieval."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> TransactionManager:
        """Create a TransactionManager instance for testing."""
        return TransactionManager(transaction_dir=tmp_path / "transactions")

    @pytest.mark.asyncio
    async def test_returns_completed_transactions(self, manager: TransactionManager) -> None:
        """Test that get_transaction_history() returns completed transactions."""
        # Create completed transaction logs
        for i in range(3):
            log = manager._transaction_dir / f"tx-{i}_completed.json"
            log.write_text(
                json.dumps(
                    {
                        "transaction_id": f"tx-{i}",
                        "entries": [{"id": str(i)}],
                        "completed_at": datetime.now().isoformat(),
                    }
                )
            )

        history = await manager.get_transaction_history()

        assert len(history) == 3
        assert all("transaction_id" in tx for tx in history)
        assert all("entries_count" in tx for tx in history)

    @pytest.mark.asyncio
    async def test_respects_limit(self, manager: TransactionManager) -> None:
        """Test that get_transaction_history() respects the limit parameter."""
        # Create 5 completed transaction logs
        for i in range(5):
            log = manager._transaction_dir / f"tx-{i}_completed.json"
            log.write_text(
                json.dumps(
                    {
                        "transaction_id": f"tx-{i}",
                        "entries": [],
                        "completed_at": datetime.now().isoformat(),
                    }
                )
            )

        history = await manager.get_transaction_history(limit=3)

        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_orders_by_newest_first(
        self, manager: TransactionManager, tmp_path: Path
    ) -> None:
        """Test that get_transaction_history() orders by newest first."""
        import time

        # Create logs with different modification times
        for i in range(3):
            log = manager._transaction_dir / f"tx-{i}_completed.json"
            log.write_text(
                json.dumps(
                    {
                        "transaction_id": f"tx-{i}",
                        "entries": [],
                        "completed_at": datetime.now().isoformat(),
                    }
                )
            )
            time.sleep(0.1)  # Ensure different timestamps

        history = await manager.get_transaction_history()

        # Newest (tx-2) should be first
        assert history[0]["transaction_id"] == "tx-2"
        assert history[-1]["transaction_id"] == "tx-0"


class TestRollbackFromLogFile:
    """Tests for rollback operations from persisted log files."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> TransactionManager:
        """Create a TransactionManager instance for testing."""
        return TransactionManager(transaction_dir=tmp_path / "transactions")

    @pytest.mark.asyncio
    async def test_rollback_from_persisted_log(
        self, manager: TransactionManager, tmp_path: Path
    ) -> None:
        """Test rollback using entries loaded from persisted log file."""
        # Create a log file directly (simulating crash recovery scenario)
        transaction_id = "persisted-tx-id"
        backup = tmp_path / "backup.txt"
        backup.write_text("backup content")

        log_data = {
            "transaction_id": transaction_id,
            "entries": [
                {
                    "id": "entry-1",
                    "action": "move",
                    "source_path": str(tmp_path / "source.txt"),
                    "target_path": str(tmp_path / "target.txt"),
                    "backup_path": str(backup),
                    "timestamp": datetime.now().isoformat(),
                    "status": "pending",
                    "metadata": {},
                }
            ],
            "created_at": datetime.now().isoformat(),
        }

        log_path = manager._transaction_dir / f"{transaction_id}.json"
        log_path.write_text(json.dumps(log_data))

        # Rollback from persisted log
        result = await manager.rollback(transaction_id)

        assert result.success is True
        assert result.restored_files == 1
        assert (tmp_path / "source.txt").exists()

    @pytest.mark.asyncio
    async def test_rollback_from_completed_log(
        self, manager: TransactionManager, tmp_path: Path
    ) -> None:
        """Test rollback using entries loaded from completed log file."""
        transaction_id = "completed-tx-id"
        target = tmp_path / "target.txt"
        target.write_text("copied content")

        log_data = {
            "transaction_id": transaction_id,
            "entries": [
                {
                    "id": "entry-1",
                    "action": "copy",
                    "source_path": str(tmp_path / "source.txt"),
                    "target_path": str(target),
                    "backup_path": None,
                    "timestamp": datetime.now().isoformat(),
                    "status": "completed",
                    "metadata": {},
                }
            ],
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
        }

        log_path = manager._transaction_dir / f"{transaction_id}_completed.json"
        log_path.write_text(json.dumps(log_data))

        result = await manager.rollback(transaction_id)

        assert result.success is True
        assert result.restored_files == 1
        assert not target.exists()

    @pytest.mark.asyncio
    async def test_rollback_nonexistent_transaction_raises_error(
        self, manager: TransactionManager
    ) -> None:
        """Test that rollback raises TransactionError for nonexistent transaction."""
        with pytest.raises(TransactionError) as exc_info:
            await manager.rollback("nonexistent-tx-id")

        assert "Transaction not found" in str(exc_info.value)


class TestRollbackEdgeCases:
    """Tests for rollback edge cases and error handling."""

    @pytest.fixture
    def manager(self, tmp_path: Path) -> TransactionManager:
        """Create a TransactionManager instance for testing."""
        return TransactionManager(transaction_dir=tmp_path / "transactions")

    @pytest.mark.asyncio
    async def test_rollback_with_unknown_action(
        self, manager: TransactionManager, tmp_path: Path
    ) -> None:
        """Test rollback with an unknown action type returns 0 restored."""
        transaction_id = await manager.begin()

        await manager.record(
            transaction_id=transaction_id,
            action="unknown_action",
            source_path=tmp_path / "source.txt",
            target_path=tmp_path / "target.txt",
        )

        result = await manager.rollback(transaction_id)

        assert result.success is True
        assert result.restored_files == 0

    @pytest.mark.asyncio
    async def test_rollback_move_without_backup_path(
        self, manager: TransactionManager, tmp_path: Path
    ) -> None:
        """Test rollback of move operation without backup_path."""
        transaction_id = await manager.begin()

        await manager.record(
            transaction_id=transaction_id,
            action="move",
            source_path=tmp_path / "source.txt",
            target_path=tmp_path / "target.txt",
            backup_path=None,
        )

        result = await manager.rollback(transaction_id)

        assert result.success is True
        assert result.restored_files == 0

    @pytest.mark.asyncio
    async def test_rollback_copy_without_target(
        self, manager: TransactionManager, tmp_path: Path
    ) -> None:
        """Test rollback of copy operation without target_path."""
        transaction_id = await manager.begin()

        await manager.record(
            transaction_id=transaction_id,
            action="copy",
            source_path=tmp_path / "source.txt",
            target_path=None,
        )

        result = await manager.rollback(transaction_id)

        assert result.success is True
        assert result.restored_files == 0

    @pytest.mark.asyncio
    async def test_rollback_delete_without_backup(
        self, manager: TransactionManager, tmp_path: Path
    ) -> None:
        """Test rollback of delete operation without backup_path."""
        transaction_id = await manager.begin()

        await manager.record(
            transaction_id=transaction_id,
            action="delete",
            source_path=tmp_path / "source.txt",
            backup_path=None,
        )

        result = await manager.rollback(transaction_id)

        assert result.success is True
        assert result.restored_files == 0

    @pytest.mark.asyncio
    async def test_rollback_cleans_up_active_transaction(
        self, manager: TransactionManager, tmp_path: Path
    ) -> None:
        """Test that rollback cleans up the active transaction."""
        transaction_id = await manager.begin()

        await manager.record(
            transaction_id=transaction_id,
            action="move",
            source_path=tmp_path / "source.txt",
            target_path=tmp_path / "target.txt",
        )

        assert transaction_id in manager._active_transactions

        await manager.rollback(transaction_id)

        assert transaction_id not in manager._active_transactions

    @pytest.mark.asyncio
    async def test_rollback_cleans_up_log_file(
        self, manager: TransactionManager, tmp_path: Path
    ) -> None:
        """Test that rollback removes the transaction log file."""
        transaction_id = await manager.begin()

        await manager.record(
            transaction_id=transaction_id,
            action="move",
            source_path=tmp_path / "source.txt",
            target_path=tmp_path / "target.txt",
        )

        log_path = manager._transaction_dir / f"{transaction_id}.json"
        assert log_path.exists()

        await manager.rollback(transaction_id)

        assert not log_path.exists()
