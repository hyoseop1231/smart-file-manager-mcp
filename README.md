# 🚀 Smart File Manager MCP

[![GitHub release](https://img.shields.io/github/release/hyoseop1231/smart-file-manager-mcp.svg)](https://github.com/hyoseop1231/smart-file-manager-mcp/releases)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Desktop](https://img.shields.io/badge/Claude%20Desktop-Compatible-green.svg)](https://claude.ai)

**AI-powered file management system with Claude Desktop integration**

Complete intelligent file management solution featuring LLM-based organization, natural language search, and Docker deployment. Combines MAFM multi-agent architecture with Local-File-Organizer capabilities for enterprise-grade file management.

## ✨ Key Features

### 🧠 AI-Powered Intelligence
- **🔍 Natural Language Search**: Find files using conversational queries
- **📁 Smart Organization**: AI-driven file categorization and structure
- **🤖 Multi-Model Support**: Qwen, LLaVA, Nomic embedding models
- **🔄 Background Processing**: Automatic indexing and analysis
- **📊 Intelligent Analytics**: File collection insights and patterns

### 🔧 Advanced Capabilities
- **🔍 Duplicate Detection**: Content-based duplicate identification
- **🧹 Cleanup Suggestions**: Smart recommendations for file management
- **🏷️ Auto Tagging**: AI-generated metadata and tags
- **📈 Batch Processing**: Parallel file analysis for large collections
- **🎛️ Smart Model Selection**: Optimal LLM choice based on file characteristics

## 🛠️ Quick Installation

### Prerequisites
- Docker & Docker Compose installed
- 8GB+ RAM recommended
- GPU support (optional, for better performance)

### 1. Clone and Setup
```bash
# Clone the repository
git clone https://github.com/hyoseop1231/smart-file-manager-mcp.git
cd smart-file-manager-mcp

# Run the automated deployment
./deploy.sh
```

### 2. Configure Claude Desktop
Add to your Claude Desktop MCP settings (`~/.claude/config.json`):
```json
{
  "mcpServers": {
    "smart-file-manager": {
      "command": "node",
      "args": ["/path/to/smart-file-manager-mcp/mcp-server/dist/index.js"],
      "env": {
        "AI_SERVICE_URL": "http://localhost:8001"
      }
    }
  }
}
```

### 3. Start Using
Restart Claude Desktop and use natural language commands:
- "PDF 파일 찾아줘" (Find PDF files)
- "다운로드 폴더 정리해줘" (Organize Downloads folder)
- "중복 파일 찾아줘" (Find duplicate files)
- "최근 파일 보여줘" (Show recent files)
- "대용량 파일 정리해줘" (Clean up large files)
- "임시 파일 삭제해줘" (Delete temporary files)

## 📋 Available MCP Commands

### Basic Commands
1. **`search_files`** - Natural language file search
2. **`quick_search`** - Fast category/extension/recent search
3. **`organize_files`** - AI-powered file organization
4. **`smart_workflow`** - Combined search and action workflows

### Advanced Commands
5. **`find_duplicates`** - Duplicate file detection
6. **`cleanup_suggestions`** - File cleanup recommendations
7. **`smart_analyze`** - Single file AI analysis
8. **`batch_analyze`** - Multiple file parallel analysis
9. **`auto_tag`** - Automatic tag generation
10. **`generate_insights`** - Collection pattern analysis

## 🔧 Configuration

### Environment Variables
Key settings in `.env`:
```bash
# Core settings
PORT=8001
SUPERVISOR_PORT=9001

# Directories to watch
HOME_DOCUMENTS=${HOME}/Documents
HOME_DOWNLOADS=${HOME}/Downloads
HOME_PICTURES=${HOME}/Pictures

# Indexing intervals
FULL_INDEXING_INTERVAL=7200    # 2 hours
QUICK_INDEXING_INTERVAL=1800   # 30 minutes

# GPU support
ENABLE_GPU=true

# Models
DEFAULT_TEXT_MODEL=qwen2.5:3b
DEFAULT_VISION_MODEL=llava:13b
DEFAULT_EMBEDDING_MODEL=nomic-embed-text
```

### Custom Directory Monitoring
Edit `docker-compose.yml` to add your directories:
```yaml
volumes:
  - /your/custom/path:/watch_directories/custom:ro
```

## 🐳 Docker Services

### Service Architecture
- **smart-file-manager**: Main API server with integrated scheduler
- **ollama**: Local LLM service
- **mcp-server**: Claude Desktop integration

### Management Commands
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f smart-file-manager

# Stop services
docker-compose down

# Restart specific service
docker-compose restart smart-file-manager

# Check health
curl http://localhost:8001/health
```

## 📊 Monitoring

### Service Monitoring
- **API Health**: `http://localhost:8001/health`
- **Supervisor Interface**: `http://localhost:9001` (admin/admin123)
- **Ollama API**: `http://localhost:11434`

### Performance Metrics
- File indexing progress
- Search performance
- LLM model usage
- Memory and CPU utilization

## 🔍 Usage Examples

### Natural Language Commands
```bash
# File search
"PDF 문서 찾아줘"                    # Find PDF documents
"어제 수정된 파일 보여줘"              # Show files modified yesterday
"코드 파일 중에서 Python 찾아줘"      # Find Python files

# Organization
"다운로드 폴더 정리해줘"               # Organize Downloads folder
"사진 파일 카테고리별로 정리해줘"       # Organize photos by category

# Advanced features
"중복 파일 찾아서 정리 제안해줘"        # Find duplicates and suggest cleanup
"대용량 파일 찾아줘"                  # Find large files
"임시 파일 정리해줘"                  # Clean up temporary files
```

### API Usage
```bash
# Direct API calls
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{"query": "presentation files", "limit": 10}'

curl -X POST http://localhost:8001/duplicate/find \
  -H "Content-Type: application/json" \
  -d '{}'
```

## 🛡️ Security

### Network Security
- Services run in isolated Docker network
- No external network access required
- Local-only LLM processing

### Data Privacy
- All processing happens locally
- No data sent to external services
- File contents never leave your machine

## 🚨 Troubleshooting

### Common Issues

**Service won't start**
```bash
# Check logs
docker-compose logs smart-file-manager

# Verify ports are available
lsof -i :8001
```

**Ollama models not loading**
```bash
# Manual model pull
docker-compose exec ollama ollama pull qwen2.5:3b
```

**Claude Desktop not connecting**
```bash
# Verify MCP server
node mcp-server/dist/index.js

# Check configuration
cat ~/.claude/config.json
```

### Performance Issues
- Increase Docker memory allocation
- Adjust indexing intervals
- Limit concurrent file processing

## 📝 Development

### Local Development
```bash
# Development mode
docker-compose -f docker-compose.dev.yml up

# Run tests
docker-compose exec smart-file-manager python -m pytest

# Live reload
docker-compose exec smart-file-manager supervisorctl restart api_server
```

### Custom Extensions
- Add new MCP commands in `mcp-server/src/`
- Extend API endpoints in `ai-services/enhanced_api.py`
- Add LLM models in `smart_model_selector.py`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## 📄 License

MIT License - see LICENSE file for details

## 🔗 Links

- [Claude Desktop](https://claude.ai/download)
- [Model Context Protocol](https://github.com/modelcontextprotocol)
- [Ollama](https://ollama.ai)
- [Docker](https://docker.com)

## 🏗️ Architecture

### System Components
- **AI Services**: FastAPI-based backend with integrated scheduler
- **MCP Server**: TypeScript-based Claude Desktop integration
- **Ollama**: Local LLM inference engine
- **Database**: SQLite with FTS5 for full-text search
- **Docker**: Containerized deployment with Supervisor

### Multi-Agent Architecture (MAFM)
- **Supervisor Agent**: Coordinates multi-agent workflows
- **Member Agents**: Specialized file processing agents
- **Analyst Agent**: Provides insights and recommendations
- **LLM Integration**: Smart model selection based on file type

## 🔄 Background Processing

### Automatic Indexing
- **Full Indexing**: Complete file scan every 2 hours
- **Quick Indexing**: Delta updates every 30 minutes
- **Smart Cleanup**: Automated maintenance every 24 hours
- **Real-time Monitoring**: File system change detection

### Supported File Types
- **Documents**: PDF, DOC, DOCX, TXT, MD, RTF
- **Images**: JPG, PNG, GIF, BMP, TIFF, WebP
- **Code**: Python, JavaScript, TypeScript, Java, C++, and more
- **Archives**: ZIP, RAR, 7Z, TAR, GZ
- **Media**: MP4, MP3, WAV, AVI, MOV

---

**Version**: 2.0.0  
**Last Updated**: 2025-07-09  
**Compatibility**: Claude Desktop 1.0+, Docker 20.0+, Ollama 0.1.0+