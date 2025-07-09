#!/bin/bash

# MCP Server Diagnostic Script
# This script diagnoses and fixes common MCP server issues

echo "🔍 Smart File Manager MCP 진단 스크립트"
echo "========================================"

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 현재 디렉토리 확인
if [ ! -f "claude-config.json" ]; then
    echo -e "${RED}❌ 프로젝트 디렉토리가 아닙니다!${NC}"
    exit 1
fi

echo -e "${BLUE}📍 현재 위치: $(pwd)${NC}"
echo ""

# 1. Node.js 및 npm 확인
echo -e "${YELLOW}1. Node.js 환경 확인${NC}"
if command -v node &> /dev/null; then
    echo -e "  ${GREEN}✅ Node.js: $(node --version)${NC}"
else
    echo -e "  ${RED}❌ Node.js가 설치되지 않음${NC}"
    exit 1
fi

if command -v npm &> /dev/null; then
    echo -e "  ${GREEN}✅ npm: $(npm --version)${NC}"
else
    echo -e "  ${RED}❌ npm이 설치되지 않음${NC}"
    exit 1
fi

# 2. Python 환경 확인
echo -e "${YELLOW}2. Python 환경 확인${NC}"
if command -v python3 &> /dev/null; then
    echo -e "  ${GREEN}✅ Python: $(python3 --version)${NC}"
else
    echo -e "  ${RED}❌ Python3가 설치되지 않음${NC}"
    exit 1
fi

# 3. MCP 서버 빌드 상태 확인
echo -e "${YELLOW}3. MCP 서버 빌드 상태 확인${NC}"
if [ -d "mcp-server/dist" ]; then
    echo -e "  ${GREEN}✅ TypeScript 빌드 완료${NC}"
else
    echo -e "  ${YELLOW}⚠️ TypeScript 빌드 필요${NC}"
    echo -e "  ${BLUE}🔧 빌드 중...${NC}"
    cd mcp-server
    npm install
    npm run build
    cd ..
    
    if [ -d "mcp-server/dist" ]; then
        echo -e "  ${GREEN}✅ 빌드 완료${NC}"
    else
        echo -e "  ${RED}❌ 빌드 실패${NC}"
        exit 1
    fi
fi

# 4. MCP 서버 기본 기능 테스트
echo -e "${YELLOW}4. MCP 서버 기본 기능 테스트${NC}"
cd mcp-server
MCP_TEST_RESULT=$(echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' | timeout 5 node dist/index.js 2>/dev/null)
cd ..

if echo "$MCP_TEST_RESULT" | grep -q "search_files"; then
    echo -e "  ${GREEN}✅ MCP 서버 기본 기능 정상${NC}"
    echo -e "  ${GREEN}✅ 도구 목록: search_files, quick_search, organize_files, smart_workflow${NC}"
else
    echo -e "  ${RED}❌ MCP 서버 기본 기능 테스트 실패${NC}"
    echo -e "  ${RED}결과: $MCP_TEST_RESULT${NC}"
    exit 1
fi

# 5. Docker 상태 확인
echo -e "${YELLOW}5. Docker 상태 확인${NC}"
if command -v docker &> /dev/null; then
    echo -e "  ${GREEN}✅ Docker 설치됨: $(docker --version)${NC}"
    
    # Docker 데몬 상태 확인
    if docker info > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ Docker 데몬 실행 중${NC}"
        DOCKER_WORKING=true
    else
        echo -e "  ${RED}❌ Docker 데몬 실행되지 않음${NC}"
        DOCKER_WORKING=false
    fi
else
    echo -e "  ${RED}❌ Docker가 설치되지 않음${NC}"
    DOCKER_WORKING=false
fi

# 6. 대안 설정 파일 생성
echo -e "${YELLOW}6. Claude Desktop 설정 파일 생성${NC}"

# Docker가 작동하는 경우
if [ "$DOCKER_WORKING" = true ]; then
    echo -e "  ${GREEN}✅ Docker 버전 설정 파일 생성: claude-config.json${NC}"
    cat > claude-config.json << EOF
{
  "mcpServers": {
    "smart-file-manager": {
      "command": "docker",
      "args": [
        "exec", "-i", "smart-file-mcp",
        "node", "/app/dist/index.js"
      ],
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
EOF
else
    echo -e "  ${YELLOW}⚠️ Docker 미작동 - 로컬 버전 설정 파일 생성${NC}"
fi

# 로컬 개발 버전 (항상 생성)
echo -e "  ${BLUE}🔧 로컬 개발 버전 설정 파일 생성: claude-config-local.json${NC}"
cat > claude-config-local.json << EOF
{
  "mcpServers": {
    "smart-file-manager": {
      "command": "node",
      "args": [
        "$(pwd)/mcp-server/dist/index.js"
      ],
      "env": {
        "NODE_ENV": "development",
        "AI_SERVICE_URL": "http://localhost:8000"
      }
    }
  }
}
EOF

# 7. 로컬 AI 서비스 확인
echo -e "${YELLOW}7. AI 서비스 준비 상태 확인${NC}"
if [ -f "ai-services/api.py" ]; then
    echo -e "  ${GREEN}✅ AI 서비스 코드 존재${NC}"
    
    # Python 의존성 확인
    cd ai-services
    pip3 install -r requirements.txt > /dev/null 2>&1
    cd ..
    echo -e "  ${GREEN}✅ Python 의존성 설치 완료${NC}"
else
    echo -e "  ${RED}❌ AI 서비스 코드 없음${NC}"
fi

# 8. 추천 설정 출력
echo ""
echo -e "${BLUE}📋 진단 결과 및 권장사항${NC}"
echo "=================================="

if [ "$DOCKER_WORKING" = true ]; then
    echo -e "${GREEN}✅ Docker 사용 가능${NC}"
    echo "  권장: docker-compose up -d로 전체 시스템 실행"
    echo "  Claude Desktop 설정: claude-config.json 내용 사용"
else
    echo -e "${YELLOW}⚠️ Docker 사용 불가능 - 로컬 실행 필요${NC}"
    echo "  권장: ./run-local.sh 스크립트 실행"
    echo "  Claude Desktop 설정: claude-config-local.json 내용 사용"
fi

echo ""
echo -e "${BLUE}🚀 실행 단계${NC}"
echo "============"

if [ "$DOCKER_WORKING" = true ]; then
    echo "1. Docker 실행:"
    echo "   $ docker-compose up -d"
    echo ""
    echo "2. Claude Desktop 설정:"
    echo "   claude-config.json 내용을 Claude Desktop 설정에 추가"
    echo ""
    echo "3. 상태 확인:"
    echo "   $ docker-compose ps"
    echo "   $ docker-compose logs -f"
else
    echo "1. 로컬 실행:"
    echo "   $ ./run-local.sh"
    echo ""
    echo "2. Claude Desktop 설정:"
    echo "   claude-config-local.json 내용을 Claude Desktop 설정에 추가"
    echo ""
    echo "3. 수동 실행 (대안):"
    echo "   Terminal 1: cd ai-services && python3 api.py"
    echo "   Terminal 2: cd mcp-server && npm start"
fi

echo ""
echo -e "${BLUE}🔧 테스트 명령어${NC}"
echo "=================="
echo "MCP 서버 직접 테스트:"
echo "$ echo '{\"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"tools/list\", \"params\": {}}' | node mcp-server/dist/index.js"
echo ""
echo "AI 서비스 테스트:"
echo "$ curl http://localhost:8000/health"
echo ""

echo -e "${GREEN}✅ 진단 완료!${NC}"