---
id: SPEC-API-001
version: "1.0.0"
status: "completed"
created: "2026-01-10"
updated: "2026-01-10"
author: "Developer"
priority: "high"
lifecycle: "spec-anchored"
dependencies:
  - SPEC-INFRA-001
---

# SPEC-API-001: Phase 2 - OpenRouter API 클라이언트 구현

## HISTORY

| 버전 | 날짜 | 작성자 | 변경사항 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-10 | Developer | 초기 SPEC 작성 |

---

## 1. 개요

### 1.1 목적

OpenRouter API와 통신하는 비동기 HTTP 클라이언트를 구현한다. 이 클라이언트는 Vision 모델을 통한 이미지/문서 분석의 핵심 인프라로서, 3단계 Fallback 체인, 지수 백오프 재시도, 비용 모니터링 기능을 포함한다.

### 1.2 범위

- httpx 기반 비동기 HTTP 클라이언트 구현
- 3단계 모델 Fallback 체인 (Primary -> Fallback -> Free)
- 지수 백오프 기반 재시도 정책
- 일일/월간 API 비용 모니터링 및 예산 제어
- 분석 결과 캐시 통합 (Redis/Memory)
- 모델 티어 구성 관리

### 1.3 SPEC-INFRA-001 의존성

이 SPEC은 다음 인프라 컴포넌트에 의존한다:

| 컴포넌트 | 파일 | 용도 |
|----------|------|------|
| Settings | `core/config.py` | API 키, 모델 설정, TTL |
| CacheInterface | `infrastructure/cache/base.py` | 캐시 추상화 |
| RedisCache | `infrastructure/cache/redis_cache.py` | 결과 캐싱 |
| MemoryCache | `infrastructure/cache/memory_cache.py` | Fallback 캐시 |
| Exceptions | `core/exceptions.py` | 에러 처리 기반 |

### 1.4 관련 문서

- `REFACTORING_SPEC_v5.md`: 전체 리팩토링 명세
- `.moai/project/tech.md`: 기술 스택 정의 (모델 티어 정보)
- `SPEC-INFRA-001`: 인프라 준비 (선행 SPEC)

---

## 2. EARS 요구사항

### 2.1 Ubiquitous Requirements (시스템 전반 적용)

**[REQ-U-001]** 시스템은 **항상** 모든 API 호출에 대해 Bearer 토큰 인증을 사용해야 한다.

**[REQ-U-002]** 시스템은 **항상** API 응답 시간과 비용을 로깅해야 한다.

**[REQ-U-003]** 시스템은 **항상** API 호출 전에 캐시를 먼저 확인해야 한다.

**[REQ-U-004]** 시스템은 **항상** 성공한 API 응답을 캐시에 저장해야 한다.

**[REQ-U-005]** 시스템은 **항상** HTTPS를 통해 API와 통신해야 한다.

**[REQ-U-006]** 시스템은 **항상** API 키를 로그에 노출하지 않아야 한다.

### 2.2 Event-Driven Requirements (API 호출 이벤트)

**[REQ-E-001]** **WHEN** API 호출이 요청되면 **THEN** 콘텐츠 해시를 기반으로 캐시를 확인하고, 캐시 히트 시 캐시된 결과를 반환해야 한다.

**[REQ-E-002]** **WHEN** Primary 모델 호출이 실패하면 **THEN** Fallback 1 모델로 자동 전환해야 한다.

**[REQ-E-003]** **WHEN** Fallback 1 모델 호출이 실패하면 **THEN** Fallback 2 (Free) 모델로 자동 전환해야 한다.

**[REQ-E-004]** **WHEN** 모든 API 모델이 실패하면 **THEN** 로컬 메타데이터 분석 결과만 반환해야 한다.

**[REQ-E-005]** **WHEN** API 호출이 타임아웃되면 **THEN** 지수 백오프로 최대 3회 재시도해야 한다.

**[REQ-E-006]** **WHEN** API 호출이 성공하면 **THEN** 결과를 7일 TTL로 캐시에 저장해야 한다.

**[REQ-E-007]** **WHEN** API 호출이 완료되면 **THEN** 예상 비용을 계산하고 일일/월간 누적 비용을 업데이트해야 한다.

**[REQ-E-008]** **WHEN** 429 (Rate Limit) 응답을 받으면 **THEN** Retry-After 헤더를 존중하고 대기 후 재시도해야 한다.

### 2.3 State-Driven Requirements (상태 기반 동작)

**[REQ-S-001]** **IF** 일일 예산($1)이 초과된 상태이면 **THEN** Free 티어 모델만 사용해야 한다.

**[REQ-S-002]** **IF** 월간 예산($30)이 초과된 상태이면 **THEN** 모든 유료 API 호출을 거부하고 Free 티어만 허용해야 한다.

**[REQ-S-003]** **IF** Redis가 사용 불가 상태이면 **THEN** MemoryCache를 사용하여 캐싱을 계속해야 한다.

**[REQ-S-004]** **IF** 모델이 Vision 기능을 지원하지 않으면 **THEN** 해당 모델을 건너뛰고 다음 Fallback으로 진행해야 한다.

**[REQ-S-005]** **IF** 이미지 크기가 20MB를 초과하면 **THEN** 자동으로 리사이징 후 API 호출해야 한다.

### 2.4 Unwanted Behavior Requirements (금지 동작)

**[REQ-N-001]** 시스템은 **무효한 API 키로 호출을 시도하면** 즉시 ConfigurationError를 발생시켜야 한다.

**[REQ-N-002]** 시스템은 **지원되지 않는 이미지 형식이 입력되면** 명확한 에러 메시지와 함께 거부해야 한다.

**[REQ-N-003]** 시스템은 **API 응답이 유효하지 않은 JSON이면** APIResponseError를 발생시켜야 한다.

**[REQ-N-004]** 시스템은 **동일 콘텐츠에 대해 캐시 미스 후 중복 API 호출을 허용하지 않아야** 한다 (Race Condition 방지).

**[REQ-N-005]** 시스템은 **예산 초과 시 유료 모델 호출을 시도하면** BudgetExceededError를 발생시켜야 한다.

### 2.5 Optional Requirements (선택적 기능)

**[REQ-O-001]** **가능하면** 응답 스트리밍을 지원하여 대용량 분석 결과를 점진적으로 처리해야 한다.

**[REQ-O-002]** **가능하면** 모델별 성능 메트릭(응답 시간, 성공률)을 수집하여 동적 Fallback 순서 최적화를 지원해야 한다.

**[REQ-O-003]** **가능하면** Circuit Breaker 패턴을 적용하여 반복 실패 시 일시적으로 해당 모델을 비활성화해야 한다.

---

## 3. 기술 명세

### 3.1 모델 티어 시스템

#### 티어 구성표

| 티어 | 모델 ID | 비용 (Input/1M) | 비용 (Output/1M) | 용도 |
|------|---------|-----------------|------------------|------|
| **Free** | `google/gemini-2.0-flash-exp:free` | $0 | $0 | 개발/테스트, Fallback 최종 |
| **Low-cost** | `qwen/qwen2.5-vl-32b-instruct` | $0.05 | $0.10 | 한국어 최적화, 비용 효율 |
| **Balanced** | `google/gemini-2.0-flash-001` | $0.10 | $0.15 | 기본 프로덕션 (Primary) |
| **Premium** | `openai/gpt-4o-mini` | $0.15 | $0.60 | 복잡한 분석 |

#### 기본 Fallback 체인

```
1. Primary: google/gemini-2.0-flash-001 (Balanced)
2. Fallback 1: qwen/qwen2.5-vl-32b-instruct (Low-cost)
3. Fallback 2: google/gemini-2.0-flash-exp:free (Free)
4. Local: 메타데이터 분석만 (API 호출 없음)
```

### 3.2 API 엔드포인트

| 항목 | 값 |
|------|-----|
| **Base URL** | `https://openrouter.ai/api/v1` |
| **Chat Completions** | `POST /chat/completions` |
| **인증** | `Authorization: Bearer {OPENROUTER_API_KEY}` |
| **Content-Type** | `application/json` |

### 3.3 재시도 정책

| 항목 | 값 |
|------|-----|
| **최대 재시도 횟수** | 3회 |
| **초기 대기 시간** | 1초 |
| **백오프 배수** | 2배 (지수 백오프) |
| **최대 대기 시간** | 30초 |
| **Jitter** | 0-500ms 랜덤 추가 |
| **재시도 대상 상태 코드** | 429, 500, 502, 503, 504 |

### 3.4 타임아웃 설정

| 항목 | 값 |
|------|-----|
| **연결 타임아웃** | 5초 |
| **읽기 타임아웃** | 30초 |
| **전체 타임아웃** | 60초 |

### 3.5 캐시 키 패턴

```
analysis:{content_hash}

예시: analysis:sha256_a1b2c3d4e5f6...
```

### 3.6 비용 모니터링 키 패턴

```
cost:daily:{YYYY-MM-DD}
cost:monthly:{YYYY-MM}

예시:
cost:daily:2026-01-10
cost:monthly:2026-01
```

### 3.7 디렉토리 구조

```
src/
└── smart_file_manager/
    ├── services/
    │   ├── __init__.py
    │   ├── openrouter_client.py    # 핵심 API 클라이언트
    │   └── model_config.py         # 모델 티어 및 Fallback 설정
    └── core/
        └── exceptions.py           # APIError 추가 (기존 파일 확장)
```

### 3.8 예외 클래스 추가

```python
class APIError(SmartFileManagerError):
    """API 호출 관련 기본 예외."""

class APIConnectionError(APIError):
    """API 연결 실패."""

class APITimeoutError(APIError):
    """API 타임아웃."""

class APIResponseError(APIError):
    """API 응답 파싱 실패."""

class RateLimitError(APIError):
    """API Rate Limit 초과."""

class BudgetExceededError(APIError):
    """일일/월간 예산 초과."""

class ModelUnavailableError(APIError):
    """모든 모델 사용 불가."""
```

---

## 4. 인터페이스 설계

### 4.1 OpenRouterClient 클래스

```python
class OpenRouterClient:
    """OpenRouter API 클라이언트.

    Attributes:
        settings: 애플리케이션 설정.
        cache: 캐시 인터페이스.
        model_config: 모델 티어 설정.
    """

    async def analyze_image(
        self,
        image_data: bytes,
        prompt: str,
        *,
        force_refresh: bool = False,
    ) -> AnalysisResult:
        """이미지 분석 API 호출."""

    async def analyze_document(
        self,
        document_data: bytes,
        prompt: str,
        *,
        force_refresh: bool = False,
    ) -> AnalysisResult:
        """문서 OCR 및 분석 API 호출."""

    async def get_cost_status(self) -> CostStatus:
        """현재 비용 상태 조회."""

    async def health_check(self) -> bool:
        """API 연결 상태 확인."""
```

### 4.2 ModelConfig 클래스

```python
@dataclass
class ModelTier:
    """모델 티어 정보."""
    id: str
    name: str
    input_cost_per_million: float
    output_cost_per_million: float
    supports_vision: bool
    max_context_tokens: int

class ModelConfig:
    """모델 티어 및 Fallback 체인 관리."""

    def get_fallback_chain(self, task_type: str) -> list[ModelTier]:
        """작업 유형별 Fallback 체인 반환."""

    def estimate_cost(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """예상 비용 계산."""
```

### 4.3 응답 데이터 구조

```python
@dataclass
class AnalysisResult:
    """분석 결과."""
    content: str
    model_used: str
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    cached: bool
    processing_time_ms: float

@dataclass
class CostStatus:
    """비용 상태."""
    daily_spent: float
    daily_limit: float
    monthly_spent: float
    monthly_limit: float
    is_daily_exceeded: bool
    is_monthly_exceeded: bool
```

---

## 5. 제약사항

### 5.1 기술적 제약

- Python 3.11 이상 필수
- httpx >= 0.27.0 필수
- 비동기 전용 (async/await)
- pydantic v2 문법 사용

### 5.2 성능 제약

| 항목 | 목표 |
|------|------|
| API 응답 시간 (P95) | < 3초 |
| Fallback 전환 시간 | < 100ms |
| 캐시 조회 시간 | < 10ms |
| 비용 계산 오버헤드 | < 1ms |

### 5.3 보안 제약

- API 키는 `SecretStr` 타입으로 관리
- 로그에 API 키 또는 요청 본문 노출 금지
- HTTPS 필수 (HTTP 연결 거부)

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
| 후속 | SPEC-VISION-001 | Vision 서비스 구현 (이미지/비디오 분석) |
| 후속 | SPEC-DOC-001 | 문서 프로세서 구현 (OCR) |

### 6.2 TAG 추적

| TAG ID | 요구사항 | 테스트 케이스 |
|--------|----------|---------------|
| API-001-U001 | REQ-U-001 | test_bearer_auth_always_used |
| API-001-U003 | REQ-U-003 | test_cache_checked_before_api_call |
| API-001-E001 | REQ-E-001 | test_cache_hit_returns_cached_result |
| API-001-E002 | REQ-E-002 | test_fallback_on_primary_failure |
| API-001-E003 | REQ-E-003 | test_fallback_chain_complete |
| API-001-E005 | REQ-E-005 | test_exponential_backoff_retry |
| API-001-E007 | REQ-E-007 | test_cost_tracking_on_success |
| API-001-S001 | REQ-S-001 | test_daily_budget_enforcement |
| API-001-S002 | REQ-S-002 | test_monthly_budget_enforcement |
| API-001-N001 | REQ-N-001 | test_invalid_api_key_error |
| API-001-N005 | REQ-N-005 | test_budget_exceeded_error |

---

## 7. 리스크 분석

### 7.1 API 가용성 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| OpenRouter 서비스 중단 | 낮음 | 높음 | 3단계 Fallback + 로컬 분석 |
| 특정 모델 비활성화 | 중간 | 중간 | 동적 Fallback 체인 |
| Rate Limit 초과 | 중간 | 낮음 | 지수 백오프 + Retry-After |

### 7.2 비용 초과 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| 일일 예산 초과 | 중간 | 낮음 | Free 티어 자동 전환 |
| 월간 예산 초과 | 낮음 | 중간 | 유료 API 차단 + 알림 |
| 예상치 못한 고비용 | 낮음 | 높음 | 비용 모니터링 + 예산 경고 |

### 7.3 성능 병목 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| API 응답 지연 | 중간 | 중간 | 타임아웃 + Fallback |
| 캐시 미스 폭주 | 낮음 | 높음 | Race Condition 방지 + 캐시 Warmup |
| 대용량 이미지 처리 | 중간 | 중간 | 자동 리사이징 |

---

## 8. 용어 정의

| 용어 | 정의 |
|------|------|
| **Fallback Chain** | Primary 모델 실패 시 순차적으로 대체 모델을 시도하는 체계 |
| **Exponential Backoff** | 재시도 간격을 지수적으로 증가시키는 재시도 전략 |
| **Jitter** | 동시 재시도로 인한 병목 방지를 위해 추가하는 랜덤 지연 |
| **Content Hash** | 동일 콘텐츠 식별을 위한 SHA256 해시값 |
| **Rate Limit** | API 호출 빈도 제한 |
| **TTL** | Time-To-Live, 캐시 항목의 유효 기간 |
