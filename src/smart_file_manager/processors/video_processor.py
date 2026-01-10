"""Video processor for Vision analysis.

TAG: VIS-M3-01 to VIS-M3-07
SPEC: SPEC-VISION-001

This module provides video processing capabilities including:
- Format validation
- FFmpeg-based keyframe extraction
- Representative frame selection
- Video metadata extraction
- Integration with ImageProcessor for frame analysis
"""

import hashlib
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING

from smart_file_manager.core.constants import (
    KEYFRAME_INTERVALS,
    MAX_REPRESENTATIVE_FRAMES,
    SUPPORTED_VIDEO_FORMATS,
    VISION_CACHE_KEY_PREFIX_VIDEO,
    VISION_CACHE_TTL_SECONDS,
)
from smart_file_manager.core.exceptions import (
    DependencyError,
    VideoProcessingError,
)
from smart_file_manager.services.vision_models import (
    FrameAnalysisResult,
    SceneChange,
    VideoAnalysisResult,
    VideoMetadata,
)

if TYPE_CHECKING:
    from smart_file_manager.infrastructure.cache.base import CacheInterface
    from smart_file_manager.processors.image_processor import ImageProcessor


class VideoProcessor:
    """Video processor for Vision analysis.

    This class handles video processing including format validation,
    keyframe extraction using FFmpeg, and frame analysis using ImageProcessor.

    Attributes:
        image_processor: ImageProcessor for analyzing extracted frames.
        cache: Optional cache interface for result caching.
    """

    def __init__(
        self,
        image_processor: "ImageProcessor",
        cache: "CacheInterface | None" = None,
    ) -> None:
        """Initialize the VideoProcessor.

        Args:
            image_processor: ImageProcessor instance for frame analysis.
            cache: Optional cache interface for caching results.
        """
        self.image_processor = image_processor
        self.cache = cache

    def validate_format(self, video_path: Path) -> bool:
        """Validate if the video format is supported.

        Args:
            video_path: Path to the video file.

        Returns:
            True if format is supported, False otherwise.
        """
        extension = video_path.suffix.lower().lstrip(".")
        return extension in SUPPORTED_VIDEO_FORMATS

    def check_ffmpeg_available(self) -> bool:
        """Check if FFmpeg is available on the system.

        Returns:
            True if FFmpeg is available, False otherwise.
        """
        return shutil.which("ffmpeg") is not None

    def check_ffprobe_available(self) -> bool:
        """Check if FFprobe is available on the system.

        Returns:
            True if FFprobe is available, False otherwise.
        """
        return shutil.which("ffprobe") is not None

    def compute_content_hash(self, video_path: Path, chunk_size: int = 8192) -> str:
        """Compute SHA256 hash of video file.

        Args:
            video_path: Path to the video file.
            chunk_size: Size of chunks to read at a time.

        Returns:
            Hexadecimal hash string.
        """
        sha256_hash = hashlib.sha256()
        with open(video_path, "rb") as f:
            while chunk := f.read(chunk_size):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def calculate_keyframe_interval(
        self,
        duration_seconds: float,
    ) -> tuple[int, int]:
        """Calculate appropriate keyframe interval based on video duration.

        Args:
            duration_seconds: Video duration in seconds.

        Returns:
            Tuple of (interval_seconds, max_frames).
        """
        for max_duration, (interval, max_frames) in sorted(KEYFRAME_INTERVALS.items()):
            if duration_seconds <= max_duration:
                return interval, max_frames

        # For videos longer than all defined thresholds, use the largest interval
        last_key = max(KEYFRAME_INTERVALS.keys())
        return KEYFRAME_INTERVALS[last_key]

    def extract_keyframes(
        self,
        video_path: Path,
        interval: float,
        output_dir: Path | None = None,
    ) -> list[bytes]:
        """Extract keyframes from video using FFmpeg.

        Args:
            video_path: Path to the video file.
            interval: Interval in seconds between keyframes.
            output_dir: Directory for temporary frame files.

        Returns:
            List of frame image bytes.

        Raises:
            DependencyError: If FFmpeg is not available.
            VideoProcessingError: If extraction fails.
        """
        if not self.check_ffmpeg_available():
            raise DependencyError(
                "FFmpeg is required for video processing",
                dependency_name="ffmpeg",
            )

        # Create temporary directory if not provided
        use_temp_dir = output_dir is None
        if use_temp_dir:
            temp_dir = tempfile.mkdtemp(prefix="vision_frames_")
            output_dir = Path(temp_dir)
        else:
            output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Build FFmpeg command
            output_pattern = output_dir / "frame_%04d.jpg"
            cmd = [
                "ffmpeg",
                "-i",
                str(video_path),
                "-vf",
                f"fps=1/{interval}",
                "-q:v",
                "2",  # High quality JPEG
                "-y",  # Overwrite output files
                str(output_pattern),
            ]

            # Run FFmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode != 0:
                raise VideoProcessingError(
                    f"FFmpeg extraction failed: {result.stderr}",
                    video_path=str(video_path),
                )

            # Read extracted frames
            frames: list[bytes] = []
            for frame_path in sorted(output_dir.glob("frame_*.jpg")):
                with open(frame_path, "rb") as f:
                    frames.append(f.read())

            return frames

        finally:
            # Clean up temporary directory
            if use_temp_dir and output_dir.exists():
                import shutil as shutil_cleanup

                shutil_cleanup.rmtree(output_dir, ignore_errors=True)

    def select_representative_frames(
        self,
        frames: list[bytes],
        max_count: int = MAX_REPRESENTATIVE_FRAMES,
    ) -> list[bytes]:
        """Select representative frames from extracted keyframes.

        Uses a simple uniform sampling strategy to select frames
        that are evenly distributed throughout the video.

        Args:
            frames: List of frame image bytes.
            max_count: Maximum number of frames to select.

        Returns:
            List of selected frame bytes.
        """
        if not frames:
            return []

        if len(frames) <= max_count:
            return frames

        # Uniform sampling - select evenly distributed frames
        step = len(frames) / max_count
        selected_indices = [int(i * step) for i in range(max_count)]

        return [frames[i] for i in selected_indices]

    def get_video_metadata(
        self,
        video_path: Path,
        content_hash: str,
    ) -> VideoMetadata:
        """Extract video metadata using FFprobe.

        Args:
            video_path: Path to the video file.
            content_hash: Pre-computed content hash.

        Returns:
            VideoMetadata with extracted information.

        Raises:
            DependencyError: If FFprobe is not available.
            VideoProcessingError: If metadata extraction fails.
        """
        if not self.check_ffprobe_available():
            raise DependencyError(
                "FFprobe is required for video metadata extraction",
                dependency_name="ffprobe",
            )

        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(video_path),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            raise VideoProcessingError(
                f"FFprobe failed: {result.stderr}",
                video_path=str(video_path),
            )

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise VideoProcessingError(
                f"Failed to parse FFprobe output: {e}",
                video_path=str(video_path),
            ) from e

        # Find video stream
        video_stream = None
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
                break

        if video_stream is None:
            raise VideoProcessingError(
                "No video stream found",
                video_path=str(video_path),
            )

        # Parse frame rate
        fps = 30.0  # Default
        r_frame_rate = video_stream.get("r_frame_rate", "30/1")
        try:
            num, denom = map(int, r_frame_rate.split("/"))
            fps = num / denom if denom != 0 else 30.0
        except (ValueError, ZeroDivisionError):
            pass

        format_info = data.get("format", {})

        return VideoMetadata(
            width=int(video_stream.get("width", 0)),
            height=int(video_stream.get("height", 0)),
            duration_seconds=float(format_info.get("duration", 0)),
            fps=fps,
            codec=video_stream.get("codec_name", "unknown"),
            size_bytes=int(format_info.get("size", 0)),
            content_hash=content_hash,
        )

    def _generate_summary(
        self,
        frame_analyses: list[FrameAnalysisResult],
        metadata: VideoMetadata,
    ) -> str:
        """Generate a summary from frame analyses.

        Args:
            frame_analyses: List of analyzed frames.
            metadata: Video metadata.

        Returns:
            Summary string describing the video.
        """
        if not frame_analyses:
            return f"Video ({metadata.codec}) with duration {metadata.duration_seconds:.1f}s"

        # Collect unique scenes and objects
        scenes = set()
        objects = set()
        for fa in frame_analyses:
            scenes.add(fa.analysis.scene)
            for obj in fa.analysis.objects:
                objects.add(obj.name)

        scene_str = ", ".join(sorted(scenes)) if scenes else "unknown"
        objects_str = ", ".join(sorted(list(objects)[:5])) if objects else "various elements"

        return (
            f"Video showing {scene_str} scenes with {objects_str}. "
            f"Duration: {metadata.duration_seconds:.1f}s, "
            f"Resolution: {metadata.width}x{metadata.height}."
        )

    def _detect_scene_changes(
        self,
        frame_analyses: list[FrameAnalysisResult],
    ) -> list[SceneChange]:
        """Detect scene changes from frame analyses.

        Args:
            frame_analyses: List of analyzed frames.

        Returns:
            List of detected scene changes.
        """
        scene_changes: list[SceneChange] = []

        for i in range(1, len(frame_analyses)):
            prev_scene = frame_analyses[i - 1].analysis.scene
            curr_scene = frame_analyses[i].analysis.scene

            if prev_scene != curr_scene:
                scene_changes.append(
                    SceneChange(
                        timestamp_seconds=frame_analyses[i].timestamp_seconds,
                        from_scene=prev_scene,
                        to_scene=curr_scene,
                    )
                )

        return scene_changes

    async def analyze(
        self,
        video_path: Path,
        content_hash: str,
        *,
        force_refresh: bool = False,
        max_frames: int = MAX_REPRESENTATIVE_FRAMES,
    ) -> VideoAnalysisResult:
        """Analyze a video by extracting and analyzing keyframes.

        This method:
        1. Checks cache for existing result (unless force_refresh)
        2. Extracts keyframes using FFmpeg
        3. Selects representative frames
        4. Analyzes each frame using ImageProcessor
        5. Aggregates results and stores in cache

        Args:
            video_path: Path to the video file.
            content_hash: SHA256 hash of the video content.
            force_refresh: If True, ignore cache and force new analysis.
            max_frames: Maximum number of frames to analyze.

        Returns:
            VideoAnalysisResult with analysis data.

        Raises:
            DependencyError: If FFmpeg is not available.
        """
        cache_key = f"{VISION_CACHE_KEY_PREFIX_VIDEO}{content_hash}"
        start_time = time.time()

        # Check cache (unless force_refresh)
        if not force_refresh and self.cache is not None:
            cached_data = await self.cache.get(cache_key)
            if cached_data is not None:
                return VideoAnalysisResult.from_dict(cached_data)

        # Check FFmpeg availability
        if not self.check_ffmpeg_available():
            raise DependencyError(
                "FFmpeg is required for video processing",
                dependency_name="ffmpeg",
            )

        # Get video metadata
        metadata = self.get_video_metadata(video_path, content_hash)

        # Calculate keyframe interval
        interval, _ = self.calculate_keyframe_interval(metadata.duration_seconds)

        # Extract keyframes
        all_frames = self.extract_keyframes(video_path, interval)

        # Select representative frames
        selected_frames = self.select_representative_frames(all_frames, max_frames)

        # Analyze each frame
        frame_analyses: list[FrameAnalysisResult] = []
        total_cost = 0.0
        model_used = "unknown"

        for idx, frame_data in enumerate(selected_frames):
            # Calculate approximate timestamp
            timestamp = idx * interval

            # Compute frame hash
            frame_hash = self.image_processor.compute_content_hash(frame_data)

            # Analyze frame
            frame_result = await self.image_processor.analyze(
                image_data=frame_data,
                content_hash=frame_hash,
            )

            frame_analyses.append(
                FrameAnalysisResult(
                    frame_index=idx,
                    timestamp_seconds=timestamp,
                    analysis=frame_result,
                )
            )

            total_cost += frame_result.estimated_cost
            model_used = frame_result.model_used

        # Detect scene changes
        scene_changes = self._detect_scene_changes(frame_analyses)

        # Generate summary
        summary = self._generate_summary(frame_analyses, metadata)

        processing_time_ms = (time.time() - start_time) * 1000

        result = VideoAnalysisResult(
            summary=summary,
            frame_analyses=frame_analyses,
            scene_changes=scene_changes,
            duration_seconds=metadata.duration_seconds,
            metadata=metadata,
            model_used=model_used,
            total_cost=total_cost,
            cached=False,
            processing_time_ms=processing_time_ms,
        )

        # Store in cache
        if self.cache is not None:
            await self.cache.set(
                cache_key,
                result.to_dict(),
                ttl=VISION_CACHE_TTL_SECONDS,
            )

        return result
