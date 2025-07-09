#!/bin/bash

# Ollama 모델 확인 스크립트 (다운로드 없음)

echo "🔍 Ollama 상태 확인 중..."

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Ollama 실행 확인
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${RED}❌ Ollama가 실행되고 있지 않습니다!${NC}"
    echo "다음 명령어로 Ollama를 시작하세요:"
    echo "  ollama serve"
    exit 1
fi

echo -e "${GREEN}✅ Ollama가 실행 중입니다.${NC}"

# 필요한 모델 목록
REQUIRED_MODELS=(
    "qwen3:30b-a3b"      # 텍스트 분석용 (qwen2.5 대체)
    "llava:13b"          # 이미지 분석용
    "nomic-embed-text"   # 임베딩용
)

# 현재 설치된 모델 확인
INSTALLED_MODELS=$(curl -s http://localhost:11434/api/tags | python3 -c "
import json, sys
data = json.load(sys.stdin)
for model in data.get('models', []):
    print(model['name'])
")

echo ""
echo "📦 필요한 모델 확인 중..."

# 설치되지 않은 모델 목록
MISSING_MODELS=()

# 각 모델 확인
for MODEL in "${REQUIRED_MODELS[@]}"; do
    if echo "$INSTALLED_MODELS" | grep -q "^$MODEL$"; then
        echo -e "  ${GREEN}✅${NC} $MODEL - 설치됨"
    else
        echo -e "  ${RED}❌${NC} $MODEL - 설치 필요"
        MISSING_MODELS+=("$MODEL")
    fi
done

echo ""

# 설치되지 않은 모델이 있는 경우
if [ ${#MISSING_MODELS[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  다음 모델들을 설치해주세요:${NC}"
    echo ""
    for MODEL in "${MISSING_MODELS[@]}"; do
        echo "  ollama pull $MODEL"
    done
    echo ""
    echo -e "${YELLOW}모든 모델을 설치한 후 다시 실행해주세요.${NC}"
    exit 1
else
    echo -e "${GREEN}✅ 모든 모델이 준비되었습니다!${NC}"
fi

# 모델 정보 표시
echo ""
echo "📊 필요한 모델 정보:"
echo "  - qwen3:30b-a3b: 한글 지원 텍스트 분석 및 분류 (기존 설치된 모델)"
echo "  - llava:13b: 이미지 내용 분석 전용 비전 모델"
echo "  - nomic-embed-text: 의미 기반 검색을 위한 임베딩 모델"