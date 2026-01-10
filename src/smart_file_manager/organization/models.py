"""Organization execution models.

TAG: ORG-001-M1
SPEC: SPEC-ORG-001

This module defines dataclasses for file organization execution,
including conflict strategies, execution results, validation,
transactions, progress tracking, and rollback operations.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID


class ConflictStrategy(Enum):
    """Strategy for handling file conflicts during organization.

    Defines how to handle situations when a target file already exists.

    Attributes:
        SKIP: Skip the file and continue with the next one.
        OVERWRITE: Overwrite the existing file.
        RENAME_SUFFIX: Add a numeric suffix to the filename (e.g., file_1.txt).
        RENAME_TIMESTAMP: Add a timestamp suffix to the filename.
        ASK_USER: Prompt the user to decide what to do.
    """

    SKIP = "skip"
    OVERWRITE = "overwrite"
    RENAME_SUFFIX = "rename_suffix"
    RENAME_TIMESTAMP = "rename_timestamp"
    ASK_USER = "ask_user"


@dataclass(frozen=True)
class ExecutionResult:
    """Result of a single file organization operation.

    Attributes:
        success: Whether the operation completed successfully.
        file_path: Original source file path.
        target_path: Destination file path.
        action: Type of action performed (move, copy, delete).
        processing_time_ms: Time taken to process in milliseconds.
        error: Error message if operation failed, None otherwise.
        transaction_id: UUID identifying the transaction.
    """

    success: bool
    file_path: Path
    target_path: Path
    action: str
    processing_time_ms: float
    error: str | None
    transaction_id: UUID


@dataclass(frozen=True)
class BatchExecutionResult:
    """Result of a batch file organization operation.

    Attributes:
        successful: Number of files successfully processed.
        failed: Number of files that failed to process.
        total: Total number of files in the batch.
        results: List of individual execution results.
        transaction_id: UUID identifying the batch transaction.
    """

    successful: int
    failed: int
    total: int
    results: list[ExecutionResult]
    transaction_id: UUID


@dataclass(frozen=True)
class Conflict:
    """Represents a file conflict during organization.

    Attributes:
        source_path: Path of the source file.
        target_path: Path of the target file.
        reason: Description of why the conflict occurred.
        suggestions: List of suggested resolutions.
    """

    source_path: Path
    target_path: Path
    reason: str
    suggestions: list[str]


@dataclass(frozen=True)
class ValidationResult:
    """Result of validating an organization plan.

    Attributes:
        valid: Whether the plan is valid and can be executed.
        conflicts: List of detected file conflicts.
        errors: List of error messages.
        warnings: List of warning messages.
    """

    valid: bool
    conflicts: list[Conflict]
    errors: list[str]
    warnings: list[str]


@dataclass(frozen=True)
class TransactionEntry:
    """Entry in a transaction log for tracking operations.

    Attributes:
        id: Unique identifier for this entry.
        action: Type of action (move, copy, delete, rename).
        source_path: Original file path.
        target_path: Destination file path (None for delete operations).
        backup_path: Path where backup is stored for rollback support.
        timestamp: When the action was performed.
        status: Current status (pending, completed, failed).
        metadata: Additional operation metadata for context.
    """

    id: str
    action: str
    source_path: Path
    target_path: Path | None
    backup_path: Path | None
    timestamp: datetime
    status: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class Progress:
    """Progress information for an ongoing organization operation.

    Attributes:
        current: Number of files processed so far.
        total: Total number of files to process.
        percentage: Completion percentage (0.0 to 100.0).
        current_file: Path of the file currently being processed.
        eta_seconds: Estimated time remaining in seconds.
        elapsed_seconds: Time elapsed since operation started in seconds.
    """

    current: int
    total: int
    percentage: float
    current_file: str
    eta_seconds: float | None
    elapsed_seconds: float


@dataclass(frozen=True)
class RollbackResult:
    """Result of a rollback operation.

    Attributes:
        success: Whether the rollback completed successfully.
        restored_files: Number of files that were successfully restored.
        failed_restorations: List of failed restoration details.
            Each dict contains entry_id, source_path, and error.
        transaction_id: ID of the transaction that was rolled back.
    """

    success: bool
    restored_files: int
    failed_restorations: list[dict[str, str]]
    transaction_id: str


@dataclass(frozen=True)
class OrganizationAction:
    """Represents a single organization action to be executed.

    Attributes:
        action: Type of action (move, copy, delete).
        source_path: Path of the source file.
        target_path: Path of the target file (None for delete).
        options: Additional options for the action.
    """

    action: str
    source_path: Path
    target_path: Path | None
    options: dict[str, Any]


__all__ = [
    "ConflictStrategy",
    "ExecutionResult",
    "BatchExecutionResult",
    "Conflict",
    "ValidationResult",
    "TransactionEntry",
    "Progress",
    "RollbackResult",
    "OrganizationAction",
]
