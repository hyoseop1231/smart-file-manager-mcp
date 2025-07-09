#!/usr/bin/env python3
"""
Enhanced AI Service with MAFM Multi-Agent + Local-File-Organizer features
Uses Ollama for local LLM processing
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import time
import json
import logging
import asyncio
from pathlib import Path
from datetime import datetime

# Import our components
from llm_organizer import LLMOrganizer
from enhanced_llm_organizer import EnhancedLLMOrganizer
from indexer import FileIndexer
from db_manager import DatabaseManager

app = FastAPI(title="Smart File Manager AI Service - Enhanced")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
llm_organizer = LLMOrganizer()
enhanced_llm_organizer = EnhancedLLMOrganizer()
db_manager = DatabaseManager("/tmp/smart-file-manager/db/file-index.db")
file_indexer = FileIndexer("/tmp/smart-file-manager/db/file-index.db", 
                          "/tmp/smart-file-manager/embeddings", 
                          "/tmp/smart-file-manager/metadata")

# Global state for background tasks
background_tasks = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Request models
class SearchRequest(BaseModel):
    query: str
    directories: Optional[List[str]] = None
    language: Optional[str] = "ko"
    limit: Optional[int] = 10
    use_llm: Optional[bool] = True  # Enable LLM-enhanced search

class OrganizeRequest(BaseModel):
    sourceDir: str
    targetDir: Optional[str] = None
    method: str = "content"  # content, date, type
    dryRun: Optional[bool] = False
    use_llm: Optional[bool] = True  # Use LLM for categorization

class WorkflowRequest(BaseModel):
    searchQuery: str
    action: str  # organize, analyze, rename, index
    options: Optional[Dict[str, Any]] = {}

class IndexRequest(BaseModel):
    directories: Optional[List[str]] = None
    force: Optional[bool] = False

@app.get("/health")
async def health_check():
    """Enhanced health check with Ollama status"""
    ollama_status = "unavailable"
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/tags") as resp:
                if resp.status == 200:
                    ollama_status = "available"
    except:
        pass
        
    stats = file_indexer.get_stats()
    
    return {
        "status": "healthy",
        "services": {
            "database": "healthy",
            "indexer": "available",
            "llm_organizer": "available",
            "ollama": ollama_status,
            "vectordb": "planned"  # For future Milvus integration
        },
        "db_stats": stats,
        "background_tasks": len(background_tasks)
    }

@app.post("/search")
async def search_files(request: SearchRequest):
    """Enhanced search with LLM understanding"""
    try:
        if request.use_llm and request.query:
            # Use LLM to understand query intent
            results = await llm_organizer.smart_search(
                request.query,
                request.directories or []
            )
            
            # Fallback to database search if LLM search returns nothing
            if not results:
                results = db_manager.search_files(
                    request.query,
                    request.directories,
                    request.limit
                )
        else:
            # Direct database search
            results = db_manager.search_files(
                request.query,
                request.directories,
                request.limit
            )
            
        return {
            "success": True,
            "count": len(results),
            "results": results,
            "method": "llm_enhanced" if request.use_llm else "keyword"
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/organize")
async def organize_files(request: OrganizeRequest, background_tasks: BackgroundTasks):
    """Organize files with LLM categorization"""
    try:
        task_id = f"organize_{int(time.time())}"
        
        if request.use_llm:
            # Start background task for LLM organization
            background_tasks.add_task(
                run_llm_organization,
                task_id,
                request.sourceDir,
                request.targetDir,
                request.method,
                request.dryRun
            )
            
            return {
                "success": True,
                "message": "Organization started",
                "task_id": task_id,
                "method": "llm_categorization"
            }
        else:
            # Simple organization without LLM
            results = await organize_simple(
                request.sourceDir,
                request.targetDir,
                request.method,
                request.dryRun
            )
            return {
                "success": True,
                "results": results,
                "method": "simple"
            }
            
    except Exception as e:
        logger.error(f"Organization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workflow")
async def smart_workflow(request: WorkflowRequest):
    """Execute complex workflows"""
    try:
        if request.action == "organize":
            # Search then organize
            search_results = db_manager.search_files(
                request.searchQuery,
                limit=100
            )
            
            if search_results:
                # Create temporary directory with search results
                temp_dir = f"/tmp/workflow_{int(time.time())}"
                os.makedirs(temp_dir, exist_ok=True)
                
                # Create symbolic links
                for result in search_results:
                    src = result['path']
                    dst = os.path.join(temp_dir, os.path.basename(src))
                    try:
                        os.symlink(src, dst)
                    except:
                        pass
                        
                # Organize the temporary directory
                organize_result = await llm_organizer.organize_directory(
                    temp_dir,
                    request.options.get('targetDir', temp_dir + "_organized"),
                    request.options.get('method', 'content'),
                    request.options.get('dryRun', False)
                )
                
                return {
                    "success": True,
                    "search_count": len(search_results),
                    "organize_result": organize_result
                }
                
        elif request.action == "analyze":
            # Analyze files matching query
            search_results = db_manager.search_files(
                request.searchQuery,
                limit=50
            )
            
            analyses = []
            for result in search_results[:10]:  # Limit to 10 files
                analysis = await llm_organizer.analyze_file_with_llm(result['path'])
                analyses.append({
                    "file": result['path'],
                    "analysis": analysis
                })
                
            return {
                "success": True,
                "count": len(analyses),
                "analyses": analyses
            }
            
        elif request.action == "index":
            # Trigger reindexing
            file_indexer.run_indexing()
            return {
                "success": True,
                "message": "Indexing completed",
                "stats": file_indexer.get_stats()
            }
            
        else:
            raise ValueError(f"Unknown action: {request.action}")
            
    except Exception as e:
        logger.error(f"Workflow error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index")
async def trigger_indexing(request: IndexRequest, background_tasks: BackgroundTasks):
    """Trigger file indexing"""
    try:
        task_id = f"index_{int(time.time())}"
        
        background_tasks.add_task(
            run_indexing,
            task_id,
            request.directories,
            request.force
        )
        
        return {
            "success": True,
            "message": "Indexing started",
            "task_id": task_id
        }
        
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Get background task status"""
    if task_id in background_tasks:
        return background_tasks[task_id]
    else:
        raise HTTPException(status_code=404, detail="Task not found")

# Category endpoints for quick access
@app.get("/category/{category}")
async def get_files_by_category(category: str, limit: int = 50):
    """Get files by category"""
    results = db_manager.search_by_category(category, limit)
    return {
        "category": category,
        "count": len(results),
        "files": results
    }

@app.get("/recent")
async def get_recent_files(hours: int = 24, limit: int = 50):
    """Get recently modified files"""
    results = db_manager.get_recent_files(hours, limit)
    return {
        "hours": hours,
        "count": len(results),
        "files": results
    }

# Background task functions
async def run_llm_organization(task_id: str, source_dir: str, target_dir: str, 
                             method: str, dry_run: bool):
    """Background task for LLM-based organization"""
    try:
        background_tasks[task_id] = {
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "progress": 0
        }
        
        results = await llm_organizer.organize_directory(
            source_dir, target_dir, method, dry_run
        )
        
        background_tasks[task_id] = {
            "status": "completed",
            "started_at": background_tasks[task_id]["started_at"],
            "completed_at": datetime.now().isoformat(),
            "results": results
        }
        
    except Exception as e:
        background_tasks[task_id] = {
            "status": "failed",
            "error": str(e),
            "started_at": background_tasks[task_id]["started_at"],
            "failed_at": datetime.now().isoformat()
        }

async def run_indexing(task_id: str, directories: Optional[List[str]], force: bool):
    """Background task for indexing"""
    try:
        background_tasks[task_id] = {
            "status": "running",
            "started_at": datetime.now().isoformat()
        }
        
        if directories:
            for directory in directories:
                file_indexer.index_directory(directory)
        else:
            file_indexer.run_indexing()
            
        stats = file_indexer.get_stats()
        
        background_tasks[task_id] = {
            "status": "completed",
            "started_at": background_tasks[task_id]["started_at"],
            "completed_at": datetime.now().isoformat(),
            "stats": stats
        }
        
    except Exception as e:
        background_tasks[task_id] = {
            "status": "failed",
            "error": str(e),
            "started_at": background_tasks[task_id]["started_at"],
            "failed_at": datetime.now().isoformat()
        }

async def organize_simple(source_dir: str, target_dir: str, method: str, dry_run: bool):
    """Simple organization without LLM"""
    # Basic implementation for non-LLM organization
    source_path = Path(source_dir)
    target_path = Path(target_dir) if target_dir else source_path / "Organized"
    
    if not source_path.exists():
        raise ValueError(f"Source directory {source_dir} does not exist")
        
    operations = []
    
    for file_path in source_path.rglob("*"):
        if file_path.is_file() and not file_path.name.startswith('.'):
            # Determine category by extension
            ext = file_path.suffix.lower()
            if ext in ['.jpg', '.png', '.gif']:
                category = "Images"
            elif ext in ['.pdf', '.doc', '.docx']:
                category = "Documents"
            elif ext in ['.mp3', '.wav']:
                category = "Audio"
            elif ext in ['.mp4', '.avi']:
                category = "Videos"
            else:
                category = "Other"
                
            target_file = target_path / category / file_path.name
            
            operations.append({
                "source": str(file_path),
                "target": str(target_file)
            })
            
            if not dry_run:
                target_file.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(str(file_path), str(target_file))
                
    return {
        "operations": operations,
        "count": len(operations)
    }

# Add smart analysis endpoint
class SmartAnalyzeRequest(BaseModel):
    file_path: str

@app.post("/analyze/smart")
async def smart_analyze_file(request: SmartAnalyzeRequest):
    """Analyze file with smart model selection"""
    try:
        result = await enhanced_llm_organizer.analyze_file_with_smart_selection(request.file_path)
        return {"success": True, "analysis": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class BatchAnalyzeRequest(BaseModel):
    file_paths: List[str]
    max_concurrent: int = 5

@app.post("/analyze/batch")
async def batch_analyze_files(request: BatchAnalyzeRequest):
    """Batch analyze files with smart model selection"""
    try:
        results = await enhanced_llm_organizer.batch_analyze_files(request.file_paths, request.max_concurrent)
        return {"success": True, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/recommendations")
async def get_model_recommendations(file_paths: List[str] = None):
    """Get model usage recommendations"""
    try:
        if file_paths:
            recommendations = enhanced_llm_organizer.get_model_recommendations(file_paths)
        else:
            recommendations = enhanced_llm_organizer.model_selector.get_model_status()
        return {"success": True, "recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Advanced file management endpoints
@app.post("/duplicate/find")
async def find_duplicates(request: dict):
    """Find duplicate files using content hash"""
    try:
        results = db_manager.find_duplicates()
        return {"success": True, "duplicates": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/similar/find")
async def find_similar_files(request: dict):
    """Find similar files using AI embeddings"""
    try:
        file_path = request.get("file_path")
        if not file_path:
            raise ValueError("file_path is required")
        
        # Get file embedding
        analysis = await enhanced_llm_organizer.analyze_file_with_smart_selection(file_path)
        if "embedding" not in analysis:
            raise ValueError("Could not generate embedding for file")
        
        # Find similar files (this would need vector similarity search)
        # For now, return placeholder
        return {"success": True, "similar_files": [], "message": "Vector search not implemented"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cleanup/suggestions")
async def get_cleanup_suggestions():
    """Get file cleanup suggestions"""
    try:
        suggestions = {
            "large_files": db_manager.get_large_files(min_size_mb=100),
            "old_files": db_manager.get_old_files(days=365),
            "temp_files": db_manager.get_temp_files(),
            "empty_files": db_manager.get_empty_files()
        }
        return {"success": True, "suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/insights/generate")
async def generate_insights():
    """Generate AI insights about file collection"""
    try:
        stats = file_indexer.get_stats()
        
        # Generate insights using LLM
        insights = await enhanced_llm_organizer.generate_collection_insights(stats)
        
        return {"success": True, "insights": insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auto-organize")
async def auto_organize_directory(request: dict):
    """Automatically organize directory with AI suggestions"""
    try:
        source_dir = request.get("source_dir")
        if not source_dir:
            raise ValueError("source_dir is required")
        
        # Get AI suggestions for organization
        suggestions = await enhanced_llm_organizer.get_organization_suggestions(source_dir)
        
        return {"success": True, "suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tags/auto-generate")
async def auto_generate_tags(request: dict):
    """Automatically generate tags for files"""
    try:
        file_paths = request.get("file_paths", [])
        if not file_paths:
            raise ValueError("file_paths is required")
        
        results = []
        for file_path in file_paths:
            analysis = await enhanced_llm_organizer.analyze_file_with_smart_selection(file_path)
            tags = analysis.get("keywords", [])
            results.append({
                "file_path": file_path,
                "tags": tags
            })
        
        return {"success": True, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add scheduler endpoints
@app.get("/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status"""
    try:
        import psutil
        scheduler_running = False
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'scheduler.py' in str(proc.info['cmdline']):
                    scheduler_running = True
                    break
            except:
                continue
        
        return {
            "scheduler_running": scheduler_running,
            "message": "Scheduler status checked"
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/scheduler/trigger")
async def trigger_scheduler_indexing():
    """Trigger immediate indexing via scheduler"""
    try:
        import requests
        # This would trigger the scheduler if it had an API endpoint
        # For now, just trigger manual indexing
        background_tasks.add_task(run_background_indexing)
        return {"message": "Indexing triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)