---
id: SPEC-STT-001
version: "1.0.0"
status: "completed"
created: "2026-01-10"
updated: "2026-01-10"
author: "Developer"
priority: "high"
lifecycle: "spec-anchored"
dependencies:
  - SPEC-INFRA-001
  - SPEC-API-001
---

# SPEC-STT-001: Phase 5 - STT (Speech-to-Text) Service

## HISTORY

| 버전 | 날짜 | 작성자 | 변경사항 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-10 | Developer | 초기 SPEC 작성 |
| 1.0.1 | 2026-01-10 | Developer | TDD 구현 완료 (69 tests, TRUST 5 검증) |

---

## 1. 개요

### 1.1 목적

Smart File Manager MCP의 음성-텍스트 변환(STT) 서비스를 Faster-Whisper (CTranslate2 기반)로 구현하여 기존 Whisper base 모델 대비 4배 이상의 속도 향상과 한국어 인식 정확도 개선을 달성한다.

### 1.2 범위

- Faster-Whisper large-v3 모델 기반 STT 서비스 구현
- 기존 인프라(Settings, Cache)와의 통합
- 오디오 파일 처리 및 메타데이터 추출
- 비동기 처리 및 배치 분석 지원
- 단어 타임스탬프 및 신뢰도 점수 제공

### 1.3 관련 문서

- `.moai/project/product.md`: 제품 요구사항 (STT 4x 실시간 속도 목표)
- `.moai/project/tech.md`: 기술 스택 (Faster-Whisper 1.0+, CUDA/CPU 지원)
- `SPEC-INFRA-001`: 캐시/설정 인프라 (의존)
- `SPEC-API-001`: OpenRouter 클라이언트 (참조 패턴)

### 1.4 용어 정의

| 용어 | 정의 |
|------|------|
| Faster-Whisper | CTranslate2 기반 Whisper 최적화 구현체 |
| CTranslate2 | Transformer 모델 추론 최적화 라이브러리 |
| VAD | Voice Activity Detection (음성 활동 감지) |
| Realtime Factor | 처리 시간 / 오디오 길이 비율 (낮을수록 빠름) |

---

## 2. EARS 요구사항

### 2.1 Ubiquitous Requirements (시스템 전반)

**[REQ-U-001]** 시스템은 **항상** 지원 오디오 포맷(mp3, wav, flac, aac, ogg, m4a, opus, wma)에 대해 STT 처리를 수행할 수 있어야 한다.

**[REQ-U-002]** 시스템은 **항상** content_hash 기반 캐싱을 통해 동일 파일의 중복 처리를 방지해야 한다.

**[REQ-U-003]** 시스템은 **항상** 처리 결과에 단어 타임스탬프, 신뢰도 점수, 감지 언어를 포함해야 한다.

**[REQ-U-004]** 시스템은 **항상** 처리 통계(총 처리 수, 캐시 히트율, 평균 처리 시간)를 추적해야 한다.

**[REQ-U-005]** 시스템은 **항상** 실시간 대비 4배 이상의 처리 속도(0.25x Realtime Factor 이하)를 달성해야 한다.

### 2.2 Event-Driven Requirements (이벤트 기반)

**[REQ-E-001]** **WHEN** STTService가 초기화되면 **THEN** Faster-Whisper large-v3 모델을 로드하고 사용 가능한 디바이스(CUDA/CPU)를 감지해야 한다.

**[REQ-E-002]** **WHEN** analyze_audio() 메서드가 호출되면 **THEN** 캐시 조회 -> 음성 변환 -> 결과 캐싱 -> 반환 순서로 처리해야 한다.

**[REQ-E-003]** **WHEN** 오디오 파일이 지원 포맷이 아니면 **THEN** UnsupportedFormatError를 발생시켜야 한다.

**[REQ-E-004]** **WHEN** 캐시에서 결과를 찾으면 **THEN** cached=True 플래그와 함께 즉시 반환해야 한다.

**[REQ-E-005]** **WHEN** batch_analyze()가 호출되면 **THEN** Semaphore 기반 동시성 제어로 병렬 처리해야 한다.

**[REQ-E-006]** **WHEN** 오디오 처리가 완료되면 **THEN** 처리 시간, 오디오 길이, Realtime Factor를 계산하여 통계에 반영해야 한다.

### 2.3 State-Driven Requirements (상태 기반)

**[REQ-S-001]** **IF** CUDA 지원 GPU가 사용 가능하면 **THEN** float16 정밀도로 GPU 추론을 수행해야 한다.

**[REQ-S-002]** **IF** GPU가 사용 불가능하면 **THEN** int8 양자화된 CPU 추론으로 폴백해야 한다.

**[REQ-S-003]** **IF** 오디오 길이가 max_duration_seconds를 초과하면 **THEN** 청크 단위로 분할 처리해야 한다.

**[REQ-S-004]** **IF** 모델이 아직 로드되지 않았으면 **THEN** 첫 요청 시 지연 로딩(lazy loading)을 수행해야 한다.

**[REQ-S-005]** **IF** detected_language 신뢰도가 낮으면 **THEN** 한국어(ko)를 기본 언어로 사용해야 한다.

### 2.4 Unwanted Behavior Requirements (금지 동작)

**[REQ-N-001]** 시스템은 **2시간을 초과하는 오디오 파일**에 대해 처리를 거부하고 AudioTooLongError를 발생시켜야 한다.

**[REQ-N-002]** 시스템은 **100MB를 초과하는 오디오 파일**에 대해 처리를 거부하고 FileTooLargeError를 발생시켜야 한다.

**[REQ-N-003]** 시스템은 **손상된 오디오 파일**에 대해 AudioProcessingError를 발생시켜야 한다.

**[REQ-N-004]** 시스템은 **메모리 부족 상황**에서 ResourceExhaustedError를 발생시키고 graceful degradation을 수행해야 한다.

### 2.5 Optional Requirements (선택 기능)

**[REQ-O-001]** **가능하면** VAD(Voice Activity Detection)를 활성화하여 무음 구간을 스킵하고 처리 속도를 향상해야 한다.

**[REQ-O-002]** **가능하면** 음악 파일(artist/album 태그 존재)에 대해 STT 처리를 스킵하는 옵션을 제공해야 한다.

**[REQ-O-003]** **가능하면** 실시간 스트리밍 STT를 위한 generator 기반 API를 제공해야 한다.

---

## 3. 기술 명세

### 3.1 클래스 구조

```
src/smart_file_manager/
├── services/
│   ├── __init__.py         # STTService 추가 export
│   ├── stt_service.py      # STT 서비스 메인 구현
│   └── stt_models.py       # Pydantic 데이터 모델
├── processors/
│   └── audio_processor.py  # 오디오 프로세서 (메타데이터 추출)
└── core/
    ├── config.py           # STT 관련 설정 추가
    └── constants.py        # SUPPORTED_AUDIO_FORMATS 추가
```

### 3.2 핵심 데이터 모델

```python
class TranscriptionSegment(BaseModel):
    """개별 발화 세그먼트"""
    start: float          # 시작 시간 (초)
    end: float            # 종료 시간 (초)
    text: str             # 변환된 텍스트
    confidence: float     # 신뢰도 (0-1)
    words: list[WordTimestamp] | None  # 단어별 타임스탬프

class WordTimestamp(BaseModel):
    """단어별 타임스탬프"""
    word: str
    start: float
    end: float
    probability: float

class AudioAnalysisResult(BaseModel):
    """오디오 분석 결과"""
    file_path: str
    content_hash: str
    transcription: str           # 전체 변환 텍스트
    segments: list[TranscriptionSegment]
    detected_language: str       # 감지된 언어 코드
    language_probability: float  # 언어 감지 신뢰도
    audio_duration_seconds: float
    processing_time_ms: float
    realtime_factor: float       # 처리시간/오디오길이
    model_used: str
    device_used: str             # cuda/cpu
    cached: bool
    audio_metadata: AudioMetadata | None
```

### 3.3 환경 변수 추가 (Settings)

| 변수명 | 타입 | 기본값 | 설명 |
|--------|------|--------|------|
| `WHISPER_MODEL_SIZE` | str | large-v3 | Whisper 모델 크기 |
| `WHISPER_DEVICE` | str | auto | 추론 디바이스 (auto/cuda/cpu) |
| `WHISPER_COMPUTE_TYPE` | str | auto | 연산 타입 (auto/float16/int8) |
| `WHISPER_LANGUAGE` | str | None | 강제 언어 (None=자동감지) |
| `STT_MAX_DURATION_SECONDS` | int | 7200 | 최대 오디오 길이 (초) |
| `STT_MAX_FILE_SIZE_MB` | int | 100 | 최대 파일 크기 (MB) |
| `STT_ENABLE_VAD` | bool | True | VAD 활성화 여부 |
| `STT_BATCH_SIZE` | int | 16 | 배치 처리 크기 |

### 3.4 의존성 패키지 추가

```toml
[project.dependencies]
faster-whisper = ">=1.0.0"
mutagen = ">=1.47.0"     # 오디오 메타데이터
torch = ">=2.2.0"        # CUDA 지원
```

### 3.5 인터페이스 설계

```python
class STTService:
    """STT 서비스 메인 클래스"""

    def __init__(
        self,
        cache: CacheInterface | None = None,
        model_size: str = "large-v3",
        device: str = "auto",
        compute_type: str = "auto",
    ) -> None: ...

    async def analyze_audio(
        self,
        audio_path: Path,
        *,
        force_refresh: bool = False,
        language: str | None = None,
        word_timestamps: bool = True,
    ) -> AudioAnalysisResult: ...

    async def batch_analyze(
        self,
        paths: list[Path],
        *,
        concurrency: int = 3,
        force_refresh: bool = False,
    ) -> list[AudioAnalysisResult]: ...

    async def get_analysis_stats(self) -> STTStats: ...

    def is_audio_file(self, file_path: Path) -> bool: ...

    def reset_stats(self) -> None: ...
```

---

## 4. 통합 포인트

### 4.1 SPEC-INFRA-001 통합 (캐시/설정)

- `Settings` 클래스에 STT 관련 환경 변수 추가
- `CacheInterface`를 통한 결과 캐싱 (`stt:{content_hash}` 키 패턴)
- 캐시 TTL은 기존 `CACHE_TTL_SECONDS` 설정 재사용

### 4.2 SPEC-API-001 참조 패턴

- VisionService와 동일한 패턴: `_update_stats()`, `_in_flight` 중복 요청 방지
- `batch_analyze()` 동시성 제어 패턴 재사용
- 통계 추적 모델 (`STTStats`) 패턴 일관성

### 4.3 향후 통합 (SPEC-EMBED-001)

- STT 결과 텍스트를 bge-m3 임베딩 서비스에 전달
- Qdrant 벡터 DB에 오디오 검색 인덱스 생성

---

## 5. 제약사항

### 5.1 기술적 제약

- Python 3.11+ 필수
- CUDA 12.x 권장 (GPU 가속용)
- FFmpeg 설치 필수 (오디오 포맷 변환)
- Faster-Whisper 1.0+ 필수

### 5.2 성능 제약

| 메트릭 | 목표값 | 측정 방법 |
|--------|--------|----------|
| Realtime Factor (GPU) | <= 0.25x | 처리시간/오디오길이 |
| Realtime Factor (CPU) | <= 1.0x | 처리시간/오디오길이 |
| 모델 로드 시간 | < 30초 | 첫 요청 시 측정 |
| 캐시 히트 응답 시간 | < 10ms | Redis 조회 시간 |
| 메모리 사용량 (GPU) | < 8GB VRAM | nvidia-smi |
| 메모리 사용량 (CPU) | < 4GB RAM | psutil |

### 5.3 품질 제약

- 한국어 인식 정확도 >= 90% (표준 발화)
- 영어 인식 정확도 >= 95% (표준 발화)
- 테스트 커버리지 >= 85%

---

## 6. 추적성

### 6.1 관련 SPEC

| SPEC ID | 관계 | 설명 |
|---------|------|------|
| SPEC-INFRA-001 | 의존 | 캐시/설정 인프라 |
| SPEC-API-001 | 참조 | OpenRouter 클라이언트 패턴 |
| SPEC-VISION-001 | 참조 | VisionService 패턴 |
| SPEC-EMBED-001 | 후속 | 임베딩 서비스 통합 |

### 6.2 TAG 추적

| TAG ID | 요구사항 | 테스트 케이스 |
|--------|----------|---------------|
| STT-001-U001 | REQ-U-001 | test_supported_audio_formats |
| STT-001-U002 | REQ-U-002 | test_cache_deduplication |
| STT-001-U003 | REQ-U-003 | test_result_contains_timestamps |
| STT-001-U004 | REQ-U-004 | test_statistics_tracking |
| STT-001-U005 | REQ-U-005 | test_realtime_factor_target |
| STT-001-E001 | REQ-E-001 | test_service_initialization |
| STT-001-E002 | REQ-E-002 | test_analyze_audio_flow |
| STT-001-E003 | REQ-E-003 | test_unsupported_format_error |
| STT-001-E004 | REQ-E-004 | test_cache_hit_returns_cached |
| STT-001-E005 | REQ-E-005 | test_batch_analyze_concurrency |
| STT-001-S001 | REQ-S-001 | test_cuda_float16_inference |
| STT-001-S002 | REQ-S-002 | test_cpu_int8_fallback |
| STT-001-N001 | REQ-N-001 | test_audio_too_long_error |
| STT-001-N002 | REQ-N-002 | test_file_too_large_error |

---

## 7. 레거시 분석

### 7.1 기존 코드 (ai-services/audio_processor.py)

| 항목 | 현재 구현 | 문제점 |
|------|----------|--------|
| 모델 | openai-whisper base | 속도 느림 (0.5x 실시간) |
| 추론 | 동기 처리 | 병렬 처리 불가 |
| 캐시 | 파일 기반 | 비효율적 |
| 메타데이터 | mutagen/eyed3 | 재사용 가능 |
| FFmpeg | 포맷 변환용 | 재사용 가능 |

### 7.2 마이그레이션 전략

1. **서비스 분리**: `AudioProcessor` -> `STTService` + `AudioProcessor`
   - STTService: Faster-Whisper 기반 STT 처리
   - AudioProcessor: 메타데이터 추출 전용 (선택적 구현)

2. **비동기 전환**: 동기 `transcribe()` -> 비동기 `analyze_audio()`

3. **캐시 통합**: 파일 기반 -> Redis (CacheInterface)

4. **모델 업그레이드**: whisper base -> faster-whisper large-v3

---

## 8. 참고 자료

### 8.1 외부 문서

- [Faster-Whisper GitHub](https://github.com/guillaumekln/faster-whisper)
- [CTranslate2 Documentation](https://opennmt.net/CTranslate2/)
- [Whisper Model Card](https://github.com/openai/whisper/blob/main/model-card.md)

### 8.2 프로젝트 내부 문서

- `/REFACTORING_SPEC_v5.md` - 전체 리팩토링 명세
- `/.moai/project/tech.md` - 기술 스택 상세
- `/.moai/project/product.md` - 제품 요구사항
