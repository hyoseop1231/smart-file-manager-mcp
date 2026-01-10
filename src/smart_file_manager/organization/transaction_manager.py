"""Transaction manager for file operations.

TAG: ORG-001-T1
SPEC: SPEC-ORG-001

This module provides transactional support for file operations,
enabling rollback capabilities and crash recovery.
"""

import asyncio
import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from smart_file_manager.core.exceptions import TransactionError
from smart_file_manager.organization.models import RollbackResult, TransactionEntry


class TransactionManager:
    """Manages file operation transactions with rollback support.

    Provides ACID-like guarantees for file operations:
    - Atomicity: All operations succeed or all fail
    - Consistency: File system state is consistent after transaction
    - Isolation: Transactions don't interfere with each other
    - Durability: Transaction logs persist to disk

    Attributes:
        DEFAULT_TRANSACTION_DIR: Default directory for transaction logs.
    """

    DEFAULT_TRANSACTION_DIR = Path.home() / ".smart_file_manager" / "transactions"

    def __init__(
        self,
        transaction_dir: Path | None = None,
    ) -> None:
        """Initialize transaction manager.

        Args:
            transaction_dir: Directory for transaction logs. If None,
                uses DEFAULT_TRANSACTION_DIR.
        """
        self._transaction_dir = transaction_dir or self.DEFAULT_TRANSACTION_DIR
        self._transaction_dir.mkdir(parents=True, exist_ok=True)

        self._active_transactions: dict[str, list[TransactionEntry]] = {}
        self._lock = asyncio.Lock()

    async def begin(self) -> str:
        """Start a new transaction.

        Creates a new transaction with a unique identifier. The transaction
        must be either committed or rolled back when complete.

        Returns:
            Transaction ID (UUID string).
        """
        transaction_id = str(uuid.uuid4())
        async with self._lock:
            self._active_transactions[transaction_id] = []
        return transaction_id

    async def record(
        self,
        transaction_id: str,
        action: str,
        source_path: Path,
        target_path: Path | None = None,
        backup_path: Path | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TransactionEntry:
        """Record an operation in the transaction log.

        Args:
            transaction_id: Active transaction ID from begin().
            action: Action type (move, copy, delete, rename).
            source_path: Original source path.
            target_path: Target path (if applicable).
            backup_path: Backup path for rollback support.
            metadata: Additional operation metadata.

        Returns:
            Created transaction entry.

        Raises:
            TransactionError: If transaction not found or already committed.
        """
        if transaction_id not in self._active_transactions:
            raise TransactionError(f"Transaction not found: {transaction_id}")

        entry = TransactionEntry(
            id=str(uuid.uuid4()),
            action=action,
            source_path=source_path,
            target_path=target_path,
            backup_path=backup_path,
            timestamp=datetime.now(),
            status="pending",
            metadata=metadata or {},
        )

        async with self._lock:
            self._active_transactions[transaction_id].append(entry)
            await self._persist_log(transaction_id)

        return entry

    async def commit(self, transaction_id: str) -> None:
        """Commit a transaction, marking all entries as completed.

        After commit, the transaction log is saved with a completed suffix
        and the transaction is removed from active transactions.

        Args:
            transaction_id: Transaction to commit.

        Raises:
            TransactionError: If transaction not found.
        """
        if transaction_id not in self._active_transactions:
            raise TransactionError(f"Transaction not found: {transaction_id}")

        async with self._lock:
            await self._persist_log(transaction_id, completed=True)
            del self._active_transactions[transaction_id]

    async def rollback(self, transaction_id: str) -> RollbackResult:
        """Rollback a transaction, reversing all operations.

        Undoes all recorded operations in reverse order. For move and delete
        operations, restores files from backup paths. For copy operations,
        removes the copied files.

        Args:
            transaction_id: Transaction to rollback.

        Returns:
            RollbackResult with restoration status.
        """
        entries = await self._get_entries(transaction_id)

        restored_files = 0
        failed_restorations: list[dict[str, str]] = []

        # Reverse the entries to undo in opposite order
        for entry in reversed(entries):
            try:
                restored = await self._undo_entry(entry)
                if restored:
                    restored_files += 1
            except Exception as e:
                failed_restorations.append(
                    {
                        "entry_id": entry.id,
                        "source_path": str(entry.source_path),
                        "error": str(e),
                    }
                )

        # Clean up transaction log
        await self._cleanup_transaction(transaction_id)

        return RollbackResult(
            success=len(failed_restorations) == 0,
            restored_files=restored_files,
            failed_restorations=failed_restorations,
            transaction_id=transaction_id,
        )

    async def recover_from_crash(self) -> list[str]:
        """Recover incomplete transactions from crash.

        Scans the transaction directory for incomplete transaction logs
        (those without the _completed suffix) that may need recovery.

        Returns:
            List of recovered transaction IDs.
        """
        recovered: list[str] = []

        for log_file in self._transaction_dir.glob("*.json"):
            if not log_file.name.endswith("_completed.json"):
                transaction_id = log_file.stem
                recovered.append(transaction_id)

        return recovered

    async def get_transaction_history(
        self,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get recent transaction history.

        Args:
            limit: Maximum number of transactions to return.

        Returns:
            List of transaction summaries ordered by newest first.
        """
        history: list[dict[str, Any]] = []

        log_files = sorted(
            self._transaction_dir.glob("*_completed.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )[:limit]

        for log_file in log_files:
            with open(log_file) as f:
                data = json.load(f)
                history.append(
                    {
                        "transaction_id": log_file.stem.replace("_completed", ""),
                        "entries_count": len(data.get("entries", [])),
                        "completed_at": data.get("completed_at"),
                    }
                )

        return history

    async def _persist_log(
        self,
        transaction_id: str,
        completed: bool = False,
    ) -> None:
        """Persist transaction log to disk.

        Args:
            transaction_id: ID of the transaction to persist.
            completed: Whether to save as a completed transaction.
        """
        suffix = "_completed" if completed else ""
        log_path = self._transaction_dir / f"{transaction_id}{suffix}.json"

        entries = self._active_transactions.get(transaction_id, [])
        data: dict[str, Any] = {
            "transaction_id": transaction_id,
            "entries": [self._entry_to_dict(e) for e in entries],
            "created_at": datetime.now().isoformat(),
        }
        if completed:
            data["completed_at"] = datetime.now().isoformat()

        with open(log_path, "w") as f:
            json.dump(data, f, indent=2)

    async def _get_entries(self, transaction_id: str) -> list[TransactionEntry]:
        """Get entries from active transactions or log file.

        Args:
            transaction_id: ID of the transaction.

        Returns:
            List of transaction entries.

        Raises:
            TransactionError: If transaction not found.
        """
        if transaction_id in self._active_transactions:
            return self._active_transactions[transaction_id]

        log_path = self._transaction_dir / f"{transaction_id}.json"
        completed_log_path = self._transaction_dir / f"{transaction_id}_completed.json"

        for path in [log_path, completed_log_path]:
            if path.exists():
                with open(path) as f:
                    data = json.load(f)
                    return [self._dict_to_entry(e) for e in data.get("entries", [])]

        raise TransactionError(f"Transaction not found: {transaction_id}")

    async def _undo_entry(self, entry: TransactionEntry) -> bool:
        """Undo a single transaction entry.

        Args:
            entry: The transaction entry to undo.

        Returns:
            True if a file was restored, False otherwise.
        """
        if entry.action == "move" and entry.backup_path:
            # Restore from backup
            if entry.backup_path.exists():
                entry.source_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(entry.backup_path), str(entry.source_path))
                return True
        elif entry.action == "copy" and entry.target_path:
            # Remove copied file
            if entry.target_path.exists():
                entry.target_path.unlink()
                return True
        elif entry.action == "delete" and entry.backup_path:
            # Restore from backup
            if entry.backup_path.exists():
                entry.source_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(entry.backup_path), str(entry.source_path))
                return True

        return False

    async def _cleanup_transaction(self, transaction_id: str) -> None:
        """Clean up transaction log files.

        Args:
            transaction_id: ID of the transaction to clean up.
        """
        async with self._lock:
            if transaction_id in self._active_transactions:
                del self._active_transactions[transaction_id]

        log_path = self._transaction_dir / f"{transaction_id}.json"
        if log_path.exists():
            log_path.unlink()

    def _entry_to_dict(self, entry: TransactionEntry) -> dict[str, Any]:
        """Convert TransactionEntry to dict for JSON serialization.

        Args:
            entry: The transaction entry to convert.

        Returns:
            Dictionary representation of the entry.
        """
        return {
            "id": entry.id,
            "action": entry.action,
            "source_path": str(entry.source_path),
            "target_path": str(entry.target_path) if entry.target_path else None,
            "backup_path": str(entry.backup_path) if entry.backup_path else None,
            "timestamp": entry.timestamp.isoformat(),
            "status": entry.status,
            "metadata": entry.metadata,
        }

    def _dict_to_entry(self, data: dict[str, Any]) -> TransactionEntry:
        """Convert dict to TransactionEntry.

        Args:
            data: Dictionary representation of a transaction entry.

        Returns:
            TransactionEntry instance.
        """
        return TransactionEntry(
            id=data["id"],
            action=data["action"],
            source_path=Path(data["source_path"]),
            target_path=Path(data["target_path"]) if data.get("target_path") else None,
            backup_path=Path(data["backup_path"]) if data.get("backup_path") else None,
            timestamp=datetime.fromisoformat(data["timestamp"]),
            status=data.get("status", "pending"),
            metadata=data.get("metadata", {}),
        )
