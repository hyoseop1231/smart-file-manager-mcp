# Smart File Manager v5.0 Configuration Guide

> SPEC-INFRA-001 Phase 1 구현에 따른 설정 가이드

## Overview

Smart File Manager v5.0은 `pydantic-settings`를 활용한 타입 안전한 설정 관리 시스템을 제공합니다. 환경 변수를 통해 애플리케이션을 구성하며, 자동 검증과 기본값을 지원합니다.

---

## Settings 클래스 사용법

### 기본 사용

```python
from smart_file_manager.core.config import get_settings

# 싱글톤 패턴으로 설정 인스턴스 획득
settings = get_settings()

# 설정 값 접근
api_key = settings.openrouter_api_key.get_secret_value()
redis_url = settings.redis_url
log_level = settings.log_level

# 환경 확인
if settings.is_development:
    print("Development mode")
```

### SecretStr 처리

API 키와 같은 민감한 정보는 `SecretStr` 타입으로 보호됩니다.

```python
# 잘못된 방법 (마스킹된 값 출력)
print(settings.openrouter_api_key)  # SecretStr('**********')

# 올바른 방법
api_key = settings.openrouter_api_key.get_secret_value()
```

---

## 환경 변수 레퍼런스

### 필수 환경 변수

| 변수명 | 타입 | 설명 | 예시 |
|--------|------|------|------|
| `OPENROUTER_API_KEY` | SecretStr | OpenRouter API 인증 키 | `sk-or-v1-xxx...` |

### 선택적 환경 변수

| 변수명 | 타입 | 기본값 | 설명 |
|--------|------|--------|------|
| `APP_ENV` | str | `development` | 실행 환경 (`development`, `staging`, `production`) |
| `REDIS_URL` | str | `redis://localhost:6379/0` | Redis 연결 URL |
| `VISION_PRIMARY_MODEL` | str | `google/gemini-2.0-flash-001` | 기본 Vision AI 모델 |
| `VISION_FALLBACK_MODEL` | str | `openai/gpt-4o-mini` | Fallback Vision 모델 |
| `CACHE_TTL_SECONDS` | int | `86400` | 캐시 TTL (초 단위, 기본 24시간) |
| `LOG_LEVEL` | str | `INFO` | 로그 레벨 (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |

---

## .env 파일 설정

### 개발 환경 예시

```bash
# .env (development)
OPENROUTER_API_KEY=sk-or-v1-your-development-key
APP_ENV=development
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=DEBUG
CACHE_TTL_SECONDS=3600
```

### 프로덕션 환경 예시

```bash
# .env (production)
OPENROUTER_API_KEY=sk-or-v1-your-production-key
APP_ENV=production
REDIS_URL=redis://redis-server:6379/0
LOG_LEVEL=WARNING
CACHE_TTL_SECONDS=86400
VISION_PRIMARY_MODEL=google/gemini-2.0-flash-001
VISION_FALLBACK_MODEL=openai/gpt-4o-mini
```

---

## Vision 모델 구성

### 지원 모델 목록

**Primary Models (추천)**:
- `google/gemini-2.0-flash-001` - 빠른 속도, 합리적인 비용
- `google/gemini-2.5-pro` - 최고 품질, 높은 비용
- `openai/gpt-4o` - 균형잡힌 성능

**Fallback Models**:
- `openai/gpt-4o-mini` - 경제적인 옵션
- `qwen/qwen2.5-vl-32b-instruct` - 한국어 최적화
- `google/gemini-2.0-flash-exp:free` - 무료 (개발용)

### Fallback 전략

```
요청 → Primary Model → 성공 → 응답 반환
           │
           └── 실패/타임아웃 (5초)
                   │
                   ↓
           Fallback Model → 성공 → 응답 반환
                   │
                   └── 실패
                           │
                           ↓
                   로컬 기본 분석 → 메타데이터만 반환
```

---

## 캐시 구성

### Redis Cache (기본)

Redis가 사용 가능한 경우 자동으로 Redis 캐시를 사용합니다.

```python
from smart_file_manager.infrastructure.cache.redis_cache import RedisCache

cache = RedisCache(
    redis_url="redis://localhost:6379/0",
    default_ttl=86400  # 24시간
)

# 연결
await cache.connect()

# 사용
await cache.set("key", {"data": "value"}, ttl=3600)
result = await cache.get("key")

# 연결 종료
await cache.disconnect()
```

### Memory Cache (Fallback)

Redis를 사용할 수 없는 경우 인메모리 캐시를 사용합니다.

```python
from smart_file_manager.infrastructure.cache.memory_cache import MemoryCache

cache = MemoryCache(
    default_ttl=86400,
    max_size=1000  # 최대 항목 수
)

# 동일한 인터페이스
await cache.set("key", {"data": "value"})
result = await cache.get("key")
```

### CacheInterface

모든 캐시 구현체는 `CacheInterface`를 따릅니다.

```python
from smart_file_manager.infrastructure.cache.base import CacheInterface

class CacheInterface(ABC):
    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def exists(self, key: str) -> bool: ...
    async def clear(self) -> None: ...
    async def health_check(self) -> bool: ...
```

---

## 검증 규칙

### CACHE_TTL_SECONDS 검증

```python
# 유효한 값
CACHE_TTL_SECONDS=1       # 최소값
CACHE_TTL_SECONDS=86400   # 24시간
CACHE_TTL_SECONDS=604800  # 7일

# 무효한 값 (ValidationError 발생)
CACHE_TTL_SECONDS=0       # 0 이하 불가
CACHE_TTL_SECONDS=-100    # 음수 불가
```

### LOG_LEVEL 검증

```python
# 유효한 값 (대소문자 구분)
LOG_LEVEL=DEBUG
LOG_LEVEL=INFO
LOG_LEVEL=WARNING
LOG_LEVEL=ERROR
LOG_LEVEL=CRITICAL

# 무효한 값 (ValidationError 발생)
LOG_LEVEL=debug    # 소문자 불가
LOG_LEVEL=WARN     # 약어 불가
```

---

## 예외 처리

### CacheConnectionError

Redis 연결 실패 시 발생합니다.

```python
from smart_file_manager.core.exceptions import CacheConnectionError

try:
    await cache.connect()
except CacheConnectionError as e:
    print(f"Redis 연결 실패: {e}")
    # Fallback to memory cache
```

### ConfigurationError

설정 값이 유효하지 않을 때 발생합니다.

```python
from smart_file_manager.core.exceptions import ConfigurationError

# 환경 변수 누락 시
# pydantic.ValidationError: OPENROUTER_API_KEY field required
```

---

## Best Practices

### 1. 환경별 설정 분리

```bash
# 파일 구조
.env              # 로컬 개발 (gitignore)
.env.example      # 템플릿 (커밋)
.env.staging      # 스테이징 환경
.env.production   # 프로덕션 환경
```

### 2. 민감한 정보 보호

```bash
# .gitignore에 추가
.env
.env.local
.env.*.local
```

### 3. 설정 테스트

```python
import pytest
from smart_file_manager.core.config import Settings

def test_settings_with_env(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings()

    assert settings.log_level == "DEBUG"
    assert settings.openrouter_api_key.get_secret_value() == "test-key"
```

---

## Troubleshooting

### OPENROUTER_API_KEY 누락 오류

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
openrouter_api_key
  Field required [type=missing, input_value={}, input_type=dict]
```

**해결방법**: `.env` 파일에 `OPENROUTER_API_KEY` 설정 또는 환경 변수로 직접 설정

### Redis 연결 실패

```
CacheConnectionError: Failed to connect to Redis: Connection refused
```

**해결방법**:
1. Redis 서버 실행 확인: `docker run -d -p 6379:6379 redis:alpine`
2. REDIS_URL 확인: `redis://localhost:6379/0`
3. 연결 불가 시 MemoryCache가 자동으로 사용됨

---

## Related Documentation

- [SPEC-INFRA-001: Infrastructure Setup](../../.moai/specs/SPEC-INFRA-001/)
- [REFACTORING_SPEC_v5.md](../../REFACTORING_SPEC_v5.md)
- [OpenRouter API Documentation](https://openrouter.ai/docs)
- [pydantic-settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
