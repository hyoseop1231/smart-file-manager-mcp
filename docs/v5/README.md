# Smart File Manager v5.0 Documentation

> SPEC-INFRA-001 리팩토링 문서

## Overview

Smart File Manager v5.0은 OpenRouter API 통합과 최적화된 캐시 시스템을 통해 성능과 비용 효율성을 크게 개선했습니다.

## Documentation Index

### Core Documentation

| 문서 | 설명 |
|------|------|
| [Configuration Guide](./configuration.md) | Settings 클래스, 환경 변수, 캐시 구성 |

### Architecture

```
src/smart_file_manager/
├── core/
│   ├── __init__.py
│   ├── config.py              # Settings (pydantic-settings)
│   └── exceptions.py          # Custom exceptions
└── infrastructure/
    ├── __init__.py
    └── cache/
        ├── __init__.py
        ├── base.py            # CacheInterface (ABC)
        ├── memory_cache.py    # MemoryCache implementation
        └── redis_cache.py     # RedisCache implementation
```

## v5.0 Key Features

### 1. OpenRouter API Integration

- **비용 절감**: OpenAI 직접 사용 대비 90% 비용 절감
- **다중 모델 지원**: Gemini, GPT-4o, Qwen 등 다양한 모델
- **Fallback 전략**: Primary -> Fallback -> 로컬 분석 자동 전환

### 2. Dual Cache System

- **Redis Cache**: 분산 환경, 영속성 지원
- **Memory Cache**: 단일 프로세스, Redis 불가 시 자동 Fallback
- **통합 인터페이스**: `CacheInterface`로 일관된 API

### 3. Type-Safe Configuration

- **pydantic-settings**: 환경 변수 자동 검증
- **SecretStr**: API 키 보안 처리
- **Validation**: 타입 및 값 범위 검증

## Quick Start

```bash
# 1. 환경 변수 설정
export OPENROUTER_API_KEY="sk-or-v1-your-key"

# 2. 패키지 설치
pip install -e ".[dev]"

# 3. 테스트 실행
pytest --cov=src/smart_file_manager

# 4. 결과 확인 (99%+ coverage expected)
```

## Test Coverage

| Module | Coverage | Tests |
|--------|----------|-------|
| core/config.py | 100% | 25 |
| core/exceptions.py | 100% | 12 |
| infrastructure/cache/base.py | 100% | 5 |
| infrastructure/cache/memory_cache.py | 100% | 18 |
| infrastructure/cache/redis_cache.py | 100% | 17 |
| **Total** | **99%+** | **77** |

## Roadmap

### Phase 1: Infrastructure Setup (Completed)
- [x] Settings class with pydantic-settings
- [x] Custom exceptions
- [x] CacheInterface (ABC)
- [x] MemoryCache implementation
- [x] RedisCache implementation
- [x] 99%+ test coverage

### Phase 2: Core Services (Planned)
- [ ] OpenRouter client
- [ ] Vision service
- [ ] STT service (Faster-Whisper)
- [ ] Embedding service (bge-m3)

### Phase 3: Database Optimization (Planned)
- [ ] Schema normalization
- [ ] Compression support
- [ ] Migration scripts

### Phase 4: API Layer (Planned)
- [ ] FastAPI integration
- [ ] MCP server update
- [ ] Health endpoints

## Related Documents

- [REFACTORING_SPEC_v5.md](../../REFACTORING_SPEC_v5.md) - 전체 리팩토링 스펙
- [README.md](../../README.md) - 프로젝트 메인 문서
- [pyproject.toml](../../pyproject.toml) - 의존성 및 빌드 설정
