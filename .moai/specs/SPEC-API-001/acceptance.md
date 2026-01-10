---
id: SPEC-API-001
version: "1.0.0"
status: "draft"
created: "2026-01-10"
updated: "2026-01-10"
---

# SPEC-API-001: 인수 기준서

## 개요

OpenRouter API 클라이언트의 인수 테스트 시나리오를 Gherkin 형식으로 정의한다. 각 시나리오는 EARS 요구사항과 연결되며, TDD 구현 시 테스트 케이스의 기반이 된다.

---

## 1. API 호출 기본 동작

### Scenario: 성공적인 API 호출

```gherkin
Feature: OpenRouter API 기본 호출
  As a 개발자
  I want API를 통해 이미지를 분석할 수 있기를
  So that Vision 기반 파일 분석이 가능하다

  Background:
    Given 유효한 OpenRouter API 키가 설정되어 있다
    And OpenRouterClient가 초기화되어 있다

  Scenario: 이미지 분석 API 호출 성공
    Given 분석할 이미지 데이터가 준비되어 있다
    And 캐시에 해당 이미지의 분석 결과가 없다
    When analyze_image 메서드를 호출한다
    Then API 호출이 성공한다
    And AnalysisResult 객체가 반환된다
    And 결과에 분석 내용(content)이 포함된다
    And 결과에 사용된 모델(model_used)이 포함된다
    And 결과에 토큰 사용량(input_tokens, output_tokens)이 포함된다
    And 결과가 캐시에 저장된다

  Scenario: Bearer 토큰 인증 헤더 사용
    Given API 호출이 발생한다
    When HTTP 요청이 전송된다
    Then Authorization 헤더에 "Bearer {API_KEY}" 형식이 포함된다
    And API 키 원문이 로그에 노출되지 않는다
```

**관련 요구사항**: REQ-U-001, REQ-U-002, REQ-U-004, REQ-U-005, REQ-U-006

---

## 2. 캐시 통합

### Scenario: 캐시 히트 시 API 호출 생략

```gherkin
Feature: 분석 결과 캐싱
  As a 시스템
  I want 동일 콘텐츠에 대해 캐시된 결과를 반환하기를
  So that API 비용을 절감하고 응답 속도를 높인다

  Scenario: 캐시 히트 시 캐시 결과 반환
    Given 이미지 콘텐츠 해시가 "sha256_abc123"이다
    And 캐시에 "analysis:sha256_abc123" 키로 결과가 저장되어 있다
    When analyze_image 메서드를 호출한다
    Then API 호출이 발생하지 않는다
    And 캐시된 결과가 반환된다
    And AnalysisResult.cached가 True이다

  Scenario: 캐시 미스 시 API 호출 및 캐싱
    Given 이미지 콘텐츠 해시가 "sha256_xyz789"이다
    And 캐시에 해당 키가 존재하지 않는다
    When analyze_image 메서드를 호출한다
    Then API 호출이 발생한다
    And 성공한 결과가 캐시에 저장된다
    And 캐시 TTL이 7일(604800초)로 설정된다

  Scenario: 캐시 강제 갱신
    Given 캐시에 기존 분석 결과가 존재한다
    When analyze_image(force_refresh=True)를 호출한다
    Then 캐시를 무시하고 API 호출이 발생한다
    And 새로운 결과로 캐시가 갱신된다
```

**관련 요구사항**: REQ-U-003, REQ-E-001, REQ-E-006

---

## 3. Fallback 체인

### Scenario: Primary 모델 실패 시 Fallback

```gherkin
Feature: 3단계 Fallback 체인
  As a 시스템
  I want Primary 모델 실패 시 자동으로 Fallback 모델을 시도하기를
  So that 99%+ 가용성을 확보한다

  Background:
    Given Fallback 체인이 다음과 같이 설정되어 있다:
      | 순서 | 모델 ID | 티어 |
      | 1 | google/gemini-2.0-flash-001 | Primary |
      | 2 | qwen/qwen2.5-vl-32b-instruct | Fallback 1 |
      | 3 | google/gemini-2.0-flash-exp:free | Fallback 2 |
      | 4 | Local | 메타데이터만 |

  Scenario: Primary 성공 시 첫 번째 모델 사용
    Given Primary 모델이 정상 동작한다
    When API 호출을 수행한다
    Then Primary 모델(google/gemini-2.0-flash-001)이 사용된다
    And AnalysisResult.model_used가 "google/gemini-2.0-flash-001"이다

  Scenario: Primary 실패 시 Fallback 1 자동 전환
    Given Primary 모델이 500 에러를 반환한다
    And Fallback 1 모델이 정상 동작한다
    When API 호출을 수행한다
    Then Fallback 1 모델(qwen/qwen2.5-vl-32b-instruct)이 사용된다
    And 실패 로그가 기록된다

  Scenario: Primary와 Fallback 1 실패 시 Fallback 2 전환
    Given Primary 모델이 503 에러를 반환한다
    And Fallback 1 모델이 타임아웃된다
    And Fallback 2 (Free) 모델이 정상 동작한다
    When API 호출을 수행한다
    Then Fallback 2 모델(google/gemini-2.0-flash-exp:free)이 사용된다

  Scenario: 모든 API 모델 실패 시 로컬 분석
    Given 모든 API 모델(Primary, Fallback 1, Fallback 2)이 실패한다
    When API 호출을 수행한다
    Then 로컬 메타데이터 분석 결과가 반환된다
    And AnalysisResult.model_used가 "local"이다
    And AnalysisResult.content에 파일 메타데이터만 포함된다
```

**관련 요구사항**: REQ-E-002, REQ-E-003, REQ-E-004

---

## 4. 재시도 정책

### Scenario: 지수 백오프 재시도

```gherkin
Feature: 지수 백오프 재시도 정책
  As a 시스템
  I want 일시적 오류 시 자동으로 재시도하기를
  So that 네트워크 불안정에도 안정적으로 동작한다

  Scenario: 5xx 에러 시 재시도
    Given API가 첫 번째와 두 번째 호출에서 503 에러를 반환한다
    And 세 번째 호출에서 성공 응답을 반환한다
    When API 호출을 수행한다
    Then 총 3회 API 호출이 발생한다
    And 첫 번째 재시도 전 약 1초 대기한다
    And 두 번째 재시도 전 약 2초 대기한다
    And 최종적으로 성공 결과가 반환된다

  Scenario: 최대 재시도 초과 시 실패
    Given API가 4회 연속 500 에러를 반환한다
    When API 호출을 수행한다
    Then 3회 재시도 후 다음 Fallback 모델로 전환된다
    And 재시도 실패 로그가 기록된다

  Scenario: 재시도 대상 아닌 에러
    Given API가 400 (Bad Request) 에러를 반환한다
    When API 호출을 수행한다
    Then 재시도 없이 즉시 다음 Fallback 모델로 전환된다
```

**관련 요구사항**: REQ-E-005

### Scenario: Rate Limit 처리

```gherkin
Feature: Rate Limit 처리
  As a 시스템
  I want 429 에러 시 Retry-After 헤더를 존중하기를
  So that API 사용 정책을 준수한다

  Scenario: Retry-After 헤더 존중
    Given API가 429 에러와 "Retry-After: 5" 헤더를 반환한다
    When API 호출을 수행한다
    Then 5초 대기 후 재시도한다
    And 지수 백오프 대신 Retry-After 값을 사용한다

  Scenario: Retry-After 없는 429
    Given API가 429 에러를 반환하고 Retry-After 헤더가 없다
    When API 호출을 수행한다
    Then 기본 지수 백오프로 재시도한다
```

**관련 요구사항**: REQ-E-008

---

## 5. 비용 모니터링

### Scenario: API 비용 추적

```gherkin
Feature: API 비용 모니터링
  As a 관리자
  I want API 호출 비용을 실시간으로 추적하기를
  So that 예산 내에서 서비스를 운영할 수 있다

  Scenario: 성공적인 API 호출 시 비용 기록
    Given Primary 모델(gemini-2.0-flash-001)로 API 호출이 성공한다
    And 응답에 input_tokens=1000, output_tokens=500이 포함된다
    When 비용이 계산된다
    Then 예상 비용이 약 $0.000175이다 (Input: $0.10/1M, Output: $0.15/1M)
    And 일일 비용(cost:daily:YYYY-MM-DD)에 추가된다
    And 월간 비용(cost:monthly:YYYY-MM)에 추가된다

  Scenario: 현재 비용 상태 조회
    Given 오늘 API 호출로 $0.50가 사용되었다
    And 이번 달 총 $15.00가 사용되었다
    When get_cost_status()를 호출한다
    Then CostStatus 객체가 반환된다
    And daily_spent가 0.50이다
    And monthly_spent가 15.00이다
    And daily_limit가 1.00이다
    And monthly_limit가 30.00이다
    And is_daily_exceeded가 False이다
    And is_monthly_exceeded가 False이다
```

**관련 요구사항**: REQ-E-007

---

## 6. 예산 제어

### Scenario: 예산 초과 시 동작

```gherkin
Feature: 예산 초과 제어
  As a 시스템
  I want 예산 초과 시 자동으로 Free 티어로 전환하기를
  So that 예상치 못한 비용 발생을 방지한다

  Scenario: 일일 예산 초과 시 Free 티어 강제
    Given 오늘 일일 예산($1.00)이 이미 초과되었다
    When 유료 모델로 API 호출을 시도한다
    Then Primary/Fallback 1 모델이 건너뛰어진다
    And Fallback 2 (Free) 모델이 직접 사용된다
    And 추가 비용이 발생하지 않는다

  Scenario: 월간 예산 초과 시 유료 API 차단
    Given 이번 달 월간 예산($30.00)이 초과되었다
    When 유료 모델로 API 호출을 시도한다
    Then Free 티어 모델만 사용 가능하다
    And 모든 유료 모델 호출이 거부된다

  Scenario: 예산 초과 에러 발생
    Given 월간 예산이 초과되었다
    And Free 티어 모델도 실패한다
    When API 호출을 시도한다
    Then BudgetExceededError 또는 ModelUnavailableError가 발생한다
```

**관련 요구사항**: REQ-S-001, REQ-S-002, REQ-N-005

---

## 7. 에러 처리

### Scenario: 예외 상황 처리

```gherkin
Feature: 에러 처리
  As a 개발자
  I want 명확한 예외가 발생하기를
  So that 문제를 쉽게 진단할 수 있다

  Scenario: 무효한 API 키
    Given OpenRouter API 키가 유효하지 않다
    When OpenRouterClient를 초기화한다
    Then ConfigurationError가 발생한다
    And 에러 메시지에 "Invalid API key" 또는 유사한 내용이 포함된다

  Scenario: 지원되지 않는 이미지 형식
    Given 입력 파일이 SVG 형식이다
    When analyze_image()를 호출한다
    Then ValueError 또는 UnsupportedFormatError가 발생한다
    And 에러 메시지에 지원 형식 목록이 포함된다

  Scenario: API 응답 JSON 파싱 실패
    Given API가 유효하지 않은 JSON을 반환한다
    When 응답을 파싱한다
    Then APIResponseError가 발생한다
    And 원본 응답 일부가 로깅된다

  Scenario: 연결 타임아웃
    Given API 서버가 응답하지 않는다
    And 연결 타임아웃이 5초로 설정되어 있다
    When API 호출을 시도한다
    Then 5초 후 APITimeoutError가 발생한다
    And 다음 Fallback 모델로 전환된다
```

**관련 요구사항**: REQ-N-001, REQ-N-002, REQ-N-003

---

## 8. 캐시 Fallback

### Scenario: Redis 장애 시 MemoryCache 전환

```gherkin
Feature: 캐시 Fallback
  As a 시스템
  I want Redis 장애 시 MemoryCache로 폴백하기를
  So that 캐싱 기능이 중단되지 않는다

  Scenario: Redis 연결 실패 시 MemoryCache 사용
    Given Redis 서버가 다운되어 있다
    When OpenRouterClient가 캐시 작업을 수행한다
    Then MemoryCache가 자동으로 사용된다
    And 캐싱 기능이 정상 동작한다
    And 경고 로그가 기록된다

  Scenario: Redis 복구 시 자동 전환
    Given MemoryCache를 사용 중이다
    And Redis 서버가 복구되었다
    When 다음 캐시 작업이 발생한다
    Then Redis로 자동 전환된다
    And MemoryCache의 데이터는 유지되지 않는다 (선택적 마이그레이션)
```

**관련 요구사항**: REQ-S-003

---

## 9. 이미지 전처리

### Scenario: 대용량 이미지 처리

```gherkin
Feature: 이미지 전처리
  As a 시스템
  I want 대용량 이미지를 자동으로 리사이징하기를
  So that API 호출 효율을 높인다

  Scenario: 20MB 초과 이미지 자동 리사이징
    Given 입력 이미지 크기가 25MB이다
    When analyze_image()를 호출한다
    Then 이미지가 자동으로 리사이징된다
    And 리사이징된 이미지 크기가 20MB 이하이다
    And 원본 해상도의 적정 비율이 유지된다
    And API 호출이 정상 수행된다

  Scenario: 정상 크기 이미지 처리
    Given 입력 이미지 크기가 5MB이다
    When analyze_image()를 호출한다
    Then 리사이징 없이 원본 이미지가 사용된다
```

**관련 요구사항**: REQ-S-005

---

## 10. Quality Gate

### Definition of Done

다음 조건이 모두 충족되면 SPEC-API-001이 완료된 것으로 간주한다:

#### 코드 품질
- [ ] 모든 Python 파일이 ruff 린트를 통과한다
- [ ] mypy 타입 검사를 통과한다 (strict 모드)
- [ ] 테스트 커버리지가 85% 이상이다

#### 기능 완료
- [ ] 모든 Ubiquitous 요구사항(REQ-U-*)이 구현되었다
- [ ] 모든 Event-Driven 요구사항(REQ-E-*)이 구현되었다
- [ ] 모든 State-Driven 요구사항(REQ-S-*)이 구현되었다
- [ ] 모든 Unwanted 요구사항(REQ-N-*)이 구현되었다

#### 테스트 통과
- [ ] 모든 단위 테스트가 통과한다
- [ ] 인수 테스트 시나리오가 모두 통과한다
- [ ] 모의 API 호출 테스트가 성공한다

#### 문서화
- [ ] 코드에 적절한 docstring이 포함되어 있다
- [ ] 주요 API 사용법 예시가 포함되어 있다

---

## 11. 테스트 매트릭스

### 요구사항-시나리오 매핑

| 요구사항 ID | 시나리오 | 테스트 파일 |
|-------------|----------|-------------|
| REQ-U-001 | Bearer 토큰 인증 헤더 사용 | test_auth.py |
| REQ-U-003 | 캐시 히트 시 캐시 결과 반환 | test_cache.py |
| REQ-U-004 | 캐시 미스 시 API 호출 및 캐싱 | test_cache.py |
| REQ-E-001 | 캐시 히트 시 캐시 결과 반환 | test_cache.py |
| REQ-E-002 | Primary 실패 시 Fallback 1 자동 전환 | test_fallback.py |
| REQ-E-003 | Primary와 Fallback 1 실패 시 Fallback 2 전환 | test_fallback.py |
| REQ-E-004 | 모든 API 모델 실패 시 로컬 분석 | test_fallback.py |
| REQ-E-005 | 5xx 에러 시 재시도 | test_retry.py |
| REQ-E-006 | 캐시 미스 시 API 호출 및 캐싱 | test_cache.py |
| REQ-E-007 | 성공적인 API 호출 시 비용 기록 | test_cost.py |
| REQ-E-008 | Retry-After 헤더 존중 | test_retry.py |
| REQ-S-001 | 일일 예산 초과 시 Free 티어 강제 | test_budget.py |
| REQ-S-002 | 월간 예산 초과 시 유료 API 차단 | test_budget.py |
| REQ-S-003 | Redis 연결 실패 시 MemoryCache 사용 | test_cache_fallback.py |
| REQ-S-005 | 20MB 초과 이미지 자동 리사이징 | test_preprocessing.py |
| REQ-N-001 | 무효한 API 키 | test_errors.py |
| REQ-N-002 | 지원되지 않는 이미지 형식 | test_errors.py |
| REQ-N-003 | API 응답 JSON 파싱 실패 | test_errors.py |
| REQ-N-005 | 예산 초과 에러 발생 | test_budget.py |
