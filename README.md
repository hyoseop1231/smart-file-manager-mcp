# Smart File Manager MCP

> AI 기반 스마트 파일 관리 시스템 - MCP(Model Context Protocol) 서버와 멀티미디어 처리 통합

[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-green)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-red)](https://fastapi.tiangolo.com/)
[![MCP](https://img.shields.io/badge/MCP-Protocol-purple)](https://github.com/modelcontextprotocol)
[![Version](https://img.shields.io/badge/Version-5.0.0-orange)](https://github.com/modelcontextprotocol)

## 📋 프로젝트 개요

Smart File Manager MCP는 Claude Desktop과 통합되는 고급 파일 관리 시스템입니다. AI 기반 파일 분석, 멀티미디어 처리, 자동 정리 기능을 제공합니다.

### 🌟 주요 기능

- **🤖 AI 기반 파일 분석**: 이미지 인식, 음성 인식, 텍스트 추출
- **📁 스마트 파일 정리**: AI가 파일 내용을 분석하여 자동 분류
- **🔍 고급 검색**: FTS5 기반 전문 검색 및 의미 기반 검색
- **🎬 멀티미디어 처리**: 이미지, 비디오, 오디오 파일 분석 및 썸네일 생성
- **📊 실시간 모니터링**: Prometheus + Grafana 통합
- **🔌 MCP 프로토콜**: Claude Desktop과의 완벽한 통합

## 🛠️ 기술 스택

- **Backend**: Python 3.11+, FastAPI, SQLite (FTS5)
- **AI/ML**: OpenRouter API (Gemini, GPT-4o, Qwen), Faster-Whisper, bge-m3
- **설정 관리**: pydantic-settings, python-dotenv
- **캐싱**: Redis (redis.asyncio), Memory Cache (Fallback)
- **검색**: SQLite FTS5, Qdrant (벡터 DB)
- **모니터링**: Prometheus, Grafana
- **컨테이너**: Docker, Docker Compose
- **MCP**: Model Context Protocol Server

## 📦 시스템 구조

### v5.0 아키텍처 (리팩토링 후)

```
smart-file-manager-mcp/
├── src/smart_file_manager/      # v5.0 리팩토링 모듈
│   ├── core/                    # 핵심 설정 및 예외
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   └── exceptions.py        # 커스텀 예외 클래스
│   ├── infrastructure/          # 인프라 계층
│   │   └── cache/               # 캐시 시스템
│   │       ├── base.py          # CacheInterface (추상 클래스)
│   │       ├── memory_cache.py  # MemoryCache
│   │       └── redis_cache.py   # RedisCache
│   └── services/                # 서비스 계층
│       ├── openrouter_client.py # OpenRouter API 클라이언트
│       └── model_config.py      # 모델 티어 및 Fallback 설정
├── ai-services/                 # Legacy AI 서비스 모듈
│   ├── multimedia_api_v4.py     # 멀티미디어 API 서버
│   ├── enhanced_indexer_v4.py   # 파일 인덱싱 엔진
│   ├── multimedia_processor.py  # 멀티미디어 처리
│   ├── ai_vision_service.py     # AI 비전 서비스
│   ├── speech_recognition_service.py  # 음성 인식
│   └── db_connection_pool.py    # DB 연결 풀
├── monitoring/                  # 모니터링 설정
│   ├── prometheus.yml
│   └── grafana/
└── docker-compose.yml           # Docker 설정
```

### API 클라이언트 아키텍처 다이어그램

```
                    ┌─────────────────────────────────────────────────┐
                    │              OpenRouter API Client              │
                    │                (SPEC-API-001)                   │
                    └─────────────────────────────────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
            ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
            │   Primary    │    │  Fallback 1  │    │  Fallback 2  │
            │  (Balanced)  │───▶│  (Low-cost)  │───▶│    (Free)    │
            │ Gemini Flash │    │  Qwen 2.5 VL │    │  Gemini Free │
            │  $0.10/1M in │    │  $0.05/1M in │    │     $0       │
            └──────────────┘    └──────────────┘    └──────────────┘
                    │                    │                    │
                    └────────────────────┼────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
            ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
            │    Cache     │    │    Retry     │    │    Budget    │
            │   (7d TTL)   │    │  (Exp B/O)   │    │  Monitoring  │
            │ Redis/Memory │    │ 1s→2s→4s+J  │    │ $1/d, $30/m  │
            └──────────────┘    └──────────────┘    └──────────────┘
```

## 🆕 v5.0.0 리팩토링

### Phase 1: 인프라 설정 (SPEC-INFRA-001) - 완료

**인프라 아키텍처**:
```
src/smart_file_manager/
├── core/
│   ├── config.py          # Settings 클래스 (pydantic-settings)
│   └── exceptions.py      # 커스텀 예외 클래스
└── infrastructure/
    └── cache/
        ├── base.py        # CacheInterface (추상 클래스)
        ├── memory_cache.py # MemoryCache (인메모리 캐시)
        └── redis_cache.py  # RedisCache (Redis 기반 캐시)
```

**주요 변경사항**:
- **OpenRouter API 통합**: OpenAI 대신 OpenRouter API 사용 (비용 90% 절감)
- **pydantic-settings**: 환경 변수 검증 및 타입 안전성
- **이중 캐시 시스템**: Redis (기본) + Memory (Fallback)
- **테스트 커버리지**: 99%+ (77개 테스트 통과)

### Phase 2: OpenRouter API 클라이언트 (SPEC-API-001) - 완료

**API 클라이언트 아키텍처**:
```
src/smart_file_manager/
└── services/
    ├── openrouter_client.py    # 핵심 API 클라이언트
    └── model_config.py         # 모델 티어 및 Fallback 설정
```

**핵심 기능**:
- **httpx 비동기 클라이언트**: Bearer 토큰 인증 기반 HTTPS 통신
- **3단계 Fallback 체인**: Balanced -> Low-cost -> Free 모델 자동 전환
  - Primary: `google/gemini-2.0-flash-001` (Balanced)
  - Fallback 1: `qwen/qwen2.5-vl-32b-instruct` (Low-cost)
  - Fallback 2: `google/gemini-2.0-flash-exp:free` (Free)
- **지수 백오프 재시도**: 1s -> 2s -> 4s + 랜덤 Jitter (0-500ms)
- **비용 모니터링**: 일일 $1 / 월간 $30 예산 제한 및 추적
- **캐시 통합**: 성공 응답 7일 TTL 캐싱 (Redis/Memory)

### v5.0 환경 변수

#### 필수 환경 변수

| 변수명 | 필수 | 기본값 | 설명 |
|--------|------|--------|------|
| `OPENROUTER_API_KEY` | Yes | - | OpenRouter API 키 |

#### 인프라 설정 (SPEC-INFRA-001)

| 변수명 | 필수 | 기본값 | 설명 |
|--------|------|--------|------|
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis 연결 URL |
| `APP_ENV` | No | `development` | 실행 환경 |
| `CACHE_TTL_SECONDS` | No | `86400` | 캐시 TTL (초) |
| `LOG_LEVEL` | No | `INFO` | 로그 레벨 |

#### API 클라이언트 설정 (SPEC-API-001)

| 변수명 | 필수 | 기본값 | 설명 |
|--------|------|--------|------|
| `VISION_PRIMARY_MODEL` | No | `google/gemini-2.0-flash-001` | Primary Vision 모델 (Balanced) |
| `VISION_FALLBACK_MODEL` | No | `qwen/qwen2.5-vl-32b-instruct` | Fallback 1 Vision 모델 (Low-cost) |
| `VISION_FREE_MODEL` | No | `google/gemini-2.0-flash-exp:free` | Fallback 2 Vision 모델 (Free) |
| `API_DAILY_BUDGET` | No | `1.00` | 일일 API 예산 (USD) |
| `API_MONTHLY_BUDGET` | No | `30.00` | 월간 API 예산 (USD) |
| `API_CONNECT_TIMEOUT` | No | `5` | API 연결 타임아웃 (초) |
| `API_READ_TIMEOUT` | No | `30` | API 읽기 타임아웃 (초) |
| `API_MAX_RETRIES` | No | `3` | 최대 재시도 횟수 |

### v5.0 Quick Start

```bash
# 1. 환경 변수 설정
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"

# 2. 선택적: Redis 실행 (없으면 Memory Cache 사용)
docker run -d -p 6379:6379 redis:alpine

# 3. 패키지 설치
pip install -e ".[dev]"

# 4. 테스트 실행
pytest --cov=src/smart_file_manager
```

---

## 📋 v4.0.2 업데이트 (Legacy)

### 개선사항
- **Qdrant 헬스체크 수정**: 올바른 엔드포인트로 변경
- **디스크 관리 도구 추가**:
  - 디스크 사용률 모니터링 API
  - 자동 정리 스크립트
  - 썸네일 및 임시 파일 정리 기능
- **디스크 사용률 권장사항**: 자동 정리 제안 시스템

### 새로운 API 엔드포인트
- `GET /disk/usage` - 현재 디스크 사용률 조회
- `POST /disk/cleanup/thumbnails` - 오래된 썸네일 정리
- `POST /disk/cleanup/temp` - 임시 파일 정리
- `GET /disk/recommendations` - 디스크 정리 권장사항

## 🚀 빠른 시작

### 사전 요구사항

- Docker 및 Docker Compose
- OpenAI API 키 (AI 기능 사용 시)
- 최소 4GB RAM, 10GB 디스크 공간

### 설치 및 실행

1. **프로젝트 클론**
```bash
git clone https://github.com/yourusername/smart-file-manager-mcp.git
cd smart-file-manager-mcp
```

2. **환경 변수 설정**
```bash
cp .env.example .env
# .env 파일을 편집하여 API 키 설정
```

3. **Docker 컨테이너 실행**
```bash
docker-compose up -d
```

4. **상태 확인**
```bash
docker-compose ps
curl http://localhost:8001/health
```

## 📡 API 엔드포인트

### 핵심 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|----------|--------|------|
| `/health` | GET | 시스템 상태 확인 |
| `/search/multimedia` | POST | 멀티미디어 파일 검색 |
| `/ai/analyze` | POST | AI 파일 분석 |
| `/stats/multimedia` | GET | 멀티미디어 통계 |
| `/media/thumbnail/{id}` | GET | 썸네일 가져오기 |

### 검색 API 예제

```bash
# 기본 검색
curl -X POST http://localhost:8001/search/multimedia \
  -H "Content-Type: application/json" \
  -d '{"query": "회의록", "limit": 10}'

# 미디어 타입 필터링
curl -X POST http://localhost:8001/search/multimedia \
  -H "Content-Type: application/json" \
  -d '{"media_types": ["image", "video"], "limit": 5}'
```

## 🔧 설정

### Docker Compose 서비스

- **smart-file-manager-multimedia-v4**: 메인 API 서버 (포트 8001)
- **smart-file-redis-v4**: Redis 캐시 (포트 16379)
- **smart-file-prometheus-v4**: 메트릭 수집 (포트 9090)
- **smart-file-grafana-v4**: 모니터링 대시보드 (포트 3003)

### 환경 변수

```env
# OpenAI API 설정
OPENAI_API_KEY=your-api-key

# 파일 경로 설정
WATCH_DIRECTORIES=/watch_directories
DB_PATH=/data/db/file-index.db
EMBEDDINGS_PATH=/data/embeddings
METADATA_PATH=/data/metadata

# 서비스 포트
MULTIMEDIA_API_PORT=8001
REDIS_PORT=16379
```

## 📊 모니터링

### Grafana 대시보드
- URL: http://localhost:3003
- 기본 계정: admin/admin
- 사전 구성된 대시보드로 시스템 메트릭 확인

### Prometheus 메트릭
- URL: http://localhost:9090
- 주요 메트릭:
  - 파일 인덱싱 상태
  - API 응답 시간
  - AI 처리 통계
  - 시스템 리소스 사용량

## 🐛 트러블슈팅

### 일반적인 문제 해결

1. **API 타입 오류**
   - 증상: `'>' not supported between instances of 'str' and 'int'`
   - 해결: 최신 버전으로 업데이트 (v4.0에서 수정됨)

2. **검색 결과 없음**
   - 증상: 검색 시 빈 결과
   - 해결: 파일 인덱싱 상태 확인
   ```bash
   curl http://localhost:8001/stats/multimedia
   ```

3. **Docker 컨테이너 재시작**
   ```bash
   docker-compose restart smart-file-manager-multimedia-v4
   ```

### 로그 확인

```bash
# API 서버 로그
docker logs -f smart-file-manager-multimedia-v4

# 전체 서비스 로그
docker-compose logs -f
```

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스로 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 👥 팀

- **개발자**: [Your Name](https://github.com/yourusername)
- **문의**: your.email@example.com

## 🙏 감사의 말

- Anthropic Claude 팀 - MCP 프로토콜 제공
- FastAPI 커뮤니티
- 모든 오픈소스 기여자들

---

**⭐ 이 프로젝트가 도움이 되었다면 Star를 눌러주세요!**