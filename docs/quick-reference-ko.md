# Smart File Manager MCP - 빠른 참조 가이드

## 🚀 빠른 시작

```bash
# 모든 서비스 시작
docker-compose up -d

# 웹 UI 접속
http://localhost:3002

# 상태 확인
curl http://localhost:8001/health
```

## 🔍 MCP 기능 (클로드 데스크탑)

### search_files (파일 검색)
```
"머신러닝 관련 Python 파일 찾아줘"
"최근 일주일간 수정된 문서 찾아줘"
"프로젝트 관련 PDF 파일 모두 보여줘"
```

### quick_search (빠른 검색)
```
"최근 24시간 내 PDF 파일 보여줘"
"이미지 파일만 보여줘"
"5MB 이상 큰 파일들 찾아줘"
```

### organize_files (파일 정리)
```
"다운로드 폴더 정리해줘"
"바탕화면 파일들 정리해줘"
"문서 폴더를 프로젝트별로 분류해줘"
```

### smart_workflow (스마트 워크플로우)
```
"프로젝트 파일 찾아서 정리해줘"
"중복 파일 찾아서 정리해줘"
"오래된 파일들 찾아서 백업 폴더로 이동해줘"
```

### analyze_file (파일 분석)
```
"이 문서가 어떤 내용인지 분석해줘"
"/path/to/document.pdf 파일 분석해줘"
"이 코드 파일의 기능을 설명해줘"
```

### system_status (시스템 상태)
```
"시스템 상태 확인"
"파일 관리자 성능 보여줘"
"인덱싱 상태 확인해줘"
```

### find_duplicates (중복 파일 찾기)
```
"중복 파일 찾아줘"
"1MB 이상 중복 파일 찾아줘"
"같은 내용의 파일들 찾아줘"
```

### batch_operation (일괄 작업)
```
"선택한 파일들 Documents 폴더로 이동"
"PDF 파일들을 모두 문서 폴더로 정리"
"이미지 파일들에 태그 추가"
```

## 🌐 웹 UI 기능

### 대시보드 (http://localhost:3002)
- 시스템 메트릭 (CPU, 메모리, 디스크)
- 최근 파일 활동
- 빠른 통계
- 서비스 상태

### 파일 탐색기
- 자연어 검색
- 고급 필터
- 일괄 작업
- 파일 미리보기

### 분석
- 중복 파일 탐지
- 저장소 인사이트
- 사용 패턴
- 성능 추세

### 파일 정리
- AI 기반 제안
- 시험 실행 모드
- 진행 상황 추적
- 실행 취소 지원

## 📡 API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|----------|--------|------|
| `/health` | GET | 시스템 상태 |
| `/search` | POST | 파일 검색 |
| `/organize` | POST | 파일 정리 |
| `/duplicates` | POST | 중복 파일 찾기 |
| `/analyze` | POST | 파일 분석 |
| `/recent` | GET | 최근 파일 |
| `/metrics` | GET | 시스템 메트릭 |
| `/task/{id}` | GET | 작업 상태 |

## 🛠️ 일반적인 명령어

### Docker 관리
```bash
# 로그 보기
docker-compose logs -f

# 서비스 재시작
docker-compose restart

# 전체 중지
docker-compose down

# 업데이트 및 재시작
docker-compose pull
docker-compose up -d
```

### 문제 해결
```bash
# 포트 확인
lsof -i :8001  # API
lsof -i :3002  # 웹 UI

# MCP 서버 테스트
node mcp-server/dist/index.js

# 데이터베이스 통계
docker exec smart-file-manager sqlite3 /data/db/file-index.db "SELECT COUNT(*) FROM files;"
```

## ⚙️ 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `PORT` | 8001 | API 포트 |
| `OLLAMA_API_URL` | http://host.docker.internal:11434 | Ollama 엔드포인트 |
| `FULL_INDEX_INTERVAL` | 7200 | 전체 스캔 간격 (초) |
| `QUICK_INDEX_INTERVAL` | 1800 | 빠른 스캔 간격 (초) |

## 🎯 성능 팁

1. **검색 최적화**
   - 구체적인 용어 사용
   - 디렉토리로 검색 범위 제한
   - LLM 사용으로 더 나은 결과

2. **정리 모범 사례**
   - 항상 시험 실행 먼저 사용
   - 작은 디렉토리부터 시작
   - AI 제안 검토

3. **시스템 리소스**
   - Docker에 4GB+ RAM 할당
   - 데이터베이스용 SSD 스토리지 사용
   - 사용량이 적은 시간에 인덱싱 스케줄

## 🌐 언어 지원

### 한국어 (기본)
- 모든 UI가 한국어로 표시
- 한국어 자연어 명령 지원
- 날짜/시간 형식 한국어

### 영어 전환
- 웹 UI 헤더의 국기 아이콘 클릭
- 즉시 언어 변경
- 설정 자동 저장

## 🔗 유용한 링크

- **GitHub**: https://github.com/hyoseop1231/smart-file-manager-mcp
- **이슈 신고**: https://github.com/hyoseop1231/smart-file-manager-mcp/issues
- **문서**: https://github.com/hyoseop1231/smart-file-manager-mcp/wiki

## 📞 지원 채널

- **버그 신고**: GitHub Issues
- **기능 요청**: GitHub Discussions
- **보안 문제**: security@example.com

## 💡 사용 예시

### 일반적인 워크플로우
```bash
# 1. 파일 검색
"프로젝트 X 관련 문서 모두 찾아줘"

# 2. 중복 제거
"중복 파일 찾아서 정리 방법 제안해줘"

# 3. 파일 정리
"다운로드 폴더를 내용별로 정리해줘"

# 4. 상태 확인
"시스템 상태와 저장 공간 확인해줘"
```

### 개발자 워크플로우
```bash
# 코드 파일 관리
"JavaScript 파일들을 프로젝트별로 정리해줘"
"최근 수정된 Python 코드 보여줘"
"테스트 파일들만 따로 정리해줘"
```

### 일반 사용자 워크플로우
```bash
# 문서 관리
"Word 문서들을 날짜별로 정리해줘"
"PDF 파일 중 중복된 것 찾아줘"
"사진들을 연도별로 분류해줘"
```

---

**버전**: 2.3.0 | **업데이트**: 2025-01-09 | **언어 지원**: 한국어 (기본), English