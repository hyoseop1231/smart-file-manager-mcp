---
id: SPEC-VISION-001
spec_ref: SPEC-VISION-001/spec.md
version: "1.0.0"
status: "planned"
created: "2026-01-10"
---

# SPEC-VISION-001: Implementation Plan

## 1. 개요

이 문서는 SPEC-VISION-001 (Vision 분석 서비스 통합)의 구현 계획을 정의한다.

## 2. 마일스톤

### Milestone 1: 기본 인프라 확장 (Priority: High)

**목표**: VisionService의 기반이 되는 예외 클래스와 상수를 정의한다.

| 태스크 | 설명 | 산출물 |
|--------|------|--------|
| VIS-M1-01 | Vision 관련 예외 클래스 추가 | `core/exceptions.py` |
| VIS-M1-02 | Vision 상수 정의 (지원 형식, 크기 제한 등) | `core/constants.py` |
| VIS-M1-03 | Vision 분석 결과 데이터 클래스 정의 | `services/vision_models.py` |

**의존성**: SPEC-INFRA-001, SPEC-API-001 완료 필수

**테스트 커버리지 목표**: 95%

---

### Milestone 2: ImageProcessor 구현 (Priority: High)

**목표**: 이미지 분석 프로세서를 OpenRouterClient와 통합하여 구현한다.

| 태스크 | 설명 | 산출물 |
|--------|------|--------|
| VIS-M2-01 | ImageProcessor 기본 클래스 구현 | `processors/image_processor.py` |
| VIS-M2-02 | 이미지 형식 검증 로직 구현 | `processors/image_processor.py` |
| VIS-M2-03 | 이미지 리사이징 로직 구현 | `processors/image_processor.py` |
| VIS-M2-04 | EXIF 메타데이터 추출 구현 | `processors/image_processor.py` |
| VIS-M2-05 | OpenRouterClient 연동 (분석 요청) | `processors/image_processor.py` |
| VIS-M2-06 | 캐시 통합 (조회/저장) | `processors/image_processor.py` |
| VIS-M2-07 | 로컬 Fallback 분석 구현 | `processors/image_processor.py` |
| VIS-M2-08 | ImageProcessor 단위 테스트 | `tests/processors/test_image_processor.py` |

**의존성**: Milestone 1 완료

**테스트 커버리지 목표**: 90%

---

### Milestone 3: VideoProcessor 구현 (Priority: High)

**목표**: 비디오 분석 프로세서를 FFmpeg 기반 키프레임 추출과 함께 구현한다.

| 태스크 | 설명 | 산출물 |
|--------|------|--------|
| VIS-M3-01 | VideoProcessor 기본 클래스 구현 | `processors/video_processor.py` |
| VIS-M3-02 | FFmpeg 키프레임 추출 구현 | `processors/video_processor.py` |
| VIS-M3-03 | 대표 프레임 선택 알고리즘 구현 | `processors/video_processor.py` |
| VIS-M3-04 | 비디오 메타데이터 추출 구현 | `processors/video_processor.py` |
| VIS-M3-05 | ImageProcessor 연동 (프레임 분석) | `processors/video_processor.py` |
| VIS-M3-06 | 분석 결과 통합 로직 구현 | `processors/video_processor.py` |
| VIS-M3-07 | FFmpeg 의존성 검사 구현 | `processors/video_processor.py` |
| VIS-M3-08 | VideoProcessor 단위 테스트 | `tests/processors/test_video_processor.py` |

**의존성**: Milestone 2 완료

**테스트 커버리지 목표**: 85%

---

### Milestone 4: VisionService 통합 (Priority: High)

**목표**: ImageProcessor와 VideoProcessor를 통합하는 VisionService를 구현한다.

| 태스크 | 설명 | 산출물 |
|--------|------|--------|
| VIS-M4-01 | VisionService 기본 클래스 구현 | `services/vision_service.py` |
| VIS-M4-02 | 파일 타입 라우팅 로직 구현 | `services/vision_service.py` |
| VIS-M4-03 | 배치 분석 기능 구현 | `services/vision_service.py` |
| VIS-M4-04 | 분석 통계 기능 구현 | `services/vision_service.py` |
| VIS-M4-05 | Race Condition 방지 로직 구현 | `services/vision_service.py` |
| VIS-M4-06 | VisionService 단위 테스트 | `tests/services/test_vision_service.py` |

**의존성**: Milestone 2, Milestone 3 완료

**테스트 커버리지 목표**: 90%

---

### Milestone 5: 통합 테스트 및 성능 최적화 (Priority: Medium)

**목표**: 전체 Vision 분석 파이프라인의 통합 테스트와 성능 최적화를 수행한다.

| 태스크 | 설명 | 산출물 |
|--------|------|--------|
| VIS-M5-01 | 이미지 분석 통합 테스트 | `tests/integration/test_vision_integration.py` |
| VIS-M5-02 | 비디오 분석 통합 테스트 | `tests/integration/test_vision_integration.py` |
| VIS-M5-03 | Fallback 체인 통합 테스트 | `tests/integration/test_vision_integration.py` |
| VIS-M5-04 | 캐시 통합 테스트 | `tests/integration/test_vision_integration.py` |
| VIS-M5-05 | 성능 벤치마크 (이미지 분석 시간) | 벤치마크 결과 문서 |
| VIS-M5-06 | 성능 벤치마크 (비디오 분석 시간) | 벤치마크 결과 문서 |
| VIS-M5-07 | 메모리 사용량 최적화 | 최적화된 코드 |

**의존성**: Milestone 4 완료

**테스트 커버리지 목표**: 90% (전체)

---

## 3. 기술적 접근 방식

### 3.1 아키텍처 설계

```
VisionService (통합 서비스)
    │
    ├── ImageProcessor
    │   ├── 형식 검증 (Pillow)
    │   ├── 리사이징 (Pillow)
    │   ├── 메타데이터 추출 (Pillow/EXIF)
    │   └── OpenRouterClient 연동
    │
    ├── VideoProcessor
    │   ├── 메타데이터 추출 (FFmpeg)
    │   ├── 키프레임 추출 (FFmpeg)
    │   ├── 대표 프레임 선택
    │   └── ImageProcessor 연동
    │
    └── 공통 기능
        ├── 캐시 관리 (CacheInterface)
        ├── 비용 추적 (CostTracker)
        └── 에러 처리 (Fallback 체인)
```

### 3.2 OpenRouterClient 통합 패턴

```python
async def analyze_with_fallback(
    self,
    image_data: bytes,
    content_hash: str,
) -> ImageAnalysisResult:
    # 1. 캐시 확인
    cached = await self.cache.get(f"vision:{content_hash}")
    if cached:
        return ImageAnalysisResult.from_cached(cached)

    # 2. API 분석 시도 (Fallback 체인)
    try:
        result = await self.client.analyze_image(
            image_data=image_data,
            prompt=VISION_ANALYSIS_PROMPT,
        )
        # 3. 캐시 저장
        await self.cache.set(
            f"vision:{content_hash}",
            result.to_dict(),
            ttl=VISION_CACHE_TTL,
        )
        return result
    except ModelUnavailableError:
        # 4. 로컬 Fallback
        return self._local_fallback_analysis(image_data)
```

### 3.3 비디오 분석 전략

```python
async def analyze_video(
    self,
    video_path: Path,
    max_frames: int = 5,
) -> VideoAnalysisResult:
    # 1. 메타데이터 추출
    metadata = self.get_video_metadata(video_path)

    # 2. 키프레임 추출 (FFmpeg)
    interval = self._calculate_interval(metadata.duration_seconds)
    keyframes = self.extract_keyframes(video_path, interval)

    # 3. 대표 프레임 선택
    representative = self.select_representative_frames(
        keyframes, max_count=max_frames
    )

    # 4. 각 프레임 분석
    frame_results = await asyncio.gather(
        *[self.image_processor.analyze(frame) for frame in representative]
    )

    # 5. 결과 통합
    return self._aggregate_results(frame_results, metadata)
```

### 3.4 캐시 키 설계

| 키 패턴 | 용도 | TTL |
|---------|------|-----|
| `vision:image:{content_hash}` | 이미지 분석 결과 | 7일 |
| `vision:video:{content_hash}` | 비디오 분석 결과 | 7일 |
| `vision:frame:{content_hash}` | 개별 프레임 분석 결과 | 7일 |
| `vision:metadata:{path_hash}` | 메타데이터 (빠른 조회용) | 1일 |

---

## 4. 테스트 전략

### 4.1 단위 테스트

**ImageProcessor 테스트:**
- 지원 형식 검증 테스트
- 비지원 형식 거부 테스트
- 이미지 리사이징 테스트
- EXIF 메타데이터 추출 테스트
- OpenRouterClient 모킹 테스트
- 캐시 히트/미스 테스트
- 로컬 Fallback 테스트

**VideoProcessor 테스트:**
- 비디오 메타데이터 추출 테스트
- 키프레임 추출 테스트 (FFmpeg 모킹)
- 대표 프레임 선택 테스트
- 프레임 분석 통합 테스트
- FFmpeg 미설치 에러 테스트

**VisionService 테스트:**
- 파일 타입 라우팅 테스트
- 배치 분석 테스트
- Race Condition 방지 테스트
- 통계 조회 테스트

### 4.2 통합 테스트

**End-to-End 시나리오:**
1. 이미지 업로드 -> 분석 -> 캐시 저장 -> 재조회 (캐시 히트)
2. 비디오 업로드 -> 키프레임 추출 -> 분석 -> 결과 통합
3. Primary 실패 -> Fallback 1 성공
4. 모든 API 실패 -> 로컬 Fallback

### 4.3 성능 테스트

| 시나리오 | 목표 |
|----------|------|
| 1MB 이미지 분석 (캐시 미스) | < 3초 |
| 1MB 이미지 분석 (캐시 히트) | < 50ms |
| 1분 비디오 분석 | < 30초 |
| 10개 이미지 배치 분석 | < 15초 |

---

## 5. 품질 기준

### 5.1 TRUST 5 품질 게이트

| 항목 | 기준 | 도구 |
|------|------|------|
| **Test-first** | 커버리지 90% 이상 | pytest-cov |
| **Readable** | Docstring 100%, Type hints 100% | ruff, mypy |
| **Unified** | Black + isort 포맷팅 | ruff format |
| **Secured** | API 키 로그 노출 없음 | 수동 검증 |
| **Trackable** | 모든 요구사항 테스트 매핑 | TAG 추적 |

### 5.2 코드 품질 기준

- 함수 최대 길이: 50줄
- 클래스 최대 메서드 수: 15개
- 순환 복잡도: 10 이하
- 중복 코드: 0%

---

## 6. 리스크 및 대응

### 6.1 기술적 리스크

| 리스크 | 대응 계획 |
|--------|----------|
| FFmpeg 설치 복잡성 | Docker 이미지에 FFmpeg 포함, 상세 설치 가이드 제공 |
| 대용량 비디오 메모리 이슈 | 스트리밍 방식 키프레임 추출, 메모리 제한 설정 |
| API 응답 형식 변경 | 응답 파싱 로직 유연하게 구현, 버전 관리 |

### 6.2 일정 리스크

| 리스크 | 대응 계획 |
|--------|----------|
| OpenRouterClient 버그 발견 | SPEC-API-001 핫픽스 우선 처리 |
| 테스트 환경 구축 지연 | 로컬 목 서버 활용, 실제 API 테스트는 후순위 |

---

## 7. 산출물 목록

### 7.1 소스 코드

| 파일 | 설명 |
|------|------|
| `src/smart_file_manager/services/vision_service.py` | VisionService 메인 클래스 |
| `src/smart_file_manager/services/vision_models.py` | 데이터 클래스 정의 |
| `src/smart_file_manager/processors/image_processor.py` | ImageProcessor 구현 |
| `src/smart_file_manager/processors/video_processor.py` | VideoProcessor 구현 |
| `src/smart_file_manager/core/exceptions.py` | VisionError 추가 |
| `src/smart_file_manager/core/constants.py` | 상수 추가 |

### 7.2 테스트 코드

| 파일 | 설명 |
|------|------|
| `tests/services/test_vision_service.py` | VisionService 단위 테스트 |
| `tests/processors/test_image_processor.py` | ImageProcessor 단위 테스트 |
| `tests/processors/test_video_processor.py` | VideoProcessor 단위 테스트 |
| `tests/integration/test_vision_integration.py` | 통합 테스트 |

---

## 8. 추적성

### SPEC 연결

- spec.md: 요구사항 정의 (EARS 형식)
- plan.md: 구현 계획 (본 문서)
- acceptance.md: 인수 기준 (Given-When-Then)

### TAG 매핑

| Milestone | 관련 요구사항 |
|-----------|---------------|
| M1 | REQ-U-004, REQ-U-005, REQ-N-001 |
| M2 | REQ-U-001~007, REQ-E-001~005, REQ-E-008~010, REQ-S-001~003, REQ-S-005~006, REQ-N-001~005 |
| M3 | REQ-E-006~007, REQ-S-004, REQ-N-006~007 |
| M4 | REQ-U-001~007, REQ-N-004, REQ-O-001~006 |
| M5 | 전체 요구사항 통합 검증 |
