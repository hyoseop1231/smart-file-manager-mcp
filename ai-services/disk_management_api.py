"""
디스크 관리 API 엔드포인트
"""

import os
import shutil
import subprocess
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

router = APIRouter(prefix="/disk", tags=["disk_management"])


def get_disk_usage() -> Dict[str, Any]:
    """현재 디스크 사용률 정보 반환"""
    total, used, free = shutil.disk_usage("/")
    usage_percent = (used / total) * 100
    
    return {
        "total_bytes": total,
        "used_bytes": used,
        "free_bytes": free,
        "usage_percent": round(usage_percent, 2),
        "total_gb": round(total / (1024**3), 2),
        "used_gb": round(used / (1024**3), 2),
        "free_gb": round(free / (1024**3), 2)
    }


@router.get("/usage")
async def get_disk_usage_info():
    """
    현재 디스크 사용률 정보 조회
    """
    try:
        usage = get_disk_usage()
        
        # 경고 수준 추가
        if usage["usage_percent"] >= 95:
            usage["warning_level"] = "critical"
            usage["message"] = "디스크 공간이 심각하게 부족합니다. 즉시 정리가 필요합니다."
        elif usage["usage_percent"] >= 90:
            usage["warning_level"] = "high"
            usage["message"] = "디스크 공간이 부족합니다. 정리를 권장합니다."
        elif usage["usage_percent"] >= 80:
            usage["warning_level"] = "medium"
            usage["message"] = "디스크 사용률이 높습니다. 모니터링이 필요합니다."
        else:
            usage["warning_level"] = "normal"
            usage["message"] = "디스크 사용률이 정상입니다."
        
        return {
            "success": True,
            "data": usage,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup/thumbnails")
async def cleanup_thumbnails(days: int = 30):
    """
    오래된 썸네일 정리
    
    Args:
        days: 이 일수보다 오래된 썸네일 삭제 (기본값: 30일)
    """
    try:
        thumbnail_dirs = [
            "/data/thumbnails",
            "/data/video_thumbnails"
        ]
        
        total_cleaned = 0
        file_count = 0
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for thumb_dir in thumbnail_dirs:
            if not os.path.exists(thumb_dir):
                continue
                
            for root, dirs, files in os.walk(thumb_dir):
                for file in files:
                    filepath = os.path.join(root, file)
                    try:
                        if datetime.fromtimestamp(os.path.getmtime(filepath)) < cutoff_date:
                            size = os.path.getsize(filepath)
                            os.remove(filepath)
                            total_cleaned += size
                            file_count += 1
                    except Exception:
                        continue
        
        # 정리 후 디스크 사용률
        new_usage = get_disk_usage()
        
        return {
            "success": True,
            "cleaned_files": file_count,
            "cleaned_bytes": total_cleaned,
            "cleaned_mb": round(total_cleaned / (1024**2), 2),
            "disk_usage_after": new_usage,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup/temp")
async def cleanup_temp_files():
    """
    임시 파일 정리
    """
    try:
        temp_patterns = ["*.tmp", "*.temp", "*.cache", "~*", ".DS_Store"]
        temp_dirs = ["/tmp", "/data/temp", "/app/temp"]
        
        total_cleaned = 0
        file_count = 0
        
        for temp_dir in temp_dirs:
            if not os.path.exists(temp_dir):
                continue
                
            for pattern in temp_patterns:
                for filepath in Path(temp_dir).rglob(pattern):
                    try:
                        size = filepath.stat().st_size
                        filepath.unlink()
                        total_cleaned += size
                        file_count += 1
                    except Exception:
                        continue
        
        # 정리 후 디스크 사용률
        new_usage = get_disk_usage()
        
        return {
            "success": True,
            "cleaned_files": file_count,
            "cleaned_bytes": total_cleaned,
            "cleaned_mb": round(total_cleaned / (1024**2), 2),
            "disk_usage_after": new_usage,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations")
async def get_cleanup_recommendations():
    """
    디스크 정리 권장사항 제공
    """
    try:
        usage = get_disk_usage()
        recommendations = []
        
        # 썸네일 디렉토리 크기 확인
        thumbnail_size = 0
        for thumb_dir in ["/data/thumbnails", "/data/video_thumbnails"]:
            if os.path.exists(thumb_dir):
                for root, dirs, files in os.walk(thumb_dir):
                    for file in files:
                        try:
                            thumbnail_size += os.path.getsize(os.path.join(root, file))
                        except:
                            pass
        
        if thumbnail_size > 1024**3:  # 1GB 이상
            recommendations.append({
                "type": "thumbnails",
                "description": "썸네일 캐시가 1GB를 초과했습니다",
                "action": "30일 이상 된 썸네일 정리를 권장합니다",
                "potential_savings_mb": round(thumbnail_size * 0.7 / (1024**2), 2)
            })
        
        # 디스크 사용률에 따른 권장사항
        if usage["usage_percent"] >= 90:
            recommendations.append({
                "type": "critical",
                "description": "디스크 사용률이 90%를 초과했습니다",
                "action": "즉시 불필요한 파일을 정리하세요",
                "potential_savings_mb": "varies"
            })
        
        # Docker 이미지 정리 권장
        recommendations.append({
            "type": "docker",
            "description": "사용하지 않는 Docker 이미지와 컨테이너",
            "action": "docker system prune -a 명령으로 정리 가능",
            "potential_savings_mb": "varies"
        })
        
        return {
            "success": True,
            "current_usage": usage,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))