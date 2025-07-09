#!/bin/bash

# Smart File Manager MCP 빌드 스크립트

echo "🚀 Smart File Manager MCP 빌드 시작..."

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Docker 확인
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker가 설치되어 있지 않습니다.${NC}"
    exit 1
fi

# 2. Docker Compose 확인
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose가 설치되어 있지 않습니다.${NC}"
    exit 1
fi

# 3. npm 의존성 설치 (로컬 개발용)
echo "📦 MCP 서버 의존성 설치..."
cd mcp-server
npm install
cd ..

# 4. Docker 이미지 빌드
echo "🔨 Docker 이미지 빌드 중..."
docker-compose build

# 5. 성공 메시지
echo -e "${GREEN}✅ 빌드 완료!${NC}"
echo ""
echo "다음 명령어로 서비스를 시작하세요:"
echo "  docker-compose up -d"
echo ""
echo "서비스 상태 확인:"
echo "  docker-compose ps"
echo ""
echo "로그 확인:"
echo "  docker-compose logs -f"