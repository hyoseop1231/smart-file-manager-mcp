"""Safety validator for file organization operations.

TAG: ORG-001-S1
SPEC: SPEC-ORG-001

This module provides safety validation for file organization operations.
It ensures file operations are safe before execution by:
- Preventing modification of protected system paths
- Checking file permissions
- Verifying disk space availability
- Detecting locked files
"""

import os
import shutil
from pathlib import Path

from smart_file_manager.core.exceptions import (
    InsufficientSpaceError,
    ProtectedPathError,
)
from smart_file_manager.organization.models import Conflict, ValidationResult

# Protected system paths that should never be modified
PROTECTED_PATHS: frozenset[Path] = frozenset(
    [
        Path("/"),
        Path("/System"),
        Path("/usr"),
        Path("/bin"),
        Path("/sbin"),
        Path("/etc"),
        Path("/var"),
        Path("/Library"),
        Path.home() / ".ssh",
        Path.home() / ".gnupg",
        Path.home() / ".config",
    ]
)

# Paths that are exceptions to protected paths (allowed even if under protected)
# These are user-accessible temporary directories on macOS/Linux
_VAR_FOLDERS = Path("/var") / "folders"  # macOS user temp directories
_VAR_TMP = Path("/var") / "tmp"  # noqa: S108  # Temp directories (safe: only used for path matching)
ALLOWED_PATHS: frozenset[Path] = frozenset([_VAR_FOLDERS, _VAR_TMP])


class SafetyValidator:
    """Validates safety of file operations.

    Ensures file operations are safe before execution:
    - Prevents modification of protected system paths
    - Checks file permissions
    - Verifies disk space availability
    - Detects locked files

    Attributes:
        _protected_paths: Set of protected paths that cannot be modified.
        _include_hidden: Whether to allow operations on hidden files.
    """

    def __init__(
        self,
        protected_paths: frozenset[Path] | None = None,
        include_hidden: bool = False,
    ) -> None:
        """Initialize validator.

        Args:
            protected_paths: Custom protected paths (defaults to PROTECTED_PATHS).
            include_hidden: Whether to allow operations on hidden files.
        """
        self._protected_paths = protected_paths or PROTECTED_PATHS
        self._include_hidden = include_hidden

    def validate_plan(
        self,
        source_path: Path,
        target_path: Path,
        action: str,
    ) -> ValidationResult:
        """Validate a file organization plan.

        Args:
            source_path: Source file path.
            target_path: Target destination path.
            action: Action type (move, copy, delete, rename).

        Returns:
            ValidationResult with valid status and any errors/warnings.

        Raises:
            ProtectedPathError: If source or target is a protected path.
            InsufficientSpaceError: If not enough disk space.
        """
        errors: list[str] = []
        warnings: list[str] = []
        conflicts: list[Conflict] = []

        # Check protected paths
        if self.is_protected_path(source_path):
            raise ProtectedPathError(f"Source path is protected: {source_path}")
        if self.is_protected_path(target_path):
            raise ProtectedPathError(f"Target path is protected: {target_path}")

        # Check hidden files
        if not self._include_hidden and self._is_hidden_file(source_path):
            warnings.append(f"Hidden file will be skipped: {source_path}")

        # Check permissions
        if not self.check_permissions(source_path, action):
            errors.append(f"Insufficient permissions for {action} on {source_path}")

        # Check disk space for copy/move operations
        if action in ("copy", "move") and source_path.exists():
            file_size = source_path.stat().st_size if source_path.is_file() else 0
            if not self.check_disk_space(target_path.parent, file_size):
                raise InsufficientSpaceError(
                    f"Insufficient disk space for {action}",
                    required_bytes=file_size,
                    available_bytes=self._get_available_space(target_path.parent),
                )

        # Check file lock
        if self.is_file_locked(source_path):
            errors.append(f"File is locked: {source_path}")

        # Check root directory target
        if target_path.parent == Path("/"):
            errors.append("Cannot create files in root directory")

        return ValidationResult(
            valid=len(errors) == 0,
            conflicts=conflicts,
            errors=errors,
            warnings=warnings,
        )

    def is_protected_path(self, path: Path) -> bool:
        """Check if path is a protected system path.

        Args:
            path: Path to check.

        Returns:
            True if path is protected.
        """
        resolved = path.resolve()
        home_resolved = Path.home().resolve()

        # First check if path is in allowed exceptions (e.g., /var/folders)
        for allowed in ALLOWED_PATHS:
            try:
                resolved.relative_to(allowed.resolve())
                return False  # Path is in an allowed exception
            except ValueError:
                continue

        # Check if path is under user's home directory
        # Home directory and its subdirectories are generally NOT protected
        # except for explicitly listed sensitive subdirs (.ssh, .gnupg, .config)
        try:
            resolved.relative_to(home_resolved)
            # Path is under home directory - check if it's a sensitive subdir
            for protected in self._protected_paths:
                protected_resolved = protected.resolve()
                # Only check home subdirs that are explicitly protected
                try:
                    protected_resolved.relative_to(home_resolved)
                    # This protected path is under home
                    try:
                        resolved.relative_to(protected_resolved)
                        # Path is under a protected home subdir
                        return True
                    except ValueError:
                        continue
                except ValueError:
                    continue
            # Path is under home but not under any protected subdir
            return False
        except ValueError:
            pass  # Path is not under home directory

        # Check if path exactly matches a protected path (excluding root for general paths)
        for protected in self._protected_paths:
            protected_resolved = protected.resolve()
            if resolved == protected_resolved:
                return True
            # Check if path is under a protected system path (not root)
            if protected_resolved != Path("/").resolve():
                try:
                    resolved.relative_to(protected_resolved)
                    return True
                except ValueError:
                    continue

        # Special case: root path itself is protected
        if resolved == Path("/").resolve():
            return True

        # Special case: direct children of root are protected (REQ-N-008)
        # This prevents creating files directly in root directory
        if resolved.parent == Path("/").resolve():
            return True

        return False

    def check_permissions(self, path: Path, action: str) -> bool:
        """Check if operation has required permissions.

        Args:
            path: Path to check.
            action: Action type.

        Returns:
            True if permissions are sufficient.
        """
        if not path.exists():
            return True  # Will be checked during execution

        if action in ("move", "delete", "rename"):
            return os.access(path, os.W_OK)
        elif action == "copy":
            return os.access(path, os.R_OK)
        return True

    def check_disk_space(self, target_dir: Path, required_bytes: int) -> bool:
        """Check if sufficient disk space is available.

        Args:
            target_dir: Target directory.
            required_bytes: Required space in bytes.

        Returns:
            True if sufficient space available.
        """
        available = self._get_available_space(target_dir)
        # Require 10% buffer
        return available >= required_bytes * 1.1

    def is_file_locked(self, path: Path) -> bool:
        """Check if file is locked by another process.

        Args:
            path: Path to check.

        Returns:
            True if file is locked.
        """
        if not path.exists() or not path.is_file():
            return False
        try:
            with open(path, "a"):
                pass
            return False
        except OSError:
            return True

    def _is_hidden_file(self, path: Path) -> bool:
        """Check if file is hidden (starts with .).

        Args:
            path: Path to check.

        Returns:
            True if file name starts with a dot.
        """
        return path.name.startswith(".")

    def _get_available_space(self, path: Path) -> int:
        """Get available disk space in bytes.

        Args:
            path: Path to check.

        Returns:
            Available disk space in bytes, or 0 if unable to determine.
        """
        try:
            check_path = path if path.exists() else path.parent
            # Keep going up until we find an existing path
            while not check_path.exists() and check_path != check_path.parent:
                check_path = check_path.parent
            if check_path.exists():
                stat = shutil.disk_usage(check_path)
                return stat.free
            return 0
        except (OSError, FileNotFoundError):
            return 0


__all__ = [
    "SafetyValidator",
    "PROTECTED_PATHS",
]
