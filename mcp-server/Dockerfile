FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY src ./src

# Build TypeScript
RUN npm run build

# Set environment variables
ENV NODE_ENV=production
ENV AI_SERVICE_URL=http://smart-file-manager:8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "console.log('MCP Server is running')"

# Run the MCP server
CMD ["node", "dist/index.js"]