"""STT (Speech-to-Text) Service.

TAG: STT-001
SPEC: SPEC-STT-001

This module provides the STTService class for transcribing audio files
using the Faster-Whisper library with local model inference.
"""

import asyncio
import hashlib
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from smart_file_manager.core.constants import (
    STT_CACHE_PREFIX,
    STT_CACHE_TTL_SECONDS,
    STT_DEFAULT_COMPUTE_TYPE,
    STT_DEFAULT_DEVICE,
    STT_DEFAULT_MODEL_SIZE,
    STT_MAX_DURATION_SECONDS,
    STT_MAX_FILE_SIZE_BYTES,
    SUPPORTED_AUDIO_FORMATS,
)
from smart_file_manager.core.exceptions import (
    AudioProcessingError,
    AudioTooLongError,
    FileTooLargeError,
    ModelLoadError,
    TranscriptionError,
    UnsupportedAudioFormatError,
)
from smart_file_manager.services.stt_models import (
    STTStats,
    TranscriptionResult,
    TranscriptionSegment,
    WordTimestamp,
)

if TYPE_CHECKING:
    from smart_file_manager.infrastructure.cache.base import CacheInterface

logger = logging.getLogger(__name__)


class STTService:
    """Service for transcribing audio files using Faster-Whisper.

    This service provides Speech-to-Text functionality using local
    Whisper model inference. It supports caching of results and
    provides statistics tracking.

    Attributes:
        cache: Optional cache interface for caching results.
    """

    def __init__(
        self,
        cache: "CacheInterface | None" = None,
        model_size: str = STT_DEFAULT_MODEL_SIZE,
        device: str = STT_DEFAULT_DEVICE,
        compute_type: str = STT_DEFAULT_COMPUTE_TYPE,
        default_language: str | None = None,
        enable_vad: bool = True,
    ) -> None:
        """Initialize the STT service.

        Args:
            cache: Optional cache interface for caching results.
            model_size: Whisper model size (tiny, base, small, medium, large-v3).
            device: Device for inference (auto, cuda, cpu).
            compute_type: Compute type (auto, float16, int8).
            default_language: Default language for transcription (None for auto-detect).
            enable_vad: Enable Voice Activity Detection.
        """
        self.cache = cache
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._default_language = default_language
        self._enable_vad = enable_vad

        # Lazy-loaded model
        self._model: Any = None

        # Statistics tracking
        self._stats = STTStats(
            total_analyses=0,
            cache_hits=0,
            total_duration_processed=0.0,
            avg_processing_time=0.0,
        )
        self._processing_times: list[float] = []

        # In-flight request tracking for deduplication
        self._in_flight: dict[str, Any] = {}

    def is_audio_file(self, path: Path) -> bool:
        """Check if a file is a supported audio file.

        Args:
            path: Path to the file.

        Returns:
            True if the file has a supported audio extension.
        """
        suffix = path.suffix.lower().lstrip(".")
        return suffix in SUPPORTED_AUDIO_FORMATS

    def _detect_device(self) -> tuple[str, str]:
        """Detect the best device and compute type for inference.

        Returns:
            Tuple of (device, compute_type).
        """
        if self._device != "auto":
            compute_type = self._compute_type
            if compute_type == "auto":
                compute_type = "int8" if self._device == "cpu" else "float16"
            return self._device, compute_type

        # Auto-detect device using lazy import
        try:
            import torch

            cuda_available = torch.cuda.is_available()
        except ImportError:
            cuda_available = False

        if cuda_available:
            device = "cuda"
            compute_type = "float16" if self._compute_type == "auto" else self._compute_type
        else:
            device = "cpu"
            compute_type = "int8" if self._compute_type == "auto" else self._compute_type

        return device, compute_type

    def _load_model(self) -> Any:
        """Load the Faster-Whisper model.

        Returns:
            The loaded WhisperModel instance.

        Raises:
            ModelLoadError: If the model fails to load.
        """
        if self._model is not None:
            return self._model

        try:
            from faster_whisper import WhisperModel

            device, compute_type = self._detect_device()
            logger.info(
                f"Loading Whisper model: {self._model_size} on {device} with {compute_type}"
            )

            self._model = WhisperModel(
                self._model_size,
                device=device,
                compute_type=compute_type,
            )

            return self._model

        except Exception as e:
            raise ModelLoadError(
                message=f"Failed to load Whisper model: {e}",
                model_name=self._model_size,
            ) from e

    def _compute_content_hash(self, content: bytes) -> str:
        """Compute SHA-256 hash of content.

        Args:
            content: File content bytes.

        Returns:
            Hex-encoded hash string.
        """
        return hashlib.sha256(content).hexdigest()

    def _get_cache_key(self, content_hash: str) -> str:
        """Generate cache key for a content hash.

        Args:
            content_hash: Content hash.

        Returns:
            Cache key string.
        """
        return f"{STT_CACHE_PREFIX}:{content_hash}"

    async def _get_cached_result(self, content_hash: str) -> TranscriptionResult | None:
        """Get cached transcription result if available.

        Args:
            content_hash: Content hash to look up.

        Returns:
            Cached result or None if not found.
        """
        if self.cache is None:
            return None

        cache_key = self._get_cache_key(content_hash)
        try:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                result = TranscriptionResult.from_dict(cached_data)
                result.cached = True
                return result
        except Exception as e:
            logger.warning(f"Failed to get cached result: {e}")

        return None

    async def _cache_result(
        self,
        content_hash: str,
        result: TranscriptionResult,
        ttl: int = STT_CACHE_TTL_SECONDS,
    ) -> None:
        """Cache a transcription result.

        Args:
            content_hash: Content hash as cache key.
            result: Result to cache.
            ttl: Time-to-live in seconds.
        """
        if self.cache is None:
            return

        cache_key = self._get_cache_key(content_hash)
        try:
            await self.cache.set(cache_key, result.to_dict(), ttl=ttl)
        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")

    def _validate_audio_file(self, path: Path) -> None:
        """Validate audio file constraints.

        Args:
            path: Path to the audio file.

        Raises:
            UnsupportedAudioFormatError: If format is not supported.
            FileTooLargeError: If file exceeds size limit.
        """
        # Check format
        if not self.is_audio_file(path):
            suffix = path.suffix.lower().lstrip(".")
            raise UnsupportedAudioFormatError(
                message=f"Unsupported audio format: {suffix}",
                format=suffix,
                supported_formats=list(SUPPORTED_AUDIO_FORMATS),
            )

        # Check file size
        file_size = path.stat().st_size
        if file_size > STT_MAX_FILE_SIZE_BYTES:
            max_size = STT_MAX_FILE_SIZE_BYTES
            raise FileTooLargeError(
                message=f"File size ({file_size}) exceeds maximum ({max_size}) bytes",
                file_size_bytes=file_size,
                max_size_bytes=max_size,
            )

    def _validate_audio_duration(self, duration_seconds: float, path: Path) -> None:
        """Validate audio duration constraint.

        Args:
            duration_seconds: Audio duration in seconds.
            path: Path to the audio file (for error message).

        Raises:
            AudioTooLongError: If duration exceeds limit.
        """
        if duration_seconds > STT_MAX_DURATION_SECONDS:
            max_duration = STT_MAX_DURATION_SECONDS
            raise AudioTooLongError(
                message=f"Audio duration ({duration_seconds:.1f}s) exceeds max ({max_duration}s)",
                duration_seconds=duration_seconds,
                max_duration_seconds=float(max_duration),
            )

    async def analyze_audio(self, path: Path) -> TranscriptionResult:
        """Transcribe an audio file.

        Args:
            path: Path to the audio file.

        Returns:
            TranscriptionResult with segments and full text.

        Raises:
            UnsupportedAudioFormatError: If format is not supported.
            FileTooLargeError: If file exceeds size limit.
            AudioTooLongError: If duration exceeds limit.
            AudioProcessingError: If audio processing fails.
            TranscriptionError: If transcription fails.
        """
        start_time = time.time()

        # Validate file
        self._validate_audio_file(path)

        # Read file content for hashing
        try:
            content = path.read_bytes()
            content_hash = self._compute_content_hash(content)
        except Exception as e:
            raise AudioProcessingError(
                message=f"Failed to read audio file: {e}",
                audio_path=str(path),
            ) from e

        # Check cache
        cached_result = await self._get_cached_result(content_hash)
        if cached_result:
            self._stats.cache_hits += 1
            self._stats.total_analyses += 1
            return cached_result

        # Load model
        model = self._load_model()

        # Transcribe
        try:
            segments_gen, info = model.transcribe(
                str(path),
                language=self._default_language,
                vad_filter=self._enable_vad,
                word_timestamps=True,
            )

            # Validate duration
            self._validate_audio_duration(info.duration, path)

            # Process segments
            segments: list[TranscriptionSegment] = []
            full_text_parts: list[str] = []

            for segment in segments_gen:
                words = None
                if segment.words:
                    words = [
                        WordTimestamp(
                            word=word.word,
                            start=word.start,
                            end=word.end,
                            confidence=word.probability,
                        )
                        for word in segment.words
                    ]

                segments.append(
                    TranscriptionSegment(
                        id=segment.id,
                        start=segment.start,
                        end=segment.end,
                        text=segment.text.strip(),
                        words=words,
                        language=info.language,
                    )
                )
                full_text_parts.append(segment.text.strip())

            result = TranscriptionResult(
                segments=segments,
                text=" ".join(full_text_parts),
                language=info.language,
                language_confidence=info.language_probability,
                duration_seconds=info.duration,
                cached=False,
            )

            # Update stats
            processing_time = time.time() - start_time
            self._update_stats(processing_time, info.duration)

            # Cache result
            await self._cache_result(content_hash, result)

            return result

        except (AudioTooLongError, UnsupportedAudioFormatError, FileTooLargeError):
            raise
        except Exception as e:
            raise TranscriptionError(
                message=f"Transcription failed: {e}",
                audio_path=str(path),
                reason=str(e),
            ) from e

    def _update_stats(self, processing_time: float, duration: float) -> None:
        """Update statistics after processing.

        Args:
            processing_time: Time taken to process in seconds.
            duration: Audio duration in seconds.
        """
        self._stats.total_analyses += 1
        self._stats.total_duration_processed += duration
        self._processing_times.append(processing_time)
        self._stats.avg_processing_time = sum(self._processing_times) / len(self._processing_times)

    def get_stats(self) -> STTStats:
        """Get current statistics.

        Returns:
            STTStats instance with current statistics.
        """
        return STTStats(
            total_analyses=self._stats.total_analyses,
            cache_hits=self._stats.cache_hits,
            total_duration_processed=self._stats.total_duration_processed,
            avg_processing_time=self._stats.avg_processing_time,
        )

    def reset_stats(self) -> None:
        """Reset all statistics to zero."""
        self._stats = STTStats(
            total_analyses=0,
            cache_hits=0,
            total_duration_processed=0.0,
            avg_processing_time=0.0,
        )
        self._processing_times.clear()

    async def batch_analyze(
        self,
        paths: list[Path],
        max_concurrent: int = 3,
    ) -> list[TranscriptionResult]:
        """Transcribe multiple audio files with concurrency control.

        Args:
            paths: List of paths to audio files.
            max_concurrent: Maximum number of concurrent transcriptions.

        Returns:
            List of TranscriptionResult objects for each processed file.
            Files with unsupported formats are skipped.
        """

        # Filter only supported audio files
        audio_paths = [p for p in paths if self.is_audio_file(p)]

        if not audio_paths:
            return []

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(path: Path) -> TranscriptionResult:
            async with semaphore:
                return await self.analyze_audio(path)

        # Process all files concurrently with semaphore limit
        tasks = [process_with_semaphore(p) for p in audio_paths]
        results = await asyncio.gather(*tasks)

        return list(results)
