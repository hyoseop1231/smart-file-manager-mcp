"""
Adaptive Thinking Algorithm for Smart File Manager
자동 사고 모드 선택 시스템
"""

import re
import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ThinkingMode(Enum):
    """사고 모드 열거형"""
    THINK_HARD = "think_hard"
    MEGATHINK = "megathink"
    ULTRATHINK = "ultrathink"

@dataclass
class ThinkingAnalysis:
    """사고 분석 결과"""
    mode: ThinkingMode
    complexity_score: float
    detected_keywords: List[str]
    estimated_tools: List[str]
    reasoning: str

class AdaptiveThinkingEngine:
    """적응형 사고 엔진"""
    
    def __init__(self):
        # 키워드 사전 정의
        self.megathink_keywords = {
            "설계": 3, "아키텍처": 3, "시스템": 2, "복잡한": 2, 
            "통합": 2, "프로젝트": 2, "분석하고": 3, "설계하고": 3,
            "구현하고": 2, "개발하고": 2, "창작": 2, "창의적": 2,
            "비교": 2, "여러": 1, "다양한": 1, "종합": 2
        }
        
        self.ultrathink_keywords = {
            "완전자동화": 5, "완전 자동화": 5, "풀스택": 4, "full-stack": 4,
            "처음부터끝까지": 4, "처음부터 끝까지": 4, "배포까지": 4, "완벽한": 3,
            "최적화": 3, "성능": 2, "확장성": 3, "CI/CD": 4, "DevOps": 4,
            "파이프라인": 3, "인프라": 3, "마이크로서비스": 4, "쿠버네티스": 3,
            "도커": 2, "클라우드": 2, "엔터프라이즈": 3, "프로덕션": 3
        }
        
        # MCP 도구별 복잡도 가중치
        self.mcp_tool_weights = {
            "sequential-thinking": 1,
            "excel": 1, "mermaid": 1, "omnisearch": 1, "youtube": 1,
            "context7": 2, "python-executor": 2, "deep-research": 2,
            "taskmaster-ai": 2, "obsidian": 1, "memory": 1,
            "docker-manager": 3, "k8s-manager": 3, "aws-cli": 3,
            "ssh-control": 2, "git-advanced": 2, "database": 2,
            "playwright": 2, "web-scraper": 2, "slack": 1
        }
        
        # 멀티스텝 패턴
        self.multistep_patterns = [
            r"(\w+)하고\s+(\w+)해", r"(\w+)해서\s+(\w+)해", 
            r"(\w+)한\s+다음\s+(\w+)해", r"(\w+)\s+그리고\s+(\w+)",
            r"(\w+)\s+and\s+(\w+)", r"(\w+),\s+(\w+)",
            r"first\s+(\w+)\s+then\s+(\w+)", r"(\w+)\s+그다음\s+(\w+)"
        ]

    def analyze_request(self, user_request: str) -> ThinkingAnalysis:
        """사용자 요청 분석하여 적절한 사고 모드 결정"""
        try:
            # 1. 키워드 분석
            keyword_score, detected_keywords = self._analyze_keywords(user_request)
            
            # 2. MCP 도구 필요성 추정
            estimated_tools = self._estimate_required_tools(user_request)
            tool_score = self._calculate_tool_complexity_score(estimated_tools)
            
            # 3. 멀티스텝 작업 감지
            multistep_score = self._detect_multistep_complexity(user_request)
            
            # 4. 전체 복잡도 계산
            complexity_score = self._calculate_total_complexity(
                keyword_score, tool_score, multistep_score, len(estimated_tools)
            )
            
            # 5. 사고 모드 결정
            thinking_mode = self._select_thinking_mode(complexity_score)
            
            # 6. 추론 설명 생성
            reasoning = self._generate_reasoning(
                thinking_mode, complexity_score, detected_keywords, 
                estimated_tools, multistep_score
            )
            
            return ThinkingAnalysis(
                mode=thinking_mode,
                complexity_score=complexity_score,
                detected_keywords=detected_keywords,
                estimated_tools=estimated_tools,
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"Error analyzing request: {e}")
            # 기본값으로 THINK_HARD 반환
            return ThinkingAnalysis(
                mode=ThinkingMode.THINK_HARD,
                complexity_score=1.0,
                detected_keywords=[],
                estimated_tools=[],
                reasoning="Error in analysis, defaulting to basic mode"
            )

    def _analyze_keywords(self, request: str) -> Tuple[float, List[str]]:
        """키워드 분석으로 복잡도 점수 계산"""
        request_lower = request.lower()
        detected_keywords = []
        score = 0
        
        # ULTRATHINK 키워드 체크
        for keyword, weight in self.ultrathink_keywords.items():
            if keyword in request_lower:
                detected_keywords.append(f"ultra:{keyword}")
                score += weight
        
        # MEGATHINK 키워드 체크
        for keyword, weight in self.megathink_keywords.items():
            if keyword in request_lower:
                detected_keywords.append(f"mega:{keyword}")
                score += weight * 0.7  # ULTRATHINK보다 낮은 가중치
        
        return score, detected_keywords

    def _estimate_required_tools(self, request: str) -> List[str]:
        """요청에서 필요한 MCP 도구들 추정"""
        request_lower = request.lower()
        estimated_tools = []
        
        # 기본적으로 sequential-thinking은 항상 사용
        estimated_tools.append("sequential-thinking")
        
        # 도구별 키워드 매핑
        tool_patterns = {
            "excel": ["엑셀", "스프레드시트", "excel", "spreadsheet", "데이터 분석", "차트", "데이터"],
            "mermaid": ["다이어그램", "플로우차트", "flowchart", "diagram", "시각화", "그래프", "아키텍처"],
            "omnisearch": ["검색", "search", "찾아", "조사", "트렌드", "최신", "연구"],
            "context7": ["라이브러리", "API", "프레임워크", "코딩", "프로그래밍", "개발", "구현"],
            "python-executor": ["python", "코드 실행", "테스트", "실행", "파이썬", "스크립트"],
            "docker-manager": ["docker", "도커", "컨테이너", "container", "배포"],
            "k8s-manager": ["kubernetes", "쿠버네티스", "k8s", "클러스터", "오케스트레이션"],
            "aws-cli": ["aws", "클라우드", "아마존", "amazon", "인프라"],
            "taskmaster-ai": ["작업 관리", "프로젝트", "task", "할일", "관리", "계획"],
            "obsidian": ["노트", "문서", "정리", "메모", "지식"],
            "git-advanced": ["git", "버전관리", "커밋", "repository", "소스"],
            "database": ["데이터베이스", "database", "SQL", "쿼리", "저장"],
            "playwright": ["브라우저", "자동화", "테스트", "웹", "UI"],
            "deep-research": ["연구", "심화", "분석", "조사", "정보"],
            "ssh-control": ["SSH", "원격", "서버", "remote"],
            "web-scraper": ["스크래핑", "웹 수집", "크롤링", "데이터 수집"]
        }
        
        for tool, keywords in tool_patterns.items():
            if any(keyword in request_lower for keyword in keywords):
                if tool not in estimated_tools:
                    estimated_tools.append(tool)
        
        return estimated_tools

    def _calculate_tool_complexity_score(self, tools: List[str]) -> float:
        """도구 복잡도 점수 계산"""
        total_weight = sum(self.mcp_tool_weights.get(tool, 1) for tool in tools)
        return min(total_weight, 10)  # 최대 10점

    def _detect_multistep_complexity(self, request: str) -> float:
        """멀티스텝 작업 복잡도 감지"""
        step_count = 0
        
        for pattern in self.multistep_patterns:
            matches = re.findall(pattern, request, re.IGNORECASE)
            step_count += len(matches)
        
        # 문장 분리로도 단계 추정
        sentences = re.split(r'[.!?]', request)
        if len(sentences) > 3:
            step_count += len(sentences) - 3
        
        return min(step_count * 1.5, 6)  # 최대 6점

    def _calculate_total_complexity(self, keyword_score: float, tool_score: float, 
                                  multistep_score: float, tool_count: int) -> float:
        """전체 복잡도 점수 계산"""
        # 가중치 적용
        keyword_weight = 0.4
        tool_weight = 0.3
        multistep_weight = 0.2
        count_weight = 0.1
        
        total_score = (
            keyword_weight * keyword_score +
            tool_weight * tool_score +
            multistep_weight * multistep_score +
            count_weight * tool_count
        )
        
        return min(total_score, 10)  # 0-10 범위로 제한

    def _select_thinking_mode(self, complexity_score: float) -> ThinkingMode:
        """복잡도 점수에 따른 사고 모드 선택"""
        if complexity_score >= 6:
            return ThinkingMode.ULTRATHINK
        elif complexity_score >= 3:
            return ThinkingMode.MEGATHINK
        else:
            return ThinkingMode.THINK_HARD

    def _generate_reasoning(self, mode: ThinkingMode, score: float, 
                          keywords: List[str], tools: List[str], 
                          multistep_score: float) -> str:
        """모드 선택 이유 설명 생성"""
        reasoning_parts = [
            f"복잡도 점수: {score:.1f}/10",
            f"선택된 모드: {mode.value.upper()}"
        ]
        
        if keywords:
            reasoning_parts.append(f"감지된 키워드: {', '.join(keywords)}")
        
        if len(tools) > 1:
            reasoning_parts.append(f"예상 도구 ({len(tools)}개): {', '.join(tools)}")
        
        if multistep_score > 2:
            reasoning_parts.append(f"멀티스텝 작업 감지: {multistep_score:.1f}점")
        
        return " | ".join(reasoning_parts)

# 전역 인스턴스
_thinking_engine = None

def get_adaptive_thinking_engine() -> AdaptiveThinkingEngine:
    """적응형 사고 엔진 싱글톤 인스턴스 반환"""
    global _thinking_engine
    if _thinking_engine is None:
        _thinking_engine = AdaptiveThinkingEngine()
    return _thinking_engine

def analyze_and_suggest_mode(user_request: str) -> ThinkingAnalysis:
    """사용자 요청 분석하여 적절한 사고 모드 제안"""
    engine = get_adaptive_thinking_engine()
    return engine.analyze_request(user_request)

def format_thinking_mode_display(analysis: ThinkingAnalysis) -> str:
    """사고 모드 표시용 포맷팅"""
    mode_icons = {
        ThinkingMode.THINK_HARD: "🔮",
        ThinkingMode.MEGATHINK: "✨", 
        ThinkingMode.ULTRATHINK: "💎"
    }
    
    icon = mode_icons.get(analysis.mode, "🔮")
    
    return f"""
╭──────────────────────────────────────╮
│ {icon} {analysis.mode.value.upper()} Mode Activated │
├──────────────────────────────────────┤
│ {analysis.reasoning}
╰──────────────────────────────────────╯
"""

# 테스트 함수들
def test_thinking_modes():
    """사고 모드 테스트"""
    test_cases = [
        "Python 함수 만들어줘",
        "웹사이트 설계하고 구현해줘",
        "풀스택 앱을 처음부터 배포까지 완전 자동화해줘",
        "데이터 분석하고 시각화해줘",
        "복잡한 시스템 아키텍처 제안해줘",
        "Docker와 쿠버네티스로 CI/CD 파이프라인 구축해줘"
    ]
    
    for request in test_cases:
        analysis = analyze_and_suggest_mode(request)
        print(f"\n요청: {request}")
        print(format_thinking_mode_display(analysis))

if __name__ == "__main__":
    test_thinking_modes()