# API Reference

## Overview

The Smart File Manager MCP provides a RESTful API for file management operations. All endpoints are available at `http://localhost:8001` by default.

## Base URL

```
http://localhost:8001
```

## Authentication

Currently, the API does not require authentication. This will be added in future versions.

## Common Response Format

All API responses follow this format:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "timestamp": "2025-07-09T12:00:00Z"
}
```

Error responses:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { ... }
  },
  "timestamp": "2025-07-09T12:00:00Z"
}
```

## Endpoints

### Health Check

#### GET /health

Check the health status of all services.

**Response:**

```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "indexer": "available",
    "llm_organizer": "available",
    "ollama": "available",
    "vectordb": "planned"
  },
  "db_stats": {
    "total_files": 114549,
    "by_category": {
      "document": 1930,
      "image": 10353,
      "video": 33,
      "audio": 67,
      "code": 64998,
      "archive": 641,
      "other": 36527
    },
    "total_size_gb": 28.08,
    "indexed_last_24h": 523
  },
  "background_tasks": 0,
  "performance": {
    "system_metrics": {
      "cpu_percent": 0.68,
      "memory_percent": 18.07,
      "disk_usage_percent": 42.74
    },
    "issues": []
  }
}
```

### File Search

#### POST /search

Search for files using natural language queries with optional LLM enhancement.

**Request Body:**

```json
{
  "query": "machine learning python notebooks",
  "directories": ["/Users/me/Projects"],
  "language": "en",
  "limit": 50,
  "use_llm": true
}
```

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| query | string | Yes | - | Natural language search query |
| directories | string[] | No | All monitored | Specific directories to search |
| language | string | No | "ko" | Query language (ko, en) |
| limit | integer | No | 10 | Maximum results (1-1000) |
| use_llm | boolean | No | true | Enable LLM-enhanced search |

**Response:**

```json
{
  "success": true,
  "count": 42,
  "results": [
    {
      "path": "/Users/me/Projects/ml-tutorial/notebook.ipynb",
      "name": "notebook.ipynb",
      "highlighted_name": "<mark>notebook</mark>.ipynb",
      "score": 0.95,
      "size": 125431,
      "modified_time": 1736432000,
      "created_time": 1736000000,
      "extension": ".ipynb",
      "category": "code",
      "snippet": "...machine <mark>learning</mark> algorithms...",
      "metadata": {
        "mime_type": "application/x-ipynb+json",
        "encoding": "utf-8"
      }
    }
  ],
  "method": "llm_enhanced",
  "query": "machine learning python notebooks",
  "search_time_ms": 373
}
```

**Error Codes:**

- `400` - Invalid query parameters
- `422` - Query validation failed
- `500` - Internal server error

#### POST /search_simple

Simplified search endpoint for debugging, bypasses LLM enhancement.

**Request Body:**

```json
{
  "query": "test",
  "directories": null,
  "limit": 10
}
```

### Quick Search

#### POST /quick-search

Fast search by category, extension, or recent files.

**Request Body:**

```json
{
  "category": "document",
  "extensions": [".pdf", ".docx"],
  "recentHours": 168,
  "limit": 50
}
```

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| category | string | No | - | File category filter |
| extensions | string[] | No | - | File extensions to include |
| recentHours | integer | No | 24 | Hours to look back |
| limit | integer | No | 50 | Maximum results |

**Categories:**
- `document` - PDF, DOC, DOCX, TXT, MD, RTF
- `image` - JPG, PNG, GIF, BMP, TIFF, WebP
- `video` - MP4, AVI, MOV, MKV, WebM
- `audio` - MP3, WAV, FLAC, AAC, OGG
- `code` - PY, JS, TS, JAVA, CPP, etc.
- `archive` - ZIP, RAR, 7Z, TAR, GZ
- `other` - All other files

### File Organization

#### POST /organize

Organize files using AI categorization or simple rules.

**Request Body:**

```json
{
  "sourceDir": "/Users/me/Downloads",
  "targetDir": "/Users/me/Downloads/Organized",
  "method": "content",
  "dryRun": true,
  "use_llm": true
}
```

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| sourceDir | string | Yes | - | Source directory path |
| targetDir | string | No | sourceDir/Organized | Target directory |
| method | string | No | "content" | Organization method |
| dryRun | boolean | No | false | Preview without moving |
| use_llm | boolean | No | true | Use AI for categorization |

**Methods:**
- `content` - AI-based content analysis
- `extension` - Group by file extension
- `date` - Organize by modification date
- `size` - Group by file size ranges

**Response (Synchronous - Simple):**

```json
{
  "success": true,
  "results": {
    "operations": [
      {
        "source": "/Users/me/Downloads/report.pdf",
        "target": "/Users/me/Downloads/Organized/Documents/report.pdf"
      }
    ],
    "count": 156
  },
  "method": "simple"
}
```

**Response (Asynchronous - LLM):**

```json
{
  "success": true,
  "message": "Organization started",
  "task_id": "organize_1736432000",
  "method": "llm_categorization"
}
```

### Background Tasks

#### GET /task/{task_id}

Check status of background organization tasks.

**Response:**

```json
{
  "status": "completed",
  "started_at": "2025-07-09T12:00:00Z",
  "completed_at": "2025-07-09T12:05:30Z",
  "progress": 100,
  "results": {
    "operations": 1523,
    "categories_created": 12,
    "errors": 0
  }
}
```

**Status Values:**
- `running` - Task in progress
- `completed` - Task finished successfully
- `failed` - Task failed with errors

### Recent Files

#### GET /recent

Get recently modified files.

**Query Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| hours | integer | No | 24 | Hours to look back |
| limit | integer | No | 50 | Maximum results |

**Example:**

```
GET /recent?hours=48&limit=100
```

**Response:**

```json
{
  "hours": 48,
  "count": 89,
  "files": [
    {
      "path": "/Users/me/Documents/report.docx",
      "name": "report.docx",
      "size": 45231,
      "modified_time": 1736430000,
      "category": "document"
    }
  ]
}
```

### Performance Metrics

#### GET /metrics

Get comprehensive system metrics.

**Response:**

```json
{
  "system": {
    "cpu_percent": 2.5,
    "memory_percent": 18.3,
    "disk_usage_percent": 42.7,
    "network_io": {
      "bytes_sent": 1024000,
      "bytes_recv": 2048000
    }
  },
  "application": {
    "uptime_seconds": 3600,
    "total_requests": 1523,
    "active_connections": 5,
    "background_tasks": 2
  },
  "database": {
    "total_files": 114549,
    "database_size_mb": 156.3,
    "cache_hit_rate": 0.85
  }
}
```

#### GET /metrics/database

Get database-specific metrics.

**Response:**

```json
{
  "connection_pool": {
    "active": 2,
    "idle": 8,
    "total": 10
  },
  "operations": {
    "searches_per_minute": 45,
    "indexing_rate": 1523,
    "cache_hit_rate": 0.85
  },
  "storage": {
    "database_size_mb": 156.3,
    "index_size_mb": 45.2,
    "cache_size_mb": 12.1
  }
}
```

#### GET /metrics/health

Get detailed health status.

**Response:**

```json
{
  "status": "healthy",
  "checks": {
    "database_connection": "pass",
    "disk_space": "pass",
    "memory_usage": "pass",
    "service_availability": "pass"
  },
  "system_metrics": {
    "cpu_percent": 2.5,
    "memory_percent": 18.3,
    "disk_free_gb": 125.4
  },
  "issues": []
}
```

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": "Error message",
  "method": "error",
  "details": {
    "code": "ERROR_CODE",
    "timestamp": "2025-07-09T12:00:00Z",
    "request_id": "uuid-here"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| INVALID_QUERY | 400 | Query parameter is missing or invalid |
| VALIDATION_ERROR | 422 | Request body validation failed |
| NOT_FOUND | 404 | Resource not found |
| INTERNAL_ERROR | 500 | Internal server error |
| SERVICE_UNAVAILABLE | 503 | Service temporarily unavailable |

## Rate Limiting

Currently, there are no rate limits. Future versions will implement:
- 1000 requests per minute per IP
- 100 concurrent connections
- 10MB maximum request size

## Webhooks (Planned)

Future versions will support webhooks for:
- File indexing completion
- Organization task completion
- Error notifications

## SDK Examples

### Python

```python
import requests

# Search files
response = requests.post('http://localhost:8001/search', json={
    'query': 'machine learning projects',
    'limit': 50,
    'use_llm': True
})

results = response.json()
for file in results['results']:
    print(f"{file['name']} - {file['path']}")
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

// Search files
async function searchFiles(query) {
  try {
    const response = await axios.post('http://localhost:8001/search', {
      query: query,
      limit: 50,
      use_llm: true
    });
    
    return response.data.results;
  } catch (error) {
    console.error('Search failed:', error);
  }
}

// Usage
const files = await searchFiles('python notebooks');
```

### cURL

```bash
# Search files
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "project documentation",
    "limit": 20,
    "use_llm": true
  }'

# Get recent files
curl "http://localhost:8001/recent?hours=48&limit=100"

# Check health
curl http://localhost:8001/health
```

## Best Practices

1. **Use LLM Enhancement Wisely**: Enable `use_llm` for natural language queries, disable for keyword searches
2. **Batch Operations**: Use background tasks for large file operations
3. **Monitor Health**: Regularly check `/health` endpoint
4. **Handle Errors**: Always check the `success` field in responses
5. **Pagination**: Use `limit` parameter to control response size

## Migration Guide

### From v1.x to v2.0

1. Update endpoint URLs:
   - `/api/search` → `/search`
   - `/api/organize` → `/organize`

2. Update request format:
   - Add `use_llm` parameter for search
   - Use `dryRun` instead of `preview`

3. Handle new response format:
   - Check `success` field
   - Results are in `results` array
   - Method information in `method` field

---

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>