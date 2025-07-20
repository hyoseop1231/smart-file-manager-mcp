# Smart File Manager MCP 🚀

> AI 기반 스마트 파일 관리 시스템 - MCP(Model Context Protocol) 서버와 멀티미디어 처리 통합

[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-red)](https://fastapi.tiangolo.com/)
[![MCP](https://img.shields.io/badge/MCP-Protocol-purple)](https://github.com/modelcontextprotocol)

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

- **Backend**: Python 3.8+, FastAPI, SQLite (FTS5)
- **AI/ML**: OpenAI GPT-4 Vision, Whisper, TensorFlow, PyTorch
- **검색**: SQLite FTS5, ChromaDB (벡터 DB)
- **모니터링**: Prometheus, Grafana
- **컨테이너**: Docker, Docker Compose
- **MCP**: Model Context Protocol Server

## 📦 시스템 구조

```
smart-file-manager-mcp/
├── ai-services/           # AI 서비스 모듈
│   ├── multimedia_api_v4.py    # 멀티미디어 API 서버
│   ├── enhanced_indexer_v4.py  # 파일 인덱싱 엔진
│   ├── multimedia_processor.py  # 멀티미디어 처리
│   ├── ai_vision_service.py    # AI 비전 서비스
│   ├── speech_recognition_service.py  # 음성 인식
│   └── db_connection_pool.py   # DB 연결 풀
├── monitoring/            # 모니터링 설정
│   ├── prometheus.yml
│   └── grafana/
└── docker-compose.yml     # Docker 설정
```

## 🆕 v4.0.2 업데이트

### 개선사항
- **✅ Qdrant 헬스체크 수정**: 올바른 엔드포인트로 변경
- **🧹 디스크 관리 도구 추가**: 
  - 디스크 사용률 모니터링 API
  - 자동 정리 스크립트
  - 썸네일 및 임시 파일 정리 기능
- **📊 디스크 사용률 권장사항**: 자동 정리 제안 시스템

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