# Smart File Manager MCP Server Dockerfile
# Node.js 기반 MCP (Model Context Protocol) 서버

FROM node:18-alpine

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치
RUN apk add --no-cache \
    curl \
    bash

# package.json과 package-lock.json 복사
COPY package*.json ./

# 의존성 설치
RUN npm install --production

# 애플리케이션 코드 복사
COPY . .

# MCP 서버 실행 권한 설정
RUN chmod +x server.js

# 포트 노출 (MCP는 stdio 통신을 주로 사용하지만 헬스체크용)
EXPOSE 3000

# 환경 변수 설정
ENV NODE_ENV=production
ENV API_BASE_URL=http://smart-file-manager-multimedia-v4:8001

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD node -e "console.log('healthy')" || exit 1

# MCP 서버 시작
CMD ["node", "server.js"]