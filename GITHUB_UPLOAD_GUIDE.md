# GitHub 업로드 가이드

## 1. GitHub에 새 저장소 생성

1. [GitHub.com](https://github.com)에 로그인
2. 우측 상단 '+' 클릭 → 'New repository'
3. 저장소 이름: `smart-file-manager-mcp`
4. 설명: "AI-powered smart file management system with MCP integration"
5. Public/Private 선택
6. **중요**: "Initialize this repository with" 옵션들은 모두 체크 해제
7. 'Create repository' 클릭

## 2. 로컬 저장소를 GitHub에 연결

GitHub에서 생성한 저장소 URL을 복사한 후:

```bash
# GitHub 원격 저장소 추가
git remote add origin https://github.com/YOUR_USERNAME/smart-file-manager-mcp.git

# 또는 SSH 사용시
git remote add origin git@github.com:YOUR_USERNAME/smart-file-manager-mcp.git

# 원격 저장소 확인
git remote -v

# 첫 번째 푸시
git push -u origin main
```

## 3. 추가 파일 제외 (선택사항)

민감한 정보나 대용량 파일이 있다면 푸시 전에 제외:

```bash
# .gitignore 수정
echo "ai-services/mafm/mafm/MAFM_test/report/*.pdf" >> .gitignore
echo "ai-services/mafm/mafm/MAFM_test/report/*.docx" >> .gitignore

# 변경사항 스테이징 및 커밋
git add .gitignore
git commit -m "chore: exclude binary files from tracking"
git push
```

## 4. GitHub Actions 설정 (선택사항)

`.github/workflows/ci.yml` 파일 생성:

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.8'
    
    - name: Build Docker images
      run: docker-compose build
    
    - name: Run tests
      run: |
        docker-compose up -d
        sleep 10
        curl -f http://localhost:8001/health || exit 1
        docker-compose down
```

## 5. README 뱃지 추가

GitHub 저장소 생성 후 README.md 상단에 추가:

```markdown
[![GitHub stars](https://img.shields.io/github/stars/YOUR_USERNAME/smart-file-manager-mcp)](https://github.com/YOUR_USERNAME/smart-file-manager-mcp/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/YOUR_USERNAME/smart-file-manager-mcp)](https://github.com/YOUR_USERNAME/smart-file-manager-mcp/issues)
[![GitHub license](https://img.shields.io/github/license/YOUR_USERNAME/smart-file-manager-mcp)](https://github.com/YOUR_USERNAME/smart-file-manager-mcp/blob/main/LICENSE)
```

## 6. 릴리스 생성

1. GitHub 저장소 페이지에서 'Releases' 클릭
2. 'Create a new release' 클릭
3. Tag version: `v4.0.0`
4. Release title: `Smart File Manager MCP v4.0`
5. 릴리스 노트 작성:

```markdown
## 🎉 Smart File Manager MCP v4.0

### ✨ 주요 기능
- AI 기반 멀티미디어 파일 분석 (이미지, 음성, 비디오)
- FTS5 기반 고급 검색 시스템
- MCP 프로토콜로 Claude Desktop 통합
- Docker Compose 기반 마이크로서비스 아키텍처
- Prometheus + Grafana 모니터링

### 🐛 버그 수정
- `/stats/multimedia` 타입 비교 오류 해결
- `/search/multimedia` JSON 파싱 오류 해결
- Row 객체 변환 로직 개선

### 📝 문서
- 포괄적인 README 및 설치 가이드
- 상세한 API 문서
- 트러블슈팅 가이드

### 🚀 시작하기
```bash
git clone https://github.com/YOUR_USERNAME/smart-file-manager-mcp.git
cd smart-file-manager-mcp
docker-compose up -d
```
```

## 7. 보안 권장사항

1. **환경 변수 보호**
   - `.env` 파일은 절대 커밋하지 않음
   - GitHub Secrets 사용 권장

2. **API 키 관리**
   - OpenAI API 키는 환경 변수로만 관리
   - 프로덕션에서는 별도 비밀 관리 시스템 사용

3. **접근 제어**
   - 프로덕션 배포 시 API 인증 구현 필수
   - 네트워크 방화벽 설정

## 8. 유지보수

### 정기 업데이트
```bash
# 로컬 변경사항 확인
git status

# 변경사항 커밋
git add .
git commit -m "feat: 새로운 기능 추가"

# GitHub에 푸시
git push origin main
```

### 이슈 관리
- GitHub Issues로 버그 및 기능 요청 관리
- Pull Request로 코드 리뷰 진행
- 마일스톤으로 버전 관리

## 완료!

이제 프로젝트가 GitHub에 업로드되었습니다. 
저장소 URL을 공유하여 다른 사람들이 사용할 수 있게 하세요! 🎉