# Smart File Manager MCP 설치 가이드

## 시스템 요구사항

### 최소 사양
- **CPU**: 2 코어 이상
- **RAM**: 4GB 이상
- **디스크**: 10GB 이상 여유 공간
- **OS**: macOS, Linux, Windows (WSL2)

### 권장 사양
- **CPU**: 4 코어 이상
- **RAM**: 8GB 이상
- **디스크**: 20GB 이상 여유 공간
- **GPU**: NVIDIA GPU (AI 가속 옵션)

### 필수 소프트웨어
- Docker Desktop 20.10+
- Docker Compose 2.0+
- Git

## 설치 단계

### 1. Docker 설치

#### macOS
```bash
# Homebrew를 사용한 설치
brew install --cask docker

# Docker Desktop 실행
open /Applications/Docker.app
```

#### Linux (Ubuntu/Debian)
```bash
# Docker 설치 스크립트
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### Windows
1. [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) 다운로드
2. WSL2 백엔드 활성화
3. 설치 완료 후 재시작

### 2. 프로젝트 클론

```bash
# GitHub에서 프로젝트 클론
git clone https://github.com/yourusername/smart-file-manager-mcp.git
cd smart-file-manager-mcp
```

### 3. 환경 설정

#### 환경 변수 파일 생성
```bash
# 환경 변수 템플릿 복사
cat > .env << EOF
# OpenAI API 설정
OPENAI_API_KEY=your-openai-api-key-here

# 파일 경로 설정
WATCH_DIRECTORIES=/watch_directories
DB_PATH=/data/db/file-index.db
EMBEDDINGS_PATH=/data/embeddings
METADATA_PATH=/data/metadata

# 서비스 포트
MULTIMEDIA_API_PORT=8001
REDIS_PORT=16379
PROMETHEUS_PORT=9090
GRAFANA_PORT=3003

# 리소스 제한
MAX_WORKERS=4
INDEX_BATCH_SIZE=100
EOF
```

#### Docker Compose 설정 확인
```bash
# docker-compose.yml 확인
cat docker-compose.yml
```

### 4. 디렉토리 구조 생성

```bash
# 필요한 디렉토리 생성
mkdir -p data/{db,embeddings,metadata,thumbnails,video_thumbnails}
mkdir -p monitoring/grafana/dashboards
mkdir -p watch_directories

# 권한 설정
chmod -R 755 data/
chmod -R 755 monitoring/
```

### 5. Docker 이미지 빌드 및 실행

```bash
# Docker 이미지 빌드
docker-compose build

# 백그라운드에서 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 6. 서비스 상태 확인

```bash
# 컨테이너 상태 확인
docker-compose ps

# API 헬스 체크
curl http://localhost:8001/health | jq

# 예상 출력:
# {
#   "status": "healthy",
#   "services": {
#     "database": "healthy",
#     "indexer": "available",
#     ...
#   }
# }
```

## Claude Desktop 통합 (MCP)

### 1. MCP 서버 설정

```bash
# MCP 설정 파일 생성
cat > ~/Library/Application\ Support/Claude/claude_desktop_config.json << EOF
{
  "mcpServers": {
    "smart-file-manager": {
      "command": "docker",
      "args": ["exec", "-i", "smart-file-mcp-server-v4", "node", "/app/index.js"]
    }
  }
}
EOF
```

### 2. Claude Desktop 재시작
1. Claude Desktop 종료
2. 다시 시작
3. MCP 서버 연결 확인

## 초기 설정

### 1. 감시 디렉토리 설정

```bash
# 감시할 디렉토리 마운트 (docker-compose.yml 수정)
volumes:
  - ~/Documents:/watch_directories/Documents:ro
  - ~/Desktop:/watch_directories/Desktop:ro
  - ~/Downloads:/watch_directories/Downloads:ro
```

### 2. 초기 인덱싱 실행

```bash
# 수동 인덱싱 트리거
docker exec smart-file-manager-multimedia-v4 python -c "
from enhanced_indexer_v4 import EnhancedFileIndexer
indexer = EnhancedFileIndexer()
indexer.index_directory('/watch_directories')
"
```

### 3. Grafana 대시보드 설정

1. 브라우저에서 http://localhost:3003 접속
2. 기본 로그인: admin/admin
3. 비밀번호 변경
4. Smart File Manager 대시보드 임포트

## 문제 해결

### Docker 관련 문제

#### 포트 충돌
```bash
# 사용 중인 포트 확인
lsof -i :8001
lsof -i :16379

# docker-compose.yml에서 포트 변경
ports:
  - "8002:8001"  # 8002로 변경
```

#### 메모리 부족
```bash
# Docker Desktop 메모리 할당 증가
# Settings > Resources > Memory: 4GB 이상
```

### API 연결 문제

#### 헬스 체크 실패
```bash
# 컨테이너 로그 확인
docker logs smart-file-manager-multimedia-v4

# 컨테이너 재시작
docker-compose restart smart-file-manager-multimedia-v4
```

#### 데이터베이스 오류
```bash
# 데이터베이스 파일 확인
docker exec smart-file-manager-multimedia-v4 ls -la /data/db/

# 데이터베이스 재초기화 (주의: 데이터 손실)
docker exec smart-file-manager-multimedia-v4 rm -f /data/db/file-index.db
docker-compose restart
```

## 업데이트 방법

```bash
# 최신 코드 가져오기
git pull origin main

# 컨테이너 중지
docker-compose down

# 이미지 재빌드
docker-compose build --no-cache

# 서비스 재시작
docker-compose up -d
```

## 백업 및 복원

### 백업
```bash
# 데이터 백업
tar -czf backup_$(date +%Y%m%d).tar.gz data/

# Docker 볼륨 백업
docker run --rm -v smart-file-manager-mcp_file-data:/data -v $(pwd):/backup alpine tar czf /backup/volume_backup.tar.gz /data
```

### 복원
```bash
# 데이터 복원
tar -xzf backup_20240118.tar.gz

# Docker 볼륨 복원
docker run --rm -v smart-file-manager-mcp_file-data:/data -v $(pwd):/backup alpine tar xzf /backup/volume_backup.tar.gz -C /
```

## 성능 최적화

### 1. 인덱싱 성능
```bash
# .env 파일에서 조정
INDEX_BATCH_SIZE=200  # 배치 크기 증가
MAX_WORKERS=8         # 워커 수 증가 (CPU 코어에 맞춰)
```

### 2. 메모리 캐시
```bash
# Redis 메모리 제한 설정
docker exec smart-file-redis-v4 redis-cli CONFIG SET maxmemory 2gb
docker exec smart-file-redis-v4 redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### 3. 데이터베이스 최적화
```bash
# SQLite 최적화
docker exec smart-file-manager-multimedia-v4 python -c "
import sqlite3
conn = sqlite3.connect('/data/db/file-index.db')
conn.execute('VACUUM')
conn.execute('ANALYZE')
conn.close()
"
```

## 보안 고려사항

1. **API 인증**: 프로덕션에서는 API 키 또는 OAuth 구현 필요
2. **네트워크 격리**: Docker 네트워크 설정으로 서비스 간 통신 제한
3. **파일 접근 권한**: 읽기 전용 마운트 사용 권장
4. **환경 변수 보호**: `.env` 파일을 `.gitignore`에 추가

## 추가 리소스

- [Docker 공식 문서](https://docs.docker.com/)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [MCP 프로토콜 가이드](https://github.com/modelcontextprotocol)
- [프로젝트 이슈 트래커](https://github.com/yourusername/smart-file-manager-mcp/issues)