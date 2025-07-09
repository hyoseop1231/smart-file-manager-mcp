#!/bin/bash

# 로컬 개발 및 테스트를 위한 스크립트

echo "🚀 Smart File Manager MCP 로컬 실행..."

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. MCP 서버 빌드
echo -e "${YELLOW}1. MCP 서버 빌드 중...${NC}"
cd mcp-server
npm run build
cd ..

# 2. Python 환경 설정
echo -e "${YELLOW}2. Python 가상 환경 설정...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r ai-services/requirements.txt

# 3. AI 서비스 시작
echo -e "${YELLOW}3. AI 서비스 시작...${NC}"
cd ai-services
python api.py &
AI_PID=$!
cd ..

# 4. 잠시 대기
sleep 5

# 5. MCP 서버 시작
echo -e "${YELLOW}4. MCP 서버 시작...${NC}"
cd mcp-server
npm start &
MCP_PID=$!
cd ..

echo -e "${GREEN}✅ 서비스가 시작되었습니다!${NC}"
echo ""
echo "AI Service PID: $AI_PID"
echo "MCP Server PID: $MCP_PID"
echo ""
echo "종료하려면 Ctrl+C를 누르세요."

# 종료 신호 처리
trap "kill $AI_PID $MCP_PID; exit" INT

# 프로세스가 계속 실행되도록 대기
wait