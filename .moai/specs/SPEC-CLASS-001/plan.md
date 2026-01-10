---
spec_id: SPEC-CLASS-001
version: "1.0.0"
created: "2026-01-10"
---

# SPEC-CLASS-001: 구현 계획

## 1. 개요

### 1.1 목표

AI 기반 스마트 파일 분류 서비스를 구현하여 VisionService와 연동된 자동 분류, 태그 생성, 파일 정리 추천 기능을 제공한다.

### 1.2 의존성

| SPEC ID | 상태 | 필수 컴포넌트 |
|---------|------|---------------|
| SPEC-INFRA-001 | completed | Settings, CacheInterface, Exceptions |
| SPEC-API-001 | completed | OpenRouterClient, ModelConfig, CostTracker |
| SPEC-VISION-001 | completed | VisionService, ImageProcessor, VideoProcessor |

---

## 2. 마일스톤 계획

### Milestone 1: 핵심 분류 엔진 (Primary Goal)

**목표**: 기본 분류 기능 구현

**태스크:**

1. **CategoryRegistry 구현**
   - 기본 카테고리 정의 (photo, screenshot, document, artwork, meme, product, video, other)
   - 하위 카테고리 정의
   - 사용자 정의 카테고리 등록/조회 인터페이스
   - 카테고리 검증 로직

2. **ClassificationEngine 구현**
   - 분류 우선순위 로직 (사용자 규칙 > AI > 메타데이터)
   - VisionService 결과 기반 AI 분류
   - 메타데이터 기반 규칙 분류
   - 신뢰도 점수 계산 알고리즘
   - requires_review 플래그 로직

3. **메타데이터 분석기 구현**
   - EXIF 정보 추출 (Pillow 기반)
   - 파일 속성 분석 (크기, 해상도, 생성일)
   - 확장자 기반 기본 분류

4. **예외 클래스 추가**
   - ClassificationError 계층 구조
   - 에러 메시지 다국어 지원

**산출물:**
- `classification/engine.py`
- `classification/category_registry.py`
- `core/exceptions.py` (ClassificationError 추가)
- 단위 테스트

**검증 기준:**
- 기본 카테고리 분류 정확도 > 80%
- 메타데이터 기반 분류 동작 확인
- 신뢰도 점수 정상 계산

---

### Milestone 2: 태그 생성 및 캐싱 (Secondary Goal)

**목표**: 자동 태그 생성 및 캐시 통합

**태스크:**

1. **TagGenerator 구현**
   - VisionService 결과 기반 태그 추출
   - 객체, 장면, 텍스트 태그 생성
   - 메타데이터 기반 태그 (날짜, 위치, 형식)
   - 태그 중복 제거 및 정규화
   - 최대 20개 태그 제한 로직

2. **태그 번역 기능**
   - 영어 -> 한국어 태그 번역
   - 번역 사전 관리
   - 번역 불가 태그 처리

3. **캐시 통합**
   - 분류 결과 캐싱 (7일 TTL)
   - content_hash 기반 캐시 키
   - 캐시 히트/미스 처리
   - Race Condition 방지 (분산 락)

4. **ClassificationService 통합**
   - VisionService 연동
   - 캐시 레이어 통합
   - 단일 파일 분류 API

**산출물:**
- `classification/tag_generator.py`
- `services/classification_service.py`
- 번역 사전 데이터
- 통합 테스트

**검증 기준:**
- 태그 생성 정확도 > 75%
- 캐시 히트 시 응답 시간 < 50ms
- 한국어/영어 태그 동시 생성

---

### Milestone 3: 정리 추천 및 배치 처리 (Tertiary Goal)

**목표**: 파일 정리 추천 및 대량 처리 기능

**태스크:**

1. **OrganizationPlanner 구현**
   - 분류 기반 정리 규칙 정의
   - 대상 경로 생성 로직
   - 정리 추천 생성 (move, copy, group)
   - 중복 파일 감지 통합

2. **BatchClassifier 구현**
   - 디렉토리 스캔 및 필터링
   - 병렬 분류 처리 (asyncio)
   - 동시성 제한 (최대 10개)
   - 오류 처리 및 계속 실행
   - 진행 상황 콜백

3. **배치 정리 계획**
   - 다중 파일 정리 계획 통합
   - 디렉토리 구조 추천
   - 중복/유사 파일 그룹화

4. **통계 및 리포팅**
   - 분류 통계 집계
   - 카테고리별 파일 수
   - 태그 빈도 분석

**산출물:**
- `classification/organization_planner.py`
- `classification/batch_classifier.py`
- 배치 처리 테스트
- 성능 벤치마크

**검증 기준:**
- 100개 파일 배치 처리 < 60초
- 오류 발생 시 계속 실행 확인
- 정리 추천 품질 검증

---

### Milestone 4: 최적화 및 확장 (Optional Goal)

**목표**: 성능 최적화 및 선택적 기능 추가

**태스크:**

1. **성능 최적화**
   - 캐시 전략 최적화
   - 메모리 사용량 최적화
   - 병렬 처리 튜닝

2. **중복 파일 감지**
   - content_hash 기반 중복 탐지
   - 유사 이미지 감지 (perceptual hash)
   - 중복 그룹화

3. **시간/위치 기반 분류**
   - EXIF 날짜 기반 분류
   - GPS 좌표 기반 위치 분류
   - 시간대별 그룹화

4. **사용자 학습 기능**
   - 분류 피드백 수집
   - 사용자 패턴 학습
   - 분류 규칙 자동 생성

**산출물:**
- 최적화된 코드
- 선택적 기능 구현
- 성능 리포트

**검증 기준:**
- 메모리 사용량 < 500MB
- 중복 탐지 정확도 > 95%

---

## 3. 기술적 접근 방식

### 3.1 아키텍처 설계

```
┌─────────────────────────────────────────────────────────────┐
│                   ClassificationService                      │
│  (단일 진입점, 캐시 관리, VisionService 연동)                  │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│Classification │    │  TagGenerator │    │ Organization  │
│    Engine     │    │               │    │   Planner     │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Category    │    │   번역 사전    │    │   정리 규칙   │
│   Registry    │    │               │    │               │
└───────────────┘    └───────────────┘    └───────────────┘
```

### 3.2 분류 흐름

```
파일 입력
    │
    ▼
┌─────────────────┐
│  캐시 확인      │ ──── 캐시 히트 ────▶ 캐시 결과 반환
└─────────────────┘
    │ 캐시 미스
    ▼
┌─────────────────┐
│ VisionService   │
│ 분석 요청       │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Classification  │
│ Engine 분류     │
│ (규칙 우선순위) │
└─────────────────┘
    │
    ├─────────────────┐
    ▼                 ▼
┌─────────────┐   ┌─────────────┐
│ TagGenerator│   │Organization │
│ 태그 생성   │   │Planner 추천 │
└─────────────┘   └─────────────┘
    │                 │
    └────────┬────────┘
             ▼
┌─────────────────┐
│  결과 통합      │
│  캐시 저장      │
└─────────────────┘
             │
             ▼
       결과 반환
```

### 3.3 데이터 모델

```python
# 핵심 데이터 클래스 (요약)

@dataclass
class Category:
    id: str                    # 고유 식별자
    name_ko: str               # 한국어 이름
    name_en: str               # 영어 이름
    sub_categories: list[str]  # 하위 카테고리 ID 목록
    rules: list[ClassificationRule]  # 분류 규칙

@dataclass
class ClassificationRule:
    type: RuleType            # pattern, extension, metadata
    pattern: str | None       # 매칭 패턴
    priority: int             # 우선순위
    target_category: str      # 대상 카테고리 ID

@dataclass
class TranslationEntry:
    en: str                   # 영어 원문
    ko: str                   # 한국어 번역
    category: str             # 번역 카테고리 (object, scene, etc.)
```

### 3.4 캐시 전략

| 데이터 | 캐시 키 패턴 | TTL | 저장소 |
|--------|-------------|-----|--------|
| 분류 결과 | `classification:{content_hash}` | 7일 | Redis |
| 태그 | `tags:{content_hash}` | 7일 | Redis |
| 정리 계획 | `org_plan:{content_hash}` | 1일 | Redis |
| 카테고리 | `categories:all` | 1시간 | Memory |
| 번역 사전 | `translations:{lang}` | 24시간 | Memory |

### 3.5 오류 처리 전략

| 오류 유형 | 처리 방식 | 복구 동작 |
|----------|----------|----------|
| VisionService 실패 | 메타데이터 분류로 폴백 | 부분 결과 반환 |
| 캐시 연결 실패 | MemoryCache 폴백 | 정상 처리 계속 |
| 배치 처리 중 단일 오류 | 해당 파일 건너뛰기 | 나머지 파일 계속 처리 |
| 태그 번역 실패 | 영어 태그만 반환 | 경고 로그 |
| 분류 신뢰도 낮음 | requires_review 플래그 | 사용자 검토 요청 |

---

## 4. 리스크 및 대응

### 4.1 기술적 리스크

| 리스크 | 확률 | 영향 | 대응 전략 |
|--------|------|------|----------|
| VisionService 지연 | 중간 | 중간 | 캐시 적극 활용, 타임아웃 설정 |
| 분류 정확도 저하 | 중간 | 중간 | 신뢰도 점수 + 사용자 검토 |
| 배치 메모리 부족 | 낮음 | 높음 | 청크 단위 처리, 동시성 제한 |
| 캐시 불일치 | 낮음 | 중간 | TTL 관리, 강제 새로고침 옵션 |

### 4.2 의존성 리스크

| 의존성 | 리스크 | 대응 |
|--------|--------|------|
| VisionService | 서비스 불가 | 메타데이터 분류 폴백 |
| Redis | 연결 실패 | MemoryCache 폴백 |
| Pillow | 호환성 | 버전 고정 (>= 10.2.0) |

---

## 5. 테스트 전략

### 5.1 단위 테스트

| 컴포넌트 | 테스트 범위 |
|----------|-------------|
| ClassificationEngine | 분류 로직, 우선순위, 신뢰도 계산 |
| CategoryRegistry | CRUD, 검증, 기본값 |
| TagGenerator | 태그 생성, 제한, 번역 |
| OrganizationPlanner | 계획 생성, 경로 계산 |

### 5.2 통합 테스트

| 시나리오 | 검증 항목 |
|----------|-----------|
| 단일 파일 분류 | E2E 흐름, 캐시 동작 |
| 배치 분류 | 병렬 처리, 오류 복구 |
| 캐시 폴백 | Redis 실패 시 Memory 전환 |
| Vision 폴백 | Vision 실패 시 메타데이터 분류 |

### 5.3 성능 테스트

| 메트릭 | 목표 | 측정 방법 |
|--------|------|----------|
| 단일 분류 (캐시 히트) | < 50ms | pytest-benchmark |
| 단일 분류 (캐시 미스) | < 5초 | pytest-benchmark |
| 배치 100개 | < 60초 | 시간 측정 |
| 메모리 사용량 | < 500MB | memory_profiler |

---

## 6. 산출물 체크리스트

### Milestone 1 산출물

- [ ] `src/smart_file_manager/classification/__init__.py`
- [ ] `src/smart_file_manager/classification/engine.py`
- [ ] `src/smart_file_manager/classification/category_registry.py`
- [ ] `src/smart_file_manager/core/exceptions.py` (ClassificationError 추가)
- [ ] `src/smart_file_manager/core/constants.py` (카테고리 상수)
- [ ] `tests/test_classification/test_engine.py`
- [ ] `tests/test_classification/test_category_registry.py`

### Milestone 2 산출물

- [ ] `src/smart_file_manager/classification/tag_generator.py`
- [ ] `src/smart_file_manager/services/classification_service.py`
- [ ] `src/smart_file_manager/data/translation_dict.json`
- [ ] `tests/test_classification/test_tag_generator.py`
- [ ] `tests/test_services/test_classification_service.py`

### Milestone 3 산출물

- [ ] `src/smart_file_manager/classification/organization_planner.py`
- [ ] `src/smart_file_manager/classification/batch_classifier.py`
- [ ] `tests/test_classification/test_organization_planner.py`
- [ ] `tests/test_classification/test_batch_classifier.py`
- [ ] `tests/test_integration/test_batch_classification.py`

### Milestone 4 산출물 (Optional)

- [ ] 성능 최적화 코드
- [ ] 중복 탐지 기능
- [ ] 시간/위치 분류 기능
- [ ] 성능 벤치마크 리포트

---

## 7. 다음 단계

SPEC-CLASS-001 완료 후:

1. **SPEC-SEARCH-001**: 시맨틱 검색 서비스 (분류 결과 및 태그 활용)
2. **SPEC-MCP-001**: MCP 서버 통합 (분류 도구 노출)
3. **SPEC-STT-001**: 오디오 파일 분류 확장
4. **SPEC-DOC-001**: 문서 파일 분류 확장
