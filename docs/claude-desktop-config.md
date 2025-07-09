# Claude Desktop Configuration Guide

This guide will help you configure Claude Desktop to use the Smart File Manager MCP server.

## Configuration File Locations

### macOS
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Windows
```
%APPDATA%\Claude\claude_desktop_config.json
```

### Linux
```
~/.config/claude/claude_desktop_config.json
```

## Basic Configuration

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "smart-file-manager": {
      "command": "node",
      "args": [
        "/path/to/smart-file-manager-mcp/mcp-server/dist/index.js"
      ],
      "env": {
        "AI_SERVICE_URL": "http://localhost:8001",
        "DEFAULT_FILE_MANAGER": "true"
      },
      "priority": 1,
      "autoApprove": [
        "search_files",
        "quick_search",
        "organize_files",
        "smart_workflow",
        "analyze_file",
        "system_status",
        "find_duplicates",
        "batch_operation"
      ],
      "description": "AI-powered file management system with semantic search and organization"
    }
  }
}
```

## Docker-based Configuration

If you're running the MCP server in Docker:

```json
{
  "mcpServers": {
    "smart-file-manager": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "smart-file-mcp-server",
        "node",
        "/app/dist/index.js"
      ],
      "env": {
        "AI_SERVICE_URL": "http://localhost:8001"
      },
      "priority": 1,
      "autoApprove": [
        "search_files",
        "quick_search",
        "organize_files",
        "smart_workflow",
        "analyze_file",
        "system_status",
        "find_duplicates",
        "batch_operation"
      ]
    }
  }
}
```

## Advanced Configuration Options

### Custom API URL

If your API service is running on a different port or host:

```json
"env": {
  "AI_SERVICE_URL": "http://192.168.1.100:8001"
}
```

### Limited Permissions

For more restrictive permissions, modify the `autoApprove` array:

```json
"autoApprove": [
  "search_files",
  "quick_search",
  "system_status"
]
```

### Multiple File Managers

You can have multiple file management servers:

```json
{
  "mcpServers": {
    "smart-file-manager": {
      // Main configuration
    },
    "backup-file-manager": {
      "command": "node",
      "args": ["/path/to/backup-server/index.js"],
      "priority": 2
    }
  }
}
```

## Troubleshooting

### Server Not Connecting

1. **Check the path**: Ensure the path to `index.js` is correct
   ```bash
   ls -la /path/to/smart-file-manager-mcp/mcp-server/dist/index.js
   ```

2. **Test the server directly**:
   ```bash
   node /path/to/smart-file-manager-mcp/mcp-server/dist/index.js
   ```

3. **Check Docker container** (if using Docker):
   ```bash
   docker ps | grep smart-file-mcp-server
   docker logs smart-file-mcp-server
   ```

### Permission Errors

If you get permission errors, ensure the MCP server has read access to your files:

```bash
# Check file permissions
ls -la ~/Documents
ls -la ~/Downloads

# For Docker, check volume mounts in docker-compose.yml
```

### API Connection Issues

1. **Verify API is running**:
   ```bash
   curl http://localhost:8001/health
   ```

2. **Check firewall settings**: Ensure port 8001 is not blocked

3. **Test from Claude Desktop**: Try a simple command:
   ```
   "test file search"
   ```

## Best Practices

1. **Security**: Only grant `autoApprove` for functions you trust
2. **Performance**: Set appropriate `priority` levels for multiple servers
3. **Logging**: Enable debug logging for troubleshooting:
   ```json
   "env": {
     "DEBUG": "true"
   }
   ```

4. **Updates**: After updating the config, restart Claude Desktop

## Useful Commands in Claude

Once configured, you can use natural language commands:

### English
- "Search for PDF files"
- "Find documents modified today"
- "Organize my Downloads folder"
- "Show system status"
- "Find duplicate files"

### Korean (한국어)
- "PDF 파일 찾아줘"
- "오늘 수정된 문서 보여줘"
- "다운로드 폴더 정리해줘"
- "시스템 상태 확인"
- "중복 파일 찾아줘"

## Environment Variables

All available environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| AI_SERVICE_URL | http://localhost:8001 | API service endpoint |
| DEFAULT_FILE_MANAGER | false | Set as default file manager |
| DEBUG | false | Enable debug logging |
| CACHE_TTL | 3600 | Cache timeout in seconds |
| MAX_RESULTS | 100 | Maximum search results |

## Version Compatibility

| Smart File Manager | Claude Desktop | Status |
|--------------------|----------------|---------|
| 2.2.0+ | 1.0+ | ✅ Fully Compatible |
| 2.0.0 - 2.1.x | 1.0+ | ✅ Compatible |
| 1.x | 0.9+ | ⚠️ Limited Features |

---

For more help, visit: https://github.com/hyoseop1231/smart-file-manager-mcp