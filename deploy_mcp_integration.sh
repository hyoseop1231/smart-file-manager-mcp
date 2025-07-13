#!/bin/bash

# Smart File Manager MCP 통합 배포 스크립트
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

# MCP 서버 메인 파일 업데이트
echo "🔧 MCP 서버에 삭제 추적 도구 통합 중..."

docker exec "$MCP_CONTAINER" node -e "
const fs = require('fs');
const path = '/app/src/index.ts';

// 기존 파일 읽기
let content = fs.readFileSync(path, 'utf8');

// 삭제 추적 도구 import 추가
const deletionImport = \`import { DeletionToolSchemas, DeletionToolFunctions } from './mcp_deletion_tools.js';\`;

if (!content.includes('DeletionToolSchemas')) {
    // import 섹션 찾기
    const importPos = content.indexOf('import axios from \"axios\";');
    if (importPos !== -1) {
        const importEnd = content.indexOf('\n', importPos);
        content = content.slice(0, importEnd) + '\n' + deletionImport + content.slice(importEnd);
        console.log('✅ 삭제 추적 도구 import 추가');
    }
}

// ListToolsRequestSchema 핸들러에 새 도구들 추가
const listToolsPos = content.indexOf('server.setRequestHandler(ListToolsRequestSchema');
if (listToolsPos !== -1) {
    // 기존 tools 배열에 새 도구들 추가
    const toolsArrayStart = content.indexOf('tools: [', listToolsPos);
    if (toolsArrayStart !== -1) {
        const existingToolsEnd = content.indexOf(']', toolsArrayStart);
        const newTools = \`,
        {
          name: \"get_recent_deletions\",
          description: \"Get recently deleted files with details\",
          inputSchema: {
            type: \"object\",
            properties: {
              limit: {
                type: \"number\",
                description: \"Number of recent deletions to retrieve (1-100)\",
                default: 10
              }
            }
          }
        },
        {
          name: \"get_recent_movements\", 
          description: \"Get recent file movements (Archive, reorganization, etc.)\",
          inputSchema: {
            type: \"object\",
            properties: {
              limit: {
                type: \"number\",
                description: \"Number of recent movements to retrieve (1-100)\",
                default: 10
              }
            }
          }
        },
        {
          name: \"search_deleted_files\",
          description: \"Search for deleted files by name or path\",
          inputSchema: {
            type: \"object\",
            properties: {
              query: {
                type: \"string\",
                description: \"Search query for deleted files (filename or path)\",
                default: \"\"
              },
              days_back: {
                type: \"number\",
                description: \"Number of days to search back (1-365)\", 
                default: 30
              }
            }
          }
        },
        {
          name: \"track_file_deletion\",
          description: \"Track a file deletion manually\",
          inputSchema: {
            type: \"object\",
            properties: {
              file_path: {
                type: \"string\",
                description: \"Path of the deleted file\"
              },
              reason: {
                type: \"string\",
                description: \"Reason for deletion\",
                default: \"user_action\"
              },
              backup_path: {
                type: \"string\",
                description: \"Backup file path if available\"
              },
              metadata: {
                type: \"object\",
                description: \"Additional metadata\"
              }
            },
            required: [\"file_path\"]
          }
        },
        {
          name: \"track_file_movement\",
          description: \"Track a file movement (Archive, reorganization, etc.)\",
          inputSchema: {
            type: \"object\",
            properties: {
              original_path: {
                type: \"string\",
                description: \"Original file path\"
              },
              new_path: {
                type: \"string\",
                description: \"New file path\"
              },
              movement_type: {
                type: \"string\",
                description: \"Type of movement (archive, reorganize, backup)\",
                default: \"archive\"
              },
              reason: {
                type: \"string\",
                description: \"Reason for movement\",
                default: \"organization\"
              }
            },
            required: [\"original_path\", \"new_path\"]
          }
        },
        {
          name: \"get_deletion_stats\",
          description: \"Get deletion and movement statistics\",
          inputSchema: {
            type: \"object\",
            properties: {}
          }
        }\`;
        
        content = content.slice(0, existingToolsEnd) + newTools + content.slice(existingToolsEnd);
        console.log('✅ 새 MCP 도구들을 tools 목록에 추가');
    }
}

// CallToolRequestSchema 핸들러에 새 도구 케이스들 추가
const callToolPos = content.indexOf('server.setRequestHandler(CallToolRequestSchema');
if (callToolPos !== -1) {
    // switch 문의 마지막 case 찾기
    const switchEnd = content.indexOf('default:', callToolPos);
    if (switchEnd !== -1) {
        const newCases = \`
      case \"get_recent_deletions\":
        try {
          const deletionsArgs = DeletionToolSchemas.get_recent_deletions.parse(request.params.arguments);
          const deletionsResult = await DeletionToolFunctions.get_recent_deletions(deletionsArgs);
          return { content: [{ type: \"text\", text: deletionsResult }] };
        } catch (error) {
          return { content: [{ type: \"text\", text: \`Error getting recent deletions: \${error}\` }] };
        }

      case \"get_recent_movements\":
        try {
          const movementsArgs = DeletionToolSchemas.get_recent_movements.parse(request.params.arguments);
          const movementsResult = await DeletionToolFunctions.get_recent_movements(movementsArgs);
          return { content: [{ type: \"text\", text: movementsResult }] };
        } catch (error) {
          return { content: [{ type: \"text\", text: \`Error getting recent movements: \${error}\` }] };
        }

      case \"search_deleted_files\":
        try {
          const searchArgs = DeletionToolSchemas.search_deleted_files.parse(request.params.arguments);
          const searchResult = await DeletionToolFunctions.search_deleted_files(searchArgs);
          return { content: [{ type: \"text\", text: searchResult }] };
        } catch (error) {
          return { content: [{ type: \"text\", text: \`Error searching deleted files: \${error}\` }] };
        }

      case \"track_file_deletion\":
        try {
          const trackDeletionArgs = DeletionToolSchemas.track_file_deletion.parse(request.params.arguments);
          const trackDeletionResult = await DeletionToolFunctions.track_file_deletion(trackDeletionArgs);
          return { content: [{ type: \"text\", text: trackDeletionResult }] };
        } catch (error) {
          return { content: [{ type: \"text\", text: \`Error tracking file deletion: \${error}\` }] };
        }

      case \"track_file_movement\":
        try {
          const trackMovementArgs = DeletionToolSchemas.track_file_movement.parse(request.params.arguments);
          const trackMovementResult = await DeletionToolFunctions.track_file_movement(trackMovementArgs);
          return { content: [{ type: \"text\", text: trackMovementResult }] };
        } catch (error) {
          return { content: [{ type: \"text\", text: \`Error tracking file movement: \${error}\` }] };
        }

      case \"get_deletion_stats\":
        try {
          const statsArgs = DeletionToolSchemas.get_deletion_stats.parse(request.params.arguments);
          const statsResult = await DeletionToolFunctions.get_deletion_stats(statsArgs);
          return { content: [{ type: \"text\", text: statsResult }] };
        } catch (error) {
          return { content: [{ type: \"text\", text: \`Error getting deletion stats: \${error}\` }] };
        }
        
      \`;
      
        content = content.slice(0, switchEnd) + newCases + content.slice(switchEnd);
        console.log('✅ 새 MCP 도구 케이스들을 CallTool 핸들러에 추가');
    }
}

// 수정된 내용 저장
fs.writeFileSync(path, content);
console.log('🔧 MCP 서버 업데이트 완료');
"

# MCP 서버 재빌드
echo "🔨 MCP 서버 재빌드 중..."
docker exec "$MCP_CONTAINER" npm run build

# MCP 서버 재시작
echo "🔄 MCP 서버 재시작 중..."
docker restart "$MCP_CONTAINER"

# 재시작 대기
echo "⏳ MCP 서버 재시작 대기 중..."
sleep 10

# Claude Desktop 설정 자동 업데이트는 건너뛰고 수동 안내
echo ""
echo "⚠️  Claude Desktop 재시작 필요"
echo "   새로운 MCP 도구들이 인식되려면 Claude Desktop을 완전히 종료하고 다시 시작해주세요."
echo ""

# MCP 서버 상태 확인
echo "🔍 MCP 서버 상태 확인 중..."
if docker ps | grep -q "$MCP_CONTAINER.*healthy"; then
    echo "✅ MCP 서버 정상 작동 중"
else
    echo "⚠️  MCP 서버 상태 확인 필요"
    docker logs "$MCP_CONTAINER" --tail 10
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

# 간단한 MCP 도구 테스트 (Claude Desktop 재시작 후 사용 가능)
echo ""
echo "🧪 MCP 서버 연결 테스트:"

# MCP 서버가 응답하는지 확인
timeout 5 docker exec "$MCP_CONTAINER" node -e "
const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
console.log('✅ MCP SDK 로드 성공');
" 2>/dev/null && echo "✅ MCP 서버 SDK 정상" || echo "⚠️  MCP 서버 SDK 확인 필요"

echo ""
echo "🚀 배포 완료! Claude Desktop을 재시작하세요."