# 🚀 Smart File Manager MCP - 빠른 시작 가이드

## ✅ 현재 상태: 준비 완료!

MCP 서버가 정상적으로 설정되었고 Claude Desktop과 연결되었습니다.

## 📋 실행 방법

### 1. AI 서비스 시작 (이미 실행 중)
```bash
cd /Users/hyoseop1231/AI_Coding/smart-file-manager-mcp
python3 ai-services/simple_api.py
```

### 2. Claude Desktop 재시작
Claude Desktop을 완전히 종료하고 다시 시작하세요.

## 🛠️ 사용 가능한 도구들

### 1. **search_files** - 파일 검색
```
"다운로드 폴더에서 이미지 파일 찾아줘"
"문서 폴더에서 프로젝트 관련 파일 검색해줘"
```

### 2. **quick_search** - 빠른 검색
```
"최근 24시간 동안 수정된 파일 보여줘"
"이미지 파일만 모두 찾아줘"
"PDF 문서들 찾아줘"
```

### 3. **organize_files** - 파일 정리
```
"다운로드 폴더를 카테고리별로 정리해줘"
"사진들을 날짜별로 분류해줘"
```

### 4. **smart_workflow** - 통합 워크플로우
```
"PDF 파일들을 찾아서 분석해줘"
"최근 프로젝트 파일들을 정리해줘"
```

## 🎯 테스트 명령어

Claude Desktop에서 다음 명령어들을 시도해보세요:

1. **파일 검색**:
   - "PDF 파일 찾아줘"
   - "이미지 파일 검색해줘"
   - "최근 일주일간 수정된 파일 보여줘"

2. **카테고리별 검색**:
   - "문서 파일만 보여줘"
   - "코드 파일들 찾아줘"
   - "동영상 파일 목록 알려줘"

3. **파일 정리**:
   - "다운로드 폴더 정리해줘"
   - "바탕화면 파일들 카테고리별로 분류해줘"

## 📊 지원하는 파일 카테고리

- **document**: PDF, Word, 텍스트 파일
- **image**: JPG, PNG, GIF, SVG 등
- **video**: MP4, AVI, MOV, MKV 등  
- **audio**: MP3, WAV, FLAC, AAC 등
- **code**: Python, JavaScript, Java, C++ 등
- **archive**: ZIP, RAR, TAR, 7Z 등
- **other**: 기타 파일들

## 🔧 문제 해결

### MCP 서버가 연결되지 않는 경우:
1. AI 서비스가 실행 중인지 확인: `curl http://localhost:8000/health`
2. Claude Desktop 완전 재시작
3. 터미널에서 MCP 서버 테스트:
   ```bash
   cd /Users/hyoseop1231/AI_Coding/smart-file-manager-mcp/mcp-server
   echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | node dist/index.js
   ```

### AI 서비스 재시작:
```bash
# 기존 프로세스 종료
pkill -f "simple_api.py"

# 다시 시작
cd /Users/hyoseop1231/AI_Coding/smart-file-manager-mcp
python3 ai-services/simple_api.py &
```

## 📈 성능 정보

- **검색 속도**: 즉시 반응 (실제 파일시스템 기반)
- **지원 디렉토리**: Documents, Downloads, Desktop
- **파일 제한**: 검색당 최대 50개 결과
- **카테고리 자동 분류**: 확장자 기반

## 🎉 준비 완료!

이제 Claude Desktop에서 파일 관리 명령어를 사용할 수 있습니다. 위의 테스트 명령어들로 시작해보세요!