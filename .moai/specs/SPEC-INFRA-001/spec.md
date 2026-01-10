---
id: SPEC-INFRA-001
version: "1.0.0"
status: "draft"
created: "2026-01-10"
updated: "2026-01-10"
author: "Developer"
priority: "high"
---

# SPEC-INFRA-001: Phase 1 - 인프라 준비

## HISTORY

| 버전 | 날짜 | 작성자 | 변경사항 |
|------|------|--------|----------|
| 1.0.0 | 2026-01-10 | Developer | 초기 SPEC 작성 |

---

## 1. 개요

### 1.1 목적

Smart File Manager MCP의 리팩토링을 위한 기반 인프라를 구성한다. Redis 캐시 시스템, OpenRouter API 연동, 환경 변수 관리 시스템을 구축하여 후속 개발 단계의 안정적인 기반을 마련한다.

### 1.2 범위

- 환경 변수 관리 시스템 (pydantic-settings 기반)
- Redis 연결 및 캐시 매니저 초기화
- OpenRouter API 클라이언트 기본 구성
- 개발/테스트/프로덕션 환경 분리

### 1.3 관련 문서

- `REFACTORING_SPEC_v5.md`: 전체 리팩토링 명세
- `.moai/project/tech.md`: 기술 스택 정의

---

## 2. EARS 요구사항

### 2.1 Ubiquitous Requirements (시스템 전반 설정)

**[REQ-U-001]** 시스템은 **항상** 시작 시 환경 변수를 로드하고 유효성을 검증해야 한다.

**[REQ-U-002]** 시스템은 **항상** 모든 설정값에 대해 타입 안전성을 보장해야 한다.

**[REQ-U-003]** 시스템은 **항상** 민감한 정보(API 키, 비밀번호)를 로그에 노출하지 않아야 한다.

### 2.2 Event-Driven Requirements (연결 및 API 호출)

**[REQ-E-001]** **WHEN** Settings 객체가 생성되면 **THEN** `.env` 파일에서 환경 변수를 로드하고 pydantic 유효성 검사를 수행해야 한다.

**[REQ-E-002]** **WHEN** 캐시 매니저가 초기화되면 **THEN** Redis 서버에 연결을 시도하고 ping 응답을 확인해야 한다.

**[REQ-E-003]** **WHEN** OpenRouter API 클라이언트가 초기화되면 **THEN** API 키 유효성을 검증해야 한다.

**[REQ-E-004]** **WHEN** 환경 변수 파일이 변경되면 **THEN** 애플리케이션 재시작 없이 설정을 다시 로드할 수 있어야 한다.

### 2.3 Unwanted Behavior Requirements (연결 실패 시 처리)

**[REQ-N-001]** 시스템은 **잘못된 타입의 환경 변수가 설정되었을 때** ValidationError를 발생시켜야 한다.

**[REQ-N-002]** 시스템은 **필수 환경 변수가 누락되었을 때** 명확한 오류 메시지와 함께 시작을 거부해야 한다.

**[REQ-N-003]** 시스템은 **Redis 연결 실패 시** graceful degradation을 수행하고 로컬 캐시로 폴백해야 한다.

**[REQ-N-004]** 시스템은 **OpenRouter API 키가 유효하지 않을 때** 초기화 단계에서 명확한 오류를 보고해야 한다.

### 2.4 State-Driven Requirements (환경별 설정 상태)

**[REQ-S-001]** **IF** `APP_ENV=development` **THEN** DEBUG 로깅이 활성화되고 상세 오류 메시지가 표시되어야 한다.

**[REQ-S-002]** **IF** `APP_ENV=production` **THEN** 최소 로깅과 보안 강화 설정이 적용되어야 한다.

**[REQ-S-003]** **IF** `APP_ENV=test` **THEN** 테스트용 mock 설정과 격리된 Redis 데이터베이스가 사용되어야 한다.

**[REQ-S-004]** **IF** Redis가 사용 불가 상태이면 **THEN** 인메모리 캐시로 자동 전환되어야 한다.

### 2.5 Optional Requirements (Docker 기반 Redis)

**[REQ-O-001]** **가능하면** Docker Compose를 통한 Redis 설정을 제공하여 개발 환경 구축을 간소화해야 한다.

**[REQ-O-002]** **가능하면** Redis Sentinel 또는 Cluster 모드 지원을 위한 설정 옵션을 제공해야 한다.

---

## 3. 기술 명세

### 3.1 환경 변수 목록

| 변수명 | 타입 | 필수 | 기본값 | 설명 |
|--------|------|------|--------|------|
| `APP_ENV` | str | N | development | 실행 환경 (development/test/production) |
| `OPENROUTER_API_KEY` | SecretStr | Y | - | OpenRouter API 인증 키 |
| `REDIS_URL` | str | N | redis://localhost:6379/0 | Redis 연결 URL |
| `VISION_PRIMARY_MODEL` | str | N | google/gemini-2.0-flash-001 | 주 비전 모델 |
| `VISION_FALLBACK_MODEL` | str | N | openai/gpt-4o-mini | 폴백 비전 모델 |
| `CACHE_TTL_SECONDS` | int | N | 86400 | 캐시 기본 TTL (초) |
| `LOG_LEVEL` | str | N | INFO | 로깅 레벨 |

### 3.2 디렉토리 구조

```
src/
└── smart_file_manager/
    ├── core/
    │   ├── __init__.py
    │   ├── config.py          # Settings 클래스, 환경 변수 관리
    │   └── exceptions.py      # 커스텀 예외 정의
    └── infrastructure/
        ├── __init__.py
        └── cache/
            ├── __init__.py
            ├── base.py        # CacheInterface 추상 클래스
            ├── redis_cache.py # Redis 캐시 구현
            └── memory_cache.py # 인메모리 캐시 구현
```

### 3.3 의존성 패키지

```toml
[project.dependencies]
pydantic = ">=2.0.0"
pydantic-settings = ">=2.1.0"
redis = ">=5.0.0"
python-dotenv = ">=1.0.0"
httpx = ">=0.27.0"
```

---

## 4. 제약사항

### 4.1 기술적 제약

- Python 3.11 이상 필수
- Redis 6.0 이상 권장
- pydantic v2 문법 사용 필수

### 4.2 보안 제약

- API 키는 `SecretStr` 타입으로 관리
- 로그에 민감 정보 출력 금지
- `.env` 파일은 `.gitignore`에 포함 필수

### 4.3 성능 제약

- Settings 로드 시간 < 100ms
- Redis 연결 타임아웃 = 5초
- Health check 응답 시간 < 50ms

---

## 5. 추적성

### 5.1 관련 SPEC

- 후속: SPEC-CACHE-001 (캐시 시스템 구현)
- 후속: SPEC-LLM-001 (LLM 서비스 레이어)

### 5.2 TAG 추적

| TAG ID | 요구사항 | 테스트 케이스 |
|--------|----------|---------------|
| INFRA-001-U001 | REQ-U-001 | test_settings_load_on_startup |
| INFRA-001-E001 | REQ-E-001 | test_settings_validation |
| INFRA-001-E002 | REQ-E-002 | test_redis_connection |
| INFRA-001-N001 | REQ-N-001 | test_invalid_type_validation |
| INFRA-001-S001 | REQ-S-001 | test_development_mode |
