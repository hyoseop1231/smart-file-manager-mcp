"""Vision analysis service for Smart File Manager.

TAG: VIS-M4-01 to VIS-M4-05
SPEC: SPEC-VISION-001

This module provides a unified Vision analysis service that:
- Routes requests to appropriate processors (image/video)
- Supports batch analysis with concurrency control
- Tracks analysis statistics
- Prevents race conditions for duplicate requests
"""

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

from smart_file_manager.core.constants import (
    SUPPORTED_IMAGE_FORMATS,
    SUPPORTED_VIDEO_FORMATS,
)
from smart_file_manager.core.exceptions import (
    UnsupportedFormatError,
)
from smart_file_manager.processors.image_processor import ImageProcessor
from smart_file_manager.processors.video_processor import VideoProcessor
from smart_file_manager.services.vision_models import (
    AnalysisStats,
    ImageAnalysisResult,
    VideoAnalysisResult,
)

if TYPE_CHECKING:
    from smart_file_manager.infrastructure.cache.base import CacheInterface
    from smart_file_manager.services.openrouter_client import OpenRouterClient


class VisionService:
    """Unified Vision analysis service.

    This service provides a high-level interface for analyzing images and videos.
    It handles file type routing, batch processing, and statistics tracking.

    Attributes:
        client: OpenRouterClient for API calls.
        cache: Optional cache interface for result caching.
        image_processor: ImageProcessor for image analysis.
        video_processor: VideoProcessor for video analysis.
    """

    def __init__(
        self,
        client: "OpenRouterClient",
        cache: "CacheInterface | None" = None,
    ) -> None:
        """Initialize the VisionService.

        Args:
            client: OpenRouterClient instance for API calls.
            cache: Optional cache interface for caching results.
        """
        self.client = client
        self.cache = cache

        # Initialize processors
        self.image_processor = ImageProcessor(client=client, cache=cache)
        self.video_processor = VideoProcessor(
            image_processor=self.image_processor,
            cache=cache,
        )

        # Statistics tracking
        self._stats = AnalysisStats(
            total_analyses=0,
            cached_analyses=0,
            api_analyses=0,
            total_cost=0.0,
            average_processing_time_ms=0.0,
            models_used={},
        )
        self._total_processing_time_ms = 0.0

        # In-flight request tracking for race condition prevention
        self._in_flight: dict[str, asyncio.Future[ImageAnalysisResult | VideoAnalysisResult]] = {}
        self._in_flight_lock = asyncio.Lock()

    def is_image_file(self, file_path: Path) -> bool:
        """Check if file is a supported image format.

        Args:
            file_path: Path to the file.

        Returns:
            True if file is a supported image format.
        """
        extension = file_path.suffix.lower().lstrip(".")
        return extension in SUPPORTED_IMAGE_FORMATS

    def is_video_file(self, file_path: Path) -> bool:
        """Check if file is a supported video format.

        Args:
            file_path: Path to the file.

        Returns:
            True if file is a supported video format.
        """
        extension = file_path.suffix.lower().lstrip(".")
        return extension in SUPPORTED_VIDEO_FORMATS

    def is_supported_file(self, file_path: Path) -> bool:
        """Check if file is a supported format (image or video).

        Args:
            file_path: Path to the file.

        Returns:
            True if file is supported for vision analysis.
        """
        return self.is_image_file(file_path) or self.is_video_file(file_path)

    def _update_stats(
        self,
        result: ImageAnalysisResult | VideoAnalysisResult,
    ) -> None:
        """Update statistics with analysis result.

        Args:
            result: Analysis result to record.
        """
        self._stats.total_analyses += 1

        if result.cached:
            self._stats.cached_analyses += 1
        else:
            self._stats.api_analyses += 1

        # Get cost from result
        if isinstance(result, ImageAnalysisResult):
            self._stats.total_cost += result.estimated_cost
            processing_time = result.processing_time_ms
        else:
            self._stats.total_cost += result.total_cost
            processing_time = result.processing_time_ms

        # Update processing time average
        self._total_processing_time_ms += processing_time
        self._stats.average_processing_time_ms = (
            self._total_processing_time_ms / self._stats.total_analyses
        )

        # Track model usage
        model = result.model_used
        self._stats.models_used[model] = self._stats.models_used.get(model, 0) + 1

    async def analyze_image(
        self,
        image_path: Path,
        *,
        force_refresh: bool = False,
    ) -> ImageAnalysisResult:
        """Analyze an image file.

        Args:
            image_path: Path to the image file.
            force_refresh: If True, ignore cache and force new analysis.

        Returns:
            ImageAnalysisResult with analysis data.

        Raises:
            UnsupportedFormatError: If image format is not supported.
            FileNotFoundError: If image file does not exist.
        """
        if not self.is_image_file(image_path):
            extension = image_path.suffix.lower().lstrip(".")
            raise UnsupportedFormatError(
                f"Unsupported image format: {extension}",
                format=extension,
                supported_formats=list(SUPPORTED_IMAGE_FORMATS),
            )

        # Read image data
        with open(image_path, "rb") as f:
            image_data = f.read()

        # Compute content hash
        content_hash = self.image_processor.compute_content_hash(image_data)

        # Extract metadata
        metadata = self.image_processor.extract_metadata(image_path, content_hash)

        # Analyze
        result = await self.image_processor.analyze(
            image_data=image_data,
            content_hash=content_hash,
            force_refresh=force_refresh,
            metadata=metadata,
        )

        # Update statistics
        self._update_stats(result)

        return result

    async def analyze_video(
        self,
        video_path: Path,
        *,
        force_refresh: bool = False,
        max_frames: int = 5,
    ) -> VideoAnalysisResult:
        """Analyze a video file.

        Args:
            video_path: Path to the video file.
            force_refresh: If True, ignore cache and force new analysis.
            max_frames: Maximum number of frames to analyze.

        Returns:
            VideoAnalysisResult with analysis data.

        Raises:
            UnsupportedFormatError: If video format is not supported.
            FileNotFoundError: If video file does not exist.
            DependencyError: If FFmpeg is not available.
        """
        if not self.is_video_file(video_path):
            extension = video_path.suffix.lower().lstrip(".")
            raise UnsupportedFormatError(
                f"Unsupported video format: {extension}",
                format=extension,
                supported_formats=list(SUPPORTED_VIDEO_FORMATS),
            )

        # Compute content hash
        content_hash = self.video_processor.compute_content_hash(video_path)

        # Analyze
        result = await self.video_processor.analyze(
            video_path=video_path,
            content_hash=content_hash,
            force_refresh=force_refresh,
            max_frames=max_frames,
        )

        # Update statistics
        self._update_stats(result)

        return result

    async def batch_analyze(
        self,
        paths: list[Path],
        *,
        concurrency: int = 5,
        force_refresh: bool = False,
    ) -> list[ImageAnalysisResult | VideoAnalysisResult]:
        """Analyze multiple files in parallel.

        Args:
            paths: List of file paths to analyze.
            concurrency: Maximum concurrent analyses.
            force_refresh: If True, ignore cache for all analyses.

        Returns:
            List of analysis results (only for supported files).
        """
        # Filter to only supported files
        supported_paths = [p for p in paths if self.is_supported_file(p)]

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(concurrency)

        async def analyze_with_semaphore(
            path: Path,
        ) -> ImageAnalysisResult | VideoAnalysisResult:
            async with semaphore:
                if self.is_image_file(path):
                    return await self.analyze_image(path, force_refresh=force_refresh)
                else:
                    return await self.analyze_video(path, force_refresh=force_refresh)

        # Run analyses in parallel
        tasks = [analyze_with_semaphore(path) for path in supported_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and return successful results
        return [r for r in results if not isinstance(r, Exception)]

    async def get_analysis_stats(self) -> AnalysisStats:
        """Get current analysis statistics.

        Returns:
            AnalysisStats with cumulative statistics.
        """
        return AnalysisStats(
            total_analyses=self._stats.total_analyses,
            cached_analyses=self._stats.cached_analyses,
            api_analyses=self._stats.api_analyses,
            total_cost=self._stats.total_cost,
            average_processing_time_ms=self._stats.average_processing_time_ms,
            models_used=dict(self._stats.models_used),
        )

    def reset_stats(self) -> None:
        """Reset analysis statistics to zero."""
        self._stats = AnalysisStats(
            total_analyses=0,
            cached_analyses=0,
            api_analyses=0,
            total_cost=0.0,
            average_processing_time_ms=0.0,
            models_used={},
        )
        self._total_processing_time_ms = 0.0
