"""STT (Speech-to-Text) data models.

TAG: STT-001
SPEC: SPEC-STT-001

This module defines dataclasses for STT analysis results,
including transcription segments, word timestamps, and statistics.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class WordTimestamp:
    """Word-level timestamp information.

    Attributes:
        word: The transcribed word.
        start: Start time in seconds.
        end: End time in seconds.
        confidence: Confidence score (0.0-1.0).
    """

    word: str
    start: float
    end: float
    confidence: float


@dataclass
class TranscriptionSegment:
    """A segment of transcribed speech.

    Attributes:
        id: Segment identifier.
        start: Start time in seconds.
        end: End time in seconds.
        text: Transcribed text for this segment.
        words: Optional list of word-level timestamps.
        language: Detected language code for this segment.
    """

    id: int
    start: float
    end: float
    text: str
    words: list[WordTimestamp] | None
    language: str


@dataclass
class AudioMetadata:
    """Metadata for an audio file.

    Attributes:
        path: Path to the audio file.
        format: Audio format (mp3, wav, etc.).
        duration_seconds: Audio duration in seconds.
        sample_rate: Sample rate in Hz.
        channels: Number of audio channels.
        size_bytes: File size in bytes.
    """

    path: str
    format: str
    duration_seconds: float
    sample_rate: int
    channels: int
    size_bytes: int


@dataclass
class TranscriptionResult:
    """Result of STT transcription.

    Attributes:
        segments: List of transcription segments.
        text: Full transcribed text.
        language: Detected language code.
        language_confidence: Confidence score for language detection.
        duration_seconds: Audio duration in seconds.
        cached: Whether the result was from cache.
    """

    segments: list[TranscriptionSegment]
    text: str
    language: str
    language_confidence: float
    duration_seconds: float
    cached: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the result.
        """
        return {
            "segments": [
                {
                    "id": seg.id,
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                    "words": (
                        [
                            {
                                "word": w.word,
                                "start": w.start,
                                "end": w.end,
                                "confidence": w.confidence,
                            }
                            for w in seg.words
                        ]
                        if seg.words
                        else None
                    ),
                    "language": seg.language,
                }
                for seg in self.segments
            ],
            "text": self.text,
            "language": self.language,
            "language_confidence": self.language_confidence,
            "duration_seconds": self.duration_seconds,
            "cached": self.cached,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TranscriptionResult":
        """Create an instance from a dictionary.

        Args:
            data: Dictionary containing the result data.

        Returns:
            TranscriptionResult instance.
        """
        segments = []
        for seg_data in data.get("segments", []):
            words = None
            if seg_data.get("words"):
                words = [
                    WordTimestamp(
                        word=w["word"],
                        start=w["start"],
                        end=w["end"],
                        confidence=w["confidence"],
                    )
                    for w in seg_data["words"]
                ]
            segments.append(
                TranscriptionSegment(
                    id=seg_data["id"],
                    start=seg_data["start"],
                    end=seg_data["end"],
                    text=seg_data["text"],
                    words=words,
                    language=seg_data.get("language", ""),
                )
            )

        return cls(
            segments=segments,
            text=data["text"],
            language=data["language"],
            language_confidence=data.get("language_confidence", 0.0),
            duration_seconds=data.get("duration_seconds", 0.0),
            cached=data.get("cached", False),
        )


@dataclass
class STTStats:
    """Statistics for STT analysis operations.

    Attributes:
        total_analyses: Total number of analyses performed.
        cache_hits: Number of analyses served from cache.
        total_duration_processed: Total audio duration processed in seconds.
        avg_processing_time: Average processing time in seconds.
    """

    total_analyses: int
    cache_hits: int
    total_duration_processed: float
    avg_processing_time: float

    @property
    def cache_hit_rate(self) -> float:
        """Calculate the cache hit rate.

        Returns:
            Cache hit rate as a decimal (0.0-1.0).
        """
        if self.total_analyses == 0:
            return 0.0
        return self.cache_hits / self.total_analyses
