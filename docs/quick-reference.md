# Smart File Manager MCP - Quick Reference

## 🚀 Quick Start

```bash
# Start all services
docker-compose up -d

# Access Web UI
http://localhost:3002

# Check health
curl http://localhost:8001/health
```

## 🔍 MCP Functions (Claude Desktop)

### search_files
```
"Find Python files about machine learning"
"최근 일주일간 수정된 문서 찾아줘"
```

### quick_search
```
"Show PDFs from last 24 hours"
"이미지 파일만 보여줘"
```

### organize_files
```
"Organize my Downloads folder"
"데스크톱 파일들 정리해줘"
```

### smart_workflow
```
"Find and organize project files"
"중복 파일 찾아서 정리해줘"
```

### analyze_file
```
"Analyze /path/to/document.pdf"
"이 파일이 어떤 내용인지 분석해줘"
```

### system_status
```
"Show system status"
"시스템 상태 확인"
```

### find_duplicates
```
"Find duplicate files"
"1MB 이상 중복 파일 찾아줘"
```

### batch_operation
```
"Move all PDFs to Documents folder"
"선택한 파일들 일괄 처리"
```

## 🌐 Web UI Features

### Dashboard (http://localhost:3002)
- System metrics (CPU, Memory, Disk)
- Recent file activity
- Quick statistics
- Service health status

### File Explorer
- Natural language search
- Advanced filters
- Batch operations
- File preview

### Analytics
- Duplicate detection
- Storage insights
- Usage patterns
- Performance trends

### Organization
- AI-powered suggestions
- Dry-run preview
- Progress tracking
- Undo support

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System health |
| `/search` | POST | Search files |
| `/organize` | POST | Organize files |
| `/duplicates` | POST | Find duplicates |
| `/analyze` | POST | Analyze file |
| `/recent` | GET | Recent files |
| `/metrics` | GET | System metrics |
| `/task/{id}` | GET | Task status |

## 🛠️ Common Commands

### Docker Management
```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop all
docker-compose down

# Update and restart
docker-compose pull
docker-compose up -d
```

### Troubleshooting
```bash
# Check ports
lsof -i :8001  # API
lsof -i :3002  # Web UI

# Test MCP server
node mcp-server/dist/index.js

# Database stats
docker exec smart-file-manager sqlite3 /data/db/file-index.db "SELECT COUNT(*) FROM files;"
```

## ⚙️ Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8001 | API port |
| `OLLAMA_API_URL` | http://host.docker.internal:11434 | Ollama endpoint |
| `FULL_INDEX_INTERVAL` | 7200 | Full scan interval (seconds) |
| `QUICK_INDEX_INTERVAL` | 1800 | Quick scan interval (seconds) |

## 🎯 Performance Tips

1. **Search Optimization**
   - Use specific terms
   - Limit search scope with directories
   - Enable LLM for better results

2. **Organization Best Practices**
   - Always use dry-run first
   - Start with smaller directories
   - Review AI suggestions

3. **System Resources**
   - Allocate 4GB+ RAM to Docker
   - Use SSD for database storage
   - Schedule heavy indexing during off-hours

## 🔗 Useful Links

- **GitHub**: https://github.com/hyoseop1231/smart-file-manager-mcp
- **Issues**: https://github.com/hyoseop1231/smart-file-manager-mcp/issues
- **Documentation**: https://github.com/hyoseop1231/smart-file-manager-mcp/wiki

## 📞 Support Channels

- **Bug Reports**: GitHub Issues
- **Feature Requests**: GitHub Discussions
- **Security Issues**: security@example.com

---

**Version**: 2.2.0 | **Updated**: 2025-01-09