"""Image processor for Vision analysis.

TAG: VIS-M2-01 to VIS-M2-07
SPEC: SPEC-VISION-001

This module provides image processing capabilities including:
- Format validation
- Image resizing
- EXIF metadata extraction
- API-based image analysis with OpenRouter
- Cache integration
- Local fallback analysis
"""

import base64
import hashlib
import io
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PIL import Image
from PIL.ExifTags import TAGS

from smart_file_manager.core.constants import (
    IMAGE_ANALYSIS_PROMPT,
    IMAGE_MIME_TYPES,
    SUPPORTED_IMAGE_FORMATS,
    TARGET_IMAGE_DIMENSION,
    VISION_CACHE_KEY_PREFIX_IMAGE,
    VISION_CACHE_TTL_SECONDS,
)
from smart_file_manager.core.exceptions import (
    ModelUnavailableError,
)
from smart_file_manager.services.vision_models import (
    DetectedObject,
    ImageAnalysisResult,
    ImageMetadata,
)

if TYPE_CHECKING:
    from smart_file_manager.infrastructure.cache.base import CacheInterface
    from smart_file_manager.services.openrouter_client import OpenRouterClient


class ImageProcessor:
    """Image processor for Vision analysis.

    This class handles image processing including format validation,
    resizing, metadata extraction, and API-based analysis using OpenRouter.

    Attributes:
        client: OpenRouterClient for API calls.
        cache: Optional cache interface for result caching.
    """

    def __init__(
        self,
        client: "OpenRouterClient",
        cache: "CacheInterface | None" = None,
    ) -> None:
        """Initialize the ImageProcessor.

        Args:
            client: OpenRouterClient instance for API calls.
            cache: Optional cache interface for caching results.
        """
        self.client = client
        self.cache = cache

    def validate_format(self, image_path: Path) -> bool:
        """Validate if the image format is supported.

        Args:
            image_path: Path to the image file.

        Returns:
            True if format is supported, False otherwise.
        """
        extension = image_path.suffix.lower().lstrip(".")
        return extension in SUPPORTED_IMAGE_FORMATS

    def resize_if_needed(
        self,
        image_data: bytes,
        max_size: int = TARGET_IMAGE_DIMENSION,
    ) -> bytes:
        """Resize image if it exceeds the maximum dimension.

        Preserves aspect ratio when resizing.

        Args:
            image_data: Raw image bytes.
            max_size: Maximum dimension (width or height) in pixels.

        Returns:
            Resized image bytes if needed, original bytes otherwise.
        """
        with Image.open(io.BytesIO(image_data)) as img:
            width, height = img.size

            # Check if resize is needed
            if width <= max_size and height <= max_size:
                return image_data

            # Calculate new dimensions preserving aspect ratio
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))

            # Resize the image
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert back to bytes
            output = io.BytesIO()
            img_format = img.format or "JPEG"
            if img.mode == "RGBA" and img_format == "JPEG":
                resized = resized.convert("RGB")
            resized.save(output, format=img_format, quality=85)
            return output.getvalue()

    def extract_metadata(
        self,
        image_path: Path,
        content_hash: str,
    ) -> ImageMetadata:
        """Extract metadata from an image file.

        Args:
            image_path: Path to the image file.
            content_hash: Pre-computed content hash.

        Returns:
            ImageMetadata with extracted information.
        """
        with Image.open(image_path) as img:
            width, height = img.size
            img_format = (img.format or "unknown").lower()

            # Extract EXIF data
            exif_data: dict[str, Any] | None = None
            try:
                raw_exif = img.getexif()
                if raw_exif:
                    exif_data = {}
                    for tag_id, value in raw_exif.items():
                        tag_name = TAGS.get(tag_id, str(tag_id))
                        # Convert bytes to string for JSON serialization
                        if isinstance(value, bytes):
                            try:
                                value = value.decode("utf-8", errors="ignore")
                            except Exception:
                                value = str(value)
                        exif_data[tag_name] = value
            except Exception:
                # EXIF extraction failed, continue without it
                pass

        # Get file size
        size_bytes = image_path.stat().st_size

        return ImageMetadata(
            width=width,
            height=height,
            format=img_format,
            size_bytes=size_bytes,
            content_hash=content_hash,
            exif=exif_data,
        )

    def compute_content_hash(self, image_data: bytes) -> str:
        """Compute SHA256 hash of image data.

        Args:
            image_data: Raw image bytes.

        Returns:
            Hexadecimal hash string.
        """
        return hashlib.sha256(image_data).hexdigest()

    def _prepare_image_message(
        self,
        image_data: bytes,
        mime_type: str,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Prepare message with base64 encoded image for Ollama API.

        Args:
            image_data: Raw image bytes.
            mime_type: MIME type of the image (not used for Ollama, but kept for compatibility).

        Returns:
            Tuple of (messages list, images list) for the Ollama API.
            - messages: List of message dictionaries with 'role' and 'content'.
            - images: List of base64 encoded image strings.
        """
        base64_image = base64.b64encode(image_data).decode("utf-8")

        # Ollama format: images are passed separately as base64 strings
        messages = [
            {
                "role": "user",
                "content": IMAGE_ANALYSIS_PROMPT,
            }
        ]
        images = [base64_image]

        return messages, images

    def _parse_api_response(
        self,
        response_content: str,
        metadata: ImageMetadata,
        model_used: str,
        prompt_tokens: int,
        completion_tokens: int,
        processing_time_ms: float,
    ) -> ImageAnalysisResult:
        """Parse API response into ImageAnalysisResult.

        Args:
            response_content: Raw JSON response from API.
            metadata: Image metadata.
            model_used: Model ID that was used.
            prompt_tokens: Number of prompt tokens.
            completion_tokens: Number of completion tokens.
            processing_time_ms: Processing time in milliseconds.

        Returns:
            Parsed ImageAnalysisResult.
        """
        try:
            data = json.loads(response_content)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            data = {
                "description": response_content[:500],
                "objects": [],
                "scene": "unknown",
                "text": None,
                "tags": [],
                "dominant_colors": [],
                "quality": "unknown",
            }

        # Parse detected objects
        objects = []
        for obj in data.get("objects", []):
            if isinstance(obj, dict):
                objects.append(
                    DetectedObject(
                        name=obj.get("name", "unknown"),
                        confidence=float(obj.get("confidence", 0.0)),
                    )
                )

        # Estimate cost (simplified calculation)
        # Based on typical OpenRouter pricing
        estimated_cost = (prompt_tokens * 0.0001 + completion_tokens * 0.00015) / 1000

        return ImageAnalysisResult(
            description=data.get("description", ""),
            objects=objects,
            scene=data.get("scene", "unknown"),
            text_content=data.get("text"),
            tags=data.get("tags", []),
            dominant_colors=data.get("dominant_colors", []),
            quality=data.get("quality", "unknown"),
            metadata=metadata,
            model_used=model_used,
            estimated_cost=estimated_cost,
            cached=False,
            processing_time_ms=processing_time_ms,
        )

    def _local_fallback_analysis(
        self,
        image_data: bytes,
        metadata: ImageMetadata,
    ) -> ImageAnalysisResult:
        """Perform local fallback analysis when API is unavailable.

        Args:
            image_data: Raw image bytes.
            metadata: Image metadata.

        Returns:
            Basic ImageAnalysisResult based on metadata.
        """
        # Determine basic tags based on metadata
        tags = ["image"]
        if metadata.format in ("jpeg", "jpg"):
            tags.append("photo")
        if metadata.exif:
            tags.append("camera")
            if "Make" in metadata.exif:
                tags.append(metadata.exif["Make"].lower())

        # Determine basic description
        description = (
            f"Image file ({metadata.format.upper()}) with dimensions "
            f"{metadata.width}x{metadata.height} pixels."
        )
        if metadata.exif and "Make" in metadata.exif:
            description += f" Taken with {metadata.exif['Make']}."

        return ImageAnalysisResult(
            description=description,
            objects=[],
            scene="unknown",
            text_content=None,
            tags=tags,
            dominant_colors=[],
            quality="unknown",
            metadata=metadata,
            model_used="local",
            estimated_cost=0.0,
            cached=False,
            processing_time_ms=10.0,
        )

    async def analyze(
        self,
        image_data: bytes,
        content_hash: str,
        *,
        force_refresh: bool = False,
        metadata: ImageMetadata | None = None,
    ) -> ImageAnalysisResult:
        """Analyze an image using OpenRouter API.

        This method:
        1. Checks cache for existing result (unless force_refresh)
        2. Calls API with fallback chain on cache miss
        3. Falls back to local analysis if all APIs fail
        4. Stores successful results in cache

        Args:
            image_data: Raw image bytes.
            content_hash: SHA256 hash of the image content.
            force_refresh: If True, ignore cache and force new analysis.
            metadata: Optional pre-computed metadata.

        Returns:
            ImageAnalysisResult with analysis data.
        """
        cache_key = f"{VISION_CACHE_KEY_PREFIX_IMAGE}{content_hash}"
        start_time = time.time()

        # Check cache (unless force_refresh)
        if not force_refresh and self.cache is not None:
            cached_data = await self.cache.get(cache_key)
            if cached_data is not None:
                return ImageAnalysisResult.from_dict(cached_data)

        # Compute metadata if not provided
        if metadata is None:
            # Create minimal metadata from image data
            with Image.open(io.BytesIO(image_data)) as img:
                metadata = ImageMetadata(
                    width=img.size[0],
                    height=img.size[1],
                    format=(img.format or "unknown").lower(),
                    size_bytes=len(image_data),
                    content_hash=content_hash,
                )

        # Determine MIME type
        mime_type = IMAGE_MIME_TYPES.get(metadata.format, "image/jpeg")

        # Prepare message for Ollama API
        messages, images = self._prepare_image_message(image_data, mime_type)

        try:
            # Call API with fallback chain (pass images separately for Ollama)
            response = await self.client.chat_completion_with_fallback(messages, images=images)

            processing_time_ms = (time.time() - start_time) * 1000

            # Parse response
            result = self._parse_api_response(
                response_content=response.content,
                metadata=metadata,
                model_used=response.model_used,
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
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

        except ModelUnavailableError:
            # All API models failed, use local fallback
            return self._local_fallback_analysis(image_data, metadata)
