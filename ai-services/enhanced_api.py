#!/usr/bin/env python3
"""
Enhanced AI Service with MAFM Multi-Agent + Local-File-Organizer features
Uses Ollama for local LLM processing - FIXED VERSION
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Body, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import time
import json
import logging
import asyncio
import sqlite3
from pathlib import Path
from datetime import datetime

# Import our components
from llm_organizer import LLMOrganizer
from enhanced_llm_organizer import EnhancedLLMOrganizer
from indexer import FileIndexer
from db_manager import DatabaseManager
from embedding_manager import EmbeddingManager
from performance_monitor import get_performance_monitor

app = FastAPI(title="Smart File Manager AI Service - Enhanced & Fixed")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handler for better debugging
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error for {request.method} {request.url}")
    logger.error(f"Request body: {await request.body()}")
    logger.error(f"Validation errors: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({
            "detail": exc.errors(),
            "body": exc.body,
            "message": "Request validation failed - check field names and types",
            "url": str(request.url),
            "method": request.method
        }),
    )

# Request debugging middleware
@app.middleware("http")
async def debug_request_middleware(request: Request, call_next):
    if request.method == "POST":
        body = await request.body()
        logger.info(f"POST request to {request.url}")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Body: {body.decode() if body else 'Empty'}")
        # Re-create request for further processing
        request._body = body
    
    response = await call_next(request)
    return response

# Initialize components
llm_organizer = LLMOrganizer()
enhanced_llm_organizer = EnhancedLLMOrganizer()

# Get paths from environment variables
db_path = os.environ.get("DB_PATH", "/tmp/smart-file-manager/db/file-index.db")
embeddings_path = os.environ.get("EMBEDDINGS_PATH", "/tmp/smart-file-manager/embeddings")
metadata_path = os.environ.get("METADATA_PATH", "/tmp/smart-file-manager/metadata")

db_manager = DatabaseManager(db_path)
file_indexer = FileIndexer(db_path, embeddings_path, metadata_path)
embedding_manager = EmbeddingManager(embeddings_path=embeddings_path)

# Global state for background tasks
background_tasks_dict = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Request models - Fixed version with proper Pydantic V2 syntax and MCP compatibility
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query in natural language")
    directories: Optional[List[str]] = Field(default_factory=list, description="Directories to search in")
    language: Optional[str] = Field(default="ko", description="Language for search")
    limit: Optional[int] = Field(default=10, description="Maximum number of results")
    use_llm: Optional[bool] = Field(default=True, description="Enable LLM-enhanced search")
    
    # MCP-specific fields that might be required
    args: Optional[List[Any]] = Field(default_factory=list, description="Additional arguments for MCP compatibility")
    kwargs: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional keyword arguments for MCP compatibility")
    
    class Config:
        # Allow extra fields that might be sent by MCP client
        extra = "allow"

class OrganizeRequest(BaseModel):
    sourceDir: str = Field(..., description="Source directory to organize")
    targetDir: Optional[str] = Field(default=None, description="Target directory for organized files")
    method: str = Field(default="content", description="Organization method")
    dryRun: Optional[bool] = Field(default=False, description="Preview mode without actual changes")
    use_llm: Optional[bool] = Field(default=True, description="Use LLM for categorization")
    
    # MCP-specific fields
    args: Optional[List[Any]] = Field(default_factory=list, description="Additional arguments for MCP compatibility")
    kwargs: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional keyword arguments for MCP compatibility")
    
    class Config:
        extra = "allow"

class WorkflowRequest(BaseModel):
    searchQuery: str = Field(..., description="Search query to find files")
    action: str = Field(..., description="Action to perform on found files")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional options")
    
    # MCP-specific fields
    args: Optional[List[Any]] = Field(default_factory=list, description="Additional arguments for MCP compatibility")
    kwargs: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional keyword arguments for MCP compatibility")
    
    class Config:
        extra = "allow"

class IndexRequest(BaseModel):
    directories: Optional[List[str]] = Field(default_factory=list, description="Directories to index")
    force: Optional[bool] = Field(default=False, description="Force reindexing")
    
    # MCP-specific fields
    args: Optional[List[Any]] = Field(default_factory=list, description="Additional arguments for MCP compatibility")
    kwargs: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional keyword arguments for MCP compatibility")
    
    class Config:
        extra = "allow"

class EmbeddingRequest(BaseModel):
    batch_size: Optional[int] = Field(default=100, description="Batch size for processing")
    file_types: Optional[List[str]] = Field(default_factory=list, description="File types to process")
    
    # MCP-specific fields
    args: Optional[List[Any]] = Field(default_factory=list, description="Additional arguments for MCP compatibility")
    kwargs: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional keyword arguments for MCP compatibility")
    
    class Config:
        extra = "allow"

@app.get("/test-db")
async def test_db():
    """Test database connectivity"""
    import sqlite3
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT COUNT(*) FROM files")
        file_count = cursor.fetchone()[0]
        
        # Test FTS query
        cursor.execute("SELECT COUNT(*) FROM files_fts WHERE files_fts MATCH 'pdf'")
        pdf_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "db_path": db_path,
            "total_files": file_count,
            "pdf_matches": pdf_count
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    """Enhanced health check with Ollama status and performance metrics"""
    monitor = get_performance_monitor()
    
    ollama_status = "unavailable"
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            ollama_base = os.environ.get("OLLAMA_API_URL", "http://host.docker.internal:11434/api/generate")
            # Extract base URL for health check
            if "/api/generate" in ollama_base:
                ollama_health_url = ollama_base.replace("/api/generate", "/api/tags")
            else:
                ollama_health_url = f"{ollama_base}/api/tags"
            
            async with session.get(ollama_health_url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("models"):
                        ollama_status = "available"
    except Exception as e:
        logger.debug(f"Ollama health check failed: {e}")
        pass
        
    stats = file_indexer.get_stats()
    health_status = monitor.get_health_status()
    
    return {
        "status": health_status["status"],
        "services": {
            "database": "healthy",
            "indexer": "available",
            "llm_organizer": "available",
            "ollama": ollama_status,
            "vectordb": "planned"
        },
        "db_stats": stats,
        "background_tasks": len(background_tasks_dict),
        "performance": {
            "system_metrics": health_status["system_metrics"],
            "issues": health_status["issues"]
        }
    }

@app.get("/metrics")
async def get_metrics():
    """Get comprehensive system metrics"""
    monitor = get_performance_monitor()
    return monitor.get_metrics_summary()

@app.get("/metrics/database")
async def get_database_metrics():
    """Get database-specific metrics"""
    monitor = get_performance_monitor()
    return monitor.get_database_metrics()

@app.get("/metrics/health")
async def get_health_metrics():
    """Get health status metrics"""
    monitor = get_performance_monitor()
    return monitor.get_health_status()

# FIXED: Primary search endpoint using raw request handling to avoid validation issues
@app.post("/search_raw")
async def search_files_raw(request: Request):
    """Enhanced search with LLM understanding and vector search - FIXED VERSION"""
    monitor = get_performance_monitor()
    start_time = time.time()
    
    try:
        monitor.increment_counter("search_requests")
        
        # Parse the request body manually to avoid validation issues
        body = await request.body()
        request_data = json.loads(body) if body else {}
        
        logger.info(f"Raw request data: {request_data}")
        
        # Extract parameters with defaults
        query = request_data.get("query", "")
        directories = request_data.get("directories", [])
        language = request_data.get("language", "ko")
        limit = request_data.get("limit", 10)
        use_llm = request_data.get("use_llm", True)
        
        logger.info(f"Search request: query='{query}', use_llm={use_llm}, limit={limit}")
        
        if not query:
            return {
                "success": False,
                "count": 0,
                "results": [],
                "method": "error",
                "error": "Query is required"
            }
        
        results = []
        search_method = "keyword"
        
        # Try LLM-enhanced search first if enabled
        if use_llm and query:
            try:
                logger.info("Attempting LLM-enhanced search")
                results = await llm_organizer.smart_search(
                    query,
                    directories or []
                )
                
                if results:
                    search_method = "llm_enhanced"
                    logger.info(f"LLM search returned {len(results)} results")
                else:
                    logger.info("LLM search returned no results, falling back to keyword search")
                    
            except Exception as llm_error:
                logger.error(f"LLM search error: {llm_error}")
                
        # If LLM search failed or returned no results, try direct database search
        if not results:
            try:
                logger.info("Performing direct database search")
                results = db_manager.search_files(
                    query,
                    directories,
                    limit
                )
                logger.info(f"Database search returned {len(results)} results")
            except Exception as db_error:
                logger.error(f"Database search error: {db_error}")
                results = []
                
        # Optional: Try vector search enhancement if available
        if results and len(results) < limit:
            try:
                query_embedding = await embedding_manager.generate_embedding(query)
                if query_embedding:
                    similar_files = await embedding_manager.search_similar(query_embedding, top_k=10)
                    
                    # Add similar files that aren't already in results
                    path_to_result = {r['path']: r for r in results}
                    
                    for sim_file in similar_files:
                        if sim_file['similarity'] > 0.6:
                            file_path = sim_file['metadata'].get('file_path')
                            if file_path and file_path not in path_to_result:
                                file_info = db_manager.get_file_by_path(file_path)
                                if file_info:
                                    file_info['score'] = sim_file['similarity']
                                    file_info['search_method'] = 'vector'
                                    results.append(file_info)
                                    
            except Exception as vector_error:
                logger.warning(f"Vector search error: {vector_error}")
                
        # Limit results and add metadata
        results = results[:limit]
        
        # Record timing
        end_time = time.time()
        duration = end_time - start_time
        monitor.record_timing("search_files", duration)
        
        return {
            "success": True,
            "count": len(results),
            "results": results,
            "method": search_method,
            "query": query
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {
            "success": False,
            "count": 0,
            "results": [],
            "method": "error",
            "error": str(e)
        }

# Original /search endpoint also fixed with raw request handling
@app.post("/search")
async def search_files(request: Request):
    """Enhanced search endpoint - same as search_raw but using original route"""
    return await search_files_raw(request)

# Alternative simple search endpoint for debugging
@app.post("/search_simple")
async def search_files_simple(raw_request: Dict[str, Any] = Body(...)):
    """Simple search endpoint for debugging"""
    try:
        query = raw_request.get("query", "")
        directories = raw_request.get("directories", None)
        limit = raw_request.get("limit", 10)
        
        logger.info(f"Simple search: query='{query}', directories={directories}, limit={limit}")
        
        if not query:
            return {"success": False, "error": "Query is required"}
        
        # Direct database search
        results = db_manager.search_files(query, directories, limit)
        
        return {
            "success": True,
            "count": len(results),
            "results": results,
            "method": "database_search",
            "query": query
        }
        
    except Exception as e:
        logger.error(f"Simple search error: {e}")
        return {
            "success": False,
            "count": 0,
            "results": [],
            "method": "error",
            "error": str(e)
        }

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

# Background task functions
async def run_llm_organization(task_id: str, source_dir: str, target_dir: str, 
                             method: str, dry_run: bool):
    """Background task for LLM-based organization"""
    try:
        background_tasks_dict[task_id] = {
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "progress": 0
        }
        
        results = await llm_organizer.organize_directory(
            source_dir, target_dir, method, dry_run
        )
        
        background_tasks_dict[task_id] = {
            "status": "completed",
            "started_at": background_tasks_dict[task_id]["started_at"],
            "completed_at": datetime.now().isoformat(),
            "results": results
        }
        
    except Exception as e:
        background_tasks_dict[task_id] = {
            "status": "failed",
            "error": str(e),
            "started_at": background_tasks_dict[task_id]["started_at"],
            "failed_at": datetime.now().isoformat()
        }

async def organize_simple(source_dir: str, target_dir: str, method: str, dry_run: bool):
    """Simple organization without LLM"""
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

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Get background task status"""
    if task_id in background_tasks_dict:
        return background_tasks_dict[task_id]
    else:
        raise HTTPException(status_code=404, detail="Task not found")

@app.get("/recent")
async def get_recent_files(hours: int = 24, limit: int = 50):
    """Get recently modified files"""
    results = db_manager.get_recent_files(hours, limit)
    return {
        "hours": hours,
        "count": len(results),
        "files": results
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)