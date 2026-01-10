# SPEC-INFRA-001 구현 계획

## 관련 SPEC

- SPEC ID: SPEC-INFRA-001
- 제목: Phase 1 - 인프라 준비 (Redis, OpenRouter API, 환경 변수 구성)
- 우선순위: HIGH

---

## 1. 구현 개요

### 1.1 목표

Smart File Manager MCP 리팩토링의 첫 번째 단계로, 안정적인 개발 기반을 구축한다. pydantic-settings 기반의 타입 안전한 설정 관리, Redis 캐시 연결, OpenRouter API 기본 구성을 완료한다.

### 1.2 핵심 산출물

- `core/config.py`: Settings 클래스 및 환경 변수 관리
- `core/exceptions.py`: 커스텀 예외 정의
- `infrastructure/cache/`: 캐시 인터페이스 및 구현체
- `.env.example`: 환경 변수 템플릿
- 단위 테스트 파일

---

## 2. 마일스톤

### Primary Goal: 환경 변수 관리 시스템

**목표**: pydantic-settings 기반의 타입 안전한 설정 관리 시스템 구축

**태스크 분해**:

1. 디렉토리 구조 생성
   - `src/smart_file_manager/core/` 디렉토리 생성
   - `src/smart_file_manager/infrastructure/cache/` 디렉토리 생성

2. `.env.example` 템플릿 작성
   - 모든 환경 변수 문서화
   - 기본값 및 설명 포함

3. `core/config.py` 구현
   - `Settings` 클래스 정의 (BaseSettings 상속)
   - 환경 변수 유효성 검사 로직
   - 환경별 설정 분기 (dev/test/prod)

4. `core/exceptions.py` 구현
   - `ConfigurationError` 정의
   - `CacheConnectionError` 정의

**완료 기준**:
- Settings 객체 생성 시 환경 변수 자동 로드
- 잘못된 타입 입력 시 ValidationError 발생
- 필수 변수 누락 시 명확한 오류 메시지

### Secondary Goal: Redis 캐시 연결

**목표**: Redis 연결 관리 및 폴백 메커니즘 구현

**태스크 분해**:

1. `infrastructure/cache/base.py` 구현
   - `CacheInterface` 추상 클래스 정의
   - `get`, `set`, `delete`, `exists` 메서드 인터페이스

2. `infrastructure/cache/redis_cache.py` 구현
   - Redis 연결 관리
   - 연결 상태 확인 (ping)
   - 재연결 로직

3. `infrastructure/cache/memory_cache.py` 구현
   - 인메모리 캐시 (폴백용)
   - TTL 지원
   - 최대 크기 제한

4. 캐시 팩토리 함수 구현
   - 환경에 따른 캐시 선택
   - Redis 실패 시 자동 폴백

**완료 기준**:
- Redis 연결 성공 시 ping 응답 확인
- 연결 실패 시 memory cache로 자동 전환
- 로그에 연결 상태 기록

### Tertiary Goal: OpenRouter API 기본 구성

**목표**: OpenRouter API 클라이언트 기본 설정 및 키 검증

**태스크 분해**:

1. API 키 검증 유틸리티 구현
   - 키 형식 검증
   - 간단한 API 호출로 유효성 확인

2. httpx 클라이언트 기본 설정
   - 타임아웃 설정
   - 재시도 정책
   - 헤더 구성

**완료 기준**:
- API 키 유효성 검증 가능
- 기본 HTTP 클라이언트 설정 완료

### Optional Goal: Docker 개발 환경

**목표**: Docker Compose를 통한 개발 환경 간소화

**태스크 분해**:

1. `docker-compose.dev.yml` 작성
   - Redis 서비스 정의
   - 볼륨 마운트 설정

2. 개발 환경 스크립트 작성
   - 환경 시작/종료 스크립트
   - 헬스 체크 스크립트

---

## 3. 기술적 접근 방식

### 3.1 Settings 클래스 설계

```python
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # 환경 설정
    app_env: str = "development"

    # OpenRouter API
    openrouter_api_key: SecretStr

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # 모델 설정
    vision_primary_model: str = "google/gemini-2.0-flash-001"
    vision_fallback_model: str = "openai/gpt-4o-mini"

    # 캐시 설정
    cache_ttl_seconds: int = 86400

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        allowed = {"development", "test", "production"}
        if v not in allowed:
            raise ValueError(f"app_env must be one of {allowed}")
        return v
```

### 3.2 캐시 인터페이스 설계

```python
from abc import ABC, abstractmethod
from typing import Any, Optional

class CacheInterface(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass
```

### 3.3 폴백 전략

1. Redis 연결 시도
2. 연결 실패 시 로그 경고 출력
3. MemoryCache 인스턴스 반환
4. 애플리케이션 정상 동작 유지

---

## 4. 테스트 전략

### 4.1 단위 테스트

- `test_config.py`: Settings 로드 및 유효성 검사
- `test_redis_cache.py`: Redis 연결 및 CRUD
- `test_memory_cache.py`: 인메모리 캐시 동작
- `test_cache_factory.py`: 캐시 선택 및 폴백

### 4.2 통합 테스트

- 실제 Redis 인스턴스 연결 테스트 (Docker 사용)
- 환경 변수 로드 E2E 테스트

### 4.3 테스트 커버리지 목표

- 최소 85% 이상
- 핵심 경로 100% 커버리지

---

## 5. 의존성

### 5.1 선행 조건

- Python 3.11+ 설치
- Redis 서버 접근 가능 (로컬 또는 Docker)
- `.env` 파일 생성

### 5.2 후속 SPEC 의존성

- SPEC-CACHE-001: 캐시 시스템 상세 구현 (이 SPEC의 기반 필요)
- SPEC-LLM-001: LLM 서비스 레이어 (config.py 의존)

---

## 6. 리스크 및 대응

### 6.1 기술적 리스크

| 리스크 | 영향도 | 대응 방안 |
|--------|--------|-----------|
| Redis 연결 불안정 | 중 | 인메모리 캐시 폴백 구현 |
| pydantic v2 호환성 | 하 | 공식 마이그레이션 가이드 참조 |
| 환경 변수 누락 | 상 | 명확한 오류 메시지와 .env.example 제공 |

### 6.2 완화 전략

- 모든 외부 의존성에 타임아웃 설정
- 상세한 로깅으로 디버깅 용이성 확보
- Docker Compose로 일관된 개발 환경 보장

---

## 7. 파일 생성 순서

1. `.env.example` - 환경 변수 템플릿
2. `src/smart_file_manager/core/__init__.py`
3. `src/smart_file_manager/core/exceptions.py`
4. `src/smart_file_manager/core/config.py`
5. `src/smart_file_manager/infrastructure/__init__.py`
6. `src/smart_file_manager/infrastructure/cache/__init__.py`
7. `src/smart_file_manager/infrastructure/cache/base.py`
8. `src/smart_file_manager/infrastructure/cache/memory_cache.py`
9. `src/smart_file_manager/infrastructure/cache/redis_cache.py`
10. `tests/test_config.py`
11. `tests/test_cache.py`

---

## 8. 추적성

| 요구사항 ID | 구현 파일 | 테스트 파일 |
|-------------|-----------|-------------|
| REQ-U-001 | core/config.py | test_config.py |
| REQ-E-001 | core/config.py | test_config.py |
| REQ-E-002 | infrastructure/cache/redis_cache.py | test_cache.py |
| REQ-N-001 | core/config.py | test_config.py |
| REQ-N-003 | infrastructure/cache/ | test_cache.py |
| REQ-S-001 | core/config.py | test_config.py |
