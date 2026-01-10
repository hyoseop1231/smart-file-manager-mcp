"""Progress tracking module for batch operations.

TAG: ORG-001-P1
SPEC: SPEC-ORG-001

This module provides the ProgressTracker class for tracking batch operation
progress, calculating ETA, and invoking progress callbacks.

REQ-E-005: Batch processing progress callback invocation
REQ-O-001: Progress tracking and reporting (percentage, current_file, eta)
"""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Awaitable, Callable
from datetime import datetime

from smart_file_manager.organization.models import Progress


class ProgressTracker:
    """Batch operation progress tracker.

    Tracks progress of batch file operations, calculates ETA based on
    moving average of processing times, and invokes callbacks on updates.

    REQ-E-005: Progress callback support for batch processing
    REQ-O-001: Progress tracking with percentage, ETA calculation

    Attributes:
        ETA_SAMPLE_SIZE: Number of recent samples used for ETA calculation.

    Example:
        tracker = ProgressTracker(total=100, callback=progress_callback)
        await tracker.start()
        for file in files:
            await process_file(file)
            await tracker.update(current_file=str(file))
        await tracker.complete()
    """

    ETA_SAMPLE_SIZE = 10

    def __init__(
        self,
        total: int,
        callback: Callable[[Progress], Awaitable[None]] | None = None,
    ) -> None:
        """Initialize ProgressTracker.

        Args:
            total: Total number of items to process.
            callback: Optional async callback invoked on each progress update.
        """
        self._total = total
        self._callback = callback
        self._current = 0
        self._current_file: str = ""

        # Timing for ETA calculation
        self._start_time: datetime | None = None
        self._processing_times: deque[float] = deque(maxlen=self.ETA_SAMPLE_SIZE)
        self._last_update_time: datetime | None = None

        # State tracking
        self._is_running = False
        self._is_completed = False
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Start progress tracking.

        Records the start time and sets the running state.
        Should be called before any update() calls.
        """
        async with self._lock:
            self._start_time = datetime.now()
            self._last_update_time = self._start_time
            self._is_running = True
            self._is_completed = False

    async def update(
        self,
        current: int | None = None,
        current_file: str | None = None,
    ) -> Progress:
        """Update progress state.

        Records processing time for ETA calculation and invokes the callback.

        Args:
            current: Current completed item count. If None, increments by 1.
            current_file: Path of the file currently being processed.

        Returns:
            Current Progress object reflecting the updated state.
        """
        async with self._lock:
            now = datetime.now()

            # Record processing time for ETA calculation
            if self._last_update_time:
                elapsed = (now - self._last_update_time).total_seconds() * 1000
                self._processing_times.append(elapsed)

            # Update current state
            if current is not None:
                self._current = current
            else:
                self._current += 1

            if current_file is not None:
                self._current_file = current_file

            self._last_update_time = now

            # Create Progress object
            progress = self._create_progress()

            # Invoke callback if provided
            if self._callback:
                await self._callback(progress)

            return progress

    async def complete(self) -> Progress:
        """Mark tracking as complete.

        Sets current to total, updates state flags, and invokes callback.

        Returns:
            Final Progress object with 100% completion.
        """
        async with self._lock:
            self._current = self._total
            self._is_running = False
            self._is_completed = True

            progress = self._create_progress()

            if self._callback:
                await self._callback(progress)

            return progress

    def _create_progress(self) -> Progress:
        """Create Progress object from current state.

        Returns:
            Progress object reflecting current tracker state.
        """
        percentage = (self._current / self._total * 100) if self._total > 0 else 100.0
        eta = self._calculate_eta()
        elapsed = self._calculate_elapsed()

        return Progress(
            current=self._current,
            total=self._total,
            current_file=self._current_file,
            percentage=percentage,
            eta_seconds=eta,
            elapsed_seconds=elapsed,
        )

    def _calculate_eta(self) -> float | None:
        """Calculate estimated time remaining.

        Uses moving average of recent processing times to estimate
        remaining time.

        Returns:
            Estimated remaining time in seconds, or None if completed
            or no samples available.
        """
        if not self._processing_times or self._current >= self._total:
            return None

        # Average processing time in milliseconds
        avg_time_ms = sum(self._processing_times) / len(self._processing_times)

        # Remaining items
        remaining = self._total - self._current

        # ETA in seconds
        eta_seconds = (avg_time_ms * remaining) / 1000
        return eta_seconds

    def _calculate_elapsed(self) -> float:
        """Calculate elapsed time since start.

        Returns:
            Elapsed time in seconds, or 0.0 if not started.
        """
        if self._start_time is None:
            return 0.0
        return (datetime.now() - self._start_time).total_seconds()

    def get_progress(self) -> Progress:
        """Get current Progress object synchronously.

        Returns:
            Progress object reflecting current tracker state.
        """
        return self._create_progress()

    @property
    def is_running(self) -> bool:
        """Check if tracking is currently in progress.

        Returns:
            True if start() was called and complete() has not been called.
        """
        return self._is_running

    @property
    def is_completed(self) -> bool:
        """Check if tracking has been completed.

        Returns:
            True if complete() has been called.
        """
        return self._is_completed

    @property
    def current(self) -> int:
        """Get current completed item count.

        Returns:
            Number of items processed so far.
        """
        return self._current

    @property
    def total(self) -> int:
        """Get total item count.

        Returns:
            Total number of items to process.
        """
        return self._total

    @property
    def percentage(self) -> float:
        """Get current completion percentage.

        Returns:
            Percentage from 0.0 to 100.0.
        """
        return (self._current / self._total * 100) if self._total > 0 else 100.0
