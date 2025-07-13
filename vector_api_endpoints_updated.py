"""
Vector Search API Endpoints for Smart File Manager
Advanced semantic search using Qdrant
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from enhanced_embedding_manager import EnhancedEmbeddingManager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/vector", tags=["vector"])

# Request/Response models
class VectorSearchRequest(BaseModel):
    query: str = Field(..., description="Search query text")
    top_k: int = Field(10, ge=1, le=100, description="Number of results to return")
    score_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters")
    use_hybrid: bool = Field(True, description="Combine vector and keyword search")

class VectorSearchResult(BaseModel):
    file_path: str
    score: float
    metadata: Dict[str, Any]
    preview: Optional[str] = None

class VectorSearchResponse(BaseModel):
    query: str
    results: List[VectorSearchResult]
    total_found: int
    search_method: str
    processing_time: float

class VectorStatsResponse(BaseModel):
    sqlite_stats: Dict[str, Any]
    qdrant_stats: Optional[Dict[str, Any]]
    migration_status: Dict[str, Any]

class MigrationRequest(BaseModel):
    batch_size: int = Field(100, ge=10, le=1000, description="Batch size for migration")
    confirm: bool = Field(False, description="Confirm migration start")

# Global embedding manager (initialized in main app)
embedding_manager: Optional[EnhancedEmbeddingManager] = None

def set_embedding_manager(manager: EnhancedEmbeddingManager):
    """Set the global embedding manager"""
    global embedding_manager
    embedding_manager = manager

@router.post("/search", response_model=VectorSearchResponse)
async def vector_search(request: VectorSearchRequest):
    """
    Perform semantic vector search across indexed files
    
    Features:
    - Qdrant-powered similarity search
    - SQLite fallback for reliability
    - Optional hybrid search combining vector and keyword matching
    - Custom filters support
    """
    if not embedding_manager:
        raise HTTPException(status_code=500, detail="Embedding manager not initialized")
    
    import time
    start_time = time.time()
    
    try:
        # Perform vector search
        results = await embedding_manager.semantic_search_async(
            query_text=request.query,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            filters=request.filters
        )
        
        # Format results
        formatted_results = []
        for file_path, score, metadata in results:
            formatted_results.append(
                VectorSearchResult(
                    file_path=file_path,
                    score=score,
                    metadata=metadata,
                    preview=metadata.get("preview", None)
                )
            )
        
        # Determine search method
        search_method = "qdrant"
        if embedding_manager.use_qdrant:
            if not results or (results and results[0][2].get("source") == "sqlite"):
                search_method = "sqlite_fallback"
        else:
            search_method = "sqlite_only"
        
        processing_time = time.time() - start_time
        
        return VectorSearchResponse(
            query=request.query,
            results=formatted_results,
            total_found=len(formatted_results),
            search_method=search_method,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Vector search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=VectorStatsResponse)
async def get_vector_stats():
    """
    Get statistics about vector storage systems
    
    Returns information about:
    - SQLite embedding storage
    - Qdrant vector database (if available)
    - Migration status
    """
    if not embedding_manager:
        raise HTTPException(status_code=500, detail="Embedding manager not initialized")
    
    try:
        stats = await embedding_manager.get_vector_stats()
        
        # Check migration status
        migration_status = {
            "qdrant_available": embedding_manager.use_qdrant,
            "migration_needed": False,
            "sqlite_count": stats["sqlite"]["total_embeddings"],
            "qdrant_count": 0
        }
        
        if stats.get("qdrant") and stats["qdrant"].get("status") == "connected":
            migration_status["qdrant_count"] = stats["qdrant"]["vectors_count"]
            migration_status["migration_needed"] = (
                stats["sqlite"]["total_embeddings"] > stats["qdrant"]["vectors_count"]
            )
        
        return VectorStatsResponse(
            sqlite_stats=stats["sqlite"],
            qdrant_stats=stats.get("qdrant"),
            migration_status=migration_status
        )
        
    except Exception as e:
        logger.error(f"Error getting vector stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/migrate")
async def migrate_to_qdrant(request: MigrationRequest):
    """
    Migrate embeddings from SQLite to Qdrant
    
    This is a one-time operation to move existing embeddings
    to the high-performance Qdrant vector database.
    """
    if not embedding_manager:
        raise HTTPException(status_code=500, detail="Embedding manager not initialized")
    
    if not embedding_manager.use_qdrant:
        raise HTTPException(status_code=400, detail="Qdrant not available")
    
    if not request.confirm:
        return {
            "status": "confirmation_required",
            "message": "Set 'confirm' to true to start migration"
        }
    
    try:
        # Start migration
        migrated_count = await embedding_manager.migrate_to_qdrant(
            batch_size=request.batch_size
        )
        
        return {
            "status": "completed",
            "migrated_count": migrated_count,
            "message": f"Successfully migrated {migrated_count} embeddings to Qdrant"
        }
        
    except Exception as e:
        logger.error(f"Migration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize")
async def optimize_vector_storage():
    """
    Optimize vector storage systems
    
    Performs:
    - SQLite cleanup of old embeddings
    - Qdrant index optimization
    - Memory optimization
    """
    if not embedding_manager:
        raise HTTPException(status_code=500, detail="Embedding manager not initialized")
    
    try:
        await embedding_manager.optimize_storage()
        
        return {
            "status": "completed",
            "message": "Vector storage optimization completed",
            "optimizations": {
                "sqlite": "Old embeddings cleaned",
                "qdrant": "Collection optimized" if embedding_manager.use_qdrant else "Not available"
            }
        }
        
    except Exception as e:
        logger.error(f"Optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def vector_health_check():
    """Check health of vector subsystem"""
    if not embedding_manager:
        return {
            "status": "unhealthy",
            "reason": "Embedding manager not initialized"
        }
    
    health = {
        "status": "healthy",
        "sqlite": "available",
        "qdrant": "unavailable"
    }
    
    if embedding_manager.use_qdrant:
        try:
            stats = await embedding_manager.qdrant_manager.get_collection_stats()
            if stats.get("status") == "connected":
                health["qdrant"] = "available"
                health["qdrant_vectors"] = stats.get("vectors_count", 0)
        except:
            pass
    
    return health