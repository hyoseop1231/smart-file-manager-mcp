#!/usr/bin/env python3
"""
간단한 AI 서비스 - MCP 테스트용
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import glob
import time
from pathlib import Path

app = FastAPI(title="Smart File Manager AI Service - Simple")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청 모델
class SearchRequest(BaseModel):
    query: str
    directories: Optional[List[str]] = None
    language: Optional[str] = "ko"
    limit: Optional[int] = 10

class OrganizeRequest(BaseModel):
    sourceDir: str
    targetDir: Optional[str] = None
    method: str
    dryRun: Optional[bool] = False

class WorkflowRequest(BaseModel):
    searchQuery: str
    action: str
    options: Optional[Dict[str, Any]] = {}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "database": "healthy", 
            "mafm": "available",
            "organizer": "available",
            "ai_models": "on-demand"
        },
        "db_stats": {
            "total_files": 1250,
            "by_category": {
                "document": {"count": 450, "size_gb": 2.3},
                "image": {"count": 320, "size_gb": 5.1},
                "video": {"count": 85, "size_gb": 12.7},
                "audio": {"count": 165, "size_gb": 3.8},
                "code": {"count": 200, "size_gb": 0.9},
                "other": {"count": 30, "size_gb": 1.2}
            },
            "active_cache_entries": 45
        }
    }

@app.post("/search")
async def search_files(request: SearchRequest):
    # 실제 파일 검색 (간단한 구현)
    search_dirs = request.directories or [str(Path.home() / "Documents"), 
                                        str(Path.home() / "Downloads"),
                                        str(Path.home() / "Desktop")]
    
    results = []
    for directory in search_dirs:
        if os.path.exists(directory):
            # 간단한 파일명 매칭
            for root, dirs, files in os.walk(directory):
                for file in files[:request.limit]:
                    if request.query.lower() in file.lower():
                        file_path = os.path.join(root, file)
                        stat = os.stat(file_path)
                        results.append({
                            "path": file_path,
                            "name": file,
                            "size": stat.st_size,
                            "modified": stat.st_mtime,
                            "score": 0.8,
                            "metadata": {
                                "category": _get_category(file),
                                "extension": Path(file).suffix
                            }
                        })
                        if len(results) >= request.limit:
                            break
                if len(results) >= request.limit:
                    break
        if len(results) >= request.limit:
            break
    
    return {
        "results": results,
        "source": "filesystem",
        "total": len(results)
    }

@app.post("/organize")
async def organize_files(request: OrganizeRequest):
    if not os.path.exists(request.sourceDir):
        raise HTTPException(status_code=404, detail="Source directory not found")
    
    # 조직화 시뮬레이션
    organized_files = []
    for root, dirs, files in os.walk(request.sourceDir):
        for file in files[:20]:  # 최대 20개 파일만 처리
            category = _get_category(file)
            target_path = f"{request.targetDir or request.sourceDir}/{category}/{file}"
            organized_files.append({
                "original_path": os.path.join(root, file),
                "new_path": target_path,
                "category": category,
                "action": "move" if not request.dryRun else "preview"
            })
    
    return {
        "organized_files": organized_files,
        "total_files": len(organized_files),
        "dry_run": request.dryRun,
        "method": request.method
    }

@app.post("/workflow")
async def smart_workflow(request: WorkflowRequest):
    # 먼저 파일 검색
    search_results = await search_files(SearchRequest(
        query=request.searchQuery,
        directories=request.options.get("directories"),
        limit=request.options.get("limit", 20)
    ))
    
    if request.action == "organize":
        return {
            "status": "success",
            "search_results": search_results,
            "action_result": {
                "organized_files": 15,
                "categories_created": ["documents", "images", "videos"],
                "preview": True
            }
        }
    elif request.action == "analyze":
        return {
            "status": "success", 
            "search_results": search_results,
            "analysis": {
                "total_files": len(search_results["results"]),
                "file_types": {"document": 8, "image": 5, "other": 2},
                "total_size": "25.7 MB",
                "recommendations": [
                    "문서 파일이 대부분입니다",
                    "날짜별로 정리하는 것을 추천합니다",
                    "중복 파일 검사가 필요합니다"
                ]
            }
        }
    else:
        return {
            "status": "success",
            "search_results": search_results,
            "rename_suggestions": [
                {
                    "original": f"file_{i}.txt",
                    "suggested": f"2024_document_{i+1}.txt"
                } for i in range(min(5, len(search_results["results"])))
            ]
        }

@app.get("/recent")
async def get_recent_files(hours: int = 24, limit: int = 50):
    """최근 수정된 파일 조회"""
    recent_files = []
    cutoff_time = time.time() - (hours * 3600)
    
    search_dirs = [str(Path.home() / "Documents"), 
                   str(Path.home() / "Downloads"),
                   str(Path.home() / "Desktop")]
    
    for directory in search_dirs:
        if os.path.exists(directory):
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        if stat.st_mtime > cutoff_time:
                            recent_files.append({
                                "path": file_path,
                                "name": file,
                                "size": stat.st_size,
                                "modified": stat.st_mtime,
                                "metadata": {
                                    "category": _get_category(file),
                                    "extension": Path(file).suffix
                                }
                            })
                    except:
                        continue
                    
                    if len(recent_files) >= limit:
                        break
                if len(recent_files) >= limit:
                    break
        if len(recent_files) >= limit:
            break
    
    # 수정 시간 순으로 정렬
    recent_files.sort(key=lambda x: x["modified"], reverse=True)
    
    return {
        "results": recent_files[:limit],
        "total": len(recent_files),
        "hours": hours
    }

@app.get("/category/{category}")
async def get_files_by_category(category: str, limit: int = 50):
    """카테고리별 파일 조회"""
    files = []
    search_dirs = [str(Path.home() / "Documents"), 
                   str(Path.home() / "Downloads"),
                   str(Path.home() / "Desktop")]
    
    for directory in search_dirs:
        if os.path.exists(directory):
            for root, dirs, file_list in os.walk(directory):
                for file in file_list:
                    if _get_category(file) == category:
                        file_path = os.path.join(root, file)
                        try:
                            stat = os.stat(file_path)
                            files.append({
                                "path": file_path,
                                "name": file,
                                "size": stat.st_size,
                                "modified": stat.st_mtime,
                                "metadata": {
                                    "category": category,
                                    "extension": Path(file).suffix
                                }
                            })
                        except:
                            continue
                        
                        if len(files) >= limit:
                            break
                if len(files) >= limit:
                    break
        if len(files) >= limit:
            break
    
    return {
        "results": files,
        "total": len(files),
        "category": category
    }

@app.post("/extension")
async def get_files_by_extension(extensions: List[str], limit: int = 50):
    """확장자별 파일 조회"""
    files = []
    search_dirs = [str(Path.home() / "Documents"), 
                   str(Path.home() / "Downloads"),
                   str(Path.home() / "Desktop")]
    
    extensions_lower = [ext.lower() for ext in extensions]
    
    for directory in search_dirs:
        if os.path.exists(directory):
            for root, dirs, file_list in os.walk(directory):
                for file in file_list:
                    if Path(file).suffix.lower() in extensions_lower:
                        file_path = os.path.join(root, file)
                        try:
                            stat = os.stat(file_path)
                            files.append({
                                "path": file_path,
                                "name": file,
                                "size": stat.st_size,
                                "modified": stat.st_mtime,
                                "metadata": {
                                    "category": _get_category(file),
                                    "extension": Path(file).suffix
                                }
                            })
                        except:
                            continue
                        
                        if len(files) >= limit:
                            break
                if len(files) >= limit:
                    break
        if len(files) >= limit:
            break
    
    return {
        "results": files,
        "total": len(files),
        "extensions": extensions
    }

def _get_category(filename: str) -> str:
    """파일명으로부터 카테고리 추출"""
    ext = Path(filename).suffix.lower()
    
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']:
        return "image"
    elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv']:
        return "video"
    elif ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']:
        return "audio"
    elif ext in ['.pdf', '.doc', '.docx', '.txt', '.md', '.rtf']:
        return "document"
    elif ext in ['.py', '.js', '.java', '.cpp', '.c', '.go', '.rs']:
        return "code"
    elif ext in ['.zip', '.tar', '.gz', '.rar', '.7z']:
        return "archive"
    else:
        return "other"

if __name__ == "__main__":
    import uvicorn
    print("🚀 Smart File Manager AI Service (Simple) 시작 중...")
    print("📍 URL: http://localhost:8001")
    print("📊 Health Check: http://localhost:8001/health")
    uvicorn.run(app, host="0.0.0.0", port=8001)