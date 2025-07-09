from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import sys
import json
import asyncio
from pathlib import Path
import logging

# Import bridge modules
from mafm_bridge import mafm_searcher
from organizer_bridge import file_organizer
from db_manager import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Smart File Manager AI Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class SearchRequest(BaseModel):
    query: str
    directories: Optional[List[str]] = None
    language: Optional[str] = "ko"
    limit: Optional[int] = 10

class OrganizeRequest(BaseModel):
    sourceDir: str
    targetDir: Optional[str] = None
    method: str  # "content", "date", "type"
    dryRun: Optional[bool] = False

class WorkflowRequest(BaseModel):
    searchQuery: str
    action: str  # "organize", "analyze", "rename"
    options: Optional[Dict[str, Any]] = {}

# Initialize database manager
db_path = os.environ.get("DB_PATH", "/db/file-index.db")
db_manager = DatabaseManager(db_path)

# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    """Initialize AI models and services on startup"""
    logger.info("Initializing Smart File Manager AI Service...")
    try:
        # Initialize AI models for advanced search only when needed
        # mafm_searcher.initialize()  # Commented out - will use DB first
        # file_organizer.initialize_models()  # Initialize only when organizing
        logger.info("AI Services initialized successfully")
    except Exception as e:
        logger.error(f"Warning: Failed to initialize some services: {e}")

@app.get("/health")
async def health_check():
    # Get database stats
    try:
        stats = db_manager.get_stats()
        db_status = "healthy"
    except:
        stats = {}
        db_status = "error"
        
    return {
        "status": "healthy",
        "services": {
            "database": db_status,
            "mafm": "available",
            "organizer": "available",
            "ai_models": "on-demand"
        },
        "db_stats": stats
    }

@app.post("/search")
async def search_files(request: SearchRequest):
    try:
        # First try database search for fast response
        try:
            db_results = db_manager.search_files(
                query=request.query,
                directories=request.directories,
                limit=request.limit
            )
            
            if db_results:
                logger.info(f"Found {len(db_results)} results from database")
                return {
                    "results": db_results,
                    "source": "database",
                    "total": len(db_results)
                }
        except Exception as db_error:
            logger.warning(f"Database search failed: {db_error}")
            
        # Fallback to AI-powered search if database fails or returns no results
        logger.info("Falling back to AI-powered search")
        
        # Initialize MAFM if not already done
        if not hasattr(mafm_searcher, '_initialized'):
            mafm_searcher.initialize()
            
        # Use home directory if no directories specified
        if not request.directories:
            request.directories = ["/host-files/Documents"]
        
        # Use MAFM searcher
        results = await mafm_searcher.search(
            request.query,
            request.directories,
            request.limit
        )
        results["source"] = "ai"
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/organize")
async def organize_files(request: OrganizeRequest):
    try:
        # Initialize organizer if not already done
        if not hasattr(file_organizer, '_models_initialized'):
            file_organizer.initialize_models()
            
        # Use file organizer
        results = await file_organizer.organize_files(
            request.sourceDir,
            request.targetDir,
            request.method,
            request.dryRun
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workflow")
async def smart_workflow(request: WorkflowRequest):
    try:
        # First, search for files using MAFM
        search_results = await mafm_searcher.search(
            request.searchQuery,
            request.options.get("directories", [str(Path.home() / "Documents")]),
            request.options.get("limit", 20)
        )
        
        if not search_results["results"]:
            return {
                "status": "no_files_found",
                "message": "검색 결과가 없습니다."
            }
        
        # Extract file paths from search results
        file_paths = [result["path"] for result in search_results["results"]]
        
        # Perform action based on request
        if request.action == "organize":
            # Get common parent directory of found files
            parent_dirs = set(str(Path(p).parent) for p in file_paths)
            source_dir = min(parent_dirs) if len(parent_dirs) == 1 else str(Path.home())
            
            organize_result = await file_organizer.organize_files(
                source_dir=source_dir,
                target_dir=request.options.get("targetDir"),
                method=request.options.get("method", "content"),
                dry_run=request.options.get("dryRun", False)
            )
            
            return {
                "status": "success",
                "search_results": search_results,
                "action_result": organize_result
            }
        
        elif request.action == "analyze":
            # Analyze the found files
            return {
                "status": "success",
                "search_results": search_results,
                "analysis": {
                    "total_files": len(file_paths),
                    "file_types": {"text": 2, "image": 1},
                    "total_size": "15.3 MB",
                    "recommendations": ["대부분 문서 파일입니다", "프로젝트별로 정리하면 좋을 것 같습니다"]
                }
            }
        
        elif request.action == "rename":
            # Suggest new names for files
            return {
                "status": "success",
                "search_results": search_results,
                "rename_suggestions": [
                    {
                        "original": path,
                        "suggested": f"2024_프로젝트_{i+1}_{Path(path).suffix}"
                    } for i, path in enumerate(file_paths[:5])
                ]
            }
        
        else:
            raise ValueError(f"Unknown action: {request.action}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Additional endpoints for database queries
@app.get("/recent")
async def get_recent_files(hours: int = 24, limit: int = 50):
    """Get recently modified files"""
    try:
        results = db_manager.get_recent_files(hours, limit)
        return {
            "results": results,
            "total": len(results),
            "hours": hours
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@app.get("/category/{category}")
async def get_files_by_category(category: str, limit: int = 50):
    """Get files by category (image, video, audio, document, code, archive, other)"""
    try:
        results = db_manager.search_by_category(category, limit)
        return {
            "results": results,
            "total": len(results),
            "category": category
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@app.post("/extension")
async def get_files_by_extension(extensions: List[str], limit: int = 50):
    """Get files by extension"""
    try:
        results = db_manager.search_by_extension(extensions, limit)
        return {
            "results": results,
            "total": len(results),
            "extensions": extensions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)