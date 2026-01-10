"""Tests for ProgressTracker.

TAG: ORG-001-T6
SPEC: SPEC-ORG-001

TDD tests for ProgressTracker class that tracks batch operation progress
and calculates ETA.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from smart_file_manager.organization.progress_tracker import ProgressTracker

from smart_file_manager.organization.models import Progress


class TestProgressTrackerBasic:
    """Basic initialization and state tests for ProgressTracker."""

    def test_init_with_total(self) -> None:
        """Test ProgressTracker initializes with correct total value."""
        tracker = ProgressTracker(total=100)

        assert tracker.total == 100
        assert tracker.current == 0
        assert tracker.is_running is False
        assert tracker.is_completed is False

    def test_init_with_callback(self) -> None:
        """Test ProgressTracker initializes with callback function."""
        callback = AsyncMock()
        tracker = ProgressTracker(total=50, callback=callback)

        assert tracker.total == 50
        assert tracker._callback is callback

    @pytest.mark.asyncio
    async def test_start_sets_running_state(self) -> None:
        """Test start() sets running state to True."""
        tracker = ProgressTracker(total=10)

        await tracker.start()

        assert tracker.is_running is True
        assert tracker.is_completed is False

    @pytest.mark.asyncio
    async def test_start_records_start_time(self) -> None:
        """Test start() records the start time."""
        tracker = ProgressTracker(total=10)

        before = datetime.now()
        await tracker.start()
        after = datetime.now()

        assert tracker._start_time is not None
        assert before <= tracker._start_time <= after


class TestProgressUpdate:
    """Tests for progress update functionality."""

    @pytest.mark.asyncio
    async def test_update_increments_current(self) -> None:
        """Test update() increments current count by 1."""
        tracker = ProgressTracker(total=10)
        await tracker.start()

        await tracker.update()
        assert tracker.current == 1

        await tracker.update()
        assert tracker.current == 2

    @pytest.mark.asyncio
    async def test_update_with_explicit_current(self) -> None:
        """Test update() with explicit current value."""
        tracker = ProgressTracker(total=10)
        await tracker.start()

        await tracker.update(current=5)
        assert tracker.current == 5

        await tracker.update(current=8)
        assert tracker.current == 8

    @pytest.mark.asyncio
    async def test_update_with_current_file(self) -> None:
        """Test update() sets current_file correctly."""
        tracker = ProgressTracker(total=10)
        await tracker.start()

        progress = await tracker.update(current_file="/path/to/file.txt")

        assert progress.current_file == "/path/to/file.txt"

    @pytest.mark.asyncio
    async def test_update_calls_callback(self) -> None:
        """Test update() calls the callback with Progress object."""
        callback = AsyncMock()
        tracker = ProgressTracker(total=10, callback=callback)
        await tracker.start()

        await tracker.update(current_file="/test/file.txt")

        callback.assert_called_once()
        call_arg = callback.call_args[0][0]
        assert isinstance(call_arg, Progress)
        assert call_arg.current == 1
        assert call_arg.current_file == "/test/file.txt"

    @pytest.mark.asyncio
    async def test_update_returns_progress(self) -> None:
        """Test update() returns a Progress object."""
        tracker = ProgressTracker(total=10)
        await tracker.start()

        progress = await tracker.update(current_file="/test/file.txt")

        assert isinstance(progress, Progress)
        assert progress.current == 1
        assert progress.total == 10
        assert progress.current_file == "/test/file.txt"


class TestProgressPercentage:
    """Tests for percentage calculation."""

    @pytest.mark.asyncio
    async def test_percentage_calculation(self) -> None:
        """Test percentage is calculated correctly."""
        tracker = ProgressTracker(total=10)
        await tracker.start()

        await tracker.update(current=5)
        assert tracker.percentage == 50.0

        await tracker.update(current=7)
        assert tracker.percentage == 70.0

    @pytest.mark.asyncio
    async def test_percentage_zero_total(self) -> None:
        """Test percentage returns 100% when total is 0."""
        tracker = ProgressTracker(total=0)
        await tracker.start()

        assert tracker.percentage == 100.0

    @pytest.mark.asyncio
    async def test_percentage_at_completion(self) -> None:
        """Test percentage is 100% when completed."""
        tracker = ProgressTracker(total=5)
        await tracker.start()

        for _ in range(5):
            await tracker.update()

        assert tracker.percentage == 100.0


class TestProgressETA:
    """Tests for ETA calculation."""

    @pytest.mark.asyncio
    async def test_eta_calculation(self) -> None:
        """Test ETA is calculated based on processing times."""
        tracker = ProgressTracker(total=10)
        await tracker.start()

        # Simulate updates with consistent timing
        for i in range(3):
            await asyncio.sleep(0.01)  # 10ms per item
            await tracker.update()

        progress = tracker.get_progress()

        # ETA should be calculated for remaining items
        assert progress.eta_seconds is not None
        assert progress.eta_seconds > 0

    @pytest.mark.asyncio
    async def test_eta_with_varying_times(self) -> None:
        """Test ETA uses moving average of processing times."""
        tracker = ProgressTracker(total=20)
        await tracker.start()

        # Simulate varying processing times
        for i in range(5):
            await asyncio.sleep(0.005 + (i * 0.002))  # 5-13ms varying
            await tracker.update()

        progress = tracker.get_progress()

        # ETA should reflect the average of recent times
        assert progress.eta_seconds is not None
        remaining = 20 - 5
        # ETA should be roughly remaining * avg_time
        assert progress.eta_seconds > 0

    @pytest.mark.asyncio
    async def test_eta_none_when_completed(self) -> None:
        """Test ETA is None when all items are processed."""
        tracker = ProgressTracker(total=3)
        await tracker.start()

        for _ in range(3):
            await tracker.update()

        progress = tracker.get_progress()

        assert progress.eta_seconds is None


class TestProgressComplete:
    """Tests for completion functionality."""

    @pytest.mark.asyncio
    async def test_complete_sets_state(self) -> None:
        """Test complete() sets is_completed to True and is_running to False."""
        tracker = ProgressTracker(total=10)
        await tracker.start()

        await tracker.update(current=5)
        progress = await tracker.complete()

        assert tracker.is_completed is True
        assert tracker.is_running is False
        assert tracker.current == 10
        assert progress.percentage == 100.0

    @pytest.mark.asyncio
    async def test_complete_calls_callback(self) -> None:
        """Test complete() calls the callback with final Progress."""
        callback = AsyncMock()
        tracker = ProgressTracker(total=10, callback=callback)
        await tracker.start()

        await tracker.complete()

        # Callback should be called with completion progress
        last_call = callback.call_args[0][0]
        assert isinstance(last_call, Progress)
        assert last_call.current == 10
        assert last_call.percentage == 100.0


class TestProgressElapsed:
    """Tests for elapsed time tracking."""

    @pytest.mark.asyncio
    async def test_elapsed_seconds_calculation(self) -> None:
        """Test elapsed_seconds is calculated correctly."""
        tracker = ProgressTracker(total=10)
        await tracker.start()

        await asyncio.sleep(0.05)  # 50ms
        progress = tracker.get_progress()

        assert progress.elapsed_seconds >= 0.05
        assert progress.elapsed_seconds < 0.2  # Should be reasonable

    @pytest.mark.asyncio
    async def test_elapsed_zero_before_start(self) -> None:
        """Test elapsed_seconds is 0 before start."""
        tracker = ProgressTracker(total=10)

        progress = tracker.get_progress()

        assert progress.elapsed_seconds == 0.0


class TestGetProgress:
    """Tests for get_progress() method."""

    def test_get_progress_returns_progress_object(self) -> None:
        """Test get_progress() returns a Progress object."""
        tracker = ProgressTracker(total=10)

        progress = tracker.get_progress()

        assert isinstance(progress, Progress)
        assert progress.current == 0
        assert progress.total == 10

    @pytest.mark.asyncio
    async def test_get_progress_reflects_current_state(self) -> None:
        """Test get_progress() reflects current tracker state."""
        tracker = ProgressTracker(total=10)
        await tracker.start()

        await tracker.update(current=3, current_file="/test.txt")
        progress = tracker.get_progress()

        assert progress.current == 3
        assert progress.total == 10
        assert progress.percentage == 30.0
        assert progress.current_file == "/test.txt"
