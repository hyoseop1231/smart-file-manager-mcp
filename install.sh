#!/bin/bash

# Smart File Manager MCP - One-Line Installer
# This script automates the installation process

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}     Smart File Manager MCP Installer${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_command() {
    if command -v $1 &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_error "$1 is not installed"
        return 1
    fi
}

# Main installation
print_header

# Check prerequisites
print_info "Checking prerequisites..."

MISSING_DEPS=0

if ! check_command docker; then
    MISSING_DEPS=1
    print_info "Please install Docker: https://docs.docker.com/get-docker/"
fi

if ! check_command docker-compose; then
    # Try docker compose (newer version)
    if docker compose version &> /dev/null; then
        print_success "docker compose is installed"
    else
        MISSING_DEPS=1
        print_info "Please install Docker Compose: https://docs.docker.com/compose/install/"
    fi
fi

if ! check_command git; then
    MISSING_DEPS=1
    print_info "Please install Git: https://git-scm.com/downloads"
fi

if ! check_command node; then
    print_warning "Node.js not found - needed for Claude Desktop integration"
    print_info "Install Node.js: https://nodejs.org/"
fi

if [ $MISSING_DEPS -eq 1 ]; then
    print_error "Missing required dependencies. Please install them and run again."
    exit 1
fi

echo ""
print_info "All prerequisites met!"
echo ""

# Clone or update repository
if [ -d "smart-file-manager-mcp" ]; then
    print_info "Repository already exists. Updating..."
    cd smart-file-manager-mcp
    git pull origin main
    cd ..
else
    print_info "Cloning repository..."
    git clone https://github.com/hyoseop1231/smart-file-manager-mcp.git
fi

cd smart-file-manager-mcp

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_info "Creating .env configuration file..."
    cat > .env << EOF
# Smart File Manager MCP Configuration
PORT=8001
SUPERVISOR_PORT=9001

# Directories to monitor (customize these paths)
HOME_DOCUMENTS=${HOME}/Documents
HOME_DOWNLOADS=${HOME}/Downloads
HOME_DESKTOP=${HOME}/Desktop
HOME_PICTURES=${HOME}/Pictures
HOME_MOVIES=${HOME}/Movies
HOME_MUSIC=${HOME}/Music

# Indexing intervals
FULL_INDEX_INTERVAL=7200    # 2 hours
QUICK_INDEX_INTERVAL=1800   # 30 minutes
CLEANUP_INTERVAL=86400      # 24 hours

# Ollama configuration
OLLAMA_API_URL=http://host.docker.internal:11434/api/generate
DEFAULT_MODEL=llama3.2:3b
EMBEDDING_MODEL=nomic-embed-text

# Performance settings
MAX_WORKERS=4
INDEXING_BATCH_SIZE=1000
ENABLE_GPU=false
EOF
    print_success "Created .env file"
else
    print_info ".env file already exists"
fi

# Check if Ollama is installed
print_info "Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    print_success "Ollama is installed"
    
    # Check if required models are available
    print_info "Checking Ollama models..."
    
    if ! ollama list | grep -q "llama3.2:3b"; then
        print_info "Pulling llama3.2:3b model..."
        ollama pull llama3.2:3b
    else
        print_success "llama3.2:3b model is available"
    fi
    
    if ! ollama list | grep -q "nomic-embed-text"; then
        print_info "Pulling nomic-embed-text model..."
        ollama pull nomic-embed-text
    else
        print_success "nomic-embed-text model is available"
    fi
else
    print_warning "Ollama not found. Please install from: https://ollama.ai"
    print_info "After installation, run: ollama pull llama3.2:3b && ollama pull nomic-embed-text"
fi

# Build MCP server
print_info "Building MCP server..."
cd mcp-server
npm install
npm run build
cd ..
print_success "MCP server built"

# Start Docker services
print_info "Starting Docker services..."
docker-compose down 2>/dev/null || true
docker-compose build
docker-compose up -d

# Wait for services to be ready
print_info "Waiting for services to start..."
sleep 10

# Check service health
print_info "Checking service health..."
if curl -s http://localhost:8001/health | grep -q "healthy"; then
    print_success "API service is healthy"
else
    print_warning "API service might still be starting up"
fi

# Generate Claude Desktop configuration
print_info "Generating Claude Desktop configuration..."
INSTALL_PATH=$(pwd)

cat > claude_desktop_config_snippet.json << EOF
{
  "mcpServers": {
    "smart-file-manager": {
      "command": "node",
      "args": [
        "${INSTALL_PATH}/mcp-server/dist/index.js"
      ],
      "env": {
        "AI_SERVICE_URL": "http://localhost:8001",
        "DEFAULT_FILE_MANAGER": "true"
      },
      "priority": 1,
      "autoApprove": ["search_files", "quick_search", "organize_files"],
      "description": "Primary file management system with AI capabilities"
    }
  }
}
EOF

echo ""
print_success "Installation completed successfully!"
echo ""
print_info "Next steps:"
echo "1. Add the following to your Claude Desktop configuration:"
echo ""
echo "   macOS/Linux: ~/.config/claude/claude_desktop_config.json"
echo "   Windows: %APPDATA%\\Claude\\claude_desktop_config.json"
echo ""
cat claude_desktop_config_snippet.json
echo ""
echo "2. Restart Claude Desktop"
echo ""
echo "3. Test with commands like:"
echo "   - \"파일 검색 테스트\" or \"test file search\""
echo "   - \"PDF 파일 찾아줘\" or \"find PDF files\""
echo ""
print_info "Service URLs:"
echo "   - API: http://localhost:8001"
echo "   - Health: http://localhost:8001/health"
echo "   - Supervisor: http://localhost:9001 (admin/admin)"
echo ""
print_info "To stop services: docker-compose down"
print_info "To view logs: docker-compose logs -f"
echo ""
print_success "Happy file managing! 🚀"

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>