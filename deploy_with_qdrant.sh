#!/bin/bash

# Smart File Manager with Qdrant Vector DB Deployment Script
set -e

echo "🚀 Smart File Manager - Qdrant Vector DB 업그레이드"
echo "=================================================="

# 1. 현재 상태 확인
echo -e "\n1️⃣ 현재 상태 확인..."
docker ps | grep -E "smart-file|qdrant" || true

# 2. 기존 컨테이너 정지
echo -e "\n2️⃣ 기존 컨테이너 정지..."
docker compose down

# 3. 이미지 재빌드
echo -e "\n3️⃣ Docker 이미지 재빌드..."
docker compose build --no-cache smart-file-manager

# 4. 새로운 구성으로 시작
echo -e "\n4️⃣ 새로운 구성으로 시작..."
docker compose up -d

# 5. 상태 확인
echo -e "\n5️⃣ 서비스 상태 확인..."
sleep 10  # 서비스 시작 대기

# Health check
echo -e "\n📊 Health Check:"
curl -s http://localhost:8001/health | jq . || echo "API 서버 시작 중..."

# Qdrant 상태
echo -e "\n🔮 Qdrant 상태:"
curl -s http://localhost:6333/ | jq . || echo "Qdrant 시작 중..."

# Vector API 상태
echo -e "\n🚀 Vector API 상태:"
curl -s http://localhost:8001/vector/health | jq . || echo "Vector API 시작 중..."

# 6. 로그 확인
echo -e "\n6️⃣ 서비스 로그 (최근 20줄):"
docker compose logs --tail 20

echo -e "\n✅ 배포 완료!"
echo "=================================================="
echo "🌐 API Server: http://localhost:8001"
echo "🔮 Qdrant UI: http://localhost:6333/dashboard"
echo "📚 API Docs: http://localhost:8001/docs"
echo ""
echo "다음 단계:"
echo "1. 벡터 DB 상태 확인: curl http://localhost:8001/vector/stats | jq"
echo "2. 기존 임베딩 마이그레이션: curl -X POST http://localhost:8001/vector/migrate -H 'Content-Type: application/json' -d '{\"confirm\": true}'"
echo "3. 벡터 검색 테스트: curl -X POST http://localhost:8001/vector/search -H 'Content-Type: application/json' -d '{\"query\": \"파이썬 프로젝트\"}' | jq"