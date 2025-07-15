#!/usr/bin/env python3
"""
Multimedia API v4.0 for Smart File Manager
Enhanced API with full multimedia content processing
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Body, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
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
import tempfile
import io

# Import enhanced components
from enhanced_indexer_v4 import EnhancedFileIndexer
from multimedia_processor import MultimediaProcessor
from ai_vision_service import AIVisionService
from speech_recognition_service import SpeechRecognitionService
from performance_monitor import get_performance_monitor
from db_connection_pool import get_db_connection
import psutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Smart File Manager Multimedia API v4.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize enhanced components
db_path = os.environ.get("DB_PATH", "/tmp/smart-file-manager/db/file-index.db")
embeddings_path = os.environ.get("EMBEDDINGS_PATH", "/tmp/smart-file-manager/embeddings")
metadata_path = os.environ.get("METADATA_PATH", "/tmp/smart-file-manager/metadata")

# Enhanced file indexer with multimedia support
enhanced_indexer = EnhancedFileIndexer(
    db_path=db_path,
    embeddings_path=embeddings_path,
    metadata_path=metadata_path,
    enable_ai_vision=True,
    enable_stt=True
)

# Initialize standalone services for direct API access
multimedia_processor = MultimediaProcessor(
    enable_ai_vision=True,
    enable_stt=True,
    cache_dir=metadata_path
)

try:
    ai_vision_service = AIVisionService(cache_dir=metadata_path)
    logger.info("✅ AI Vision service available")
except Exception as e:
    ai_vision_service = None
    logger.warning(f"⚠️ AI Vision service unavailable: {e}")

try:
    speech_recognition_service = SpeechRecognitionService(cache_dir=metadata_path)
    logger.info("✅ Speech Recognition service available")
except Exception as e:
    speech_recognition_service = None
    logger.warning(f"⚠️ Speech Recognition service unavailable: {e}")

# Background task management
background_tasks_dict = {}

# Request models
class MultimediaSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    media_types: Optional[List[str]] = Field(default=None, description="Filter by media types: image, video, audio")
    categories: Optional[List[str]] = Field(default=None, description="Filter by categories")
    limit: Optional[int] = Field(default=20, description="Maximum results")
    include_ai_analysis: Optional[bool] = Field(default=False, description="Include AI analysis in results")
    
class AIAnalysisRequest(BaseModel):
    file_path: str = Field(..., description="Path to file for analysis")
    analysis_type: str = Field(default="auto", description="Type of analysis: auto, image, speech")
    force_reanalysis: Optional[bool] = Field(default=False, description="Force re-analysis even if cached")

class ThumbnailRequest(BaseModel):
    file_path: str = Field(..., description="Path to media file")
    size: Optional[str] = Field(default="medium", description="Thumbnail size: small, medium, large")
    format: Optional[str] = Field(default="jpeg", description="Output format: jpeg, png")

# Static files for thumbnails and cache
thumbnail_dir = Path(metadata_path) / "thumbnails"
thumbnail_dir.mkdir(parents=True, exist_ok=True)
app.mount("/thumbnails", StaticFiles(directory=str(thumbnail_dir)), name="thumbnails")

video_thumbnail_dir = Path(metadata_path) / "video_thumbnails"
video_thumbnail_dir.mkdir(parents=True, exist_ok=True)
app.mount("/video_thumbnails", StaticFiles(directory=str(video_thumbnail_dir)), name="video_thumbnails")


@app.get("/")
async def root():
    """API root with version information"""
    return {
        "name": "Smart File Manager Multimedia API",
        "version": "4.0.0",
        "features": [
            "multimedia_content_extraction",
            "ai_image_analysis", 
            "speech_recognition",
            "thumbnail_generation",
            "enhanced_search",
            "real_time_processing"
        ],
        "endpoints": {
            "search": "/search/multimedia",
            "ai_analysis": "/ai/analyze",
            "thumbnails": "/media/thumbnail",
            "statistics": "/stats/multimedia",
            "processing": "/processing/status"
        }
    }


@app.get("/health")
async def health_check():
    """Enhanced health check with multimedia services"""
    monitor = get_performance_monitor()
    health_status = monitor.get_health_status()
    
    # Check multimedia services
    multimedia_status = {
        "multimedia_processor": "available",
        "ai_vision": "available" if ai_vision_service else "unavailable",
        "speech_recognition": "available" if speech_recognition_service else "unavailable",
        "enhanced_indexer": "available"
    }
    
    # Get indexer stats
    indexer_stats = enhanced_indexer.get_stats()
    multimedia_stats = enhanced_indexer.get_multimedia_stats()
    
    return {
        "status": health_status.get("status", "unknown"),
        "services": {
            "database": "healthy",
            "indexer": "available",
            **multimedia_status
        },
        "indexer_stats": indexer_stats,
        "multimedia_capabilities": multimedia_stats,
        "background_tasks": len(background_tasks_dict),
        "performance": {
            "system_metrics": {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            }
        }
    }


@app.post("/search/multimedia")
async def search_multimedia_content(request: MultimediaSearchRequest):
    """Advanced multimedia content search"""
    monitor = get_performance_monitor()
    start_time = time.time()
    
    try:
        monitor.increment_counter("multimedia_search_requests")
        
        # Build search query
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Base query with multimedia content
            sql_parts = []
            params = []
            
            if request.query:
                # Enhanced FTS search including multimedia content and AI analysis
                escaped_query = request.query.replace("'", "''")
                sql_parts.append("""
                    SELECT f.*, 
                           highlight(files_fts, 0, '<mark>', '</mark>') as highlighted_name,
                           highlight(files_fts, 1, '<mark>', '</mark>') as highlighted_path,
                           highlight(files_fts, 2, '<mark>', '</mark>') as highlighted_text_content,
                           highlight(files_fts, 3, '<mark>', '</mark>') as highlighted_multimedia_content,
                           highlight(files_fts, 4, '<mark>', '</mark>') as highlighted_ai_analysis,
                           bm25(files_fts) as relevance_score
                    FROM files f
                    JOIN files_fts ON f.id = files_fts.rowid
                    WHERE files_fts MATCH ?
                """)
                params.append(escaped_query)
            else:
                sql_parts.append("SELECT * FROM files f WHERE 1=1")
            
            # Filter by media types
            if request.media_types:
                if len(request.media_types) == 1:
                    sql_parts.append("AND f.media_type = ?")
                    params.append(request.media_types[0])
                else:
                    placeholders = ','.join(['?' for _ in request.media_types])
                    sql_parts.append(f"AND f.media_type IN ({placeholders})")
                    params.extend(request.media_types)
            
            # Filter by categories
            if request.categories:
                if len(request.categories) == 1:
                    sql_parts.append("AND f.category = ?")
                    params.append(request.categories[0])
                else:
                    placeholders = ','.join(['?' for _ in request.categories])
                    sql_parts.append(f"AND f.category IN ({placeholders})")
                    params.extend(request.categories)
            
            # Ordering and limit
            if request.query:
                sql_parts.append("ORDER BY relevance_score DESC, f.modified_time DESC")
            else:
                sql_parts.append("ORDER BY f.modified_time DESC")
            
            sql_parts.append(f"LIMIT {request.limit}")
            
            # Execute search
            sql = ' '.join(sql_parts)
            cursor.execute(sql, params)
            
            results = []
            for row in cursor.fetchall():
                result = {
                    'id': row['id'],
                    'path': row['path'],
                    'name': row['name'],
                    'size': row['size'],
                    'modified_time': row['modified_time'],
                    'media_type': row['media_type'],
                    'category': row['category'],
                    'has_multimedia_content': bool(row.get('multimedia_content')),
                    'has_ai_analysis': bool(row.get('ai_analysis')),
                    'has_thumbnail': bool(row.get('thumbnail_path')),
                    'processing_status': json.loads(row['processing_status']) if row.get('processing_status') else {},
                    'score': abs(float(row['relevance_score'])) if 'relevance_score' in row.keys() and row['relevance_score'] else 1.0
                }
                
                # Add highlights
                for field in ['highlighted_name', 'highlighted_path', 'highlighted_text_content', 
                            'highlighted_multimedia_content', 'highlighted_ai_analysis']:
                    if field in row.keys() and row[field]:
                        result[field] = row[field]
                
                # Include AI analysis if requested
                if request.include_ai_analysis and row.get('ai_analysis'):
                    result['ai_analysis'] = row['ai_analysis']
                
                # Add multimedia metadata summary
                if row.get('multimedia_metadata'):
                    try:
                        mm_meta = json.loads(row['multimedia_metadata'])
                        result['multimedia_info'] = {
                            'duration': mm_meta.get('duration'),
                            'resolution': mm_meta.get('resolution'),
                            'format': mm_meta.get('format'),
                            'codec': mm_meta.get('video_codec') or mm_meta.get('audio_codec')
                        }
                    except:
                        pass
                
                # Add thumbnail URL if available
                if row.get('thumbnail_path'):
                    thumbnail_path = Path(row['thumbnail_path'])
                    if thumbnail_path.exists():
                        # Generate relative URL
                        if 'video_thumbnails' in str(thumbnail_path):
                            result['thumbnail_url'] = f"/video_thumbnails/{thumbnail_path.name}"
                        else:
                            result['thumbnail_url'] = f"/thumbnails/{thumbnail_path.name}"
                
                results.append(result)
            
            # Record timing
            duration = time.time() - start_time
            monitor.record_timing("multimedia_search", duration)
            
            return {
                "success": True,
                "count": len(results),
                "results": results,
                "search_method": "multimedia_enhanced",
                "query": request.query,
                "filters": {
                    "media_types": request.media_types,
                    "categories": request.categories
                },
                "processing_time": duration
            }
    
    except Exception as e:
        logger.error(f"Multimedia search error: {e}")
        return {
            "success": False,
            "count": 0,
            "results": [],
            "error": str(e)
        }


@app.post("/ai/analyze")
async def ai_analyze_file(request: AIAnalysisRequest):
    """Perform AI analysis on a file"""
    file_path = Path(request.file_path)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        analysis_results = {}
        
        # Determine analysis type
        if request.analysis_type == "auto":
            # Auto-detect based on file extension
            extension = file_path.suffix.lower()
            if extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                analysis_type = "image"
            elif extension in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']:
                analysis_type = "speech"
            elif extension in ['.mp4', '.avi', '.mkv', '.mov']:
                analysis_type = "video"  # Can include both image and speech analysis
            else:
                analysis_type = "multimedia"
        else:
            analysis_type = request.analysis_type
        
        # Perform image analysis
        if analysis_type in ["image", "video"] and ai_vision_service:
            try:
                description, confidence, metadata = ai_vision_service.analyze_image(str(file_path))
                analysis_results["image_analysis"] = {
                    "description": description,
                    "confidence": confidence,
                    "metadata": metadata,
                    "analysis_time": time.time()
                }
            except Exception as e:
                analysis_results["image_analysis"] = {"error": str(e)}
        
        # Perform speech analysis
        if analysis_type in ["speech", "audio", "video"] and speech_recognition_service:
            try:
                # For video files, extract audio first
                if analysis_type == "video":
                    audio_path = str(file_path)  # Let speech service handle conversion
                else:
                    audio_path = str(file_path)
                
                text, confidence, metadata = speech_recognition_service.transcribe_audio(
                    audio_path, language="ko"
                )
                analysis_results["speech_analysis"] = {
                    "transcription": text,
                    "confidence": confidence,
                    "metadata": metadata,
                    "analysis_time": time.time()
                }
            except Exception as e:
                analysis_results["speech_analysis"] = {"error": str(e)}
        
        # Perform general multimedia analysis
        if analysis_type == "multimedia":
            try:
                text, success, metadata = multimedia_processor.extract_content(str(file_path))
                analysis_results["multimedia_analysis"] = {
                    "extracted_text": text,
                    "success": success,
                    "metadata": metadata,
                    "analysis_time": time.time()
                }
            except Exception as e:
                analysis_results["multimedia_analysis"] = {"error": str(e)}
        
        # Update database with analysis results
        if analysis_results and not any("error" in result for result in analysis_results.values()):
            try:
                with get_db_connection(db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Combine AI analysis text
                    ai_text_parts = []
                    if "image_analysis" in analysis_results:
                        ai_text_parts.append(f"Image: {analysis_results['image_analysis']['description']}")
                    if "speech_analysis" in analysis_results:
                        ai_text_parts.append(f"Speech: {analysis_results['speech_analysis']['transcription']}")
                    
                    ai_analysis_text = " | ".join(ai_text_parts)
                    
                    # Update file record
                    cursor.execute("""
                        UPDATE files 
                        SET ai_analysis = ?, last_analyzed = ?
                        WHERE path = ?
                    """, (ai_analysis_text, time.time(), str(file_path)))
                    
                    conn.commit()
            except Exception as e:
                logger.warning(f"Failed to update database with analysis results: {e}")
        
        return {
            "success": True,
            "file_path": str(file_path),
            "analysis_type": analysis_type,
            "results": analysis_results,
            "analyzed_at": time.time()
        }
    
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/media/thumbnail/{file_id}")
async def get_thumbnail(file_id: int, size: str = "medium"):
    """Get thumbnail for media file"""
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT path, thumbnail_path, category, media_type 
                FROM files WHERE id = ?
            """, (file_id,))
            
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="File not found")
            
            file_path, thumbnail_path, category, media_type = row
            
            # If thumbnail exists, serve it
            if thumbnail_path and os.path.exists(thumbnail_path):
                return FileResponse(thumbnail_path)
            
            # Generate thumbnail on-demand
            if media_type == "multimedia":
                if category == "image" and ai_vision_service:
                    # Generate image thumbnail using multimedia processor
                    try:
                        _, _, metadata = multimedia_processor.extract_content(file_path)
                        if metadata.get("thumbnail_path"):
                            return FileResponse(metadata["thumbnail_path"])
                    except:
                        pass
                
                elif category in ["video", "audio"]:
                    # Generate video thumbnail
                    try:
                        # Use multimedia processor to generate thumbnail
                        _, _, metadata = multimedia_processor.extract_content(file_path)
                        thumbnail_paths = metadata.get("thumbnail_paths", [])
                        if thumbnail_paths:
                            return FileResponse(thumbnail_paths[0])
                    except:
                        pass
            
            # Fallback: return default thumbnail based on file type
            default_thumbnails = {
                "image": "/static/default_image_thumb.png",
                "video": "/static/default_video_thumb.png", 
                "audio": "/static/default_audio_thumb.png",
                "document": "/static/default_doc_thumb.png"
            }
            
            default_thumb = default_thumbnails.get(category, "/static/default_file_thumb.png")
            raise HTTPException(status_code=404, detail=f"Thumbnail not available. Use {default_thumb}")
    
    except Exception as e:
        logger.error(f"Thumbnail generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload/analyze")
async def upload_and_analyze(file: UploadFile = File(...), analysis_type: str = "auto"):
    """Upload file and perform immediate analysis"""
    try:
        # Save uploaded file temporarily
        temp_dir = Path(metadata_path) / "temp_uploads"
        temp_dir.mkdir(exist_ok=True)
        
        temp_file = temp_dir / f"{int(time.time())}_{file.filename}"
        
        with open(temp_file, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Perform analysis
        analysis_request = AIAnalysisRequest(
            file_path=str(temp_file),
            analysis_type=analysis_type,
            force_reanalysis=True
        )
        
        result = await ai_analyze_file(analysis_request)
        
        # Clean up temporary file
        os.unlink(temp_file)
        
        # Remove file path from result for security
        result["file_path"] = file.filename
        
        return result
    
    except Exception as e:
        logger.error(f"Upload and analyze error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats/multimedia")
async def get_multimedia_statistics():
    """Get comprehensive multimedia processing statistics"""
    try:
        # Get indexer stats
        indexer_stats = enhanced_indexer.get_stats()
        multimedia_stats = enhanced_indexer.get_multimedia_stats()
        
        # Get service capabilities
        capabilities = {
            "multimedia_processor": multimedia_processor.get_statistics(),
            "ai_vision": ai_vision_service.get_statistics() if ai_vision_service else {},
            "speech_recognition": speech_recognition_service.get_statistics() if speech_recognition_service else {}
        }
        
        # Database multimedia statistics
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Processing status breakdown
            cursor.execute("""
                SELECT 
                    JSON_EXTRACT(processing_status, '$.status') as status,
                    media_type,
                    COUNT(*) as count
                FROM files
                WHERE processing_status IS NOT NULL
                GROUP BY JSON_EXTRACT(processing_status, '$.status'), media_type
            """)
            
            processing_breakdown = {}
            for row in cursor.fetchall():
                status, media_type, count = row
                if status not in processing_breakdown:
                    processing_breakdown[status] = {}
                processing_breakdown[status][media_type or "unknown"] = count
            
            # AI analysis statistics
            cursor.execute("""
                SELECT 
                    media_type,
                    COUNT(*) as total,
                    SUM(CASE WHEN ai_analysis IS NOT NULL AND ai_analysis != '' THEN 1 ELSE 0 END) as analyzed
                FROM files
                WHERE media_type = 'multimedia'
                GROUP BY media_type
            """)
            
            ai_analysis_stats = {}
            for row in cursor.fetchall():
                media_type, total, analyzed = row
                ai_analysis_stats[media_type] = {
                    "total": total,
                    "analyzed": analyzed,
                    "percentage": (analyzed / total * 100) if total > 0 else 0
                }
        
        return {
            "indexer_statistics": indexer_stats,
            "multimedia_capabilities": multimedia_stats,
            "service_capabilities": capabilities,
            "processing_breakdown": processing_breakdown,
            "ai_analysis_coverage": ai_analysis_stats,
            "timestamp": time.time()
        }
    
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/processing/status/{file_id}")
async def get_processing_status(file_id: int):
    """Get processing status for a specific file"""
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name, processing_status, media_type, category, 
                       content_extracted, ai_analysis, thumbnail_path
                FROM files WHERE id = ?
            """, (file_id,))
            
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="File not found")
            
            name, processing_status, media_type, category, content_extracted, ai_analysis, thumbnail_path = row
            
            status_data = json.loads(processing_status) if processing_status else {}
            
            return {
                "file_id": file_id,
                "file_name": name,
                "media_type": media_type,
                "category": category,
                "processing_status": status_data,
                "content_extracted": bool(content_extracted),
                "has_ai_analysis": bool(ai_analysis),
                "has_thumbnail": bool(thumbnail_path),
                "processing_complete": status_data.get("status") == "completed"
            }
    
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/processing/reprocess/{file_id}")
async def reprocess_file(file_id: int, background_tasks: BackgroundTasks):
    """Reprocess a file with latest multimedia capabilities"""
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT path FROM files WHERE id = ?", (file_id,))
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="File not found")
            
            file_path = row[0]
            
            # Start background reprocessing
            task_id = f"reprocess_{file_id}_{int(time.time())}"
            background_tasks.add_task(
                reprocess_file_background,
                task_id,
                file_path
            )
            
            return {
                "success": True,
                "task_id": task_id,
                "message": "Reprocessing started",
                "file_id": file_id
            }
    
    except Exception as e:
        logger.error(f"Reprocess request error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def reprocess_file_background(task_id: str, file_path: str):
    """Background task for reprocessing files"""
    try:
        background_tasks_dict[task_id] = {
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "progress": 0
        }
        
        # Reindex the file
        success = enhanced_indexer.index_file(file_path)
        
        background_tasks_dict[task_id] = {
            "status": "completed" if success else "failed",
            "started_at": background_tasks_dict[task_id]["started_at"],
            "completed_at": datetime.now().isoformat(),
            "success": success
        }
        
    except Exception as e:
        background_tasks_dict[task_id] = {
            "status": "failed",
            "error": str(e),
            "started_at": background_tasks_dict[task_id]["started_at"],
            "failed_at": datetime.now().isoformat()
        }


@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Get background task status"""
    if task_id in background_tasks_dict:
        return background_tasks_dict[task_id]
    else:
        raise HTTPException(status_code=404, detail="Task not found")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)