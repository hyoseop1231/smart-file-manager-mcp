---
id: SPEC-CLASS-001
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
  - SPEC-VISION-001
---

# SPEC-CLASS-001: Phase 4 - 파일 분류 서비스

## HISTORY

| 버전 | 날짜 | 작성자 | 변경사항 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-10 | Developer | 초기 SPEC 작성 |

---

## 1. 개요

### 1.1 목적

AI 기반 스마트 파일 분류 및 정리 자동화 서비스를 구현한다. SPEC-VISION-001에서 구현된 VisionService와 연동하여 이미지/비디오 분석 결과를 기반으로 자동 분류, 태그 생성, 파일 정리 추천 기능을 제공한다.

### 1.2 범위

**핵심 구현 범위:**
- ClassificationEngine: 핵심 분류 로직 (규칙 기반 + AI 기반 하이브리드)
- CategoryRegistry: 사전 정의 카테고리 + 사용자 정의 카테고리 관리
- TagGenerator: VisionService 분석 결과 기반 자동 태그 생성
- OrganizationPlanner: 파일 정리 추천 시스템
- BatchClassifier: 디렉토리 단위 일괄 분류

**제외 범위:**
- 파일 이동/복사 실행 (추천만 제공, 실제 이동은 사용자 확인 후)
- 오디오 파일 분류 (SPEC-STT-001 이후 확장)
- 문서 파일 분류 (SPEC-DOC-001 이후 확장)

### 1.3 SPEC 의존성

이 SPEC은 다음 선행 SPEC에 의존한다:

| SPEC ID | 컴포넌트 | 용도 |
|---------|----------|------|
| SPEC-INFRA-001 | Settings, CacheInterface, Exceptions | 인프라 기반 |
| SPEC-API-001 | OpenRouterClient, ModelConfig, CostTracker | API 호출 기반 |
| SPEC-VISION-001 | VisionService, ImageProcessor, VideoProcessor | 시각 분석 결과 |

### 1.4 관련 문서

- `REFACTORING_SPEC_v5.md`: 전체 리팩토링 명세
- `.moai/project/product.md`: 파일 분류 요구사항 (사용자 시나리오 참조)
- `.moai/project/tech.md`: 기술 스택 정보
- `.moai/project/structure.md`: 데이터 흐름 및 저장소 구조

---

## 2. EARS 요구사항

### 2.1 Ubiquitous Requirements (시스템 전반 적용)

**[REQ-U-001]** 시스템은 **항상** 분류 작업 전에 VisionService의 분석 결과를 확인해야 한다.

**[REQ-U-002]** 시스템은 **항상** 분류 결과를 content_hash 기반으로 캐시에 저장해야 한다 (TTL: 7일).

**[REQ-U-003]** 시스템은 **항상** 사용자 정의 카테고리가 기본 카테고리보다 우선하도록 처리해야 한다.

**[REQ-U-004]** 시스템은 **항상** 분류 결과에 신뢰도 점수(0.0-1.0)를 포함해야 한다.

**[REQ-U-005]** 시스템은 **항상** 분류 메트릭(처리 시간, 사용된 규칙/AI, 태그 수)을 결과에 포함해야 한다.

**[REQ-U-006]** 시스템은 **항상** 분류 결과를 구조화된 JSON 형식으로 반환해야 한다.

**[REQ-U-007]** 시스템은 **항상** 한국어와 영어 태그를 동시에 생성해야 한다.

### 2.2 Event-Driven Requirements (이벤트 기반 동작)

**[REQ-E-001]** **WHEN** 파일 분류가 요청되면 **THEN** 먼저 캐시를 확인하고, 캐시 히트 시 캐시된 분류 결과를 반환해야 한다.

**[REQ-E-002]** **WHEN** 캐시 미스가 발생하면 **THEN** VisionService를 호출하여 파일 분석을 수행해야 한다.

**[REQ-E-003]** **WHEN** VisionService 분석이 완료되면 **THEN** ClassificationEngine을 통해 카테고리와 태그를 생성해야 한다.

**[REQ-E-004]** **WHEN** 분류가 완료되면 **THEN** OrganizationPlanner를 통해 파일 정리 추천을 생성해야 한다.

**[REQ-E-005]** **WHEN** 배치 분류가 요청되면 **THEN** 디렉토리 내 모든 지원 파일을 병렬로 분류해야 한다.

**[REQ-E-006]** **WHEN** 사용자 정의 카테고리가 등록되면 **THEN** CategoryRegistry에 추가하고 분류 규칙을 업데이트해야 한다.

**[REQ-E-007]** **WHEN** 태그 생성 시 VisionService 분석 결과가 없으면 **THEN** 메타데이터 기반 기본 태그만 생성해야 한다.

**[REQ-E-008]** **WHEN** 분류 신뢰도가 0.5 미만이면 **THEN** 결과에 "requires_review" 플래그를 설정해야 한다.

**[REQ-E-009]** **WHEN** 동일 카테고리 파일이 10개 이상이면 **THEN** 하위 분류(sub-category)를 추천해야 한다.

**[REQ-E-010]** **WHEN** 배치 분류 중 오류가 발생하면 **THEN** 해당 파일만 건너뛰고 나머지 파일 분류를 계속해야 한다.

### 2.3 State-Driven Requirements (상태 기반 동작)

**[REQ-S-001]** **IF** VisionService가 사용 불가 상태이면 **THEN** 메타데이터 기반 규칙 분류만 수행해야 한다.

**[REQ-S-002]** **IF** 일일 API 예산($1)이 초과된 상태이면 **THEN** 캐시된 분석 결과만 활용해야 한다.

**[REQ-S-003]** **IF** 파일이 이미 분류된 상태(캐시 히트)이면 **THEN** 캐시된 결과를 반환하고 API 호출을 생략해야 한다.

**[REQ-S-004]** **IF** 사용자 정의 규칙이 활성화된 상태이면 **THEN** AI 분류보다 사용자 규칙을 우선 적용해야 한다.

**[REQ-S-005]** **IF** 배치 처리 중인 상태이면 **THEN** 동시성 제한(최대 10개)을 적용해야 한다.

**[REQ-S-006]** **IF** Redis가 사용 불가 상태이면 **THEN** MemoryCache를 사용하여 캐싱을 계속해야 한다.

### 2.4 Unwanted Behavior Requirements (금지 동작)

**[REQ-N-001]** 시스템은 **지원되지 않는 파일 형식이 입력되면** UnsupportedFormatError를 발생시켜야 한다.

**[REQ-N-002]** 시스템은 **파일이 존재하지 않으면** FileNotFoundError를 발생시켜야 한다.

**[REQ-N-003]** 시스템은 **동일 파일에 대해 중복 분류 요청을 허용하지 않아야** 한다 (Race Condition 방지).

**[REQ-N-004]** 시스템은 **분류 결과 없이 정리 추천을 생성하지 않아야** 한다.

**[REQ-N-005]** 시스템은 **사용자 확인 없이 파일을 이동/삭제하지 않아야** 한다.

**[REQ-N-006]** 시스템은 **카테고리 이름에 특수문자를 허용하지 않아야** 한다 (영문, 숫자, 하이픈, 언더스코어만).

**[REQ-N-007]** 시스템은 **태그 수가 20개를 초과하면** 상위 20개만 반환해야 한다.

### 2.5 Optional Requirements (선택적 기능)

**[REQ-O-001]** **가능하면** 중복 파일을 감지하여 분류 결과에 표시해야 한다.

**[REQ-O-002]** **가능하면** 유사 파일을 그룹화하여 표시해야 한다.

**[REQ-O-003]** **가능하면** 시간대별(년/월/일) 분류를 지원해야 한다 (EXIF 날짜 기반).

**[REQ-O-004]** **가능하면** 위치 기반 분류를 지원해야 한다 (GPS EXIF 기반).

**[REQ-O-005]** **가능하면** 얼굴 감지 결과를 기반으로 인물 분류를 지원해야 한다.

**[REQ-O-006]** **가능하면** 분류 학습을 통해 사용자 패턴에 맞게 정확도를 개선해야 한다.

---

## 3. 기술 명세

### 3.1 기본 카테고리 정의

| 카테고리 ID | 이름 (한국어) | 이름 (영어) | 설명 | 하위 카테고리 |
|-------------|---------------|-------------|------|---------------|
| `photo` | 사진 | Photo | 일반 사진 | portrait, landscape, macro, aerial |
| `screenshot` | 스크린샷 | Screenshot | 화면 캡처 | desktop, mobile, web, game |
| `document` | 문서 | Document | 문서 이미지 | scan, receipt, id_card, form |
| `artwork` | 아트워크 | Artwork | 예술 작품, 일러스트 | illustration, painting, digital_art |
| `meme` | 밈 | Meme | 인터넷 밈, 재미있는 이미지 | reaction, text_meme, comic |
| `product` | 제품 | Product | 제품 이미지 | electronics, fashion, food |
| `video` | 비디오 | Video | 동영상 파일 | clip, movie, recording, tutorial |
| `other` | 기타 | Other | 분류 불가 | - |

### 3.2 분류 규칙 우선순위

```
1. 사용자 정의 규칙 (최고 우선순위)
   - 파일 경로 패턴 매칭
   - 파일명 패턴 매칭
   - 확장자 기반 규칙

2. AI 분류 (VisionService 기반)
   - scene 분석 결과
   - objects 감지 결과
   - text_content (OCR) 분석

3. 메타데이터 규칙 (기본)
   - EXIF 정보 분석
   - 파일 크기/해상도 분석
   - 생성일/수정일 분석
```

### 3.3 태그 생성 전략

| 소스 | 태그 유형 | 예시 |
|------|-----------|------|
| VisionService.objects | 객체 태그 | 사람, 자동차, 건물, person, car, building |
| VisionService.scene | 장면 태그 | 실내, 야외, 자연, indoor, outdoor, nature |
| VisionService.text_content | 텍스트 태그 | 추출된 키워드 |
| EXIF.DateTimeOriginal | 시간 태그 | 2026, January, morning |
| EXIF.GPSInfo | 위치 태그 | Seoul, Korea, Asia |
| File.extension | 형식 태그 | jpg, png, mp4 |
| Classification.category | 카테고리 태그 | photo, screenshot |

### 3.4 정리 추천 규칙

| 조건 | 추천 액션 | 대상 경로 |
|------|-----------|-----------|
| 스크린샷 | 폴더 이동 | `~/Screenshots/{year}/{month}/` |
| 사진 (날짜 있음) | 날짜별 정리 | `~/Photos/{year}/{month}/` |
| 사진 (위치 있음) | 위치별 정리 | `~/Photos/{location}/` |
| 문서 | 문서 폴더 | `~/Documents/Scans/` |
| 중복 파일 | 삭제 추천 | (원본 유지, 중복 삭제 추천) |
| 유사 파일 | 그룹화 | `~/Photos/Similar/{group_id}/` |

### 3.5 디렉토리 구조

```
src/
└── smart_file_manager/
    ├── services/
    │   ├── __init__.py
    │   ├── vision_service.py        # SPEC-VISION-001에서 구현됨
    │   └── classification_service.py # [NEW] 분류 서비스 통합
    │
    ├── classification/
    │   ├── __init__.py
    │   ├── engine.py                 # [NEW] ClassificationEngine
    │   ├── category_registry.py      # [NEW] CategoryRegistry
    │   ├── tag_generator.py          # [NEW] TagGenerator
    │   ├── organization_planner.py   # [NEW] OrganizationPlanner
    │   └── batch_classifier.py       # [NEW] BatchClassifier
    │
    └── core/
        ├── exceptions.py             # ClassificationError 추가
        └── constants.py              # 카테고리 상수 추가
```

### 3.6 예외 클래스 추가

```python
class ClassificationError(SmartFileManagerError):
    """분류 관련 기본 예외."""

class CategoryNotFoundError(ClassificationError):
    """카테고리를 찾을 수 없음."""

class InvalidCategoryNameError(ClassificationError):
    """유효하지 않은 카테고리 이름."""

class ClassificationFailedError(ClassificationError):
    """분류 실패 (모든 방법 실패)."""

class OrganizationPlanError(ClassificationError):
    """정리 계획 생성 실패."""
```

---

## 4. 인터페이스 설계

### 4.1 ClassificationService 클래스

```python
class ClassificationService:
    """통합 분류 서비스.

    Attributes:
        vision_service: VisionService 인스턴스
        engine: ClassificationEngine 인스턴스
        cache: CacheInterface 인스턴스
        category_registry: CategoryRegistry 인스턴스
        tag_generator: TagGenerator 인스턴스
        organization_planner: OrganizationPlanner 인스턴스
    """

    async def classify_file(
        self,
        file_path: Path,
        *,
        force_refresh: bool = False,
        include_organization_plan: bool = True,
    ) -> ClassificationResult:
        """단일 파일 분류 수행."""

    async def classify_directory(
        self,
        directory_path: Path,
        *,
        recursive: bool = True,
        concurrency: int = 10,
        file_filter: FileFilter | None = None,
    ) -> BatchClassificationResult:
        """디렉토리 일괄 분류 수행."""

    async def get_classification_stats(self) -> ClassificationStats:
        """분류 통계 조회."""

    def register_custom_category(
        self,
        category: CustomCategory,
    ) -> None:
        """사용자 정의 카테고리 등록."""
```

### 4.2 ClassificationEngine 클래스

```python
class ClassificationEngine:
    """핵심 분류 엔진.

    규칙 기반 + AI 기반 하이브리드 분류를 수행한다.
    """

    def classify(
        self,
        vision_result: ImageAnalysisResult | VideoAnalysisResult | None,
        metadata: FileMetadata,
    ) -> Classification:
        """분류 수행."""

    def apply_user_rules(
        self,
        file_path: Path,
        metadata: FileMetadata,
    ) -> Classification | None:
        """사용자 정의 규칙 적용."""

    def apply_ai_classification(
        self,
        vision_result: ImageAnalysisResult | VideoAnalysisResult,
    ) -> Classification:
        """AI 분류 적용."""

    def apply_metadata_rules(
        self,
        metadata: FileMetadata,
    ) -> Classification:
        """메타데이터 규칙 적용."""
```

### 4.3 TagGenerator 클래스

```python
class TagGenerator:
    """태그 생성기.

    VisionService 분석 결과와 메타데이터를 기반으로 태그를 생성한다.
    """

    def generate_tags(
        self,
        vision_result: ImageAnalysisResult | VideoAnalysisResult | None,
        metadata: FileMetadata,
        classification: Classification,
        *,
        max_tags: int = 20,
    ) -> TagSet:
        """태그 생성."""

    def translate_tags(
        self,
        tags: list[str],
        target_language: str = "ko",
    ) -> list[str]:
        """태그 번역 (영어 -> 한국어)."""
```

### 4.4 OrganizationPlanner 클래스

```python
class OrganizationPlanner:
    """파일 정리 추천 생성기.

    분류 결과를 기반으로 파일 정리 추천을 생성한다.
    """

    def create_plan(
        self,
        file_path: Path,
        classification: ClassificationResult,
    ) -> OrganizationPlan:
        """정리 계획 생성."""

    def create_batch_plan(
        self,
        classifications: list[ClassificationResult],
    ) -> BatchOrganizationPlan:
        """배치 정리 계획 생성."""

    def suggest_directory_structure(
        self,
        classifications: list[ClassificationResult],
    ) -> DirectoryStructure:
        """디렉토리 구조 추천."""
```

### 4.5 응답 데이터 구조

```python
@dataclass
class Classification:
    """분류 결과."""
    category: str              # 주 카테고리
    sub_category: str | None   # 하위 카테고리
    confidence: float          # 신뢰도 (0.0-1.0)
    method: str                # 분류 방법 (user_rule, ai, metadata)
    requires_review: bool      # 검토 필요 여부

@dataclass
class TagSet:
    """태그 집합."""
    tags_en: list[str]         # 영어 태그
    tags_ko: list[str]         # 한국어 태그
    source_breakdown: dict[str, list[str]]  # 소스별 태그

@dataclass
class ClassificationResult:
    """전체 분류 결과."""
    file_path: Path
    content_hash: str
    classification: Classification
    tags: TagSet
    organization_plan: OrganizationPlan | None
    vision_result: ImageAnalysisResult | VideoAnalysisResult | None
    metadata: FileMetadata
    processing_time_ms: float
    cached: bool

@dataclass
class OrganizationPlan:
    """정리 계획."""
    action: str                # move, copy, delete, group
    source_path: Path
    target_path: Path
    reason: str                # 추천 이유
    confidence: float          # 추천 신뢰도

@dataclass
class BatchClassificationResult:
    """배치 분류 결과."""
    total_files: int
    successful: int
    failed: int
    results: list[ClassificationResult]
    errors: list[ClassificationError]
    organization_plan: BatchOrganizationPlan | None
    total_processing_time_ms: float
```

---

## 5. 제약사항

### 5.1 기술적 제약

- Python 3.11 이상 필수
- VisionService (SPEC-VISION-001) 필수
- CacheInterface (SPEC-INFRA-001) 필수
- Pillow >= 10.2.0 필수 (메타데이터 추출)

### 5.2 성능 제약

| 항목 | 목표 |
|------|------|
| 단일 파일 분류 시간 (캐시 미스) | < 5초 |
| 단일 파일 분류 시간 (캐시 히트) | < 50ms |
| 배치 분류 처리량 (100 파일) | < 60초 |
| 태그 생성 시간 | < 100ms |
| 정리 계획 생성 시간 | < 200ms |
| 최대 동시 분류 수 | 10개 |

### 5.3 파일 크기 제약

| 항목 | 제한 |
|------|------|
| 지원 이미지 최대 크기 | 20MB (VisionService 제약) |
| 지원 비디오 최대 크기 | 500MB (VisionService 제약) |
| 배치 분류 최대 파일 수 | 1000개 |

### 5.4 태그 제약

| 항목 | 제한 |
|------|------|
| 파일당 최대 태그 수 | 20개 |
| 태그 최소 길이 | 2자 |
| 태그 최대 길이 | 50자 |
| 허용 태그 문자 | 영문, 숫자, 한글, 하이픈, 언더스코어 |

---

## 6. 추적성

### 6.1 선행/후속 SPEC

| 관계 | SPEC ID | 설명 |
|------|---------|------|
| 선행 | SPEC-INFRA-001 | 인프라 준비 (Settings, Cache, Exceptions) |
| 선행 | SPEC-API-001 | OpenRouter API 클라이언트 |
| 선행 | SPEC-VISION-001 | Vision 분석 서비스 |
| 후속 | SPEC-SEARCH-001 | 시맨틱 검색 서비스 (분류 결과 활용) |
| 후속 | SPEC-MCP-001 | MCP 서버 통합 |

### 6.2 TAG 추적

| TAG ID | 요구사항 | 테스트 케이스 |
|--------|----------|---------------|
| CLASS-001-U001 | REQ-U-001 | test_vision_result_checked_before_classification |
| CLASS-001-U002 | REQ-U-002 | test_classification_cached_with_7day_ttl |
| CLASS-001-U003 | REQ-U-003 | test_user_category_priority |
| CLASS-001-U004 | REQ-U-004 | test_confidence_score_included |
| CLASS-001-E001 | REQ-E-001 | test_cache_hit_returns_cached_classification |
| CLASS-001-E002 | REQ-E-002 | test_vision_called_on_cache_miss |
| CLASS-001-E003 | REQ-E-003 | test_classification_after_vision_analysis |
| CLASS-001-E004 | REQ-E-004 | test_organization_plan_generated |
| CLASS-001-E005 | REQ-E-005 | test_batch_classification_parallel |
| CLASS-001-E008 | REQ-E-008 | test_requires_review_flag_on_low_confidence |
| CLASS-001-E010 | REQ-E-010 | test_batch_continues_on_error |
| CLASS-001-S001 | REQ-S-001 | test_metadata_only_when_vision_unavailable |
| CLASS-001-S002 | REQ-S-002 | test_cache_only_on_budget_exceeded |
| CLASS-001-S005 | REQ-S-005 | test_concurrency_limit_in_batch |
| CLASS-001-N001 | REQ-N-001 | test_unsupported_format_error |
| CLASS-001-N003 | REQ-N-003 | test_no_duplicate_classification |
| CLASS-001-N005 | REQ-N-005 | test_no_auto_file_move |
| CLASS-001-N007 | REQ-N-007 | test_max_20_tags |

### 6.3 레거시 파일 매핑

| v4.0 파일 | v5.0 파일 | 변경 유형 |
|-----------|-----------|----------|
| `ai-services/llm_organizer.py` | `classification/engine.py` | REPLACE |
| (신규) | `services/classification_service.py` | NEW |
| (신규) | `classification/category_registry.py` | NEW |
| (신규) | `classification/tag_generator.py` | NEW |
| (신규) | `classification/organization_planner.py` | NEW |
| (신규) | `classification/batch_classifier.py` | NEW |

---

## 7. 리스크 분석

### 7.1 VisionService 의존성 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| VisionService 장애 | 낮음 | 높음 | 메타데이터 기반 규칙 분류로 폴백 |
| Vision 분석 지연 | 중간 | 중간 | 캐시 적극 활용 + 비동기 처리 |
| Vision 결과 품질 저하 | 낮음 | 중간 | 신뢰도 기반 검토 플래그 |

### 7.2 성능 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| 대용량 배치 처리 지연 | 중간 | 중간 | 동시성 제한 + 진행 상황 피드백 |
| 캐시 미스 폭주 | 낮음 | 높음 | Race Condition 방지 + 요청 큐잉 |
| 메모리 부족 (배치) | 낮음 | 중간 | 청크 단위 처리 |

### 7.3 분류 품질 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| 잘못된 분류 | 중간 | 중간 | 신뢰도 점수 + 사용자 검토 옵션 |
| 태그 과다/부족 | 중간 | 낮음 | 태그 수 제한 + 품질 필터링 |
| 한국어 태그 품질 | 중간 | 중간 | 번역 사전 활용 + 검증 |

---

## 8. 용어 정의

| 용어 | 정의 |
|------|------|
| **분류(Classification)** | 파일을 사전 정의된 카테고리로 구분하는 작업 |
| **태그(Tag)** | 파일의 특성을 나타내는 키워드 |
| **카테고리(Category)** | 파일의 주요 유형을 나타내는 분류 |
| **하위 카테고리(Sub-category)** | 카테고리 내 세부 분류 |
| **신뢰도(Confidence)** | 분류 결과의 정확도를 나타내는 점수 (0.0-1.0) |
| **정리 계획(Organization Plan)** | 파일 이동/정리를 위한 추천 사항 |
| **배치 분류(Batch Classification)** | 여러 파일을 동시에 분류하는 작업 |
| **콘텐츠 해시(Content Hash)** | 파일 콘텐츠의 SHA256 해시값 |
