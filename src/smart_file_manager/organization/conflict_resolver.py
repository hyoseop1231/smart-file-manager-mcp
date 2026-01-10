"""Conflict resolution module for file organization.

TAG: ORG-001-C1
SPEC: SPEC-ORG-001

This module provides conflict detection and resolution functionality
for file organization operations.

REQ-E-002: Target path conflict detection
REQ-S-003: Strategy-based conflict resolution
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from datetime import datetime
from pathlib import Path

from smart_file_manager.core.exceptions import ConflictError
from smart_file_manager.organization.models import (
    Conflict,
    ConflictStrategy,
    OrganizationAction,
)


class ConflictResolver:
    """File conflict detection and resolution class.

    This class handles detecting file conflicts when a target path
    already exists and resolving them based on configured strategies.

    Attributes:
        MAX_FILENAME_LENGTH: Maximum allowed filename length (255 chars).

    REQ-E-002: Conflict detection
    REQ-S-003: Strategy-based conflict resolution
    """

    MAX_FILENAME_LENGTH = 255

    def __init__(
        self,
        default_strategy: ConflictStrategy = ConflictStrategy.SKIP,
        user_prompt_callback: Callable[[Conflict], Awaitable[ConflictStrategy]] | None = None,
    ) -> None:
        """Initialize ConflictResolver.

        Args:
            default_strategy: Default conflict resolution strategy.
            user_prompt_callback: Callback function for ASK_USER strategy.
        """
        self._default_strategy = default_strategy
        self._user_prompt_callback = user_prompt_callback

    async def detect_conflict(self, target_path: Path) -> Conflict | None:
        """Detect if a conflict exists at the target path.

        Args:
            target_path: Path to check for conflicts.

        Returns:
            Conflict object if path exists, None otherwise.
        """
        if target_path.exists():
            return Conflict(
                source_path=Path(""),
                target_path=target_path,
                reason="File already exists",
                suggestions=["Skip", "Overwrite", "Rename"],
            )
        return None

    async def detect_conflicts_for_action(
        self,
        action: OrganizationAction,
    ) -> Conflict | None:
        """Detect conflict for an OrganizationAction.

        Args:
            action: The organization action to check.

        Returns:
            Conflict object with source path if conflict exists, None otherwise.
        """
        if action.target_path is None:
            return None

        conflict = await self.detect_conflict(action.target_path)
        if conflict:
            return Conflict(
                source_path=action.source_path,
                target_path=conflict.target_path,
                reason=conflict.reason,
                suggestions=conflict.suggestions,
            )
        return None

    async def resolve(
        self,
        conflict: Conflict,
        strategy: ConflictStrategy | None = None,
    ) -> tuple[Path, bool]:
        """Resolve a conflict using the specified or default strategy.

        Args:
            conflict: The conflict to resolve.
            strategy: Strategy to use (uses default if None).

        Returns:
            Tuple of (final target path, should_proceed).
            If should_proceed is False, the operation should be skipped.

        Raises:
            ConflictError: If ASK_USER strategy is used without callback,
                or if an invalid strategy is provided.
        """
        strategy = strategy or self._default_strategy

        if strategy == ConflictStrategy.SKIP:
            return conflict.target_path, False

        elif strategy == ConflictStrategy.OVERWRITE:
            return conflict.target_path, True

        elif strategy == ConflictStrategy.RENAME_SUFFIX:
            new_path = self.generate_unique_name(
                conflict.target_path,
                use_timestamp=False,
            )
            return new_path, True

        elif strategy == ConflictStrategy.RENAME_TIMESTAMP:
            new_path = self.generate_unique_name(
                conflict.target_path,
                use_timestamp=True,
            )
            return new_path, True

        elif strategy == ConflictStrategy.ASK_USER:
            if self._user_prompt_callback is None:
                raise ConflictError(
                    f"ASK_USER strategy requires user_prompt_callback: {conflict.target_path}"
                )
            user_strategy = await self._user_prompt_callback(conflict)
            if user_strategy == ConflictStrategy.ASK_USER:
                raise ConflictError("User must select a valid strategy (not ASK_USER)")
            return await self.resolve(conflict, user_strategy)

        raise ConflictError(f"Unsupported conflict resolution strategy: {strategy}")

    def generate_unique_name(
        self,
        target_path: Path,
        use_timestamp: bool = False,
    ) -> Path:
        """Generate a unique filename that doesn't conflict.

        Args:
            target_path: Original target path.
            use_timestamp: If True, use timestamp suffix; otherwise use numeric.

        Returns:
            A new path that doesn't exist.

        Raises:
            ConflictError: If unable to generate a unique name.
        """
        parent = target_path.parent
        stem = target_path.stem
        suffix = target_path.suffix

        if use_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_stem = self._truncate_stem(stem, len(f"_{timestamp}{suffix}"))
            new_name = f"{new_stem}_{timestamp}{suffix}"
            new_path = parent / new_name

            counter = 1
            while new_path.exists():
                ms_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                new_stem = self._truncate_stem(stem, len(f"_{ms_timestamp}{suffix}"))
                new_name = f"{new_stem}_{ms_timestamp}{suffix}"
                new_path = parent / new_name
                counter += 1
                if counter > 100:
                    raise ConflictError(f"Unable to generate unique filename: {target_path}")
            return new_path
        else:
            base_stem = self._extract_base_stem(stem)

            counter = 1
            while True:
                new_stem = self._truncate_stem(base_stem, len(f"_{counter}{suffix}"))
                new_name = f"{new_stem}_{counter}{suffix}"
                new_path = parent / new_name
                if not new_path.exists():
                    return new_path
                counter += 1
                if counter > 10000:
                    raise ConflictError(f"Unable to generate unique filename: {target_path}")

    def _extract_base_stem(self, stem: str) -> str:
        """Extract base stem by removing existing numeric suffix.

        Examples:
            "file_1" -> "file"
            "document_23" -> "document"
            "report_final" -> "report_final" (no numeric suffix)

        Args:
            stem: The filename stem to process.

        Returns:
            The base stem without numeric suffix.
        """
        pattern = r"^(.+)_\d+$"
        match = re.match(pattern, stem)
        if match:
            return match.group(1)
        return stem

    def _truncate_stem(self, stem: str, reserved_length: int) -> str:
        """Truncate stem to ensure filename doesn't exceed max length.

        Args:
            stem: The stem to potentially truncate.
            reserved_length: Space reserved for suffix and extension.

        Returns:
            Truncated stem if necessary.
        """
        max_stem_length = self.MAX_FILENAME_LENGTH - reserved_length
        if len(stem) > max_stem_length:
            return stem[:max_stem_length]
        return stem

    @property
    def default_strategy(self) -> ConflictStrategy:
        """Get the default conflict resolution strategy."""
        return self._default_strategy

    @default_strategy.setter
    def default_strategy(self, value: ConflictStrategy) -> None:
        """Set the default conflict resolution strategy."""
        self._default_strategy = value


__all__ = ["ConflictResolver"]
