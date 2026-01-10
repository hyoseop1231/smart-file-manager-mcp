---
id: SPEC-STT-001
document: plan
version: "1.0.0"
created: "2026-01-10"
updated: "2026-01-10"
---

# SPEC-STT-001: 구현 계획

## 1. 마일스톤 개요

### Primary Goal: 핵심 STT 서비스 구현

Faster-Whisper 기반 핵심 STT 기능 구현 및 기존 인프라 통합

| 작업 | 우선순위 | 복잡도 | 의존성 |
|------|----------|--------|--------|
| 환경 변수 및 Settings 확장 | High | Low | SPEC-INFRA-001 |
| STT 데이터 모델 정의 | High | Low | - |
| STTService 핵심 구현 | High | High | Faster-Whisper |
| 캐시 통합 | High | Medium | CacheInterface |
| 단위 테스트 작성 | High | Medium | pytest |

### Secondary Goal: 고급 기능 및 최적화

배치 처리, 통계, GPU 최적화

| 작업 | 우선순위 | 복잡도 | 의존성 |
|------|----------|--------|--------|
| batch_analyze() 구현 | Medium | Medium | Primary Goal |
| 통계 추적 시스템 | Medium | Low | Primary Goal |
| GPU/CPU 자동 감지 | Medium | Medium | torch |
| 청크 분할 처리 | Medium | High | Primary Goal |

### Final Goal: 통합 및 문서화

전체 시스템 통합 및 품질 검증

| 작업 | 우선순위 | 복잡도 | 의존성 |
|------|----------|--------|--------|
| 통합 테스트 | Low | Medium | Secondary Goal |
| 성능 벤치마크 | Low | Medium | Secondary Goal |
| API 문서화 | Low | Low | Final Goal |

---

## 2. 기술 접근 방식

### 2.1 아키텍처 설계

```
                    +-----------------+
                    |   STTService    |
                    +-----------------+
                    |                 |
        +-----------+-----------+     |
        |                       |     |
   +----v----+            +----v----+ |
   |  Cache  |            | Faster  | |
   |Interface|            | Whisper | |
   +---------+            +---------+ |
        |                       |     |
   +----v----+            +----v----+ |
   |  Redis  |            |  CUDA/  | |
   | (L2캐시)|            |   CPU   | |
   +---------+            +---------+ |
                                      |
                    +-----------------+
                    | AudioMetadata   |
                    | (mutagen)       |
                    +-----------------+
```

### 2.2 핵심 구현 전략

#### Phase 1: 데이터 모델 정의

```python
# services/stt_models.py
from pydantic import BaseModel, Field
from typing import Optional

class WordTimestamp(BaseModel):
    """단어별 타임스탬프"""
    word: str
    start: float
    end: float
    probability: float

class TranscriptionSegment(BaseModel):
    """발화 세그먼트"""
    start: float
    end: float
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    words: list[WordTimestamp] | None = None

class AudioMetadata(BaseModel):
    """오디오 메타데이터"""
    duration_seconds: float
    sample_rate: int
    channels: int
    codec: str | None = None
    bitrate: int | None = None
    # 음악 태그 (선택)
    title: str | None = None
    artist: str | None = None
    album: str | None = None

class AudioAnalysisResult(BaseModel):
    """STT 분석 결과"""
    file_path: str
    content_hash: str
    transcription: str
    segments: list[TranscriptionSegment]
    detected_language: str
    language_probability: float
    audio_duration_seconds: float
    processing_time_ms: float
    realtime_factor: float
    model_used: str
    device_used: str
    cached: bool
    audio_metadata: AudioMetadata | None = None

class STTStats(BaseModel):
    """STT 통계"""
    total_analyses: int
    cached_analyses: int
    api_analyses: int
    total_audio_seconds: float
    total_processing_time_ms: float
    average_realtime_factor: float
    devices_used: dict[str, int]
```

#### Phase 2: Settings 확장

```python
# core/config.py 추가 필드
class Settings(BaseSettings):
    # ... 기존 필드 ...

    # STT Configuration
    whisper_model_size: str = Field(
        default="large-v3",
        description="Whisper model size (tiny/base/small/medium/large-v3)",
    )
    whisper_device: str = Field(
        default="auto",
        description="Inference device (auto/cuda/cpu)",
    )
    whisper_compute_type: str = Field(
        default="auto",
        description="Compute type (auto/float16/int8)",
    )
    whisper_language: str | None = Field(
        default=None,
        description="Force language (None for auto-detection)",
    )
    stt_max_duration_seconds: int = Field(
        default=7200,
        ge=60,
        description="Maximum audio duration in seconds",
    )
    stt_max_file_size_mb: int = Field(
        default=100,
        ge=1,
        description="Maximum file size in MB",
    )
    stt_enable_vad: bool = Field(
        default=True,
        description="Enable Voice Activity Detection",
    )
    stt_batch_size: int = Field(
        default=16,
        ge=1,
        description="Batch processing size",
    )
```

#### Phase 3: STTService 핵심 구현

```python
# services/stt_service.py
class STTService:
    """Faster-Whisper 기반 STT 서비스"""

    def __init__(
        self,
        cache: CacheInterface | None = None,
        model_size: str = "large-v3",
        device: str = "auto",
        compute_type: str = "auto",
    ) -> None:
        self.cache = cache
        self.model_size = model_size
        self.device = self._detect_device(device)
        self.compute_type = self._detect_compute_type(compute_type)

        # Lazy loading
        self._model: WhisperModel | None = None
        self._model_lock = asyncio.Lock()

        # Statistics
        self._stats = STTStats(...)
        self._in_flight: dict[str, asyncio.Future] = {}
        self._in_flight_lock = asyncio.Lock()

    def _detect_device(self, device: str) -> str:
        """CUDA 가용성 자동 감지"""
        if device == "auto":
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device

    def _detect_compute_type(self, compute_type: str) -> str:
        """디바이스에 따른 최적 연산 타입"""
        if compute_type == "auto":
            return "float16" if self.device == "cuda" else "int8"
        return compute_type

    async def _ensure_model_loaded(self) -> WhisperModel:
        """모델 지연 로딩"""
        if self._model is None:
            async with self._model_lock:
                if self._model is None:
                    from faster_whisper import WhisperModel
                    self._model = WhisperModel(
                        self.model_size,
                        device=self.device,
                        compute_type=self.compute_type,
                    )
        return self._model

    async def analyze_audio(
        self,
        audio_path: Path,
        *,
        force_refresh: bool = False,
        language: str | None = None,
        word_timestamps: bool = True,
    ) -> AudioAnalysisResult:
        """오디오 파일 분석"""
        # 1. 파일 검증
        self._validate_file(audio_path)

        # 2. content_hash 계산
        content_hash = self._compute_content_hash(audio_path)

        # 3. 캐시 확인
        if not force_refresh and self.cache:
            cached = await self.cache.get(f"stt:{content_hash}")
            if cached:
                return AudioAnalysisResult(**cached, cached=True)

        # 4. 중복 요청 방지
        async with self._in_flight_lock:
            if content_hash in self._in_flight:
                return await self._in_flight[content_hash]
            future = asyncio.get_event_loop().create_future()
            self._in_flight[content_hash] = future

        try:
            # 5. STT 처리
            result = await self._transcribe(
                audio_path, content_hash, language, word_timestamps
            )

            # 6. 캐시 저장
            if self.cache:
                await self.cache.set(
                    f"stt:{content_hash}",
                    result.model_dump(exclude={"cached"})
                )

            # 7. 통계 업데이트
            self._update_stats(result)

            future.set_result(result)
            return result

        finally:
            async with self._in_flight_lock:
                self._in_flight.pop(content_hash, None)
```

### 2.3 테스트 전략

#### 단위 테스트 구조

```
tests/
├── services/
│   ├── test_stt_service.py
│   └── test_stt_models.py
└── integration/
    └── test_stt_integration.py
```

#### 핵심 테스트 케이스

1. **모델 초기화**: CUDA/CPU 자동 감지
2. **포맷 검증**: 지원/비지원 포맷 처리
3. **캐시 동작**: 히트/미스 시나리오
4. **타임스탬프**: 단어/세그먼트 타임스탬프 정확성
5. **에러 처리**: 파일 크기/길이 제한 검증
6. **배치 처리**: 동시성 제어 검증

---

## 3. 리스크 및 대응 전략

### 3.1 기술 리스크

| 리스크 | 영향도 | 대응 전략 |
|--------|--------|----------|
| CUDA 미지원 환경 | Medium | CPU int8 폴백 구현 |
| 모델 로드 시간 | Low | 지연 로딩 + 워밍업 엔드포인트 |
| 메모리 부족 | High | 청크 처리 + OOM 핸들링 |
| FFmpeg 미설치 | Medium | 의존성 체크 + 명확한 에러 메시지 |

### 3.2 통합 리스크

| 리스크 | 영향도 | 대응 전략 |
|--------|--------|----------|
| Redis 연결 실패 | Low | 메모리 캐시 폴백 (SPEC-INFRA-001) |
| Settings 충돌 | Low | 네임스페이스 분리 (STT_*) |

---

## 4. 성능 목표

### 4.1 벤치마크 기준

| 메트릭 | GPU (CUDA) | CPU (int8) |
|--------|------------|------------|
| Realtime Factor | <= 0.25x | <= 1.0x |
| 1분 오디오 처리 | < 15초 | < 60초 |
| 모델 로드 시간 | < 30초 | < 30초 |
| 캐시 히트 응답 | < 10ms | < 10ms |

### 4.2 메모리 사용량

| 환경 | 목표 |
|------|------|
| GPU VRAM | < 8GB |
| CPU RAM | < 4GB |
| Peak Memory | < 12GB (GPU) / < 6GB (CPU) |

---

## 5. 검증 체크리스트

### 5.1 기능 검증

- [ ] MP3, WAV, FLAC, OGG, M4A 포맷 처리
- [ ] 한국어 인식 정확도 >= 90%
- [ ] 영어 인식 정확도 >= 95%
- [ ] 단어 타임스탬프 생성
- [ ] 캐시 히트/미스 동작
- [ ] 배치 처리 동시성 제어

### 5.2 성능 검증

- [ ] GPU Realtime Factor <= 0.25x
- [ ] CPU Realtime Factor <= 1.0x
- [ ] 캐시 히트 응답 < 10ms
- [ ] 메모리 사용량 목표 달성

### 5.3 품질 검증

- [ ] 테스트 커버리지 >= 85%
- [ ] ruff 린트 통과
- [ ] mypy 타입 체크 통과
- [ ] 문서화 완료

---

## 6. 참조

### 6.1 관련 SPEC

- `SPEC-INFRA-001`: 캐시/설정 인프라 (의존)
- `SPEC-API-001`: OpenRouter 클라이언트 패턴 (참조)
- `SPEC-VISION-001`: VisionService 패턴 (참조)

### 6.2 레거시 코드

- `ai-services/audio_processor.py`: 기존 Whisper 구현 (참고용)
