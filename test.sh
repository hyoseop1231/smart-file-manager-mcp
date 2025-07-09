#!/bin/bash

# Smart File Manager MCP 테스트 스크립트

echo "🧪 Smart File Manager MCP 테스트 시작..."

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# API 서버 URL
API_URL="http://localhost:8000"

# 서비스가 준비될 때까지 대기
echo "⏳ 서비스가 준비될 때까지 대기 중..."
for i in {1..30}; do
    if curl -s "$API_URL/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 서비스가 준비되었습니다!${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

echo ""

# 1. Health Check
echo -e "${YELLOW}1. Health Check 테스트${NC}"
curl -s "$API_URL/health" | python -m json.tool

echo ""
echo ""

# 2. 파일 검색 테스트
echo -e "${YELLOW}2. 파일 검색 테스트${NC}"
curl -s -X POST "$API_URL/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "프로젝트 문서",
    "directories": ["'$HOME'/Documents"],
    "limit": 5
  }' | python -m json.tool

echo ""
echo ""

# 3. 파일 정리 테스트 (미리보기 모드)
echo -e "${YELLOW}3. 파일 정리 테스트 (미리보기)${NC}"
curl -s -X POST "$API_URL/organize" \
  -H "Content-Type: application/json" \
  -d '{
    "sourceDir": "'$HOME'/Downloads",
    "method": "type",
    "dryRun": true
  }' | python -m json.tool

echo ""
echo ""

# 4. 워크플로우 테스트
echo -e "${YELLOW}4. 스마트 워크플로우 테스트${NC}"
curl -s -X POST "$API_URL/workflow" \
  -H "Content-Type: application/json" \
  -d '{
    "searchQuery": "이미지 파일",
    "action": "analyze",
    "options": {
      "directories": ["'$HOME'/Pictures"],
      "limit": 10
    }
  }' | python -m json.tool

echo ""
echo -e "${GREEN}✅ 테스트 완료!${NC}"