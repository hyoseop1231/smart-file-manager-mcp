#!/usr/bin/env python3
"""
Deletion Tracking API Endpoints for Smart File Manager
삭제된 파일 추적 및 관리를 위한 FastAPI 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from enhanced_deletion_tracking import deletion_tracker

logger = logging.getLogger(__name__)

# API 라우터 생성
deletion_router = APIRouter(prefix="/api/deletion", tags=["deletion-tracking"])

# Request/Response 모델 정의
class DeletionRequest(BaseModel):
    file_path: str = Field(..., description="삭제된 파일의 원본 경로")
    reason: str = Field(default="user_action", description="삭제 이유")
    backup_path: Optional[str] = Field(None, description="백업 파일 경로")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 메타데이터")

class MovementRequest(BaseModel):
    original_path: str = Field(..., description="원본 파일 경로")
    new_path: str = Field(..., description="새 파일 경로")
    movement_type: str = Field(default="archive", description="이동 타입")
    reason: str = Field(default="organization", description="이동 이유")

class SearchRequest(BaseModel):
    query: Optional[str] = Field("", description="검색어")
    days_back: int = Field(default=30, description="검색할 일수")

# API 엔드포인트 정의

@deletion_router.get("/recent-deletions")
async def get_recent_deletions(limit: int = Query(default=10, ge=1, le=100)):
    """
    최근 삭제된 파일 목록 조회
    
    Parameters:
    - limit: 조회할 파일 개수 (1-100)
    
    Returns:
    - 최근 삭제된 파일들의 목록
    """
    try:
        deleted_files = deletion_tracker.get_recent_deletions(limit)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "count": len(deleted_files),
                "deleted_files": deleted_files,
                "message": f"최근 삭제된 파일 {len(deleted_files)}개 조회 완료"
            }
        )
        
    except Exception as e:
        logger.error(f"최근 삭제 파일 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")

@deletion_router.get("/recent-movements")
async def get_recent_movements(limit: int = Query(default=10, ge=1, le=100)):
    """
    최근 파일 이동 목록 조회 (Archive 등)
    
    Parameters:
    - limit: 조회할 이동 기록 개수 (1-100)
    
    Returns:
    - 최근 파일 이동 기록들의 목록
    """
    try:
        movements = deletion_tracker.get_recent_movements(limit)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "count": len(movements),
                "movements": movements,
                "message": f"최근 파일 이동 기록 {len(movements)}개 조회 완료"
            }
        )
        
    except Exception as e:
        logger.error(f"최근 파일 이동 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")

@deletion_router.post("/track-deletion")
async def track_file_deletion(request: DeletionRequest):
    """
    파일 삭제 추적 등록
    
    Body:
    - file_path: 삭제된 파일 경로
    - reason: 삭제 이유
    - backup_path: 백업 경로 (선택사항)
    - metadata: 추가 메타데이터 (선택사항)
    
    Returns:
    - 삭제 추적 ID 및 상태
    """
    try:
        deletion_id = deletion_tracker.track_deletion(
            file_path=request.file_path,
            reason=request.reason,
            backup_path=request.backup_path,
            metadata=request.metadata
        )
        
        if deletion_id > 0:
            return JSONResponse(
                status_code=201,
                content={
                    "status": "success",
                    "deletion_id": deletion_id,
                    "file_path": request.file_path,
                    "message": "파일 삭제 추적 등록 완료"
                }
            )
        else:
            raise HTTPException(status_code=500, detail="삭제 추적 등록 실패")
            
    except Exception as e:
        logger.error(f"파일 삭제 추적 실패: {e}")
        raise HTTPException(status_code=500, detail=f"추적 실패: {str(e)}")

@deletion_router.post("/track-movement")
async def track_file_movement(request: MovementRequest):
    """
    파일 이동 추적 등록 (Archive 등)
    
    Body:
    - original_path: 원본 파일 경로
    - new_path: 새 파일 경로
    - movement_type: 이동 타입 (archive, reorganize, backup)
    - reason: 이동 이유
    
    Returns:
    - 이동 추적 ID 및 상태
    """
    try:
        movement_id = deletion_tracker.track_movement(
            original_path=request.original_path,
            new_path=request.new_path,
            movement_type=request.movement_type,
            reason=request.reason
        )
        
        if movement_id > 0:
            return JSONResponse(
                status_code=201,
                content={
                    "status": "success",
                    "movement_id": movement_id,
                    "original_path": request.original_path,
                    "new_path": request.new_path,
                    "message": "파일 이동 추적 등록 완료"
                }
            )
        else:
            raise HTTPException(status_code=500, detail="이동 추적 등록 실패")
            
    except Exception as e:
        logger.error(f"파일 이동 추적 실패: {e}")
        raise HTTPException(status_code=500, detail=f"추적 실패: {str(e)}")

@deletion_router.post("/search-deleted")
async def search_deleted_files(request: SearchRequest):
    """
    삭제된 파일 검색
    
    Body:
    - query: 검색어 (파일명 또는 경로에서 검색)
    - days_back: 검색할 기간 (일수)
    
    Returns:
    - 검색 조건에 맞는 삭제된 파일들의 목록
    """
    try:
        deleted_files = deletion_tracker.search_deleted_files(
            query=request.query,
            days_back=request.days_back
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "count": len(deleted_files),
                "query": request.query,
                "days_back": request.days_back,
                "deleted_files": deleted_files,
                "message": f"검색 조건에 맞는 삭제된 파일 {len(deleted_files)}개 발견"
            }
        )
        
    except Exception as e:
        logger.error(f"삭제된 파일 검색 실패: {e}")
        raise HTTPException(status_code=500, detail=f"검색 실패: {str(e)}")

@deletion_router.get("/stats")
async def get_deletion_stats():
    """
    삭제 및 이동 통계 조회
    
    Returns:
    - 삭제/이동 파일 통계 정보
    """
    try:
        stats = deletion_tracker.get_deletion_stats()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "stats": stats,
                "timestamp": datetime.now().isoformat(),
                "message": "삭제/이동 통계 조회 완료"
            }
        )
        
    except Exception as e:
        logger.error(f"삭제 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")

@deletion_router.get("/health")
async def deletion_tracker_health():
    """
    삭제 추적 시스템 상태 확인
    
    Returns:
    - 시스템 상태 및 버전 정보
    """
    try:
        # 간단한 헬스체크 - 데이터베이스 연결 확인
        stats = deletion_tracker.get_deletion_stats()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "service": "deletion-tracker",
                "version": "1.0.0",
                "database_connected": True,
                "features": [
                    "deletion_tracking",
                    "movement_tracking", 
                    "search_deleted_files",
                    "recovery_support",
                    "statistics"
                ],
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"삭제 추적 헬스체크 실패: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "deletion-tracker",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

# 편의 기능 엔드포인트들

@deletion_router.get("/deleted-files") 
async def get_deleted_files_simple(limit: int = Query(default=5, ge=1, le=50)):
    """
    간단한 삭제된 파일 목록 조회 (MCP 호환)
    
    Parameters:
    - limit: 조회할 파일 개수
    
    Returns:
    - 최근 삭제된 파일들의 간단한 목록
    """
    try:
        deleted_files = deletion_tracker.get_recent_deletions(limit)
        
        # 간단한 형태로 변환
        simple_list = []
        for file in deleted_files:
            simple_list.append({
                "filename": file['filename'],
                "original_path": file['original_path'],
                "deleted_at": file['deleted_at'],
                "size_mb": round(file['file_size'] / (1024*1024), 2) if file['file_size'] else 0,
                "recoverable": file['recovery_possible']
            })
        
        return {
            "recent_deletions": simple_list,
            "total_count": len(simple_list)
        }
        
    except Exception as e:
        logger.error(f"간단한 삭제 파일 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 라우터 내보내기
__all__ = ['deletion_router']