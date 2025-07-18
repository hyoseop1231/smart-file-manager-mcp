# Smart File Manager MCP 트러블슈팅 가이드

## 목차
1. [일반적인 문제](#일반적인-문제)
2. [API 오류](#api-오류)
3. [Docker 관련](#docker-관련)
4. [데이터베이스 문제](#데이터베이스-문제)
5. [성능 문제](#성능-문제)
6. [AI 서비스 문제](#ai-서비스-문제)

## 일반적인 문제

### 🔴 서비스가 시작되지 않음

**증상:**
- `docker-compose up` 실행 시 오류 발생
- 컨테이너가 계속 재시작됨

**해결 방법:**
```bash
# 1. 기존 컨테이너 정리
docker-compose down -v

# 2. 오래된 이미지 제거
docker system prune -a

# 3. 재빌드 및 시작
docker-compose build --no-cache
docker-compose up -d

# 4. 로그 확인
docker-compose logs -f
```

### 🔴 포트 충돌

**증상:**
- `bind: address already in use` 오류

**해결 방법:**
```bash
# 사용 중인 포트 확인
sudo lsof -i :8001
sudo lsof -i :16379
sudo lsof -i :9090
sudo lsof -i :3003

# 프로세스 종료
sudo kill -9 <PID>

# 또는 docker-compose.yml에서 포트 변경
ports:
  - "8002:8001"  # 외부 포트를 8002로 변경
```

## API 오류

### 🟡 타입 비교 오류 (v4.0에서 수정됨)

**증상:**
```
TypeError: '>' not supported between instances of 'str' and 'int'
```

**해결 방법:**
```python
# 이미 수정된 코드 (multimedia_api_v4.py)
total = int(total) if total is not None else 0
analyzed = int(analyzed) if analyzed is not None else 0
```

### 🟡 JSON 파싱 오류 (v4.0에서 수정됨)

**증상:**
```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**해결 방법:**
1. 최신 버전 확인
2. API 재시작
```bash
docker exec smart-file-manager-multimedia-v4 pkill -f multimedia_api_v4.py
# 자동으로 재시작됨
```

### 🟡 검색 결과 없음

**증상:**
- 검색 시 빈 결과 반환
- 파일이 있는데도 찾지 못함

**해결 방법:**
```bash
# 1. 인덱싱 상태 확인
curl http://localhost:8001/stats/multimedia | jq

# 2. 수동 재인덱싱
docker exec smart-file-manager-multimedia-v4 python -c "
from enhanced_indexer_v4 import EnhancedFileIndexer
indexer = EnhancedFileIndexer('/data/db/file-index.db')
stats = indexer.get_stats()
print(f'Indexed files: {stats.get(\"total_files\", 0)}')
"

# 3. 특정 디렉토리 재인덱싱
docker exec smart-file-manager-multimedia-v4 python -c "
from enhanced_indexer_v4 import EnhancedFileIndexer
indexer = EnhancedFileIndexer('/data/db/file-index.db')
indexer.index_directory('/watch_directories/Desktop')
"
```

## Docker 관련

### 🔴 컨테이너 메모리 부족

**증상:**
- `Container killed due to memory limit` 오류
- 시스템이 느려짐

**해결 방법:**
1. Docker Desktop 메모리 할당 증가
   - Settings → Resources → Memory: 6GB 이상

2. docker-compose.yml에서 메모리 제한 설정
```yaml
services:
  smart-file-manager-multimedia-v4:
    mem_limit: 4g
    memswap_limit: 4g
```

### 🔴 볼륨 마운트 실패

**증상:**
- `no such file or directory` 오류
- 파일을 찾을 수 없음

**해결 방법:**
```bash
# 1. 절대 경로 사용
volumes:
  - /Users/username/Documents:/watch_directories/Documents:ro

# 2. 디렉토리 생성
mkdir -p ~/Documents
mkdir -p data/db data/embeddings data/metadata

# 3. 권한 확인
ls -la data/
chmod -R 755 data/
```

## 데이터베이스 문제

### 🟡 데이터베이스 잠김

**증상:**
- `database is locked` 오류
- 쓰기 작업 실패

**해결 방법:**
```bash
# 1. 연결 확인
docker exec smart-file-manager-multimedia-v4 python -c "
import sqlite3
conn = sqlite3.connect('/data/db/file-index.db')
conn.execute('PRAGMA journal_mode=WAL')
conn.close()
"

# 2. 데이터베이스 정리
docker exec smart-file-manager-multimedia-v4 python -c "
import sqlite3
conn = sqlite3.connect('/data/db/file-index.db')
conn.execute('VACUUM')
conn.execute('ANALYZE')
conn.close()
"
```

### 🟡 FTS 검색 오류

**증상:**
- FTS 테이블 관련 오류
- 전문 검색 실패

**해결 방법:**
```bash
# FTS 테이블 재구성
docker exec smart-file-manager-multimedia-v4 python -c "
import sqlite3
conn = sqlite3.connect('/data/db/file-index.db')
cursor = conn.cursor()

# FTS 테이블 재생성
cursor.execute('DROP TABLE IF EXISTS files_fts')
cursor.execute('''
CREATE VIRTUAL TABLE files_fts USING fts5(
    name, path, text_content, multimedia_content, ai_analysis,
    content=files, content_rowid=id
)
''')

# 트리거 재생성
cursor.execute('''
CREATE TRIGGER files_ai AFTER INSERT ON files BEGIN
    INSERT INTO files_fts(rowid, name, path, text_content, multimedia_content, ai_analysis)
    VALUES (new.id, new.name, new.path, new.text_content, new.multimedia_content, new.ai_analysis);
END
''')

conn.commit()
conn.close()
print('FTS tables recreated successfully')
"
```

## 성능 문제

### 🟠 느린 인덱싱

**증상:**
- 파일 인덱싱이 매우 느림
- CPU 사용률 높음

**해결 방법:**
```bash
# 1. 배치 크기 조정 (.env)
INDEX_BATCH_SIZE=50  # 기본값 100에서 감소

# 2. 워커 수 조정
MAX_WORKERS=2  # CPU 코어 수에 맞춰 조정

# 3. 특정 확장자 제외
EXCLUDE_EXTENSIONS=.log,.tmp,.cache

# 4. 컨테이너 재시작
docker-compose restart smart-file-manager-multimedia-v4
```

### 🟠 API 응답 지연

**증상:**
- API 응답 시간 > 1초
- 타임아웃 발생

**해결 방법:**
```bash
# 1. Redis 캐시 상태 확인
docker exec smart-file-redis-v4 redis-cli ping

# 2. 캐시 비우기
docker exec smart-file-redis-v4 redis-cli FLUSHALL

# 3. 연결 풀 크기 조정
docker exec smart-file-manager-multimedia-v4 python -c "
# db_connection_pool.py의 max_connections 조정
"

# 4. 인덱스 최적화
docker exec smart-file-manager-multimedia-v4 python -c "
import sqlite3
conn = sqlite3.connect('/data/db/file-index.db')
conn.execute('CREATE INDEX IF NOT EXISTS idx_files_media_type ON files(media_type)')
conn.execute('CREATE INDEX IF NOT EXISTS idx_files_category ON files(category)')
conn.execute('CREATE INDEX IF NOT EXISTS idx_files_modified ON files(modified_time)')
conn.close()
"
```

## AI 서비스 문제

### 🔴 OpenAI API 오류

**증상:**
- `Invalid API key` 오류
- Rate limit 초과

**해결 방법:**
```bash
# 1. API 키 확인
cat .env | grep OPENAI_API_KEY

# 2. 환경 변수 재설정
docker-compose down
# .env 파일 수정
docker-compose up -d

# 3. Rate limit 대응
# ai_vision_service.py에서 재시도 로직 확인
```

### 🔴 AI 분석 실패

**증상:**
- 이미지/음성 분석 오류
- 메모리 부족

**해결 방법:**
```bash
# 1. 개별 파일 테스트
curl -X POST http://localhost:8001/ai/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/watch_directories/test.jpg",
    "analysis_type": "image"
  }'

# 2. 로그 확인
docker logs smart-file-manager-multimedia-v4 | grep -i error

# 3. AI 서비스 비활성화 (임시)
# .env 파일에서
ENABLE_AI_VISION=false
ENABLE_STT=false
```

## 진단 도구

### 시스템 상태 종합 점검

```bash
# check_system.sh 스크립트 생성
cat > check_system.sh << 'EOF'
#!/bin/bash
echo "=== Smart File Manager System Check ==="
echo ""

echo "1. Docker 상태:"
docker-compose ps
echo ""

echo "2. API 헬스 체크:"
curl -s http://localhost:8001/health | jq '.status'
echo ""

echo "3. 데이터베이스 파일 수:"
curl -s http://localhost:8001/stats/multimedia | jq '.indexer_statistics.total_files'
echo ""

echo "4. Redis 상태:"
docker exec smart-file-redis-v4 redis-cli ping
echo ""

echo "5. 최근 로그 (에러만):"
docker-compose logs --tail=20 | grep -i error
echo ""

echo "6. 디스크 사용량:"
df -h | grep -E "(Filesystem|docker|/data)"
echo ""

echo "7. 메모리 사용량:"
docker stats --no-stream
EOF

chmod +x check_system.sh
./check_system.sh
```

### 로그 수집

```bash
# 전체 로그 수집
docker-compose logs > smart-file-manager-logs-$(date +%Y%m%d-%H%M%S).log

# 특정 서비스 로그
docker logs smart-file-manager-multimedia-v4 > api-logs.log
docker logs smart-file-redis-v4 > redis-logs.log
```

## 복구 절차

### 전체 시스템 초기화

⚠️ **경고: 모든 데이터가 삭제됩니다!**

```bash
# 1. 백업 (중요!)
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# 2. 완전 초기화
docker-compose down -v
rm -rf data/
docker system prune -a --volumes

# 3. 재설치
mkdir -p data/{db,embeddings,metadata,thumbnails,video_thumbnails}
docker-compose build --no-cache
docker-compose up -d
```

## 지원 받기

문제가 해결되지 않으면:

1. **로그 수집**: 위의 진단 도구로 로그 수집
2. **이슈 생성**: [GitHub Issues](https://github.com/yourusername/smart-file-manager-mcp/issues)
3. **정보 포함**:
   - 오류 메시지 전문
   - 재현 단계
   - 시스템 정보 (OS, Docker 버전)
   - 관련 로그

## 자주 묻는 질문 (FAQ)

**Q: 파일이 인덱싱되지 않아요**
A: 파일 경로가 올바르게 마운트되었는지 확인하고, 파일 권한을 체크하세요.

**Q: 검색이 너무 느려요**
A: 데이터베이스 최적화를 실행하고, 인덱스를 재구성하세요.

**Q: AI 분석이 작동하지 않아요**
A: OpenAI API 키가 올바른지 확인하고, 할당량을 체크하세요.