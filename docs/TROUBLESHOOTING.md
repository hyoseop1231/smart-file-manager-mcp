# Troubleshooting Guide

This guide helps you resolve common issues with Smart File Manager MCP.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Docker Issues](#docker-issues)
- [Claude Desktop Integration](#claude-desktop-integration)
- [Performance Issues](#performance-issues)
- [Search Problems](#search-problems)
- [Database Issues](#database-issues)
- [Ollama/LLM Issues](#ollamallm-issues)
- [Common Error Messages](#common-error-messages)
- [Debug Commands](#debug-commands)

## Installation Issues

### Docker not found

**Problem:** `docker: command not found`

**Solution:**
1. Install Docker Desktop from https://docker.com
2. Start Docker Desktop
3. Verify installation:
   ```bash
   docker --version
   docker-compose --version
   ```

### Permission denied errors

**Problem:** Permission errors when running Docker commands

**Solution:**
```bash
# Add user to docker group (Linux/macOS)
sudo usermod -aG docker $USER
# Log out and back in

# Or run with sudo (not recommended)
sudo docker-compose up -d
```

### Port already in use

**Problem:** `bind: address already in use`

**Solution:**
```bash
# Find what's using the port
lsof -i :8001
lsof -i :9001

# Kill the process or change ports in .env
PORT=8002
SUPERVISOR_PORT=9002
```

## Docker Issues

### Container won't start

**Problem:** Container exits immediately

**Debug steps:**
```bash
# Check logs
docker-compose logs smart-file-manager

# Check container status
docker-compose ps

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Out of memory

**Problem:** Container killed due to memory limits

**Solution:**
1. Increase Docker memory allocation:
   - Docker Desktop → Settings → Resources → Memory: 4GB minimum
2. Reduce batch sizes in .env:
   ```bash
   INDEXING_BATCH_SIZE=500
   MAX_WORKERS=2
   ```

### Slow performance

**Problem:** Container running slowly

**Solutions:**
1. Check resource usage:
   ```bash
   docker stats
   ```
2. Optimize Docker settings:
   - Enable "Use the WSL 2 based engine" (Windows)
   - Increase CPU/Memory allocation
3. Use production build:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Claude Desktop Integration

### MCP server not found

**Problem:** Claude Desktop can't find the MCP server

**Solution:**
1. Verify installation path:
   ```bash
   ls -la /path/to/smart-file-manager-mcp/mcp-server/dist/index.js
   ```
2. Test MCP server directly:
   ```bash
   node /path/to/smart-file-manager-mcp/mcp-server/dist/index.js
   ```
3. Check Claude config:
   ```bash
   # macOS/Linux
   cat ~/.config/claude/claude_desktop_config.json
   
   # Windows
   type %APPDATA%\Claude\claude_desktop_config.json
   ```

### 422 Unprocessable Entity

**Problem:** Claude Desktop receives 422 errors

**Solution:**
1. Update to latest version:
   ```bash
   git pull origin main
   docker-compose build
   docker-compose up -d
   ```
2. Verify API is using raw request handling
3. Check logs for validation errors:
   ```bash
   docker-compose logs -f smart-file-manager | grep 422
   ```

### Tools not appearing

**Problem:** MCP tools don't show in Claude Desktop

**Solution:**
1. Restart Claude Desktop after config changes
2. Check priority setting:
   ```json
   {
     "smart-file-manager": {
       "priority": 1,
       "autoApprove": ["search_files", "quick_search"]
     }
   }
   ```
3. Verify MCP server is running:
   ```bash
   curl http://localhost:8001/health
   ```

## Performance Issues

### Slow search results

**Problem:** Searches taking too long

**Solutions:**
1. Check database size:
   ```bash
   docker exec smart-file-manager sqlite3 /data/db/file-index.db "SELECT COUNT(*) FROM files;"
   ```
2. Optimize database:
   ```bash
   docker exec smart-file-manager python -c "
   from indexer import FileIndexer
   indexer = FileIndexer()
   indexer.clean_cache()
   "
   ```
3. Disable LLM for simple searches:
   ```json
   {
     "query": "test.pdf",
     "use_llm": false
   }
   ```

### High memory usage

**Problem:** Container using too much memory

**Solutions:**
1. Check current usage:
   ```bash
   docker stats smart-file-manager
   ```
2. Reduce concurrent operations:
   ```bash
   MAX_WORKERS=2
   INDEXING_BATCH_SIZE=500
   ```
3. Increase cleanup frequency:
   ```bash
   CLEANUP_INTERVAL=43200  # 12 hours
   ```

### Indexing takes forever

**Problem:** Initial indexing very slow

**Solutions:**
1. Reduce monitored directories
2. Exclude large directories:
   ```yaml
   volumes:
     - /path/to/dir:/watch_directories/dir:ro
     - /path/to/dir/node_modules:/watch_directories/dir/node_modules:ro
   ```
3. Check disk I/O:
   ```bash
   iostat -x 1
   ```

## Search Problems

### No results found

**Problem:** Search returns empty results

**Debug steps:**
1. Check if files are indexed:
   ```bash
   docker exec smart-file-manager sqlite3 /data/db/file-index.db \
     "SELECT COUNT(*) FROM files WHERE name LIKE '%keyword%';"
   ```
2. Try simple search:
   ```bash
   curl -X POST http://localhost:8001/search_simple \
     -H "Content-Type: application/json" \
     -d '{"query": "test"}'
   ```
3. Check Ollama connection:
   ```bash
   curl http://localhost:11434/api/tags
   ```

### Wrong results

**Problem:** Search returns irrelevant files

**Solutions:**
1. Disable LLM enhancement for keyword search
2. Use specific file extensions:
   ```json
   {
     "extensions": [".pdf", ".docx"],
     "category": "document"
   }
   ```
3. Rebuild search index:
   ```bash
   docker exec smart-file-manager python -c "
   from scheduler import SmartFileScheduler
   scheduler = SmartFileScheduler()
   scheduler.run_full_indexing()
   "
   ```

## Database Issues

### Database locked

**Problem:** `database is locked` errors

**Solutions:**
1. Ensure WAL mode is enabled:
   ```bash
   docker exec smart-file-manager sqlite3 /data/db/file-index.db \
     "PRAGMA journal_mode=WAL;"
   ```
2. Check for stuck processes:
   ```bash
   docker exec smart-file-manager lsof /data/db/file-index.db
   ```
3. Restart container:
   ```bash
   docker-compose restart smart-file-manager
   ```

### Corrupted database

**Problem:** Database corruption errors

**Recovery steps:**
1. Backup current database:
   ```bash
   docker cp smart-file-manager:/data/db/file-index.db ./backup.db
   ```
2. Check integrity:
   ```bash
   docker exec smart-file-manager sqlite3 /data/db/file-index.db \
     "PRAGMA integrity_check;"
   ```
3. Rebuild if needed:
   ```bash
   docker-compose down
   docker volume rm smart-file-manager_smart_file_data
   docker-compose up -d
   ```

## Ollama/LLM Issues

### Ollama not available

**Problem:** LLM features not working

**Solutions:**
1. Install Ollama:
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```
2. Start Ollama:
   ```bash
   ollama serve
   ```
3. Pull required models:
   ```bash
   ollama pull llama3.2:3b
   ollama pull nomic-embed-text
   ```

### Model loading failed

**Problem:** Ollama models won't load

**Solutions:**
1. Check available models:
   ```bash
   ollama list
   ```
2. Re-pull models:
   ```bash
   ollama rm llama3.2:3b
   ollama pull llama3.2:3b
   ```
3. Check Ollama logs:
   ```bash
   journalctl -u ollama -f
   ```

### Slow LLM responses

**Problem:** AI features very slow

**Solutions:**
1. Use smaller model:
   ```bash
   DEFAULT_MODEL=llama3.2:1b
   ```
2. Disable for simple operations:
   ```json
   {
     "use_llm": false
   }
   ```
3. Enable GPU if available:
   ```bash
   ENABLE_GPU=true
   ```

## Common Error Messages

### "Field required" (422 error)

**Cause:** MCP protocol validation issue

**Fix:** Update to latest version with raw request handling

### "Connection refused"

**Cause:** Service not running or wrong port

**Fix:**
```bash
# Check if service is running
docker-compose ps

# Check correct port
curl http://localhost:8001/health
```

### "No such file or directory"

**Cause:** Incorrect path mapping

**Fix:** Verify volume mounts in docker-compose.yml match actual paths

### "Out of memory"

**Cause:** Insufficient memory allocation

**Fix:** Increase Docker memory or reduce batch sizes

## Debug Commands

### View real-time logs
```bash
# All logs
docker-compose logs -f

# Specific service
docker-compose logs -f smart-file-manager

# Filter by error
docker-compose logs -f | grep ERROR
```

### Check service status
```bash
# Container status
docker-compose ps

# Service health
curl http://localhost:8001/health

# System metrics
curl http://localhost:8001/metrics
```

### Database inspection
```bash
# File count
docker exec smart-file-manager sqlite3 /data/db/file-index.db \
  "SELECT COUNT(*) FROM files;"

# Category breakdown
docker exec smart-file-manager sqlite3 /data/db/file-index.db \
  "SELECT category, COUNT(*) FROM files GROUP BY category;"

# Recent files
docker exec smart-file-manager sqlite3 /data/db/file-index.db \
  "SELECT name, path FROM files ORDER BY modified_time DESC LIMIT 10;"
```

### Test endpoints
```bash
# Search test
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 5}'

# Recent files
curl http://localhost:8001/recent?hours=24

# Quick search
curl -X POST http://localhost:8001/quick-search \
  -H "Content-Type: application/json" \
  -d '{"category": "document", "limit": 10}'
```

### Reset everything
```bash
# Stop and remove everything
docker-compose down -v

# Remove all data
docker volume rm smart-file-manager_smart_file_data
docker volume rm smart-file-manager_smart_file_embeddings
docker volume rm smart-file-manager_smart_file_metadata

# Rebuild and start fresh
docker-compose build --no-cache
docker-compose up -d
```

## Getting Help

If these solutions don't resolve your issue:

1. Check existing issues: https://github.com/hyoseop1231/smart-file-manager-mcp/issues
2. Search discussions: https://github.com/hyoseop1231/smart-file-manager-mcp/discussions
3. Create a new issue with:
   - Error messages
   - Steps to reproduce
   - System information
   - Docker logs

---

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>