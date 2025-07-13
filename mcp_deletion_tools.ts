import { z } from "zod";
import axios from "axios";

// 삭제 추적 관련 MCP 도구 스키마 정의

// 최근 삭제된 파일 조회 스키마
const GetRecentDeletionsSchema = z.object({
  limit: z.number().optional().default(10).describe("Number of recent deletions to retrieve (1-100)"),
});

// 최근 파일 이동 조회 스키마  
const GetRecentMovementsSchema = z.object({
  limit: z.number().optional().default(10).describe("Number of recent movements to retrieve (1-100)"),
});

// 삭제된 파일 검색 스키마
const SearchDeletedFilesSchema = z.object({
  query: z.string().optional().default("").describe("Search query for deleted files (filename or path)"),
  days_back: z.number().optional().default(30).describe("Number of days to search back (1-365)"),
});

// 파일 삭제 추적 등록 스키마
const TrackFileDeletionSchema = z.object({
  file_path: z.string().describe("Path of the deleted file"),
  reason: z.string().optional().default("user_action").describe("Reason for deletion"),
  backup_path: z.string().optional().describe("Backup file path if available"),
  metadata: z.record(z.any()).optional().describe("Additional metadata"),
});

// 파일 이동 추적 등록 스키마
const TrackFileMovementSchema = z.object({
  original_path: z.string().describe("Original file path"),
  new_path: z.string().describe("New file path"),
  movement_type: z.string().optional().default("archive").describe("Type of movement (archive, reorganize, backup)"),
  reason: z.string().optional().default("organization").describe("Reason for movement"),
});

// 삭제 통계 조회 스키마 (파라미터 없음)
const GetDeletionStatsSchema = z.object({});

// MCP 도구 구현 함수들

// API 베이스 URL
const API_BASE_URL = "http://localhost:8001/api/deletion";

/**
 * 최근 삭제된 파일 조회
 */
export async function getRecentDeletions(args: z.infer<typeof GetRecentDeletionsSchema>) {
  try {
    const response = await axios.get(`${API_BASE_URL}/deleted-files`, {
      params: { limit: args.limit },
      timeout: 5000
    });

    const data = response.data;
    
    if (data.recent_deletions && data.recent_deletions.length > 0) {
      let result = `📁 최근 삭제된 파일 ${data.total_count}개:\n\n`;
      
      data.recent_deletions.forEach((file: any, index: number) => {
        result += `${index + 1}. **${file.filename}**\n`;
        result += `   📍 원본 경로: ${file.original_path}\n`;
        result += `   🗓️  삭제 시간: ${file.deleted_at}\n`;
        result += `   💾 크기: ${file.size_mb}MB\n`;
        result += `   🔄 복구 가능: ${file.recoverable ? '✅ 예' : '❌ 아니오'}\n\n`;
      });
      
      return result;
    } else {
      return "📁 최근 삭제된 파일이 없습니다.";
    }
    
  } catch (error: any) {
    console.error("Recent deletions API error:", error);
    return `❌ 최근 삭제된 파일 조회 실패: ${error.message}`;
  }
}

/**
 * 최근 파일 이동 기록 조회
 */
export async function getRecentMovements(args: z.infer<typeof GetRecentMovementsSchema>) {
  try {
    const response = await axios.get(`${API_BASE_URL}/recent-movements`, {
      params: { limit: args.limit },
      timeout: 5000
    });

    const data = response.data;
    
    if (data.movements && data.movements.length > 0) {
      let result = `📦 최근 파일 이동 기록 ${data.count}개:\n\n`;
      
      data.movements.forEach((movement: any, index: number) => {
        result += `${index + 1}. **${movement.filename}**\n`;
        result += `   📂 이동 타입: ${movement.movement_type}\n`;
        result += `   📍 원본: ${movement.original_path}\n`;
        result += `   📍 새 위치: ${movement.new_path}\n`;
        result += `   🗓️  이동 시간: ${movement.moved_at}\n`;
        result += `   💡 이유: ${movement.reason}\n\n`;
      });
      
      return result;
    } else {
      return "📦 최근 파일 이동 기록이 없습니다.";
    }
    
  } catch (error: any) {
    console.error("Recent movements API error:", error);
    return `❌ 최근 파일 이동 기록 조회 실패: ${error.message}`;
  }
}

/**
 * 삭제된 파일 검색
 */
export async function searchDeletedFiles(args: z.infer<typeof SearchDeletedFilesSchema>) {
  try {
    const response = await axios.post(`${API_BASE_URL}/search-deleted`, {
      query: args.query,
      days_back: args.days_back
    }, {
      headers: { 'Content-Type': 'application/json' },
      timeout: 5000
    });

    const data = response.data;
    
    if (data.deleted_files && data.deleted_files.length > 0) {
      let result = `🔍 검색 결과: "${args.query}" (${args.days_back}일 이내)\n`;
      result += `📁 총 ${data.count}개 파일 발견:\n\n`;
      
      data.deleted_files.forEach((file: any, index: number) => {
        result += `${index + 1}. **${file.filename}**\n`;
        result += `   📍 원본 경로: ${file.original_path}\n`;
        result += `   🗓️  삭제 시간: ${file.deleted_at}\n`;
        result += `   💾 크기: ${Math.round(file.file_size / (1024*1024) * 100) / 100}MB\n`;
        result += `   📂 타입: ${file.file_type}\n`;
        result += `   💡 삭제 이유: ${file.deletion_reason}\n`;
        result += `   🔄 복구 가능: ${file.recovery_possible ? '✅ 예' : '❌ 아니오'}\n\n`;
      });
      
      return result;
    } else {
      return `🔍 검색어 "${args.query}"에 해당하는 삭제된 파일을 찾을 수 없습니다. (${args.days_back}일 이내)`;
    }
    
  } catch (error: any) {
    console.error("Search deleted files API error:", error);
    return `❌ 삭제된 파일 검색 실패: ${error.message}`;
  }
}

/**
 * 파일 삭제 추적 등록
 */
export async function trackFileDeletion(args: z.infer<typeof TrackFileDeletionSchema>) {
  try {
    const response = await axios.post(`${API_BASE_URL}/track-deletion`, {
      file_path: args.file_path,
      reason: args.reason,
      backup_path: args.backup_path,
      metadata: args.metadata
    }, {
      headers: { 'Content-Type': 'application/json' },
      timeout: 5000
    });

    const data = response.data;
    
    if (data.status === 'success') {
      return `✅ 파일 삭제 추적 등록 완료!\n\n` +
             `📁 파일: ${args.file_path}\n` +
             `🆔 추적 ID: ${data.deletion_id}\n` +
             `💡 삭제 이유: ${args.reason}\n` +
             `📦 백업 경로: ${args.backup_path || '없음'}\n`;
    } else {
      return `❌ 파일 삭제 추적 등록 실패: ${data.message}`;
    }
    
  } catch (error: any) {
    console.error("Track deletion API error:", error);
    return `❌ 파일 삭제 추적 등록 실패: ${error.message}`;
  }
}

/**
 * 파일 이동 추적 등록
 */
export async function trackFileMovement(args: z.infer<typeof TrackFileMovementSchema>) {
  try {
    const response = await axios.post(`${API_BASE_URL}/track-movement`, {
      original_path: args.original_path,
      new_path: args.new_path,
      movement_type: args.movement_type,
      reason: args.reason
    }, {
      headers: { 'Content-Type': 'application/json' },
      timeout: 5000
    });

    const data = response.data;
    
    if (data.status === 'success') {
      return `✅ 파일 이동 추적 등록 완료!\n\n` +
             `📂 이동 타입: ${args.movement_type}\n` +
             `📍 원본: ${args.original_path}\n` +
             `📍 새 위치: ${args.new_path}\n` +
             `🆔 추적 ID: ${data.movement_id}\n` +
             `💡 이동 이유: ${args.reason}\n`;
    } else {
      return `❌ 파일 이동 추적 등록 실패: ${data.message}`;
    }
    
  } catch (error: any) {
    console.error("Track movement API error:", error);
    return `❌ 파일 이동 추적 등록 실패: ${error.message}`;
  }
}

/**
 * 삭제/이동 통계 조회
 */
export async function getDeletionStats(args: z.infer<typeof GetDeletionStatsSchema>) {
  try {
    const response = await axios.get(`${API_BASE_URL}/stats`, {
      timeout: 5000
    });

    const data = response.data;
    const stats = data.stats;
    
    let result = `📊 파일 삭제/이동 통계\n`;
    result += `🕐 조회 시간: ${data.timestamp}\n\n`;
    
    result += `🗑️  **삭제 통계**\n`;
    result += `   • 총 삭제된 파일: ${stats.total_deleted_files}개\n`;
    result += `   • 오늘 삭제된 파일: ${stats.deleted_today}개\n`;
    result += `   • 복구 가능한 파일: ${stats.recoverable_files}개\n\n`;
    
    result += `📦 **이동 통계**\n`;
    result += `   • 총 파일 이동: ${stats.total_file_movements}개\n\n`;
    
    if (stats.category_breakdown && Object.keys(stats.category_breakdown).length > 0) {
      result += `📂 **카테고리별 삭제 현황**\n`;
      for (const [category, count] of Object.entries(stats.category_breakdown)) {
        result += `   • ${category}: ${count}개\n`;
      }
    } else {
      result += `📂 **카테고리별 삭제 현황**: 기록 없음\n`;
    }
    
    return result;
    
  } catch (error: any) {
    console.error("Deletion stats API error:", error);
    return `❌ 삭제 통계 조회 실패: ${error.message}`;
  }
}

// 스키마 및 함수 내보내기
export const DeletionToolSchemas = {
  get_recent_deletions: GetRecentDeletionsSchema,
  get_recent_movements: GetRecentMovementsSchema,
  search_deleted_files: SearchDeletedFilesSchema,
  track_file_deletion: TrackFileDeletionSchema,
  track_file_movement: TrackFileMovementSchema,
  get_deletion_stats: GetDeletionStatsSchema,
};

export const DeletionToolFunctions = {
  get_recent_deletions: getRecentDeletions,
  get_recent_movements: getRecentMovements,
  search_deleted_files: searchDeletedFiles,
  track_file_deletion: trackFileDeletion,
  track_file_movement: trackFileMovement,
  get_deletion_stats: getDeletionStats,
};