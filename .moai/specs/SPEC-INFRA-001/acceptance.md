# SPEC-INFRA-001 인수 기준

## 관련 SPEC

- SPEC ID: SPEC-INFRA-001
- 제목: Phase 1 - 인프라 준비 (Redis, OpenRouter API, 환경 변수 구성)
- 우선순위: HIGH

---

## 1. 인수 기준 개요

이 문서는 SPEC-INFRA-001의 완료를 검증하기 위한 상세한 인수 기준과 테스트 시나리오를 정의한다.

---

## 2. 테스트 시나리오

### Scenario 1: 환경 변수 로드

```gherkin
Feature: 환경 변수 로드
  Settings 클래스가 .env 파일에서 환경 변수를 올바르게 로드하는지 검증한다.

  Scenario: 유효한 .env 파일에서 설정 로드
    Given .env 파일이 모든 필수 환경 변수와 함께 존재할 때
    And OPENROUTER_API_KEY가 "sk-or-test-12345"로 설정되어 있을 때
    And REDIS_URL이 "redis://localhost:6379/0"으로 설정되어 있을 때
    When Settings 객체가 생성되면
    Then 모든 환경 변수가 올바른 타입으로 로드되어야 한다
    And openrouter_api_key는 SecretStr 타입이어야 한다
    And redis_url은 "redis://localhost:6379/0"이어야 한다

  Scenario: 환경 변수 파일 없이 기본값 사용
    Given .env 파일이 존재하지 않을 때
    And 환경 변수가 시스템에 직접 설정되어 있을 때
    When Settings 객체가 생성되면
    Then 기본값이 적용되어야 한다
    And app_env는 "development"여야 한다
    And cache_ttl_seconds는 86400이어야 한다
```

### Scenario 2: Redis 연결

```gherkin
Feature: Redis 연결
  캐시 매니저가 Redis 서버에 정상적으로 연결되는지 검증한다.

  Scenario: Redis 서버 연결 성공
    Given Redis 서버가 localhost:6379에서 실행 중일 때
    And REDIS_URL이 "redis://localhost:6379/0"으로 설정되어 있을 때
    When 캐시 매니저가 초기화되면
    Then Redis에 연결되어야 한다
    And ping 명령에 "PONG" 응답을 받아야 한다
    And health_check() 메서드가 True를 반환해야 한다

  Scenario: Redis 연결 실패 시 폴백
    Given Redis 서버가 사용 불가능할 때
    When 캐시 매니저가 초기화되면
    Then 인메모리 캐시로 자동 전환되어야 한다
    And 경고 로그가 기록되어야 한다
    And 애플리케이션이 정상 동작해야 한다
```

### Scenario 3: OpenRouter API 검증

```gherkin
Feature: OpenRouter API 키 검증
  OpenRouter API 클라이언트가 API 키를 올바르게 검증하는지 확인한다.

  Scenario: 유효한 API 키 설정
    Given OPENROUTER_API_KEY가 유효한 키로 설정되어 있을 때
    When API 클라이언트가 초기화되면
    Then API 키가 SecretStr로 안전하게 저장되어야 한다
    And API 키가 로그에 노출되지 않아야 한다

  Scenario: API 키 누락
    Given OPENROUTER_API_KEY가 설정되지 않았을 때
    When Settings 객체 생성을 시도하면
    Then ValidationError가 발생해야 한다
    And 오류 메시지에 "OPENROUTER_API_KEY"가 포함되어야 한다
```

### Scenario 4: 설정 타입 검증

```gherkin
Feature: 설정 타입 검증
  잘못된 타입의 환경 변수가 설정되었을 때 적절한 오류가 발생하는지 검증한다.

  Scenario: 잘못된 정수 타입
    Given CACHE_TTL_SECONDS가 "not-a-number"로 설정되어 있을 때
    When Settings 로드를 시도하면
    Then ValidationError가 발생해야 한다
    And 오류 메시지에 타입 오류 정보가 포함되어야 한다

  Scenario: 잘못된 환경 값
    Given APP_ENV가 "invalid_environment"로 설정되어 있을 때
    When Settings 로드를 시도하면
    Then ValidationError가 발생해야 한다
    And 오류 메시지에 허용된 값 목록이 포함되어야 한다

  Scenario: 잘못된 Redis URL 형식
    Given REDIS_URL이 "not-a-valid-url"로 설정되어 있을 때
    When 캐시 매니저가 초기화되면
    Then 연결 오류가 발생해야 한다
    And 인메모리 캐시로 폴백되어야 한다
```

### Scenario 5: 환경별 설정 분기

```gherkin
Feature: 환경별 설정 분기
  APP_ENV 값에 따라 적절한 설정이 적용되는지 검증한다.

  Scenario: Development 환경
    Given APP_ENV가 "development"로 설정되어 있을 때
    When Settings 객체가 생성되면
    Then DEBUG 로깅이 활성화되어야 한다
    And 상세 오류 메시지가 표시되어야 한다

  Scenario: Production 환경
    Given APP_ENV가 "production"으로 설정되어 있을 때
    When Settings 객체가 생성되면
    Then 최소 로깅 레벨이 적용되어야 한다
    And 민감 정보가 오류 메시지에 포함되지 않아야 한다

  Scenario: Test 환경
    Given APP_ENV가 "test"로 설정되어 있을 때
    When Settings 객체가 생성되면
    Then 테스트용 설정이 적용되어야 한다
    And 격리된 캐시 인스턴스가 사용되어야 한다
```

### Scenario 6: 캐시 CRUD 작업

```gherkin
Feature: 캐시 기본 작업
  캐시 인터페이스의 기본 CRUD 작업이 정상 동작하는지 검증한다.

  Scenario: 캐시 값 저장 및 조회
    Given 캐시 매니저가 초기화되어 있을 때
    When "test_key"에 "test_value"를 저장하면
    Then set() 메서드가 True를 반환해야 한다
    And get("test_key")가 "test_value"를 반환해야 한다

  Scenario: 캐시 값 삭제
    Given "test_key"에 값이 저장되어 있을 때
    When delete("test_key")를 호출하면
    Then True가 반환되어야 한다
    And exists("test_key")가 False를 반환해야 한다

  Scenario: TTL 만료
    Given 캐시 값이 TTL 1초로 저장되어 있을 때
    When 2초가 경과하면
    Then get() 호출 시 None이 반환되어야 한다
```

---

## 3. 품질 게이트 기준

### 3.1 테스트 커버리지

| 항목 | 최소 기준 | 목표 기준 |
|------|-----------|-----------|
| 라인 커버리지 | 85% | 90% |
| 브랜치 커버리지 | 80% | 85% |
| 핵심 경로 커버리지 | 100% | 100% |

### 3.2 코드 품질

| 항목 | 기준 |
|------|------|
| ruff 린팅 오류 | 0개 |
| mypy 타입 오류 | 0개 |
| 복잡도 (McCabe) | 함수당 최대 10 |
| 문서화 | 모든 public 함수 docstring 필수 |

### 3.3 성능 기준

| 항목 | 기준 |
|------|------|
| Settings 로드 시간 | < 100ms |
| Redis 연결 시간 | < 5초 (타임아웃) |
| Health check 응답 시간 | < 50ms |
| 캐시 get/set 응답 시간 | < 10ms |

---

## 4. 검증 방법

### 4.1 자동화 테스트

```bash
# 단위 테스트 실행
pytest tests/test_config.py tests/test_cache.py -v

# 커버리지 측정
pytest --cov=src/smart_file_manager/core --cov=src/smart_file_manager/infrastructure --cov-report=html

# 타입 검사
mypy src/smart_file_manager/core src/smart_file_manager/infrastructure

# 린팅
ruff check src/smart_file_manager/core src/smart_file_manager/infrastructure
```

### 4.2 수동 검증

1. `.env.example`을 `.env`로 복사하고 값 설정
2. Python REPL에서 Settings 객체 생성 확인
3. Redis 연결 상태 확인 (redis-cli ping)
4. 로그 출력에서 민감 정보 노출 여부 확인

---

## 5. Definition of Done

### 5.1 필수 완료 조건

- [ ] 모든 단위 테스트 통과
- [ ] 테스트 커버리지 85% 이상
- [ ] ruff 린팅 오류 0개
- [ ] mypy 타입 오류 0개
- [ ] `.env.example` 템플릿 작성 완료
- [ ] README에 설정 방법 문서화

### 5.2 인수 조건

- [ ] Settings 클래스가 환경 변수를 올바르게 로드함
- [ ] Redis 연결 성공 시 ping 응답 확인됨
- [ ] Redis 연결 실패 시 인메모리 캐시로 폴백됨
- [ ] 잘못된 설정 시 명확한 오류 메시지 출력됨
- [ ] API 키가 로그에 노출되지 않음

### 5.3 문서화 조건

- [ ] 모든 public 함수에 docstring 작성
- [ ] 환경 변수 목록 문서화
- [ ] 트러블슈팅 가이드 작성

---

## 6. 추적성 매트릭스

| 시나리오 | 요구사항 ID | 테스트 함수 |
|----------|-------------|-------------|
| 환경 변수 로드 | REQ-U-001, REQ-E-001 | test_settings_load_valid_env |
| Redis 연결 | REQ-E-002, REQ-N-003, REQ-S-004 | test_redis_connection, test_redis_fallback |
| OpenRouter API 검증 | REQ-E-003, REQ-N-004 | test_api_key_validation |
| 설정 타입 검증 | REQ-N-001, REQ-N-002 | test_invalid_type_validation |
| 환경별 설정 | REQ-S-001, REQ-S-002, REQ-S-003 | test_environment_settings |
| 캐시 CRUD | - | test_cache_crud_operations |
