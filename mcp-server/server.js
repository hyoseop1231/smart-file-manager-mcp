#!/usr/bin/env node

/**
 * Smart File Manager MCP Server
 * Model Context Protocol server for Claude Desktop integration
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const axios = require('axios');
const fs = require('fs-extra');
const path = require('path');
const mimeTypes = require('mime-types');

// 환경 변수 설정
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8001';
const WATCH_DIRECTORIES = process.env.WATCH_DIRECTORIES || '/watch_directories';

// MCP 서버 인스턴스 생성
const server = new Server(
  {
    name: 'smart-file-manager-mcp',
    version: '4.0.2',
  },
  {
    capabilities: {
      tools: {},
      resources: {},
    },
  }
);

// API 클라이언트 설정
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 도구 목록 정의
server.setRequestHandler('tools/list', async () => {
  return {
    tools: [
      {
        name: 'search_files',
        description: 'Search for files using multimedia content analysis',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: 'Search query text',
            },
            media_types: {
              type: 'array',
              items: { type: 'string' },
              description: 'Filter by media types (image, video, audio, document, text)',
            },
            limit: {
              type: 'number',
              description: 'Maximum number of results (default: 20)',
              default: 20,
            },
          },
          required: ['query'],
        },
      },
      {
        name: 'analyze_file',
        description: 'Analyze a file using AI (vision, speech recognition, etc.)',
        inputSchema: {
          type: 'object',
          properties: {
            file_path: {
              type: 'string',
              description: 'Path to the file to analyze',
            },
            analysis_type: {
              type: 'string',
              enum: ['auto', 'image', 'video', 'audio', 'document'],
              description: 'Type of analysis to perform',
              default: 'auto',
            },
          },
          required: ['file_path'],
        },
      },
      {
        name: 'get_file_info',
        description: 'Get detailed information about a file',
        inputSchema: {
          type: 'object',
          properties: {
            file_path: {
              type: 'string',
              description: 'Path to the file',
            },
          },
          required: ['file_path'],
        },
      },
      {
        name: 'get_system_stats',
        description: 'Get system statistics and multimedia capabilities',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'cleanup_disk',
        description: 'Clean up disk space by removing old thumbnails and temp files',
        inputSchema: {
          type: 'object',
          properties: {
            cleanup_type: {
              type: 'string',
              enum: ['thumbnails', 'temp', 'all'],
              description: 'Type of cleanup to perform',
              default: 'thumbnails',
            },
            days: {
              type: 'number',
              description: 'Remove files older than this many days',
              default: 30,
            },
          },
        },
      },
    ],
  };
});

// 도구 호출 핸들러
server.setRequestHandler('tools/call', async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'search_files':
        return await handleSearchFiles(args);
      case 'analyze_file':
        return await handleAnalyzeFile(args);
      case 'get_file_info':
        return await handleGetFileInfo(args);
      case 'get_system_stats':
        return await handleGetSystemStats(args);
      case 'cleanup_disk':
        return await handleCleanupDisk(args);
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// 파일 검색 핸들러
async function handleSearchFiles(args) {
  const { query, media_types = [], limit = 20 } = args;

  try {
    const response = await apiClient.post('/search/multimedia', {
      query,
      media_types,
      limit,
      include_ai_analysis: false,
    });

    const results = response.data.results || [];
    
    if (results.length === 0) {
      return {
        content: [
          {
            type: 'text',
            text: `No files found for query: "${query}"`,
          },
        ],
      };
    }

    const formattedResults = results.map((file, index) => {
      return `${index + 1}. **${file.name}**
   - Path: ${file.path}
   - Size: ${(file.size / 1024 / 1024).toFixed(2)} MB
   - Type: ${file.media_type} / ${file.category}
   - Score: ${(file.score * 100).toFixed(1)}%
   - Modified: ${new Date(file.modified_time * 1000).toLocaleString()}`;
    }).join('\n\n');

    return {
      content: [
        {
          type: 'text',
          text: `Found ${results.length} files matching "${query}":\n\n${formattedResults}`,
        },
      ],
    };
  } catch (error) {
    throw new Error(`Search failed: ${error.message}`);
  }
}

// 파일 분석 핸들러
async function handleAnalyzeFile(args) {
  const { file_path, analysis_type = 'auto' } = args;

  try {
    const response = await apiClient.post('/ai/analyze', {
      file_path,
      analysis_type,
    });

    const results = response.data.results || {};
    let analysisText = `Analysis of: ${file_path}\n\n`;

    if (results.image_analysis) {
      analysisText += `**Image Analysis:**\n`;
      analysisText += `- Description: ${results.image_analysis.description || 'N/A'}\n`;
      analysisText += `- Objects: ${results.image_analysis.objects?.join(', ') || 'N/A'}\n`;
      analysisText += `- Text: ${results.image_analysis.text || 'N/A'}\n\n`;
    }

    if (results.speech_analysis) {
      analysisText += `**Speech Analysis:**\n`;
      analysisText += `- Transcript: ${results.speech_analysis.transcript || 'N/A'}\n`;
      analysisText += `- Language: ${results.speech_analysis.language || 'N/A'}\n\n`;
    }

    if (results.metadata) {
      analysisText += `**Metadata:**\n`;
      Object.entries(results.metadata).forEach(([key, value]) => {
        analysisText += `- ${key}: ${value}\n`;
      });
    }

    return {
      content: [
        {
          type: 'text',
          text: analysisText,
        },
      ],
    };
  } catch (error) {
    throw new Error(`Analysis failed: ${error.message}`);
  }
}

// 파일 정보 핸들러
async function handleGetFileInfo(args) {
  const { file_path } = args;

  try {
    const fullPath = path.join(WATCH_DIRECTORIES, file_path);
    
    if (!await fs.pathExists(fullPath)) {
      throw new Error(`File not found: ${file_path}`);
    }

    const stats = await fs.stat(fullPath);
    const mimeType = mimeTypes.lookup(fullPath) || 'unknown';

    const fileInfo = {
      name: path.basename(fullPath),
      path: file_path,
      size: stats.size,
      sizeFormatted: `${(stats.size / 1024 / 1024).toFixed(2)} MB`,
      mimeType,
      created: stats.ctime.toISOString(),
      modified: stats.mtime.toISOString(),
      isDirectory: stats.isDirectory(),
      isFile: stats.isFile(),
    };

    const infoText = `**File Information:**
- Name: ${fileInfo.name}
- Path: ${fileInfo.path}
- Size: ${fileInfo.sizeFormatted} (${fileInfo.size} bytes)
- MIME Type: ${fileInfo.mimeType}
- Created: ${new Date(fileInfo.created).toLocaleString()}
- Modified: ${new Date(fileInfo.modified).toLocaleString()}
- Type: ${fileInfo.isDirectory ? 'Directory' : 'File'}`;

    return {
      content: [
        {
          type: 'text',
          text: infoText,
        },
      ],
    };
  } catch (error) {
    throw new Error(`Failed to get file info: ${error.message}`);
  }
}

// 시스템 통계 핸들러
async function handleGetSystemStats(args) {
  try {
    const response = await apiClient.get('/stats/multimedia');
    const stats = response.data;

    let statsText = `**Smart File Manager System Statistics:**\n\n`;
    
    if (stats.indexer_statistics) {
      statsText += `**File Index:**\n`;
      statsText += `- Total Files: ${stats.indexer_statistics.total_files.toLocaleString()}\n`;
      
      if (stats.indexer_statistics.by_category) {
        statsText += `\n**By Category:**\n`;
        Object.entries(stats.indexer_statistics.by_category).forEach(([category, data]) => {
          statsText += `- ${category}: ${data.count?.toLocaleString() || 0} files (${data.size_gb?.toFixed(2) || 0} GB)\n`;
        });
      }
    }

    if (stats.multimedia_capabilities) {
      statsText += `\n**Multimedia Capabilities:**\n`;
      if (stats.multimedia_capabilities.supported_extensions) {
        const extensions = stats.multimedia_capabilities.supported_extensions;
        statsText += `- Images: ${extensions.images?.length || 0} formats\n`;
        statsText += `- Videos: ${extensions.videos?.length || 0} formats\n`;
        statsText += `- Audio: ${extensions.audio?.length || 0} formats\n`;
      }
    }

    return {
      content: [
        {
          type: 'text',
          text: statsText,
        },
      ],
    };
  } catch (error) {
    throw new Error(`Failed to get system stats: ${error.message}`);
  }
}

// 디스크 정리 핸들러
async function handleCleanupDisk(args) {
  const { cleanup_type = 'thumbnails', days = 30 } = args;

  try {
    let endpoint;
    switch (cleanup_type) {
      case 'thumbnails':
        endpoint = `/disk/cleanup/thumbnails?days=${days}`;
        break;
      case 'temp':
        endpoint = '/disk/cleanup/temp';
        break;
      case 'all':
        // 순차적으로 모든 정리 수행
        const thumbnailResponse = await apiClient.post(`/disk/cleanup/thumbnails?days=${days}`);
        const tempResponse = await apiClient.post('/disk/cleanup/temp');
        
        const totalCleaned = thumbnailResponse.data.cleaned_bytes + tempResponse.data.cleaned_bytes;
        const totalFiles = thumbnailResponse.data.cleaned_files + tempResponse.data.cleaned_files;
        
        return {
          content: [
            {
              type: 'text',
              text: `**Disk Cleanup Complete:**
- Cleaned Files: ${totalFiles}
- Space Freed: ${(totalCleaned / 1024 / 1024).toFixed(2)} MB
- Thumbnails: ${thumbnailResponse.data.cleaned_files} files
- Temp Files: ${tempResponse.data.cleaned_files} files`,
            },
          ],
        };
      default:
        throw new Error(`Unknown cleanup type: ${cleanup_type}`);
    }

    const response = await apiClient.post(endpoint);
    const result = response.data;

    const cleanupText = `**Disk Cleanup Complete:**
- Cleanup Type: ${cleanup_type}
- Files Cleaned: ${result.cleaned_files}
- Space Freed: ${(result.cleaned_bytes / 1024 / 1024).toFixed(2)} MB
- Current Disk Usage: ${result.disk_usage_after?.usage_percent?.toFixed(1)}%`;

    return {
      content: [
        {
          type: 'text',
          text: cleanupText,
        },
      ],
    };
  } catch (error) {
    throw new Error(`Cleanup failed: ${error.message}`);
  }
}

// 리소스 목록 핸들러
server.setRequestHandler('resources/list', async () => {
  return {
    resources: [
      {
        uri: 'file://watch_directories',
        name: 'Watch Directories',
        description: 'Access to monitored file directories',
        mimeType: 'inode/directory',
      },
    ],
  };
});

// 서버 시작
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Smart File Manager MCP Server running on stdio');
}

// 오류 처리
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

// 서버 시작
main().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});