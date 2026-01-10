---
id: SPEC-VISION-001
version: "1.0.0"
status: "planned"
created: "2026-01-10"
updated: "2026-01-10"
author: "Developer"
priority: "high"
lifecycle: "spec-anchored"
dependencies:
  - SPEC-INFRA-001
  - SPEC-API-001
---

# SPEC-VISION-001: Phase 3 - Vision 분석 서비스 통합

## HISTORY

| 버전 | 날짜 | 작성자 | 변경사항 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-10 | Developer | 초기 SPEC 작성 |

---

## 1. 개요

### 1.1 목적

이미지 및 비디오 AI 분석을 위한 Vision 서비스를 구현한다. 기존 로컬 CLIP+BLIP 모델을 OpenRouter API 기반으로 교체하고, SPEC-API-001에서 구현된 OpenRouterClient를 활용하여 3-tier Fallback 체인, 캐싱, 비용 모니터링 기능을 통합한다.

### 1.2 범위

**핵심 구현 범위:**
- VisionService: 통합 Vision 분석 서비스 (이미지/비디오)
- ImageProcessor: 이미지 분석 (scene description, object detection, text extraction)
- VideoProcessor: 비디오 분석 (keyframe extraction, scene analysis)
- OpenRouterClient 통합: SPEC-API-001의 클라이언트 활용
- 캐시 통합: 분석 결과 캐싱 (7일 TTL)
- 로컬 Fallback: API 전체 실패 시 메타데이터 기반 기본 분석

**제외 범위:**
- 로컬 AI 모델 (CLIP, BLIP) - 완전 제거
- 오디오 분석 (SPEC-STT-001에서 별도 구현)
- 문서 OCR (SPEC-DOC-001에서 별도 구현)

### 1.3 SPEC 의존성

이 SPEC은 다음 선행 SPEC에 의존한다:

| SPEC ID | 컴포넌트 | 용도 |
|---------|----------|------|
| SPEC-INFRA-001 | Settings, CacheInterface, Exceptions | 인프라 기반 |
| SPEC-API-001 | OpenRouterClient, ModelConfig, CostTracker | API 호출 기반 |

### 1.4 관련 문서

- `REFACTORING_SPEC_v5.md`: 전체 리팩토링 명세
- `.moai/project/product.md`: Vision 분석 요구사항
- `.moai/project/tech.md`: OpenRouter 모델 티어 정보
- `.moai/project/structure.md`: 목표 디렉토리 구조

---

## 2. EARS 요구사항

### 2.1 Ubiquitous Requirements (시스템 전반 적용)

**[REQ-U-001]** 시스템은 **항상** 이미지 분석 요청 전에 콘텐츠 해시를 기반으로 캐시를 확인해야 한다.

**[REQ-U-002]** 시스템은 **항상** 성공한 분석 결과를 7일 TTL로 캐시에 저장해야 한다.

**[REQ-U-003]** 시스템은 **항상** API 분석 비용을 CostTracker를 통해 추적해야 한다.

**[REQ-U-004]** 시스템은 **항상** 분석 결과에 구조화된 JSON 형식을 사용해야 한다.

**[REQ-U-005]** 시스템은 **항상** 지원되는 이미지 형식(JPEG, PNG, GIF, WebP, BMP)만 처리해야 한다.

**[REQ-U-006]** 시스템은 **항상** 비디오 분석 시 키프레임을 추출하여 이미지로 분석해야 한다.

**[REQ-U-007]** 시스템은 **항상** 분석 메트릭(처리 시간, 사용 모델, 비용)을 결과에 포함해야 한다.

### 2.2 Event-Driven Requirements (이벤트 기반 동작)

**[REQ-E-001]** **WHEN** 이미지 분석이 요청되면 **THEN** 캐시를 확인하고, 캐시 히트 시 캐시된 결과를 반환해야 한다.

**[REQ-E-002]** **WHEN** 캐시 미스가 발생하면 **THEN** OpenRouterClient를 통해 API 분석을 요청해야 한다.

**[REQ-E-003]** **WHEN** Primary 모델(gemini-2.0-flash-001) 호출이 실패하면 **THEN** Fallback 1(qwen2.5-vl-32b-instruct)로 자동 전환해야 한다.

**[REQ-E-004]** **WHEN** Fallback 1 모델 호출이 실패하면 **THEN** Fallback 2(gemini-2.0-flash-exp:free)로 자동 전환해야 한다.

**[REQ-E-005]** **WHEN** 모든 API 모델이 실패하면 **THEN** 로컬 메타데이터 분석 결과를 반환해야 한다.

**[REQ-E-006]** **WHEN** 비디오 분석이 요청되면 **THEN** FFmpeg를 사용하여 키프레임을 추출해야 한다.

**[REQ-E-007]** **WHEN** 키프레임이 추출되면 **THEN** 대표 프레임(최대 5개)을 선택하여 이미지 분석을 수행해야 한다.

**[REQ-E-008]** **WHEN** 이미지 크기가 20MB를 초과하면 **THEN** 자동으로 리사이징(최대 4096px)하여 분석해야 한다.

**[REQ-E-009]** **WHEN** API 분석이 성공하면 **THEN** 결과를 캐시에 저장하고 비용을 업데이트해야 한다.

**[REQ-E-010]** **WHEN** 분석 요청 시 force_refresh=True이면 **THEN** 캐시를 무시하고 새로운 분석을 수행해야 한다.

### 2.3 State-Driven Requirements (상태 기반 동작)

**[REQ-S-001]** **IF** 일일 예산($1)이 초과된 상태이면 **THEN** Free 티어 모델만 사용해야 한다.

**[REQ-S-002]** **IF** 월간 예산($30)이 초과된 상태이면 **THEN** 유료 API 호출을 거부하고 Free 티어만 허용해야 한다.

**[REQ-S-003]** **IF** Redis가 사용 불가 상태이면 **THEN** MemoryCache를 사용하여 캐싱을 계속해야 한다.

**[REQ-S-004]** **IF** 비디오 길이가 10분을 초과하면 **THEN** 키프레임 샘플링 간격을 증가시켜야 한다.

**[REQ-S-005]** **IF** 이미지가 손상되었거나 디코딩 불가능하면 **THEN** CorruptedFileError를 발생시켜야 한다.

**[REQ-S-006]** **IF** OpenRouterClient가 초기화되지 않은 상태이면 **THEN** ConfigurationError를 발생시켜야 한다.

### 2.4 Unwanted Behavior Requirements (금지 동작)

**[REQ-N-001]** 시스템은 **지원되지 않는 이미지 형식이 입력되면** UnsupportedFormatError를 발생시켜야 한다.

**[REQ-N-002]** 시스템은 **파일이 존재하지 않으면** FileNotFoundError를 발생시켜야 한다.

**[REQ-N-003]** 시스템은 **API 응답이 유효하지 않은 JSON이면** APIResponseError를 발생시켜야 한다.

**[REQ-N-004]** 시스템은 **동일 콘텐츠에 대해 중복 API 호출을 허용하지 않아야** 한다 (Race Condition 방지).

**[REQ-N-005]** 시스템은 **예산 초과 시 유료 모델 호출을 시도하면** BudgetExceededError를 발생시켜야 한다.

**[REQ-N-006]** 시스템은 **비디오 코덱이 지원되지 않으면** UnsupportedFormatError를 발생시켜야 한다.

**[REQ-N-007]** 시스템은 **FFmpeg가 설치되지 않은 환경에서 비디오 분석을 시도하면** DependencyError를 발생시켜야 한다.

### 2.5 Optional Requirements (선택적 기능)

**[REQ-O-001]** **가능하면** 이미지에서 OCR을 수행하여 텍스트를 추출해야 한다.

**[REQ-O-002]** **가능하면** 객체 감지 결과에 바운딩 박스 좌표를 포함해야 한다.

**[REQ-O-003]** **가능하면** 비디오 분석 시 장면 전환을 감지하여 키프레임을 선택해야 한다.

**[REQ-O-004]** **가능하면** 분석 결과에 신뢰도 점수를 포함해야 한다.

**[REQ-O-005]** **가능하면** 얼굴 감지 및 표정 분석을 지원해야 한다.

**[REQ-O-006]** **가능하면** 다국어(한국어, 영어, 일본어) 분석 결과를 지원해야 한다.

---

## 3. 기술 명세

### 3.1 OpenRouter 모델 티어 (Vision 전용)

| 티어 | 모델 ID | 비용 (Input/1M) | 비용 (Output/1M) | 용도 |
|------|---------|-----------------|------------------|------|
| **Primary (Balanced)** | `google/gemini-2.0-flash-001` | $0.10 | $0.15 | 기본 프로덕션 |
| **Fallback 1 (Low-cost)** | `qwen/qwen2.5-vl-32b-instruct` | $0.05 | $0.10 | 한국어 최적화 |
| **Fallback 2 (Free)** | `google/gemini-2.0-flash-exp:free` | $0.00 | $0.00 | 예산 초과/테스트 |
| **Local** | N/A | $0.00 | $0.00 | API 전체 실패 시 |

### 3.2 Vision Fallback 체인

```
1. Primary: google/gemini-2.0-flash-001 (Balanced)
   - 타임아웃: 30초
   - 재시도: 지수 백오프 (최대 3회)

2. Fallback 1: qwen/qwen2.5-vl-32b-instruct (Low-cost)
   - 타임아웃: 30초
   - 재시도: 지수 백오프 (최대 2회)

3. Fallback 2: google/gemini-2.0-flash-exp:free (Free)
   - 타임아웃: 60초 (Free 티어 지연 허용)
   - 재시도: 지수 백오프 (최대 3회)

4. Local: 메타데이터 분석만 (API 호출 없음)
   - 파일 크기, 해상도, EXIF 정보
   - 기본 분류 (photo, screenshot, document, etc.)
```

### 3.3 이미지 분석 프롬프트 템플릿

```
Analyze this image and provide a structured JSON response with:
1. description: A detailed description of the image content (2-3 sentences)
2. objects: List of detected objects with confidence scores
3. scene: The overall scene type (indoor, outdoor, nature, urban, etc.)
4. text: Any visible text in the image (OCR)
5. tags: List of relevant tags for searchability
6. dominant_colors: Top 3 dominant colors in the image
7. quality: Image quality assessment (sharp, blurry, dark, etc.)

Respond ONLY with valid JSON, no additional text.
```

### 3.4 비디오 분석 전략

| 비디오 길이 | 키프레임 추출 전략 | 최대 프레임 수 |
|-------------|-------------------|----------------|
| 0-60초 | 5초 간격 | 12 프레임 |
| 1-5분 | 15초 간격 | 20 프레임 |
| 5-10분 | 30초 간격 | 20 프레임 |
| 10분 이상 | 60초 간격 | 30 프레임 |

대표 프레임 선택:
- 장면 변화가 큰 프레임 우선 선택
- 최대 5개의 대표 프레임만 API 분석
- 나머지 프레임은 유사도 기반 그룹화

### 3.5 지원 형식

**이미지 형식:**
| 형식 | MIME Type | 지원 |
|------|-----------|------|
| JPEG | image/jpeg | O |
| PNG | image/png | O |
| GIF | image/gif | O (첫 프레임만) |
| WebP | image/webp | O |
| BMP | image/bmp | O |
| TIFF | image/tiff | X (변환 필요) |
| HEIC | image/heic | X (변환 필요) |

**비디오 형식:**
| 형식 | 컨테이너 | 코덱 | 지원 |
|------|----------|------|------|
| MP4 | MPEG-4 | H.264/H.265 | O |
| MKV | Matroska | H.264/H.265/VP9 | O |
| AVI | AVI | MPEG-4 | O |
| MOV | QuickTime | H.264 | O |
| WebM | WebM | VP8/VP9 | O |
| WMV | WMV | WMV | X |

### 3.6 디렉토리 구조

```
src/
└── smart_file_manager/
    ├── services/
    │   ├── __init__.py
    │   ├── openrouter_client.py     # SPEC-API-001에서 구현됨
    │   ├── model_config.py          # SPEC-API-001에서 구현됨
    │   └── vision_service.py        # [NEW] 통합 Vision 서비스
    │
    ├── processors/
    │   ├── __init__.py
    │   ├── base_processor.py        # 추상 기반 클래스
    │   ├── image_processor.py       # [REFACTOR] 이미지 분석
    │   └── video_processor.py       # [REFACTOR] 비디오 분석
    │
    └── core/
        ├── exceptions.py            # VisionError 추가
        └── constants.py             # 상수 정의
```

### 3.7 예외 클래스 추가

```python
class VisionError(SmartFileManagerError):
    """Vision 분석 관련 기본 예외."""

class UnsupportedFormatError(VisionError):
    """지원되지 않는 파일 형식."""

class CorruptedFileError(VisionError):
    """손상된 파일."""

class DependencyError(VisionError):
    """필수 의존성 누락 (FFmpeg 등)."""

class AnalysisFailedError(VisionError):
    """분석 실패 (모든 Fallback 포함)."""
```

---

## 4. 인터페이스 설계

### 4.1 VisionService 클래스

```python
class VisionService:
    """통합 Vision 분석 서비스.

    Attributes:
        client: OpenRouterClient 인스턴스
        cache: CacheInterface 인스턴스
        image_processor: ImageProcessor 인스턴스
        video_processor: VideoProcessor 인스턴스
    """

    async def analyze_image(
        self,
        image_path: Path,
        *,
        force_refresh: bool = False,
        analysis_type: AnalysisType = AnalysisType.FULL,
    ) -> ImageAnalysisResult:
        """이미지 분석 수행."""

    async def analyze_video(
        self,
        video_path: Path,
        *,
        force_refresh: bool = False,
        max_frames: int = 5,
    ) -> VideoAnalysisResult:
        """비디오 분석 수행."""

    async def batch_analyze(
        self,
        paths: list[Path],
        *,
        concurrency: int = 5,
    ) -> list[AnalysisResult]:
        """배치 분석 수행."""

    async def get_analysis_stats(self) -> AnalysisStats:
        """분석 통계 조회."""
```

### 4.2 ImageProcessor 클래스

```python
class ImageProcessor:
    """이미지 분석 프로세서.

    OpenRouterClient를 사용하여 이미지 분석을 수행한다.
    """

    async def analyze(
        self,
        image_data: bytes,
        content_hash: str,
        *,
        force_refresh: bool = False,
    ) -> ImageAnalysisResult:
        """이미지 분석 수행."""

    def validate_format(self, image_path: Path) -> bool:
        """이미지 형식 검증."""

    def resize_if_needed(
        self,
        image_data: bytes,
        max_size: int = 4096,
    ) -> bytes:
        """필요시 이미지 리사이징."""

    def extract_metadata(self, image_path: Path) -> ImageMetadata:
        """EXIF 등 메타데이터 추출."""
```

### 4.3 VideoProcessor 클래스

```python
class VideoProcessor:
    """비디오 분석 프로세서.

    FFmpeg를 사용하여 키프레임을 추출하고 ImageProcessor로 분석한다.
    """

    async def analyze(
        self,
        video_path: Path,
        *,
        force_refresh: bool = False,
        max_frames: int = 5,
    ) -> VideoAnalysisResult:
        """비디오 분석 수행."""

    def extract_keyframes(
        self,
        video_path: Path,
        interval: float,
    ) -> list[bytes]:
        """키프레임 추출."""

    def select_representative_frames(
        self,
        frames: list[bytes],
        max_count: int = 5,
    ) -> list[bytes]:
        """대표 프레임 선택."""

    def get_video_metadata(self, video_path: Path) -> VideoMetadata:
        """비디오 메타데이터 추출."""
```

### 4.4 응답 데이터 구조

```python
@dataclass
class ImageAnalysisResult:
    """이미지 분석 결과."""
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

@dataclass
class VideoAnalysisResult:
    """비디오 분석 결과."""
    summary: str
    frame_analyses: list[ImageAnalysisResult]
    scene_changes: list[SceneChange]
    duration_seconds: float
    metadata: VideoMetadata
    model_used: str
    total_cost: float
    cached: bool
    processing_time_ms: float

@dataclass
class DetectedObject:
    """감지된 객체."""
    name: str
    confidence: float
    bounding_box: BoundingBox | None = None

@dataclass
class ImageMetadata:
    """이미지 메타데이터."""
    width: int
    height: int
    format: str
    size_bytes: int
    exif: dict[str, Any] | None = None
    content_hash: str

@dataclass
class VideoMetadata:
    """비디오 메타데이터."""
    width: int
    height: int
    duration_seconds: float
    fps: float
    codec: str
    size_bytes: int
    content_hash: str
```

---

## 5. 제약사항

### 5.1 기술적 제약

- Python 3.11 이상 필수
- OpenRouterClient (SPEC-API-001) 필수
- FFmpeg 설치 필요 (비디오 분석)
- Pillow >= 10.2.0 필수
- opencv-python-headless >= 4.9.0 필수

### 5.2 성능 제약

| 항목 | 목표 |
|------|------|
| 이미지 분석 시간 (P95) | < 3초 |
| 비디오 분석 시간 (1분 영상) | < 30초 |
| 캐시 조회 시간 | < 10ms |
| 키프레임 추출 시간 (1분 영상) | < 5초 |
| 메모리 사용량 (이미지 분석) | < 500MB |
| 메모리 사용량 (비디오 분석) | < 1GB |

### 5.3 파일 크기 제약

| 항목 | 제한 |
|------|------|
| 이미지 최대 크기 | 20MB |
| 이미지 최대 해상도 | 8192 x 8192 px |
| 비디오 최대 크기 | 500MB |
| 비디오 최대 길이 | 30분 |

### 5.4 비용 제약

| 항목 | 제한 |
|------|------|
| 일일 예산 | $1.00 |
| 월간 예산 | $30.00 |
| Free 티어 | 무제한 |

---

## 6. 추적성

### 6.1 선행/후속 SPEC

| 관계 | SPEC ID | 설명 |
|------|---------|------|
| 선행 | SPEC-INFRA-001 | 인프라 준비 (Settings, Cache, Exceptions) |
| 선행 | SPEC-API-001 | OpenRouter API 클라이언트 |
| 후속 | SPEC-DOC-001 | 문서 프로세서 (OCR 전용) |
| 후속 | SPEC-STT-001 | 음성 변환 서비스 |

### 6.2 TAG 추적

| TAG ID | 요구사항 | 테스트 케이스 |
|--------|----------|---------------|
| VIS-001-U001 | REQ-U-001 | test_cache_checked_before_analysis |
| VIS-001-U002 | REQ-U-002 | test_result_cached_with_7day_ttl |
| VIS-001-U003 | REQ-U-003 | test_cost_tracked_on_analysis |
| VIS-001-E001 | REQ-E-001 | test_cache_hit_returns_cached_result |
| VIS-001-E002 | REQ-E-002 | test_api_called_on_cache_miss |
| VIS-001-E003 | REQ-E-003 | test_fallback_to_qwen_on_primary_failure |
| VIS-001-E004 | REQ-E-004 | test_fallback_to_free_on_qwen_failure |
| VIS-001-E005 | REQ-E-005 | test_local_fallback_on_all_api_failure |
| VIS-001-E006 | REQ-E-006 | test_keyframe_extraction_with_ffmpeg |
| VIS-001-E007 | REQ-E-007 | test_representative_frame_selection |
| VIS-001-E008 | REQ-E-008 | test_auto_resize_large_images |
| VIS-001-S001 | REQ-S-001 | test_free_tier_on_daily_budget_exceeded |
| VIS-001-S002 | REQ-S-002 | test_reject_paid_on_monthly_budget_exceeded |
| VIS-001-N001 | REQ-N-001 | test_unsupported_format_error |
| VIS-001-N002 | REQ-N-002 | test_file_not_found_error |
| VIS-001-N004 | REQ-N-004 | test_no_duplicate_api_calls |
| VIS-001-N007 | REQ-N-007 | test_ffmpeg_dependency_error |

### 6.3 레거시 파일 매핑

| v4.0 파일 | v5.0 파일 | 변경 유형 |
|-----------|-----------|----------|
| `ai-services/ai_vision_service.py` | `services/vision_service.py` | REPLACE |
| `ai-services/image_processor.py` | `processors/image_processor.py` | REFACTOR |
| `ai-services/video_processor.py` | `processors/video_processor.py` | REFACTOR |
| `ai-services/multimedia_processor.py` | (삭제) | SPLIT |

---

## 7. 리스크 분석

### 7.1 API 가용성 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| OpenRouter 서비스 중단 | 낮음 | 높음 | 3단계 Fallback + 로컬 분석 |
| 특정 모델 비활성화 | 중간 | 중간 | 동적 Fallback 체인 |
| Rate Limit 초과 | 중간 | 낮음 | 지수 백오프 + Retry-After |

### 7.2 성능 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| 대용량 이미지 처리 지연 | 중간 | 중간 | 자동 리사이징 |
| 비디오 키프레임 추출 지연 | 중간 | 중간 | 샘플링 간격 조정 |
| 캐시 미스 폭주 | 낮음 | 높음 | Race Condition 방지 |

### 7.3 의존성 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| FFmpeg 미설치 | 중간 | 높음 | 명확한 에러 메시지 + 문서화 |
| Pillow 버전 호환성 | 낮음 | 중간 | 버전 고정 |
| OpenCV 호환성 | 낮음 | 중간 | headless 버전 사용 |

---

## 8. 용어 정의

| 용어 | 정의 |
|------|------|
| **Vision 분석** | AI 모델을 통한 이미지/비디오 콘텐츠 분석 |
| **키프레임** | 비디오에서 장면을 대표하는 중요한 프레임 |
| **장면 전환** | 비디오에서 시각적으로 다른 장면으로 바뀌는 지점 |
| **바운딩 박스** | 감지된 객체의 위치를 나타내는 사각형 영역 |
| **EXIF** | 이미지 파일에 포함된 메타데이터 표준 |
| **OCR** | Optical Character Recognition, 이미지에서 텍스트 추출 |
| **콘텐츠 해시** | 파일 콘텐츠의 SHA256 해시값 |
| **Fallback 체인** | Primary 모델 실패 시 순차적으로 대체 모델을 시도하는 체계 |
