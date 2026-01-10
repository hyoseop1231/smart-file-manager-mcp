"""Organization module for file organization execution.

TAG: ORG-001-M1
SPEC: SPEC-ORG-001

This module provides the file organization execution service that
executes OrganizationPlans from the classification module.
"""

from smart_file_manager.organization.conflict_resolver import ConflictResolver
from smart_file_manager.organization.models import (
    BatchExecutionResult,
    Conflict,
    ConflictStrategy,
    ExecutionResult,
    OrganizationAction,
    Progress,
    RollbackResult,
    TransactionEntry,
    ValidationResult,
)
from smart_file_manager.organization.organization_executor import OrganizationExecutor
from smart_file_manager.organization.organization_service import OrganizationService
from smart_file_manager.organization.progress_tracker import ProgressTracker
from smart_file_manager.organization.safety_validator import (
    PROTECTED_PATHS,
    SafetyValidator,
)
from smart_file_manager.organization.transaction_manager import TransactionManager

__all__ = [
    "ConflictResolver",
    "ConflictStrategy",
    "ExecutionResult",
    "BatchExecutionResult",
    "Conflict",
    "ValidationResult",
    "TransactionEntry",
    "Progress",
    "ProgressTracker",
    "RollbackResult",
    "OrganizationAction",
    "SafetyValidator",
    "PROTECTED_PATHS",
    "TransactionManager",
    "OrganizationExecutor",
    "OrganizationService",
]
