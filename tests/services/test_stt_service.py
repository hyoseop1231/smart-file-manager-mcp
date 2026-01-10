"""Tests for STT Service.

TAG: STT-001
SPEC: SPEC-STT-001

TDD Tests for Speech-to-Text Service implementation.
"""

from smart_file_manager.core.exceptions import (
    AudioProcessingError,
    AudioTooLongError,
    FileTooLargeError,
    ModelLoadError,
    SmartFileManagerError,
    STTError,
    TranscriptionError,
    UnsupportedAudioFormatError,
)


class TestSTTExceptions:
    """Tests for STT exception hierarchy (TASK-001)."""

    def test_stt_error_inherits_from_base(self) -> None:
        """STTError should inherit from SmartFileManagerError."""
        error = STTError("Test error")
        assert isinstance(error, SmartFileManagerError)
        assert str(error) == "Test error"

    def test_stt_error_default_message(self) -> None:
        """STTError should have default message."""
        error = STTError()
        assert "STT" in str(error) or "error" in str(error).lower()

    def test_unsupported_audio_format_error(self) -> None:
        """UnsupportedAudioFormatError should contain format info."""
        error = UnsupportedAudioFormatError(
            message="Unsupported format: xyz",
            format="xyz",
            supported_formats=["mp3", "wav", "flac"],
        )
        assert isinstance(error, STTError)
        assert error.format == "xyz"
        assert "mp3" in error.supported_formats
        assert "wav" in error.supported_formats

    def test_audio_processing_error(self) -> None:
        """AudioProcessingError should contain audio path info."""
        error = AudioProcessingError(
            message="Failed to process audio",
            audio_path="/path/to/audio.mp3",
        )
        assert isinstance(error, STTError)
        assert error.audio_path == "/path/to/audio.mp3"

    def test_audio_processing_error_default(self) -> None:
        """AudioProcessingError should work with defaults."""
        error = AudioProcessingError()
        assert isinstance(error, STTError)
        assert error.audio_path is None

    def test_model_load_error(self) -> None:
        """ModelLoadError should contain model info."""
        error = ModelLoadError(
            message="Failed to load model",
            model_name="large-v3",
        )
        assert isinstance(error, STTError)
        assert error.model_name == "large-v3"

    def test_transcription_error(self) -> None:
        """TranscriptionError should contain transcription failure info."""
        error = TranscriptionError(
            message="Transcription failed",
            audio_path="/path/to/audio.mp3",
            reason="Corrupted audio data",
        )
        assert isinstance(error, STTError)
        assert error.audio_path == "/path/to/audio.mp3"
        assert error.reason == "Corrupted audio data"

    def test_audio_too_long_error(self) -> None:
        """AudioTooLongError should contain duration info (REQ-N-001)."""
        error = AudioTooLongError(
            message="Audio too long",
            duration_seconds=7500.0,
            max_duration_seconds=7200.0,
        )
        assert isinstance(error, STTError)
        assert error.duration_seconds == 7500.0
        assert error.max_duration_seconds == 7200.0

    def test_file_too_large_error(self) -> None:
        """FileTooLargeError should contain size info (REQ-N-002)."""
        error = FileTooLargeError(
            message="File too large",
            file_size_bytes=110_000_000,
            max_size_bytes=100_000_000,
        )
        assert isinstance(error, STTError)
        assert error.file_size_bytes == 110_000_000
        assert error.max_size_bytes == 100_000_000


class TestSTTConstants:
    """Tests for STT constants (TASK-002)."""

    def test_supported_audio_formats_contains_required_formats(self) -> None:
        """SUPPORTED_AUDIO_FORMATS should contain all required formats (REQ-U-001)."""
        from smart_file_manager.core.constants import SUPPORTED_AUDIO_FORMATS

        required_formats = {"mp3", "wav", "flac", "aac", "ogg", "m4a", "opus", "wma"}
        for fmt in required_formats:
            assert fmt in SUPPORTED_AUDIO_FORMATS, f"Missing format: {fmt}"

    def test_supported_audio_formats_is_frozenset(self) -> None:
        """SUPPORTED_AUDIO_FORMATS should be immutable."""
        from smart_file_manager.core.constants import SUPPORTED_AUDIO_FORMATS

        assert isinstance(SUPPORTED_AUDIO_FORMATS, frozenset)

    def test_stt_cache_prefix(self) -> None:
        """STT_CACHE_PREFIX should be defined."""
        from smart_file_manager.core.constants import STT_CACHE_PREFIX

        assert STT_CACHE_PREFIX == "stt"

    def test_stt_cache_ttl_seconds(self) -> None:
        """STT_CACHE_TTL_SECONDS should be 7 days."""
        from smart_file_manager.core.constants import STT_CACHE_TTL_SECONDS

        seven_days_seconds = 7 * 24 * 60 * 60
        assert STT_CACHE_TTL_SECONDS == seven_days_seconds

    def test_stt_max_duration_seconds(self) -> None:
        """STT_MAX_DURATION_SECONDS should be 2 hours (REQ-N-001)."""
        from smart_file_manager.core.constants import STT_MAX_DURATION_SECONDS

        two_hours_seconds = 2 * 60 * 60  # 7200 seconds
        assert STT_MAX_DURATION_SECONDS == two_hours_seconds

    def test_stt_max_file_size_bytes(self) -> None:
        """STT_MAX_FILE_SIZE_BYTES should be 100MB (REQ-N-002)."""
        from smart_file_manager.core.constants import STT_MAX_FILE_SIZE_BYTES

        hundred_mb = 100 * 1024 * 1024
        assert STT_MAX_FILE_SIZE_BYTES == hundred_mb


class TestSTTSettings:
    """Tests for STT settings in config (TASK-003)."""

    def test_settings_has_stt_model_size(self) -> None:
        """Settings should have STT_MODEL_SIZE field with default."""
        import os

        os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
        from smart_file_manager.core.config import Settings

        settings = Settings()
        assert hasattr(settings, "stt_model_size")
        assert settings.stt_model_size == "large-v3"

    def test_settings_has_stt_device(self) -> None:
        """Settings should have STT_DEVICE field with default 'auto'."""
        import os

        os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
        from smart_file_manager.core.config import Settings

        settings = Settings()
        assert hasattr(settings, "stt_device")
        assert settings.stt_device == "auto"

    def test_settings_has_stt_compute_type(self) -> None:
        """Settings should have STT_COMPUTE_TYPE field with default 'auto'."""
        import os

        os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
        from smart_file_manager.core.config import Settings

        settings = Settings()
        assert hasattr(settings, "stt_compute_type")
        assert settings.stt_compute_type == "auto"

    def test_settings_has_stt_default_language(self) -> None:
        """Settings should have STT_DEFAULT_LANGUAGE field with default None."""
        import os

        os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
        from smart_file_manager.core.config import Settings

        settings = Settings()
        assert hasattr(settings, "stt_default_language")
        assert settings.stt_default_language is None

    def test_settings_has_stt_chunk_length_seconds(self) -> None:
        """Settings should have STT_CHUNK_LENGTH_SECONDS field with default 30."""
        import os

        os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
        from smart_file_manager.core.config import Settings

        settings = Settings()
        assert hasattr(settings, "stt_chunk_length_seconds")
        assert settings.stt_chunk_length_seconds == 30

    def test_settings_has_stt_enable_vad(self) -> None:
        """Settings should have STT_ENABLE_VAD field with default True."""
        import os

        os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
        from smart_file_manager.core.config import Settings

        settings = Settings()
        assert hasattr(settings, "stt_enable_vad")
        assert settings.stt_enable_vad is True


class TestSTTDataModels:
    """Tests for STT data models (TASK-004)."""

    def test_word_timestamp_dataclass(self) -> None:
        """WordTimestamp should have required fields."""
        from smart_file_manager.services.stt_models import WordTimestamp

        word = WordTimestamp(
            word="hello",
            start=0.0,
            end=0.5,
            confidence=0.95,
        )
        assert word.word == "hello"
        assert word.start == 0.0
        assert word.end == 0.5
        assert word.confidence == 0.95

    def test_transcription_segment_dataclass(self) -> None:
        """TranscriptionSegment should have required fields (REQ-U-003)."""
        from smart_file_manager.services.stt_models import (
            TranscriptionSegment,
            WordTimestamp,
        )

        segment = TranscriptionSegment(
            id=0,
            start=0.0,
            end=2.5,
            text="Hello world",
            words=[
                WordTimestamp(word="Hello", start=0.0, end=0.5, confidence=0.9),
                WordTimestamp(word="world", start=0.6, end=1.0, confidence=0.95),
            ],
            language="en",
        )
        assert segment.id == 0
        assert segment.start == 0.0
        assert segment.end == 2.5
        assert segment.text == "Hello world"
        assert len(segment.words) == 2
        assert segment.language == "en"

    def test_transcription_segment_optional_words(self) -> None:
        """TranscriptionSegment words field should be optional."""
        from smart_file_manager.services.stt_models import TranscriptionSegment

        segment = TranscriptionSegment(
            id=0,
            start=0.0,
            end=2.5,
            text="Hello world",
            words=None,
            language="en",
        )
        assert segment.words is None

    def test_audio_metadata_dataclass(self) -> None:
        """AudioMetadata should have required fields."""
        from smart_file_manager.services.stt_models import AudioMetadata

        metadata = AudioMetadata(
            path="/path/to/audio.mp3",
            format="mp3",
            duration_seconds=120.5,
            sample_rate=44100,
            channels=2,
            size_bytes=2_000_000,
        )
        assert metadata.path == "/path/to/audio.mp3"
        assert metadata.format == "mp3"
        assert metadata.duration_seconds == 120.5
        assert metadata.sample_rate == 44100
        assert metadata.channels == 2
        assert metadata.size_bytes == 2_000_000

    def test_transcription_result_dataclass(self) -> None:
        """TranscriptionResult should have required fields (REQ-U-003)."""
        from smart_file_manager.services.stt_models import (
            TranscriptionResult,
            TranscriptionSegment,
        )

        result = TranscriptionResult(
            segments=[
                TranscriptionSegment(
                    id=0,
                    start=0.0,
                    end=2.5,
                    text="Hello world",
                    words=None,
                    language="en",
                )
            ],
            text="Hello world",
            language="en",
            language_confidence=0.98,
            duration_seconds=2.5,
            cached=False,
        )
        assert result.text == "Hello world"
        assert result.language == "en"
        assert result.language_confidence == 0.98
        assert result.duration_seconds == 2.5
        assert result.cached is False
        assert len(result.segments) == 1

    def test_stt_stats_dataclass(self) -> None:
        """STTStats should have required fields (REQ-U-004)."""
        from smart_file_manager.services.stt_models import STTStats

        stats = STTStats(
            total_analyses=10,
            cache_hits=3,
            total_duration_processed=500.0,
            avg_processing_time=1.5,
        )
        assert stats.total_analyses == 10
        assert stats.cache_hits == 3
        assert stats.total_duration_processed == 500.0
        assert stats.avg_processing_time == 1.5

    def test_stt_stats_cache_hit_rate(self) -> None:
        """STTStats should calculate cache hit rate correctly."""
        from smart_file_manager.services.stt_models import STTStats

        stats = STTStats(
            total_analyses=10,
            cache_hits=3,
            total_duration_processed=500.0,
            avg_processing_time=1.5,
        )
        assert stats.cache_hit_rate == 0.3

    def test_stt_stats_cache_hit_rate_zero_analyses(self) -> None:
        """STTStats cache_hit_rate should return 0.0 when no analyses."""
        from smart_file_manager.services.stt_models import STTStats

        stats = STTStats(
            total_analyses=0,
            cache_hits=0,
            total_duration_processed=0.0,
            avg_processing_time=0.0,
        )
        assert stats.cache_hit_rate == 0.0


class TestSTTServiceCore:
    """Tests for STTService core functionality (TASK-005)."""

    def test_stt_service_init_without_cache(self) -> None:
        """STTService should initialize without cache."""
        from smart_file_manager.services.stt_service import STTService

        service = STTService()
        assert service.cache is None
        assert service._model is None  # Lazy loading

    def test_stt_service_init_with_cache(self) -> None:
        """STTService should accept optional cache."""
        from unittest.mock import MagicMock

        from smart_file_manager.services.stt_service import STTService

        mock_cache = MagicMock()
        service = STTService(cache=mock_cache)
        assert service.cache == mock_cache

    def test_stt_service_init_with_settings(self) -> None:
        """STTService should accept settings parameters."""
        from smart_file_manager.services.stt_service import STTService

        service = STTService(
            model_size="base",
            device="cpu",
            compute_type="int8",
        )
        assert service._model_size == "base"
        assert service._device == "cpu"
        assert service._compute_type == "int8"

    def test_is_audio_file_mp3(self) -> None:
        """Should identify MP3 files as audio."""
        from pathlib import Path

        from smart_file_manager.services.stt_service import STTService

        service = STTService()
        assert service.is_audio_file(Path("test.mp3")) is True
        assert service.is_audio_file(Path("test.MP3")) is True

    def test_is_audio_file_wav(self) -> None:
        """Should identify WAV files as audio."""
        from pathlib import Path

        from smart_file_manager.services.stt_service import STTService

        service = STTService()
        assert service.is_audio_file(Path("test.wav")) is True

    def test_is_audio_file_flac(self) -> None:
        """Should identify FLAC files as audio."""
        from pathlib import Path

        from smart_file_manager.services.stt_service import STTService

        service = STTService()
        assert service.is_audio_file(Path("test.flac")) is True

    def test_is_audio_file_all_supported_formats(self) -> None:
        """Should identify all supported audio formats (REQ-U-001)."""
        from pathlib import Path

        from smart_file_manager.services.stt_service import STTService

        service = STTService()
        supported = ["mp3", "wav", "flac", "aac", "ogg", "m4a", "opus", "wma"]
        for fmt in supported:
            assert service.is_audio_file(Path(f"test.{fmt}")) is True

    def test_is_audio_file_unsupported(self) -> None:
        """Should return False for unsupported formats."""
        from pathlib import Path

        from smart_file_manager.services.stt_service import STTService

        service = STTService()
        assert service.is_audio_file(Path("test.txt")) is False
        assert service.is_audio_file(Path("test.jpg")) is False
        assert service.is_audio_file(Path("test.mp4")) is False

    def test_detect_device_auto_cpu(self) -> None:
        """_detect_device should return cpu when CUDA not available."""
        from unittest.mock import MagicMock, patch

        from smart_file_manager.services.stt_service import STTService

        service = STTService(device="auto")
        # Mock torch module for the lazy import
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        with patch.dict("sys.modules", {"torch": mock_torch}):
            device, compute_type = service._detect_device()
            assert device == "cpu"
            assert compute_type == "int8"

    def test_detect_device_explicit_cpu(self) -> None:
        """_detect_device should respect explicit cpu setting."""
        from smart_file_manager.services.stt_service import STTService

        service = STTService(device="cpu", compute_type="int8")
        device, compute_type = service._detect_device()
        assert device == "cpu"
        assert compute_type == "int8"

    def test_get_stats_initial(self) -> None:
        """get_stats should return initial stats with zeros."""
        from smart_file_manager.services.stt_models import STTStats
        from smart_file_manager.services.stt_service import STTService

        service = STTService()
        stats = service.get_stats()
        assert isinstance(stats, STTStats)
        assert stats.total_analyses == 0
        assert stats.cache_hits == 0

    def test_reset_stats(self) -> None:
        """reset_stats should reset all statistics to zero."""
        from smart_file_manager.services.stt_service import STTService

        service = STTService()
        # Manually set some stats
        service._stats.total_analyses = 10
        service._stats.cache_hits = 5

        service.reset_stats()

        stats = service.get_stats()
        assert stats.total_analyses == 0
        assert stats.cache_hits == 0


class TestSTTServiceBatchProcessing:
    """Tests for STTService batch processing (TASK-006)."""

    import pytest

    @pytest.mark.asyncio
    async def test_batch_analyze_single_file(self) -> None:
        """batch_analyze should handle single file."""
        from pathlib import Path
        from unittest.mock import AsyncMock, patch

        from smart_file_manager.services.stt_models import (
            TranscriptionResult,
            TranscriptionSegment,
        )
        from smart_file_manager.services.stt_service import STTService

        service = STTService()

        mock_result = TranscriptionResult(
            segments=[
                TranscriptionSegment(
                    id=0,
                    start=0.0,
                    end=2.0,
                    text="Hello",
                    words=None,
                    language="en",
                )
            ],
            text="Hello",
            language="en",
            language_confidence=0.95,
            duration_seconds=2.0,
            cached=False,
        )

        with patch.object(service, "analyze_audio", new_callable=AsyncMock) as mock:
            mock.return_value = mock_result
            paths = [Path("/test/audio.mp3")]
            results = await service.batch_analyze(paths)

            assert len(results) == 1
            assert results[0].text == "Hello"
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_analyze_multiple_files(self) -> None:
        """batch_analyze should handle multiple files."""
        from pathlib import Path
        from unittest.mock import AsyncMock, patch

        from smart_file_manager.services.stt_models import (
            TranscriptionResult,
            TranscriptionSegment,
        )
        from smart_file_manager.services.stt_service import STTService

        service = STTService()

        mock_result = TranscriptionResult(
            segments=[
                TranscriptionSegment(
                    id=0,
                    start=0.0,
                    end=2.0,
                    text="Test",
                    words=None,
                    language="en",
                )
            ],
            text="Test",
            language="en",
            language_confidence=0.95,
            duration_seconds=2.0,
            cached=False,
        )

        with patch.object(service, "analyze_audio", new_callable=AsyncMock) as mock:
            mock.return_value = mock_result
            paths = [
                Path("/test/audio1.mp3"),
                Path("/test/audio2.wav"),
                Path("/test/audio3.flac"),
            ]
            results = await service.batch_analyze(paths)

            assert len(results) == 3
            assert mock.call_count == 3

    @pytest.mark.asyncio
    async def test_batch_analyze_respects_concurrency_limit(self) -> None:
        """batch_analyze should respect max_concurrent limit."""
        import asyncio
        from pathlib import Path
        from unittest.mock import patch

        from smart_file_manager.services.stt_models import (
            TranscriptionResult,
            TranscriptionSegment,
        )
        from smart_file_manager.services.stt_service import STTService

        service = STTService()
        concurrent_count = 0
        max_concurrent_seen = 0

        async def tracking_analyze(*args, **kwargs):
            nonlocal concurrent_count, max_concurrent_seen
            concurrent_count += 1
            max_concurrent_seen = max(max_concurrent_seen, concurrent_count)
            await asyncio.sleep(0.01)
            concurrent_count -= 1
            return TranscriptionResult(
                segments=[
                    TranscriptionSegment(
                        id=0,
                        start=0.0,
                        end=1.0,
                        text="Test",
                        words=None,
                        language="en",
                    )
                ],
                text="Test",
                language="en",
                language_confidence=0.95,
                duration_seconds=1.0,
                cached=False,
            )

        with patch.object(service, "analyze_audio", side_effect=tracking_analyze):
            paths = [Path(f"/test/audio{i}.mp3") for i in range(10)]
            results = await service.batch_analyze(paths, max_concurrent=3)

            assert len(results) == 10
            assert max_concurrent_seen <= 3

    @pytest.mark.asyncio
    async def test_batch_analyze_skips_unsupported_files(self) -> None:
        """batch_analyze should skip unsupported files."""
        from pathlib import Path
        from unittest.mock import AsyncMock, patch

        from smart_file_manager.services.stt_models import (
            TranscriptionResult,
            TranscriptionSegment,
        )
        from smart_file_manager.services.stt_service import STTService

        service = STTService()

        mock_result = TranscriptionResult(
            segments=[
                TranscriptionSegment(
                    id=0,
                    start=0.0,
                    end=2.0,
                    text="Test",
                    words=None,
                    language="en",
                )
            ],
            text="Test",
            language="en",
            language_confidence=0.95,
            duration_seconds=2.0,
            cached=False,
        )

        with patch.object(service, "analyze_audio", new_callable=AsyncMock) as mock:
            mock.return_value = mock_result
            paths = [
                Path("/test/audio.mp3"),
                Path("/test/document.txt"),
                Path("/test/video.mp4"),
                Path("/test/audio2.wav"),
            ]
            results = await service.batch_analyze(paths)

            # Only 2 audio files should be processed
            assert len(results) == 2
            assert mock.call_count == 2

    @pytest.mark.asyncio
    async def test_batch_analyze_empty_list(self) -> None:
        """batch_analyze should handle empty list."""
        from smart_file_manager.services.stt_service import STTService

        service = STTService()
        results = await service.batch_analyze([])

        assert len(results) == 0


class TestSTTServiceCacheIntegration:
    """Tests for STTService cache integration (TASK-007)."""

    import pytest

    def test_compute_content_hash(self) -> None:
        """_compute_content_hash should return consistent SHA-256 hash."""
        from smart_file_manager.services.stt_service import STTService

        service = STTService()
        content = b"test audio content"

        hash1 = service._compute_content_hash(content)
        hash2 = service._compute_content_hash(content)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_compute_content_hash_different_content(self) -> None:
        """_compute_content_hash should return different hash for different content."""
        from smart_file_manager.services.stt_service import STTService

        service = STTService()

        hash1 = service._compute_content_hash(b"content1")
        hash2 = service._compute_content_hash(b"content2")

        assert hash1 != hash2

    def test_get_cache_key(self) -> None:
        """_get_cache_key should return properly formatted cache key."""
        from smart_file_manager.services.stt_service import STTService

        service = STTService()
        content_hash = "abc123"

        cache_key = service._get_cache_key(content_hash)

        assert cache_key == "stt:abc123"

    @pytest.mark.asyncio
    async def test_get_cached_result_no_cache(self) -> None:
        """_get_cached_result should return None when no cache configured."""
        from smart_file_manager.services.stt_service import STTService

        service = STTService(cache=None)
        result = await service._get_cached_result("test_hash")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_cached_result_cache_miss(self) -> None:
        """_get_cached_result should return None on cache miss."""
        from unittest.mock import AsyncMock, MagicMock

        from smart_file_manager.services.stt_service import STTService

        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value=None)

        service = STTService(cache=mock_cache)
        result = await service._get_cached_result("test_hash")

        assert result is None
        mock_cache.get.assert_called_once_with("stt:test_hash")

    @pytest.mark.asyncio
    async def test_get_cached_result_cache_hit(self) -> None:
        """_get_cached_result should return TranscriptionResult on cache hit."""
        from unittest.mock import AsyncMock, MagicMock

        from smart_file_manager.services.stt_service import STTService

        cached_data = {
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 2.0,
                    "text": "Hello",
                    "words": None,
                    "language": "en",
                }
            ],
            "text": "Hello",
            "language": "en",
            "language_confidence": 0.95,
            "duration_seconds": 2.0,
            "cached": False,
        }

        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value=cached_data)

        service = STTService(cache=mock_cache)
        result = await service._get_cached_result("test_hash")

        assert result is not None
        assert result.text == "Hello"
        assert result.cached is True  # Should be set to True for cache hit

    @pytest.mark.asyncio
    async def test_cache_result_no_cache(self) -> None:
        """_cache_result should do nothing when no cache configured."""
        from smart_file_manager.services.stt_models import (
            TranscriptionResult,
            TranscriptionSegment,
        )
        from smart_file_manager.services.stt_service import STTService

        service = STTService(cache=None)
        result = TranscriptionResult(
            segments=[
                TranscriptionSegment(
                    id=0, start=0.0, end=2.0, text="Test", words=None, language="en"
                )
            ],
            text="Test",
            language="en",
            language_confidence=0.95,
            duration_seconds=2.0,
            cached=False,
        )

        # Should not raise any error
        await service._cache_result("test_hash", result)

    @pytest.mark.asyncio
    async def test_cache_result_stores_data(self) -> None:
        """_cache_result should store result in cache."""
        from unittest.mock import AsyncMock, MagicMock

        from smart_file_manager.core.constants import STT_CACHE_TTL_SECONDS
        from smart_file_manager.services.stt_models import (
            TranscriptionResult,
            TranscriptionSegment,
        )
        from smart_file_manager.services.stt_service import STTService

        mock_cache = MagicMock()
        mock_cache.set = AsyncMock()

        service = STTService(cache=mock_cache)
        result = TranscriptionResult(
            segments=[
                TranscriptionSegment(
                    id=0, start=0.0, end=2.0, text="Test", words=None, language="en"
                )
            ],
            text="Test",
            language="en",
            language_confidence=0.95,
            duration_seconds=2.0,
            cached=False,
        )

        await service._cache_result("test_hash", result)

        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args
        assert call_args[0][0] == "stt:test_hash"
        assert call_args[1]["ttl"] == STT_CACHE_TTL_SECONDS

    @pytest.mark.asyncio
    async def test_cache_result_custom_ttl(self) -> None:
        """_cache_result should accept custom TTL."""
        from unittest.mock import AsyncMock, MagicMock

        from smart_file_manager.services.stt_models import (
            TranscriptionResult,
            TranscriptionSegment,
        )
        from smart_file_manager.services.stt_service import STTService

        mock_cache = MagicMock()
        mock_cache.set = AsyncMock()

        service = STTService(cache=mock_cache)
        result = TranscriptionResult(
            segments=[
                TranscriptionSegment(
                    id=0, start=0.0, end=2.0, text="Test", words=None, language="en"
                )
            ],
            text="Test",
            language="en",
            language_confidence=0.95,
            duration_seconds=2.0,
            cached=False,
        )

        custom_ttl = 3600
        await service._cache_result("test_hash", result, ttl=custom_ttl)

        call_args = mock_cache.set.call_args
        assert call_args[1]["ttl"] == custom_ttl

    @pytest.mark.asyncio
    async def test_cache_hit_updates_stats(self) -> None:
        """Cache hit should increment cache_hits and total_analyses stats."""
        import tempfile
        from pathlib import Path
        from unittest.mock import AsyncMock, MagicMock

        from smart_file_manager.services.stt_service import STTService

        # Create a temporary audio file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"fake audio content")
            temp_path = Path(f.name)

        try:
            cached_data = {
                "segments": [
                    {
                        "id": 0,
                        "start": 0.0,
                        "end": 2.0,
                        "text": "Cached",
                        "words": None,
                        "language": "en",
                    }
                ],
                "text": "Cached",
                "language": "en",
                "language_confidence": 0.95,
                "duration_seconds": 2.0,
                "cached": False,
            }

            mock_cache = MagicMock()
            mock_cache.get = AsyncMock(return_value=cached_data)

            service = STTService(cache=mock_cache)

            # Initial stats
            assert service.get_stats().cache_hits == 0
            assert service.get_stats().total_analyses == 0

            result = await service.analyze_audio(temp_path)

            # Stats after cache hit
            stats = service.get_stats()
            assert stats.cache_hits == 1
            assert stats.total_analyses == 1
            assert result.cached is True

        finally:
            temp_path.unlink()


class TestSTTServiceValidation:
    """Tests for STTService validation logic."""

    def test_validate_audio_file_unsupported_format(self) -> None:
        """_validate_audio_file should raise UnsupportedAudioFormatError."""
        import tempfile
        from pathlib import Path

        import pytest

        from smart_file_manager.core.exceptions import UnsupportedAudioFormatError
        from smart_file_manager.services.stt_service import STTService

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"not audio")
            temp_path = Path(f.name)

        try:
            service = STTService()
            with pytest.raises(UnsupportedAudioFormatError) as exc_info:
                service._validate_audio_file(temp_path)

            assert exc_info.value.format == "txt"
            assert "mp3" in exc_info.value.supported_formats
        finally:
            temp_path.unlink()

    def test_validate_audio_file_too_large(self) -> None:
        """_validate_audio_file should raise FileTooLargeError for large files."""
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        import pytest

        from smart_file_manager.core.exceptions import FileTooLargeError
        from smart_file_manager.services.stt_service import STTService

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"small audio")
            temp_path = Path(f.name)

        try:
            service = STTService()

            # Mock file size to exceed limit
            with patch.object(Path, "stat") as mock_stat:
                mock_stat.return_value.st_size = 200 * 1024 * 1024  # 200MB

                with pytest.raises(FileTooLargeError) as exc_info:
                    service._validate_audio_file(temp_path)

                assert exc_info.value.file_size_bytes == 200 * 1024 * 1024
        finally:
            temp_path.unlink()

    def test_validate_audio_duration_too_long(self) -> None:
        """_validate_audio_duration should raise AudioTooLongError."""
        from pathlib import Path

        import pytest

        from smart_file_manager.core.exceptions import AudioTooLongError
        from smart_file_manager.services.stt_service import STTService

        service = STTService()

        with pytest.raises(AudioTooLongError) as exc_info:
            service._validate_audio_duration(8000.0, Path("/test/audio.mp3"))

        assert exc_info.value.duration_seconds == 8000.0
        assert exc_info.value.max_duration_seconds == 7200.0

    def test_validate_audio_duration_within_limit(self) -> None:
        """_validate_audio_duration should not raise for valid duration."""
        from pathlib import Path

        from smart_file_manager.services.stt_service import STTService

        service = STTService()
        # Should not raise
        service._validate_audio_duration(3600.0, Path("/test/audio.mp3"))

    def test_analyze_audio_read_error(self) -> None:
        """analyze_audio should raise AudioProcessingError on read failure."""
        import asyncio
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        import pytest

        from smart_file_manager.core.exceptions import AudioProcessingError
        from smart_file_manager.services.stt_service import STTService

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(b"audio content")
            temp_path = Path(f.name)

        try:
            service = STTService()

            # Mock read_bytes to raise an error
            with patch.object(Path, "read_bytes", side_effect=OSError("Read error")):
                with pytest.raises(AudioProcessingError) as exc_info:
                    asyncio.run(service.analyze_audio(temp_path))

                assert "Read error" in str(exc_info.value)
                assert exc_info.value.audio_path == str(temp_path)
        finally:
            temp_path.unlink()


class TestSTTServiceDeviceDetection:
    """Tests for STTService device detection."""

    def test_detect_device_explicit_cuda(self) -> None:
        """_detect_device should respect explicit cuda setting."""
        from smart_file_manager.services.stt_service import STTService

        service = STTService(device="cuda", compute_type="float16")
        device, compute_type = service._detect_device()

        assert device == "cuda"
        assert compute_type == "float16"

    def test_detect_device_explicit_cpu_auto_compute(self) -> None:
        """_detect_device should set int8 for cpu when compute_type is auto."""
        from smart_file_manager.services.stt_service import STTService

        service = STTService(device="cpu", compute_type="auto")
        device, compute_type = service._detect_device()

        assert device == "cpu"
        assert compute_type == "int8"

    def test_detect_device_explicit_cuda_auto_compute(self) -> None:
        """_detect_device should set float16 for cuda when compute_type is auto."""
        from smart_file_manager.services.stt_service import STTService

        service = STTService(device="cuda", compute_type="auto")
        device, compute_type = service._detect_device()

        assert device == "cuda"
        assert compute_type == "float16"

    def test_detect_device_auto_cuda_available(self) -> None:
        """_detect_device should detect cuda when available."""
        from unittest.mock import MagicMock, patch

        from smart_file_manager.services.stt_service import STTService

        service = STTService(device="auto")

        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True

        with patch.dict("sys.modules", {"torch": mock_torch}):
            device, compute_type = service._detect_device()

            assert device == "cuda"
            assert compute_type == "float16"

    def test_detect_device_auto_no_torch(self) -> None:
        """_detect_device should fallback to cpu when torch not installed."""
        from unittest.mock import patch

        from smart_file_manager.services.stt_service import STTService

        service = STTService(device="auto")

        # Simulate torch import error
        with patch.dict("sys.modules", {"torch": None}):
            # Need to also patch the import to raise ImportError
            import builtins

            original_import = builtins.__import__

            def mock_import(name, *args, **kwargs):
                if name == "torch":
                    raise ImportError("No module named 'torch'")
                return original_import(name, *args, **kwargs)

            with patch.object(builtins, "__import__", side_effect=mock_import):
                device, compute_type = service._detect_device()

                assert device == "cpu"
                assert compute_type == "int8"


class TestTranscriptionResultSerialization:
    """Tests for TranscriptionResult serialization."""

    def test_to_dict_with_words(self) -> None:
        """to_dict should include word timestamps when present."""
        from smart_file_manager.services.stt_models import (
            TranscriptionResult,
            TranscriptionSegment,
            WordTimestamp,
        )

        result = TranscriptionResult(
            segments=[
                TranscriptionSegment(
                    id=0,
                    start=0.0,
                    end=2.0,
                    text="Hello world",
                    words=[
                        WordTimestamp(word="Hello", start=0.0, end=0.5, confidence=0.9),
                        WordTimestamp(word="world", start=0.6, end=1.0, confidence=0.95),
                    ],
                    language="en",
                )
            ],
            text="Hello world",
            language="en",
            language_confidence=0.98,
            duration_seconds=2.0,
            cached=False,
        )

        data = result.to_dict()

        assert data["text"] == "Hello world"
        assert len(data["segments"]) == 1
        assert data["segments"][0]["words"] is not None
        # to_dict returns a generator for words, convert to list
        words_list = list(data["segments"][0]["words"])
        assert len(words_list) == 2
        assert words_list[0]["word"] == "Hello"

    def test_from_dict_with_words(self) -> None:
        """from_dict should restore word timestamps."""
        from smart_file_manager.services.stt_models import TranscriptionResult

        data = {
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 2.0,
                    "text": "Hello world",
                    "words": [
                        {"word": "Hello", "start": 0.0, "end": 0.5, "confidence": 0.9},
                        {"word": "world", "start": 0.6, "end": 1.0, "confidence": 0.95},
                    ],
                    "language": "en",
                }
            ],
            "text": "Hello world",
            "language": "en",
            "language_confidence": 0.98,
            "duration_seconds": 2.0,
            "cached": False,
        }

        result = TranscriptionResult.from_dict(data)

        assert result.text == "Hello world"
        assert len(result.segments) == 1
        assert result.segments[0].words is not None
        assert len(result.segments[0].words) == 2
        assert result.segments[0].words[0].word == "Hello"

    def test_from_dict_without_words(self) -> None:
        """from_dict should handle segments without words."""
        from smart_file_manager.services.stt_models import TranscriptionResult

        data = {
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 2.0,
                    "text": "Hello world",
                    "words": None,
                    "language": "en",
                }
            ],
            "text": "Hello world",
            "language": "en",
            "language_confidence": 0.98,
            "duration_seconds": 2.0,
            "cached": False,
        }

        result = TranscriptionResult.from_dict(data)

        assert result.segments[0].words is None
