"""Vision analysis data models.

TAG: VIS-M1-03
SPEC: SPEC-VISION-001

This module defines dataclasses for Vision analysis results,
including image metadata, video metadata, and analysis outputs.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BoundingBox:
    """Bounding box coordinates for detected objects.

    Attributes:
        x: X coordinate of the top-left corner.
        y: Y coordinate of the top-left corner.
        width: Width of the bounding box.
        height: Height of the bounding box.
    """

    x: int
    y: int
    width: int
    height: int


@dataclass
class DetectedObject:
    """A detected object in an image.

    Attributes:
        name: Name of the detected object.
        confidence: Confidence score (0.0-1.0).
        bounding_box: Optional bounding box coordinates.
    """

    name: str
    confidence: float
    bounding_box: BoundingBox | None = None


@dataclass
class ImageMetadata:
    """Metadata for an image file.

    Attributes:
        width: Image width in pixels.
        height: Image height in pixels.
        format: Image format (jpeg, png, etc.).
        size_bytes: File size in bytes.
        content_hash: SHA256 hash of the file content.
        exif: Optional EXIF metadata dictionary.
    """

    width: int
    height: int
    format: str
    size_bytes: int
    content_hash: str
    exif: dict[str, Any] | None = None


@dataclass
class VideoMetadata:
    """Metadata for a video file.

    Attributes:
        width: Video width in pixels.
        height: Video height in pixels.
        duration_seconds: Video duration in seconds.
        fps: Frames per second.
        codec: Video codec name.
        size_bytes: File size in bytes.
        content_hash: SHA256 hash of the file content.
    """

    width: int
    height: int
    duration_seconds: float
    fps: float
    codec: str
    size_bytes: int
    content_hash: str


@dataclass
class ImageAnalysisResult:
    """Result of image analysis.

    Attributes:
        description: Detailed description of the image content.
        objects: List of detected objects.
        scene: Overall scene type (indoor, outdoor, etc.).
        text_content: OCR extracted text, or None.
        tags: List of relevant tags.
        dominant_colors: Top 3 dominant colors.
        quality: Image quality assessment.
        metadata: Image metadata.
        model_used: The AI model used for analysis.
        estimated_cost: Estimated API cost in USD.
        cached: Whether the result was from cache.
        processing_time_ms: Processing time in milliseconds.
    """

    description: str
    objects: list[DetectedObject]
    scene: str
    text_content: str | None
    tags: list[str]
    dominant_colors: list[str]
    quality: str
    metadata: ImageMetadata
    model_used: str
    estimated_cost: float
    cached: bool
    processing_time_ms: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the result.
        """
        return {
            "description": self.description,
            "objects": [
                {
                    "name": obj.name,
                    "confidence": obj.confidence,
                    "bounding_box": (
                        {
                            "x": obj.bounding_box.x,
                            "y": obj.bounding_box.y,
                            "width": obj.bounding_box.width,
                            "height": obj.bounding_box.height,
                        }
                        if obj.bounding_box
                        else None
                    ),
                }
                for obj in self.objects
            ],
            "scene": self.scene,
            "text_content": self.text_content,
            "tags": self.tags,
            "dominant_colors": self.dominant_colors,
            "quality": self.quality,
            "metadata": {
                "width": self.metadata.width,
                "height": self.metadata.height,
                "format": self.metadata.format,
                "size_bytes": self.metadata.size_bytes,
                "content_hash": self.metadata.content_hash,
                "exif": self.metadata.exif,
            },
            "model_used": self.model_used,
            "estimated_cost": self.estimated_cost,
            "cached": self.cached,
            "processing_time_ms": self.processing_time_ms,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImageAnalysisResult":
        """Create an instance from a dictionary.

        Args:
            data: Dictionary containing the result data.

        Returns:
            ImageAnalysisResult instance.
        """
        objects = []
        for obj_data in data.get("objects", []):
            bbox = None
            if obj_data.get("bounding_box"):
                bbox_data = obj_data["bounding_box"]
                bbox = BoundingBox(
                    x=bbox_data["x"],
                    y=bbox_data["y"],
                    width=bbox_data["width"],
                    height=bbox_data["height"],
                )
            objects.append(
                DetectedObject(
                    name=obj_data["name"],
                    confidence=obj_data["confidence"],
                    bounding_box=bbox,
                )
            )

        metadata_data = data["metadata"]
        metadata = ImageMetadata(
            width=metadata_data["width"],
            height=metadata_data["height"],
            format=metadata_data["format"],
            size_bytes=metadata_data["size_bytes"],
            content_hash=metadata_data["content_hash"],
            exif=metadata_data.get("exif"),
        )

        return cls(
            description=data["description"],
            objects=objects,
            scene=data["scene"],
            text_content=data.get("text_content"),
            tags=data.get("tags", []),
            dominant_colors=data.get("dominant_colors", []),
            quality=data.get("quality", "unknown"),
            metadata=metadata,
            model_used=data.get("model_used", "unknown"),
            estimated_cost=data.get("estimated_cost", 0.0),
            cached=data.get("cached", False),
            processing_time_ms=data.get("processing_time_ms", 0.0),
        )


@dataclass
class FrameAnalysisResult:
    """Result of analyzing a single video frame.

    Attributes:
        frame_index: Index of the frame in the video.
        timestamp_seconds: Timestamp of the frame in seconds.
        analysis: The image analysis result for this frame.
    """

    frame_index: int
    timestamp_seconds: float
    analysis: ImageAnalysisResult


@dataclass
class SceneChange:
    """Represents a scene change in a video.

    Attributes:
        timestamp_seconds: Time when the scene change occurred.
        from_scene: The scene type before the change.
        to_scene: The scene type after the change.
    """

    timestamp_seconds: float
    from_scene: str
    to_scene: str


@dataclass
class VideoAnalysisResult:
    """Result of video analysis.

    Attributes:
        summary: Summary description of the video content.
        frame_analyses: List of analyzed frames.
        scene_changes: List of detected scene changes.
        duration_seconds: Video duration in seconds.
        metadata: Video metadata.
        model_used: The AI model used for analysis.
        total_cost: Total API cost in USD.
        cached: Whether the result was from cache.
        processing_time_ms: Total processing time in milliseconds.
    """

    summary: str
    frame_analyses: list[FrameAnalysisResult]
    scene_changes: list[SceneChange]
    duration_seconds: float
    metadata: VideoMetadata
    model_used: str
    total_cost: float
    cached: bool
    processing_time_ms: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the result.
        """
        return {
            "summary": self.summary,
            "frame_analyses": [
                {
                    "frame_index": fa.frame_index,
                    "timestamp_seconds": fa.timestamp_seconds,
                    "analysis": fa.analysis.to_dict(),
                }
                for fa in self.frame_analyses
            ],
            "scene_changes": [
                {
                    "timestamp_seconds": sc.timestamp_seconds,
                    "from_scene": sc.from_scene,
                    "to_scene": sc.to_scene,
                }
                for sc in self.scene_changes
            ],
            "duration_seconds": self.duration_seconds,
            "metadata": {
                "width": self.metadata.width,
                "height": self.metadata.height,
                "duration_seconds": self.metadata.duration_seconds,
                "fps": self.metadata.fps,
                "codec": self.metadata.codec,
                "size_bytes": self.metadata.size_bytes,
                "content_hash": self.metadata.content_hash,
            },
            "model_used": self.model_used,
            "total_cost": self.total_cost,
            "cached": self.cached,
            "processing_time_ms": self.processing_time_ms,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VideoAnalysisResult":
        """Create an instance from a dictionary.

        Args:
            data: Dictionary containing the result data.

        Returns:
            VideoAnalysisResult instance.
        """
        frame_analyses = []
        for fa_data in data.get("frame_analyses", []):
            frame_analyses.append(
                FrameAnalysisResult(
                    frame_index=fa_data["frame_index"],
                    timestamp_seconds=fa_data["timestamp_seconds"],
                    analysis=ImageAnalysisResult.from_dict(fa_data["analysis"]),
                )
            )

        scene_changes = []
        for sc_data in data.get("scene_changes", []):
            scene_changes.append(
                SceneChange(
                    timestamp_seconds=sc_data["timestamp_seconds"],
                    from_scene=sc_data["from_scene"],
                    to_scene=sc_data["to_scene"],
                )
            )

        metadata_data = data["metadata"]
        metadata = VideoMetadata(
            width=metadata_data["width"],
            height=metadata_data["height"],
            duration_seconds=metadata_data["duration_seconds"],
            fps=metadata_data["fps"],
            codec=metadata_data["codec"],
            size_bytes=metadata_data["size_bytes"],
            content_hash=metadata_data["content_hash"],
        )

        return cls(
            summary=data["summary"],
            frame_analyses=frame_analyses,
            scene_changes=scene_changes,
            duration_seconds=data["duration_seconds"],
            metadata=metadata,
            model_used=data.get("model_used", "unknown"),
            total_cost=data.get("total_cost", 0.0),
            cached=data.get("cached", False),
            processing_time_ms=data.get("processing_time_ms", 0.0),
        )


@dataclass
class AnalysisStats:
    """Statistics for vision analysis operations.

    Attributes:
        total_analyses: Total number of analyses performed.
        cached_analyses: Number of analyses served from cache.
        api_analyses: Number of analyses that required API calls.
        total_cost: Total cost in USD.
        average_processing_time_ms: Average processing time in milliseconds.
        models_used: Dictionary mapping model IDs to usage counts.
    """

    total_analyses: int
    cached_analyses: int
    api_analyses: int
    total_cost: float
    average_processing_time_ms: float
    models_used: dict[str, int] = field(default_factory=dict)

    @property
    def cache_hit_rate(self) -> float:
        """Calculate the cache hit rate.

        Returns:
            Cache hit rate as a decimal (0.0-1.0).
        """
        if self.total_analyses == 0:
            return 0.0
        return self.cached_analyses / self.total_analyses
