---
id: SPEC-API-001
version: "1.0.0"
status: "draft"
created: "2026-01-10"
updated: "2026-01-10"
---

# SPEC-API-001: 구현 계획서

## 개요

OpenRouter API 클라이언트 구현을 위한 단계별 구현 계획서이다. 마일스톤은 우선순위 기반으로 구성되며, 시간 예측은 포함하지 않는다.

---

## 1. 마일스톤

### Primary Goal: OpenRouter 클라이언트 기본 구현

**목표**: httpx 기반 비동기 클라이언트의 핵심 기능 구현

**산출물**:
- `src/smart_file_manager/services/__init__.py`
- `src/smart_file_manager/services/openrouter_client.py`
- `src/smart_file_manager/services/model_config.py`
- `src/smart_file_manager/core/exceptions.py` (확장)

**세부 태스크**:

1. **예외 클래스 확장** (core/exceptions.py)
   - APIError 기본 클래스 추가
   - APIConnectionError 추가
   - APITimeoutError 추가
   - APIResponseError 추가
   - RateLimitError 추가
   - BudgetExceededError 추가
   - ModelUnavailableError 추가

2. **모델 설정 구현** (services/model_config.py)
   - ModelTier 데이터클래스 정의
   - 4개 티어 모델 정의 (Free, Low-cost, Balanced, Premium)
   - ModelConfig 클래스 구현
   - Fallback 체인 반환 로직

3. **OpenRouter 클라이언트 기본 구현** (services/openrouter_client.py)
   - OpenRouterClient 클래스 구조
   - httpx.AsyncClient 초기화
   - Bearer 토큰 인증 헤더 설정
   - 기본 API 호출 메서드 (_call_api)
   - 응답 파싱 로직

**완료 기준**:
- [ ] 단일 모델로 API 호출 성공
- [ ] 응답 JSON 파싱 정상 동작
- [ ] 기본 예외 처리 동작

---

### Secondary Goal: Fallback 체인 및 재시도 정책

**목표**: 3단계 Fallback 체인과 지수 백오프 재시도 구현

**산출물**:
- `src/smart_file_manager/services/openrouter_client.py` (확장)

**세부 태스크**:

1. **Fallback 체인 구현**
   - Primary 모델 호출 실패 감지
   - Fallback 1 자동 전환 로직
   - Fallback 2 (Free) 자동 전환 로직
   - 로컬 메타데이터 분석 최종 Fallback
   - 모델별 실패 로깅

2. **지수 백오프 재시도 구현**
   - 재시도 대상 상태 코드 정의 (429, 5xx)
   - 초기 대기 시간: 1초
   - 백오프 배수: 2배
   - 최대 재시도: 3회
   - 최대 대기 시간: 30초
   - Jitter 추가 (0-500ms)

3. **Rate Limit 처리**
   - 429 응답 감지
   - Retry-After 헤더 파싱
   - 대기 후 재시도

4. **타임아웃 설정**
   - 연결 타임아웃: 5초
   - 읽기 타임아웃: 30초
   - 전체 타임아웃: 60초

**완료 기준**:
- [ ] Primary 실패 시 Fallback 1 자동 전환
- [ ] Fallback 1 실패 시 Fallback 2 자동 전환
- [ ] 모든 모델 실패 시 로컬 분석 반환
- [ ] 5xx 에러 시 재시도 동작
- [ ] 429 에러 시 Retry-After 대기

---

### Tertiary Goal: 비용 모니터링 및 예산 제어

**목표**: 일일/월간 API 비용 추적 및 예산 초과 방지

**산출물**:
- `src/smart_file_manager/services/openrouter_client.py` (확장)
- `src/smart_file_manager/services/cost_tracker.py` (신규)

**세부 태스크**:

1. **비용 추적 모듈 구현** (cost_tracker.py)
   - CostTracker 클래스 정의
   - Redis 기반 비용 저장 (cost:daily:{date}, cost:monthly:{month})
   - 일일/월간 비용 조회 메서드
   - 비용 추가 메서드 (atomic increment)

2. **비용 계산 로직**
   - 모델별 토큰 비용 계산
   - Input/Output 토큰 분리 계산
   - 예상 비용 추정

3. **예산 제어 구현**
   - 일일 예산 확인 ($1.00)
   - 월간 예산 확인 ($30.00)
   - 예산 초과 시 Free 티어 강제 전환
   - BudgetExceededError 발생 조건

4. **비용 상태 조회 API**
   - CostStatus 데이터클래스
   - get_cost_status() 메서드 구현
   - 예산 사용률 계산

**완료 기준**:
- [ ] API 호출 시 비용 자동 추적
- [ ] 일일 예산 초과 시 Free 티어 전환
- [ ] 월간 예산 초과 시 유료 API 차단
- [ ] 현재 비용 상태 조회 가능

---

### Optional Goal: 고급 기능

**목표**: 성능 최적화 및 모니터링 기능 추가

**산출물**:
- 추가 개선된 클라이언트 코드

**세부 태스크**:

1. **캐시 통합 강화**
   - 콘텐츠 해시 기반 캐시 키 생성
   - 캐시 히트/미스 로깅
   - 캐시 TTL 설정 (7일)
   - Race Condition 방지 (분산 락)

2. **이미지 전처리**
   - 대용량 이미지 감지 (>20MB)
   - 자동 리사이징 로직
   - Base64 인코딩 최적화

3. **성능 메트릭 수집**
   - 모델별 응답 시간 추적
   - 모델별 성공률 추적
   - 동적 Fallback 순서 최적화 (선택)

4. **Circuit Breaker 패턴 (선택)**
   - 연속 실패 횟수 추적
   - 임계값 초과 시 모델 비활성화
   - 복구 시도 로직

**완료 기준**:
- [ ] 캐시 통합 정상 동작
- [ ] 대용량 이미지 자동 리사이징
- [ ] 성능 메트릭 로깅

---

## 2. 기술적 접근 방식

### 2.1 아키텍처 설계

```
┌──────────────────────────────────────────────────────────┐
│                    OpenRouterClient                       │
├──────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │ ModelConfig │  │ CostTracker │  │ CacheInterface  │   │
│  └─────────────┘  └─────────────┘  └─────────────────┘   │
├──────────────────────────────────────────────────────────┤
│                    httpx.AsyncClient                      │
├──────────────────────────────────────────────────────────┤
│                  OpenRouter API (HTTPS)                   │
└──────────────────────────────────────────────────────────┘
```

### 2.2 Fallback 체인 흐름도

```
API 호출 요청
     │
     ▼
캐시 확인 ─── 히트 ───► 캐시 결과 반환
     │
   미스
     ▼
Primary 모델 호출 ─── 성공 ───► 결과 캐싱 & 반환
     │
   실패
     ▼
Fallback 1 호출 ─── 성공 ───► 결과 캐싱 & 반환
     │
   실패
     ▼
Fallback 2 (Free) 호출 ─── 성공 ───► 결과 캐싱 & 반환
     │
   실패
     ▼
로컬 메타데이터 분석 반환
```

### 2.3 재시도 로직 흐름도

```
API 호출
     │
     ▼
응답 수신 ─── 성공 (2xx) ───► 정상 처리
     │
   실패
     ▼
재시도 가능? (상태코드 429/5xx, 재시도 < 3)
     │
   아니오 ───► 예외 발생
     │
   예
     ▼
429? ─── 예 ───► Retry-After 대기
     │
   아니오
     ▼
지수 백오프 대기 (1s, 2s, 4s) + Jitter
     │
     ▼
재시도 카운터 증가
     │
     ▼
API 호출 (반복)
```

### 2.4 의존성 주입 패턴

```python
class OpenRouterClient:
    def __init__(
        self,
        settings: Settings,
        cache: CacheInterface,
        model_config: ModelConfig | None = None,
        cost_tracker: CostTracker | None = None,
    ) -> None:
        self.settings = settings
        self.cache = cache
        self.model_config = model_config or ModelConfig()
        self.cost_tracker = cost_tracker or CostTracker(cache)
```

---

## 3. 테스트 전략

### 3.1 단위 테스트

**테스트 파일**: `tests/test_openrouter_client.py`

| 테스트 | 설명 | 관련 요구사항 |
|--------|------|---------------|
| test_bearer_auth_header | Bearer 토큰 헤더 확인 | REQ-U-001 |
| test_cache_hit | 캐시 히트 시 API 미호출 | REQ-U-003, REQ-E-001 |
| test_cache_miss_calls_api | 캐시 미스 시 API 호출 | REQ-U-003 |
| test_success_result_cached | 성공 결과 캐싱 확인 | REQ-U-004 |
| test_fallback_on_primary_failure | Primary 실패 시 Fallback | REQ-E-002 |
| test_fallback_chain_exhausted | 전체 Fallback 체인 소진 | REQ-E-004 |
| test_exponential_backoff | 지수 백오프 확인 | REQ-E-005 |
| test_rate_limit_retry_after | 429 Retry-After 처리 | REQ-E-008 |
| test_daily_budget_exceeded | 일일 예산 초과 | REQ-S-001 |
| test_monthly_budget_exceeded | 월간 예산 초과 | REQ-S-002 |
| test_invalid_api_key | 무효 API 키 에러 | REQ-N-001 |
| test_invalid_json_response | JSON 파싱 실패 | REQ-N-003 |

### 3.2 테스트 Fixtures

```python
@pytest.fixture
def mock_settings():
    """테스트용 Settings mock."""
    return Settings(
        openrouter_api_key=SecretStr("test-api-key"),
        vision_primary_model="google/gemini-2.0-flash-001",
        vision_fallback_model="openai/gpt-4o-mini",
    )

@pytest.fixture
def memory_cache():
    """테스트용 MemoryCache."""
    return MemoryCache(default_ttl=3600)

@pytest.fixture
async def openrouter_client(mock_settings, memory_cache):
    """테스트용 OpenRouterClient."""
    client = OpenRouterClient(
        settings=mock_settings,
        cache=memory_cache,
    )
    yield client
    await client.close()
```

### 3.3 Mock 전략

- `httpx.AsyncClient`: respx 또는 AsyncMock 사용
- `CacheInterface`: MemoryCache 또는 AsyncMock 사용
- `time.sleep`: pytest-freezegun 또는 time mocking

---

## 4. 위험 완화 계획

### 4.1 API 가용성 위험

| 위험 | 완화 전략 |
|------|----------|
| OpenRouter 서비스 중단 | 3단계 Fallback + 로컬 분석 |
| 특정 모델 비활성화 | 동적 Fallback 체인 |
| Rate Limit | 지수 백오프 + Retry-After 존중 |

### 4.2 비용 위험

| 위험 | 완화 전략 |
|------|----------|
| 예산 초과 | 실시간 비용 추적 + 예산 제어 |
| 비용 급증 | Free 티어 자동 전환 |

### 4.3 성능 위험

| 위험 | 완화 전략 |
|------|----------|
| API 응답 지연 | 타임아웃 설정 + Fallback |
| 캐시 미스 폭주 | Race Condition 방지 |

---

## 5. 의존성

### 5.1 외부 의존성

| 패키지 | 버전 | 용도 |
|--------|------|------|
| httpx | >=0.27.0 | 비동기 HTTP 클라이언트 |
| pydantic | >=2.0.0 | 데이터 유효성 검사 |
| redis | >=5.0.0 | 비용 추적 저장소 |

### 5.2 내부 의존성 (SPEC-INFRA-001)

| 컴포넌트 | 파일 | 상태 |
|----------|------|------|
| Settings | core/config.py | 완료 |
| CacheInterface | infrastructure/cache/base.py | 완료 |
| RedisCache | infrastructure/cache/redis_cache.py | 완료 |
| MemoryCache | infrastructure/cache/memory_cache.py | 완료 |
| SmartFileManagerError | core/exceptions.py | 완료 |

---

## 6. 추적성

### 6.1 파일-요구사항 매핑

| 파일 | 관련 요구사항 |
|------|---------------|
| services/openrouter_client.py | REQ-U-001 ~ REQ-E-008 |
| services/model_config.py | REQ-E-002, REQ-E-003, REQ-S-004 |
| services/cost_tracker.py | REQ-E-007, REQ-S-001, REQ-S-002 |
| core/exceptions.py | REQ-N-001 ~ REQ-N-005 |

### 6.2 테스트-요구사항 매핑

| 테스트 파일 | 관련 요구사항 |
|-------------|---------------|
| test_openrouter_client.py | 전체 REQ-* |
| test_model_config.py | REQ-E-002, REQ-E-003 |
| test_cost_tracker.py | REQ-E-007, REQ-S-001, REQ-S-002 |
