# Smart File Manager MCP API 가이드

## 올바른 API 사용법

### 1. Organize Files (파일 정리)

**엔드포인트:** `POST /organize` (NOT `/api/organize`)

**요청 형식:**
```json
{
  "sourceDir": "/watch_directories/Desktop",
  "targetDir": "/watch_directories/Desktop/Organized",  // Optional
  "method": "content",  // "content", "date", or "type"
  "dryRun": true,       // true for preview, false for actual organization
  "use_llm": true       // Automatically set based on method
}
```

**curl 예시:**
```bash
curl -X POST http://localhost:8001/organize \
  -H "Content-Type: application/json" \
  -d '{
    "sourceDir": "/watch_directories/Desktop",
    "dryRun": true,
    "method": "content"
  }'
```

### 2. Search Files (파일 검색)

**엔드포인트:** `POST /search`

**요청 형식:**
```json
{
  "query": "프로젝트 문서",
  "path": "/watch_directories",  // Optional
  "filters": {
    "extensions": [".pdf", ".docx"],
    "size_range": {"min": 0, "max": 10485760}
  }
}
```

### 3. 작업 상태 확인

**엔드포인트:** `GET /task/{task_id}`

**예시:**
```bash
curl http://localhost:8001/task/organize_1234567890
```

## MCP 툴 사용 시 주의사항

1. **경로는 항상 `/watch_directories/`로 시작**
   - ❌ 잘못됨: `/Users/username/Desktop`
   - ✅ 올바름: `/watch_directories/Desktop`

2. **메소드는 반드시 POST 사용**
   - ❌ 잘못됨: `GET /organize?path=...`
   - ✅ 올바름: `POST /organize` with JSON body

3. **Content-Type 헤더 필수**
   - 항상 `Content-Type: application/json` 포함

## 디버깅 체크리스트

1. **Docker 컨테이너 실행 확인:**
   ```bash
   docker ps | grep smart-file-manager
   ```

2. **API 상태 확인:**
   ```bash
   curl http://localhost:8001/health
   ```

3. **로그 확인:**
   ```bash
   docker logs smart-file-manager --tail 50
   ```

4. **MCP 서버 로그:**
   ```bash
   docker logs smart-file-mcp-server --tail 50
   ```

## 자동화 스크립트

편의를 위한 스크립트들:
- `~/Desktop/자동화_스크립트/smart_file_organize.sh` - 파일 정리
- `~/Desktop/자동화_스크립트/diagnose_smart_file_mcp.sh` - 진단 도구
EOF < /dev/null