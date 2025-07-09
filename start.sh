#!/bin/bash

# Smart File Manager MCP 통합 실행 스크립트

echo "🚀 Smart File Manager MCP 시작..."

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Ollama 확인
echo -e "${YELLOW}1. Ollama 상태 확인 중...${NC}"
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${RED}❌ Ollama가 실행되고 있지 않습니다!${NC}"
    echo "다음 명령어로 Ollama를 시작하세요:"
    echo "  ollama serve"
    exit 1
fi
echo -e "${GREEN}✅ Ollama가 실행 중입니다.${NC}"

# 2. 필요한 모델 확인 및 설치
echo ""
echo -e "${YELLOW}2. AI 모델 확인 및 설치 중...${NC}"

REQUIRED_MODELS=(
    "qwen3:30b-a3b"      # 텍스트 분석용
    "llava:13b"          # 이미지 분석용
    "nomic-embed-text"   # 임베딩용
)

INSTALLED_MODELS=$(curl -s http://localhost:11434/api/tags | python3 -c "
import json, sys
data = json.load(sys.stdin)
for model in data.get('models', []):
    print(model['name'])
")

for MODEL in "${REQUIRED_MODELS[@]}"; do
    if echo "$INSTALLED_MODELS" | grep -q "^$MODEL$"; then
        echo -e "  ${GREEN}✅${NC} $MODEL - 이미 설치됨"
    else
        echo -e "  ${YELLOW}📥${NC} $MODEL - 설치 중..."
        ollama pull $MODEL
        if [ $? -eq 0 ]; then
            echo -e "  ${GREEN}✅${NC} $MODEL - 설치 완료!"
        else
            echo -e "  ${RED}❌${NC} $MODEL - 설치 실패!"
            exit 1
        fi
    fi
done

# 3. Docker 서비스 시작
echo ""
echo -e "${YELLOW}3. Docker 서비스 시작 중...${NC}"
docker-compose down > /dev/null 2>&1  # 기존 컨테이너 정리
docker-compose up -d

# 4. 서비스 준비 대기
echo ""
echo -e "${YELLOW}4. 서비스가 준비될 때까지 대기 중...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8100/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ AI 서비스가 준비되었습니다!${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

# 5. 초기 인덱싱 상태 확인
echo ""
echo -e "${YELLOW}5. 파일 인덱싱 상태 확인 중...${NC}"
DB_STATS=$(curl -s http://localhost:8100/health | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    stats = data.get('db_stats', {})
    total = stats.get('total_files', 0)
    categories = stats.get('by_category', {})
    print(f'총 파일: {total:,}개')
    if categories:
        print('카테고리별:')
        for cat, info in categories.items():
            if isinstance(info, dict):
                count = info.get('count', 0)
                size = info.get('size_gb', 0)
                print(f'  - {cat}: {count:,}개 ({size:.1f}GB)')
            else:
                print(f'  - {cat}: {info}개')
except:
    print('인덱싱 진행 중...')
")
echo "$DB_STATS"

# 6. 상태 확인
echo ""
echo -e "${YELLOW}6. 서비스 상태 확인${NC}"
docker-compose ps

# 인덱서 로그 확인
echo ""
echo -e "${YELLOW}백그라운드 인덱싱 상태:${NC}"
docker logs smart-file-indexer --tail 5 2>/dev/null || echo "인덱서가 시작되지 않았습니다."

echo ""
echo -e "${GREEN}✅ Smart File Manager MCP가 실행 중입니다!${NC}"
echo ""
echo "📝 사용 방법:"
echo "1. Claude Desktop 설정에 claude-config.json 내용 추가"
echo "2. Claude와 대화하며 파일 검색 및 정리"
echo ""
echo "💬 예시 명령어:"
echo '  "다운로드 폴더에서 프로젝트 관련 파일 찾아줘"'
echo '  "최근 24시간 동안 수정된 파일 보여줘"'
echo '  "이미지 파일만 찾아줘"'
echo '  "사진들을 내용별로 정리해줘"'
echo '  "작년 문서들 날짜별로 분류해줘"'
echo ""
echo "🔍 빠른 검색 (인덱싱 DB 사용):"
echo '  - 카테고리별: image, video, audio, document, code, archive'
echo '  - 확장자별: .pdf, .docx, .jpg, .mp4 등'
echo '  - 최근 파일: 최근 N시간 내 수정된 파일'
echo ""
echo "⚡ 성능 정보:"
echo '  - 파일 인덱싱: 2시간마다 자동 업데이트'
echo '  - 빠른 검색: 인덱싱된 DB 우선 사용'
echo '  - AI 검색: DB에 없을 때 자동 전환'
echo ""
echo "🛑 종료하려면: docker-compose down"
echo "📊 로그 확인: docker-compose logs -f"
echo "📈 인덱서 로그: docker logs -f smart-file-indexer"