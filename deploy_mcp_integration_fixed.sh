#!/bin/bash

# Smart File Manager MCP 통합 배포 스크립트 (수정된 버전)
# Claude Desktop 및 Claude Code CLI와의 완전 연동

set -e

echo "🚀 Smart File Manager MCP 통합 배포 시작..."

# 변수 설정
MCP_CONTAINER="smart-file-mcp-server"
SOURCE_DIR="/Users/hyoseop1231/Desktop/05_Tools_도구_🛠️/smart-file-manager"
BACKUP_DIR="$SOURCE_DIR/mcp_backup_$(date +%Y%m%d_%H%M%S)"

# 백업 디렉토리 생성
echo "📦 기존 MCP 서버 설정 백업 중..."
mkdir -p "$BACKUP_DIR"

# MCP 컨테이너 확인
if docker ps | grep -q "$MCP_CONTAINER"; then
    echo "✅ Smart File Manager MCP 서버 발견: $MCP_CONTAINER"
    
    # 기존 파일 백업
    docker cp "$MCP_CONTAINER:/app/src/index.ts" "$BACKUP_DIR/index.ts.backup" 2>/dev/null || echo "⚠️  index.ts 백업 실패"
    
else
    echo "❌ Smart File Manager MCP 서버를 찾을 수 없습니다: $MCP_CONTAINER"
    exit 1
fi

# 새 삭제 추적 도구 모듈 복사
echo "📁 삭제 추적 MCP 도구 모듈 복사 중..."
docker cp "$SOURCE_DIR/mcp_deletion_tools.ts" "$MCP_CONTAINER:/app/src/"
echo "✅ mcp_deletion_tools.ts 복사 완료"

# 수정된 index.ts 파일을 직접 생성
echo "🔧 새로운 index.ts 파일 생성 중..."

# 임시 파일에 새로운 index.ts 작성
cat > "/tmp/new_index.ts" << 'EOF'
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import axios from "axios";
import { DeletionToolSchemas, DeletionToolFunctions } from './mcp_deletion_tools.js';

// 기존 Tool schemas (유지)
const SearchFilesSchema = z.object({
  query: z.string().describe("Search query in natural language"),
  directories: z.array(z.string()).optional().describe("Directories to search in"),
  language: z.string().optional().default("ko").describe("Language for search"),
  limit: z.number().optional().default(10).describe("Maximum number of results"),
}).transform((data) => ({
  ...data,
  directories: data.directories && data.directories.length > 0 ? data.directories : undefined,
}));

const QuickSearchSchema = z.object({
  category: z.enum(["image", "video", "audio", "document", "code", "archive", "other"]).optional(),
  extensions: z.array(z.string()).optional(),
  recentHours: z.number().optional(),
  limit: z.number().optional().default(50),
});

const OrganizeFilesSchema = z.object({
  sourceDir: z.string().describe("Source directory to organize"),
  targetDir: z.string().optional().describe("Target directory for organized files"),
  method: z.enum(["content", "date", "type"]).describe("Organization method"),
  dryRun: z.boolean().optional().default(false).describe("Preview mode without actual changes"),
});

const SmartWorkflowSchema = z.object({
  searchQuery: z.string().describe("Search query to find files"),
  action: z.enum(["organize", "analyze", "rename"]).describe("Action to perform on found files"),
  options: z.record(z.any()).optional().describe("Additional options for the action"),
});

const AnalyzeFileSchema = z.object({
  filePath: z.string().describe("Path to the file to analyze"),
  analysisType: z.enum(["content", "metadata", "vision", "smart"]).optional().default("smart").describe("Type of analysis to perform"),
});

const SystemStatusSchema = z.object({
  detailed: z.boolean().optional().default(false).describe("Get detailed system metrics"),
});

// API Base URLs
const BASE_URL = "http://host.docker.internal:8001";
const API_ENDPOINTS = {
  search: `${BASE_URL}/api/search`,
  organize: `${BASE_URL}/api/organize`,
  workflow: `${BASE_URL}/api/workflow`,
  analyze: `${BASE_URL}/api/analyze`,
  health: `${BASE_URL}/health`,
  metrics: `${BASE_URL}/api/metrics`,
};

// Server 인스턴스 생성
const server = new Server(
  {
    name: "smart-file-manager",
    version: "2.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Tools 목록 핸들러
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "search_files",
        description: "Search and filter files using natural language queries with AI-powered analysis",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "Search query in natural language (e.g., 'find large video files', 'recent Python files')"
            },
            directories: {
              type: "array",
              items: { type: "string" },
              description: "Specific directories to search in (optional)"
            },
            language: {
              type: "string",
              description: "Language for search results and analysis (default: ko)",
              default: "ko"
            },
            limit: {
              type: "number",
              description: "Maximum number of results to return",
              default: 10
            }
          },
          required: ["query"]
        }
      },
      {
        name: "quick_search",
        description: "Quick file search by category, extension, or recent activity",
        inputSchema: {
          type: "object",
          properties: {
            category: {
              type: "string",
              enum: ["image", "video", "audio", "document", "code", "archive", "other"],
              description: "File category to search for"
            },
            extensions: {
              type: "array",
              items: { type: "string" },
              description: "File extensions to filter by (e.g., ['.jpg', '.png'])"
            },
            recentHours: {
              type: "number",
              description: "Find files modified within this many hours"
            },
            limit: {
              type: "number",
              description: "Maximum number of results",
              default: 50
            }
          }
        }
      },
      {
        name: "organize_files",
        description: "Organize files using AI-powered categorization and smart folder structures",
        inputSchema: {
          type: "object",
          properties: {
            sourceDir: {
              type: "string",
              description: "Source directory to organize"
            },
            targetDir: {
              type: "string",
              description: "Target directory for organized files (optional)"
            },
            method: {
              type: "string",
              enum: ["content", "date", "type"],
              description: "Organization method: content (AI analysis), date (by modification time), type (by file extension)"
            },
            dryRun: {
              type: "boolean",
              description: "Preview mode - show what would be done without making changes",
              default: false
            }
          },
          required: ["sourceDir", "method"]
        }
      },
      {
        name: "smart_workflow",
        description: "Execute smart workflows that combine search, analysis, and organization",
        inputSchema: {
          type: "object",
          properties: {
            searchQuery: {
              type: "string",
              description: "Query to find files for the workflow"
            },
            action: {
              type: "string",
              enum: ["organize", "analyze", "rename"],
              description: "Action to perform on found files"
            },
            options: {
              type: "object",
              description: "Additional options for the workflow action"
            }
          },
          required: ["searchQuery", "action"]
        }
      },
      {
        name: "analyze_file",
        description: "Analyze file content, metadata, or perform vision analysis on images",
        inputSchema: {
          type: "object",
          properties: {
            filePath: {
              type: "string",
              description: "Path to the file to analyze"
            },
            analysisType: {
              type: "string",
              enum: ["content", "metadata", "vision", "smart"],
              description: "Type of analysis: content (text analysis), metadata (file properties), vision (image analysis), smart (automatic selection)",
              default: "smart"
            }
          },
          required: ["filePath"]
        }
      },
      {
        name: "get_system_status",
        description: "Get Smart File Manager system status, health metrics, and performance data",
        inputSchema: {
          type: "object",
          properties: {
            detailed: {
              type: "boolean",
              description: "Include detailed system metrics and performance data",
              default: false
            }
          }
        }
      },
      {
        name: "get_recent_deletions",
        description: "Get recently deleted files with details",
        inputSchema: {
          type: "object",
          properties: {
            limit: {
              type: "number",
              description: "Number of recent deletions to retrieve (1-100)",
              default: 10
            }
          }
        }
      },
      {
        name: "get_recent_movements", 
        description: "Get recent file movements (Archive, reorganization, etc.)",
        inputSchema: {
          type: "object",
          properties: {
            limit: {
              type: "number",
              description: "Number of recent movements to retrieve (1-100)",
              default: 10
            }
          }
        }
      },
      {
        name: "search_deleted_files",
        description: "Search for deleted files by name or path",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "Search query for deleted files (filename or path)",
              default: ""
            },
            days_back: {
              type: "number",
              description: "Number of days to search back (1-365)", 
              default: 30
            }
          }
        }
      },
      {
        name: "track_file_deletion",
        description: "Track a file deletion manually",
        inputSchema: {
          type: "object",
          properties: {
            file_path: {
              type: "string",
              description: "Path of the deleted file"
            },
            reason: {
              type: "string",
              description: "Reason for deletion",
              default: "user_action"
            },
            backup_path: {
              type: "string",
              description: "Backup file path if available"
            },
            metadata: {
              type: "object",
              description: "Additional metadata"
            }
          },
          required: ["file_path"]
        }
      },
      {
        name: "track_file_movement",
        description: "Track a file movement (Archive, reorganization, etc.)",
        inputSchema: {
          type: "object",
          properties: {
            original_path: {
              type: "string",
              description: "Original file path"
            },
            new_path: {
              type: "string",
              description: "New file path"
            },
            movement_type: {
              type: "string",
              description: "Type of movement (archive, reorganize, backup)",
              default: "archive"
            },
            reason: {
              type: "string",
              description: "Reason for movement",
              default: "organization"
            }
          },
          required: ["original_path", "new_path"]
        }
      },
      {
        name: "get_deletion_stats",
        description: "Get deletion and movement statistics",
        inputSchema: {
          type: "object",
          properties: {}
        }
      }
    ]
  };
});

// Tool 실행 핸들러
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "search_files":
        try {
          const searchArgs = SearchFilesSchema.parse(args);
          const response = await axios.post(API_ENDPOINTS.search, searchArgs, {
            timeout: 30000,
            headers: { 'Content-Type': 'application/json' }
          });
          return { content: [{ type: "text", text: JSON.stringify(response.data, null, 2) }] };
        } catch (error: any) {
          return { content: [{ type: "text", text: `Search error: ${error.message}` }] };
        }

      case "quick_search":
        try {
          const quickArgs = QuickSearchSchema.parse(args);
          const response = await axios.post(`${API_ENDPOINTS.search}/quick`, quickArgs, {
            timeout: 15000,
            headers: { 'Content-Type': 'application/json' }
          });
          return { content: [{ type: "text", text: JSON.stringify(response.data, null, 2) }] };
        } catch (error: any) {
          return { content: [{ type: "text", text: `Quick search error: ${error.message}` }] };
        }

      case "organize_files":
        try {
          const organizeArgs = OrganizeFilesSchema.parse(args);
          const response = await axios.post(API_ENDPOINTS.organize, organizeArgs, {
            timeout: 60000,
            headers: { 'Content-Type': 'application/json' }
          });
          return { content: [{ type: "text", text: JSON.stringify(response.data, null, 2) }] };
        } catch (error: any) {
          return { content: [{ type: "text", text: `Organization error: ${error.message}` }] };
        }

      case "smart_workflow":
        try {
          const workflowArgs = SmartWorkflowSchema.parse(args);
          const response = await axios.post(API_ENDPOINTS.workflow, workflowArgs, {
            timeout: 90000,
            headers: { 'Content-Type': 'application/json' }
          });
          return { content: [{ type: "text", text: JSON.stringify(response.data, null, 2) }] };
        } catch (error: any) {
          return { content: [{ type: "text", text: `Workflow error: ${error.message}` }] };
        }

      case "analyze_file":
        try {
          const analyzeArgs = AnalyzeFileSchema.parse(args);
          const response = await axios.post(API_ENDPOINTS.analyze, analyzeArgs, {
            timeout: 30000,
            headers: { 'Content-Type': 'application/json' }
          });
          return { content: [{ type: "text", text: JSON.stringify(response.data, null, 2) }] };
        } catch (error: any) {
          return { content: [{ type: "text", text: `Analysis error: ${error.message}` }] };
        }

      case "get_system_status":
        try {
          const statusArgs = SystemStatusSchema.parse(args);
          const healthResponse = await axios.get(API_ENDPOINTS.health, { timeout: 10000 });
          
          if (statusArgs.detailed) {
            const metricsResponse = await axios.get(API_ENDPOINTS.metrics, { timeout: 10000 });
            return { 
              content: [{ 
                type: "text", 
                text: JSON.stringify({
                  health: healthResponse.data,
                  metrics: metricsResponse.data
                }, null, 2) 
              }] 
            };
          } else {
            return { content: [{ type: "text", text: JSON.stringify(healthResponse.data, null, 2) }] };
          }
        } catch (error: any) {
          return { content: [{ type: "text", text: `System status error: ${error.message}` }] };
        }

      case "get_recent_deletions":
        try {
          const deletionsArgs = DeletionToolSchemas.get_recent_deletions.parse(args);
          const deletionsResult = await DeletionToolFunctions.get_recent_deletions(deletionsArgs);
          return { content: [{ type: "text", text: deletionsResult }] };
        } catch (error: any) {
          return { content: [{ type: "text", text: `Error getting recent deletions: ${error.message}` }] };
        }

      case "get_recent_movements":
        try {
          const movementsArgs = DeletionToolSchemas.get_recent_movements.parse(args);
          const movementsResult = await DeletionToolFunctions.get_recent_movements(movementsArgs);
          return { content: [{ type: "text", text: movementsResult }] };
        } catch (error: any) {
          return { content: [{ type: "text", text: `Error getting recent movements: ${error.message}` }] };
        }

      case "search_deleted_files":
        try {
          const searchArgs = DeletionToolSchemas.search_deleted_files.parse(args);
          const searchResult = await DeletionToolFunctions.search_deleted_files(searchArgs);
          return { content: [{ type: "text", text: searchResult }] };
        } catch (error: any) {
          return { content: [{ type: "text", text: `Error searching deleted files: ${error.message}` }] };
        }

      case "track_file_deletion":
        try {
          const trackDeletionArgs = DeletionToolSchemas.track_file_deletion.parse(args);
          const trackDeletionResult = await DeletionToolFunctions.track_file_deletion(trackDeletionArgs);
          return { content: [{ type: "text", text: trackDeletionResult }] };
        } catch (error: any) {
          return { content: [{ type: "text", text: `Error tracking file deletion: ${error.message}` }] };
        }

      case "track_file_movement":
        try {
          const trackMovementArgs = DeletionToolSchemas.track_file_movement.parse(args);
          const trackMovementResult = await DeletionToolFunctions.track_file_movement(trackMovementArgs);
          return { content: [{ type: "text", text: trackMovementResult }] };
        } catch (error: any) {
          return { content: [{ type: "text", text: `Error tracking file movement: ${error.message}` }] };
        }

      case "get_deletion_stats":
        try {
          const statsArgs = DeletionToolSchemas.get_deletion_stats.parse(args);
          const statsResult = await DeletionToolFunctions.get_deletion_stats(statsArgs);
          return { content: [{ type: "text", text: statsResult }] };
        } catch (error: any) {
          return { content: [{ type: "text", text: `Error getting deletion stats: ${error.message}` }] };
        }
        
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error: any) {
    return {
      content: [{ type: "text", text: `Error: ${error.message}` }],
      isError: true,
    };
  }
});

// Server 시작
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Smart File Manager MCP Server v2.1.0 with Deletion Tracking running...");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
EOF

# 새로운 index.ts 파일 복사
echo "📝 새로운 index.ts 파일 배포 중..."
docker cp "/tmp/new_index.ts" "$MCP_CONTAINER:/app/src/index.ts"
echo "✅ 새로운 index.ts 파일 배포 완료"

# 임시 파일 정리
rm "/tmp/new_index.ts"

# MCP 서버 재빌드
echo "🔨 MCP 서버 재빌드 중..."
docker exec "$MCP_CONTAINER" npm run build

# MCP 서버 재시작
echo "🔄 MCP 서버 재시작 중..."
docker restart "$MCP_CONTAINER"

# 재시작 대기
echo "⏳ MCP 서버 재시작 대기 중..."
sleep 15

# MCP 서버 상태 확인
echo "🔍 MCP 서버 상태 확인 중..."
if docker ps | grep -q "$MCP_CONTAINER.*healthy"; then
    echo "✅ MCP 서버 정상 작동 중"
else
    echo "⚠️  MCP 서버 상태 확인 중..."
    docker logs "$MCP_CONTAINER" --tail 5
fi

echo ""
echo "🎉 Smart File Manager MCP 통합 배포 완료!"
echo ""
echo "📋 새로 추가된 MCP 도구들:"
echo "   🗑️  get_recent_deletions - 최근 삭제된 파일 조회"
echo "   📦 get_recent_movements - 최근 파일 이동 기록 조회"
echo "   🔍 search_deleted_files - 삭제된 파일 검색"
echo "   📝 track_file_deletion - 파일 삭제 추적 등록"
echo "   📝 track_file_movement - 파일 이동 추적 등록"
echo "   📊 get_deletion_stats - 삭제/이동 통계 조회"
echo ""
echo "🎯 이제 Claude Desktop에서 다음과 같이 요청할 수 있습니다:"
echo '   "최근 삭제된 파일 5개만 보여줘"'
echo '   "Archive로 이동한 파일들 보여줘"'
echo '   "삭제 통계 알려줘"'
echo '   "processed_files로 시작하는 삭제된 파일 찾아줘"'
echo ""
echo "📁 백업 위치: $BACKUP_DIR"
echo ""
echo "🔄 다음 단계:"
echo "   1. Claude Desktop 완전 종료 및 재시작"
echo "   2. 새로운 MCP 도구들 테스트"
echo ""
echo "🚀 배포 완료! Claude Desktop을 재시작하세요."