# 클로드 데스크탑 설정 가이드

이 가이드는 클로드 데스크탑에서 Smart File Manager MCP 서버를 사용하도록 설정하는 방법을 설명합니다.

## 설정 파일 위치

### macOS
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Windows
```
%APPDATA%\Claude\claude_desktop_config.json
```

### Linux
```
~/.config/claude/claude_desktop_config.json
```

## 기본 설정

`claude_desktop_config.json` 파일에 다음 내용을 추가하세요:

```json
{
  "mcpServers": {
    "smart-file-manager": {
      "command": "node",
      "args": [
        "/path/to/smart-file-manager-mcp/mcp-server/dist/index.js"
      ],
      "env": {
        "AI_SERVICE_URL": "http://localhost:8001",
        "DEFAULT_FILE_MANAGER": "true"
      },
      "priority": 1,
      "autoApprove": [
        "search_files",
        "quick_search",
        "organize_files",
        "smart_workflow",
        "analyze_file",
        "system_status",
        "find_duplicates",
        "batch_operation"
      ],
      "description": "AI 기반 파일 관리 시스템 - 한국어 지원"
    }
  }
}
```

## Docker 기반 설정

MCP 서버를 Docker에서 실행하는 경우:

```json
{
  "mcpServers": {
    "smart-file-manager": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "smart-file-mcp-server",
        "node",
        "/app/dist/index.js"
      ],
      "env": {
        "AI_SERVICE_URL": "http://localhost:8001"
      },
      "priority": 1,
      "autoApprove": [
        "search_files",
        "quick_search",
        "organize_files",
        "smart_workflow",
        "analyze_file",
        "system_status",
        "find_duplicates",
        "batch_operation"
      ],
      "description": "AI 기반 파일 관리 시스템 - 한국어 지원"
    }
  }
}
```

## 고급 설정 옵션

### 사용자 지정 API URL

API 서비스가 다른 포트나 호스트에서 실행되는 경우:

```json
"env": {
  "AI_SERVICE_URL": "http://192.168.1.100:8001"
}
```

### 제한된 권한

더 제한적인 권한을 위해 `autoApprove` 배열을 수정:

```json
"autoApprove": [
  "search_files",
  "quick_search",
  "system_status"
]
```

### 여러 파일 관리자

여러 파일 관리 서버를 사용할 수 있습니다:

```json
{
  "mcpServers": {
    "smart-file-manager": {
      // 메인 설정
    },
    "backup-file-manager": {
      "command": "node",
      "args": ["/path/to/backup-server/index.js"],
      "priority": 2
    }
  }
}
```

## 문제 해결

### 서버 연결 안됨

1. **경로 확인**: `index.js` 파일 경로가 올바른지 확인
   ```bash
   ls -la /path/to/smart-file-manager-mcp/mcp-server/dist/index.js
   ```

2. **서버 직접 테스트**:
   ```bash
   node /path/to/smart-file-manager-mcp/mcp-server/dist/index.js
   ```

3. **Docker 컨테이너 확인** (Docker 사용 시):
   ```bash
   docker ps | grep smart-file-mcp-server
   docker logs smart-file-mcp-server
   ```

### 권한 오류

파일에 대한 읽기 권한이 있는지 확인:

```bash
# 파일 권한 확인
ls -la ~/Documents
ls -la ~/Downloads

# Docker의 경우 docker-compose.yml에서 볼륨 마운트 확인
```

### API 연결 문제

1. **API 실행 확인**:
   ```bash
   curl http://localhost:8001/health
   ```

2. **방화벽 설정**: 포트 8001이 차단되지 않았는지 확인

3. **클로드 데스크탑에서 테스트**: 간단한 명령 시도:
   ```
   "파일 검색 테스트"
   ```

## 모범 사례

1. **보안**: 신뢰할 수 있는 기능에만 `autoApprove` 권한 부여
2. **성능**: 여러 서버에 적절한 `priority` 레벨 설정
3. **로깅**: 문제 해결을 위한 디버그 로깅 활성화:
   ```json
   "env": {
     "DEBUG": "true"
   }
   ```

4. **업데이트**: 설정 변경 후 클로드 데스크탑 재시작

## 클로드에서 사용할 수 있는 명령어

설정이 완료되면 다음과 같은 자연어 명령을 사용할 수 있습니다:

### 한국어 명령
- "PDF 파일 찾아줘"
- "오늘 수정된 문서 보여줘"
- "다운로드 폴더 정리해줘"
- "시스템 상태 확인"
- "중복 파일 찾아줘"
- "프로젝트 관련 파일 모두 찾아줘"
- "사진 파일 날짜별로 정리해줘"

### English Commands
- "Search for PDF files"
- "Find documents modified today"
- "Organize my Downloads folder"
- "Show system status"
- "Find duplicate files"

## 환경 변수

사용 가능한 모든 환경 변수:

| 변수 | 기본값 | 설명 |
|------|--------|------|
| AI_SERVICE_URL | http://localhost:8001 | API 서비스 엔드포인트 |
| DEFAULT_FILE_MANAGER | false | 기본 파일 관리자로 설정 |
| DEBUG | false | 디버그 로깅 활성화 |
| CACHE_TTL | 3600 | 캐시 타임아웃 (초) |
| MAX_RESULTS | 100 | 최대 검색 결과 수 |

## 버전 호환성

| Smart File Manager | Claude Desktop | 상태 |
|--------------------|----------------|------|
| 2.3.0+ | 1.0+ | ✅ 완전 호환 (한국어 지원) |
| 2.0.0 - 2.2.x | 1.0+ | ✅ 호환 |
| 1.x | 0.9+ | ⚠️ 제한된 기능 |

## 웹 UI 접속

설정 완료 후 웹 UI도 함께 사용할 수 있습니다:

- **개발 모드**: `./start-webui.sh` 실행 후 http://localhost:3002
- **운영 모드**: `docker-compose up -d` 후 http://localhost:3002
- **언어**: 기본 한국어, 헤더의 국기 아이콘으로 영어 전환 가능

---

더 많은 도움이 필요하시면: https://github.com/hyoseop1231/smart-file-manager-mcp