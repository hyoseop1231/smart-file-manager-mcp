"""
Qdrant Vector Database Manager for Smart File Manager
High-performance vector search using Qdrant
"""

import os
import logging
import hashlib
import uuid
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, 
    Filter, FieldCondition, Range,
    SearchRequest, SearchParams,
    UpdateStatus, CollectionStatus
)
from qdrant_client.http.exceptions import UnexpectedResponse

logger = logging.getLogger(__name__)

class QdrantVectorManager:
    """Advanced vector database manager using Qdrant"""
    
    def __init__(
        self, 
        qdrant_url: str = None,
        collection_name: str = "smart_files",
        embedding_dim: int = 768,  # nomic-embed-text dimension
        use_grpc: bool = False
    ):
        self.qdrant_url = qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        
        # Initialize Qdrant client
        try:
            self.client = QdrantClient(
                url=self.qdrant_url,
                prefer_grpc=use_grpc,
                timeout=30
            )
            logger.info(f"Connected to Qdrant at {self.qdrant_url}")
            
            # Initialize collection
            self._initialize_collection()
            
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            self.client = None
            
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def _initialize_collection(self):
        """Initialize or verify Qdrant collection"""
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                # Create new collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection '{self.collection_name}'")
            else:
                # Verify collection
                info = self.client.get_collection(self.collection_name)
                logger.info(f"Using existing collection '{self.collection_name}' with {info.points_count} points")
                
        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
    
    def generate_file_id(self, file_path: str) -> str:
        """Generate unique UUID for file using UUID v5 (deterministic)"""
        # Use a fixed namespace for file paths
        namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # URL namespace
        return str(uuid.uuid5(namespace, file_path))
    
    async def store_embedding(
        self, 
        file_path: str, 
        embedding: np.ndarray,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Store file embedding in Qdrant"""
        if not self.client:
            return False
            
        try:
            # Generate unique ID
            point_id = self.generate_file_id(file_path)
            
            # Prepare metadata
            payload = {
                "file_path": file_path,
                "indexed_at": datetime.now().isoformat(),
                "embedding_model": "nomic-embed-text"
            }
            
            if metadata:
                payload.update(metadata)
            
            # Create point
            point = PointStruct(
                id=point_id,
                vector=embedding.tolist(),
                payload=payload
            )
            
            # Upsert to Qdrant
            operation_info = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.upsert(
                    collection_name=self.collection_name,
                    points=[point]
                )
            )
            
            if operation_info.status == UpdateStatus.COMPLETED:
                logger.debug(f"Stored embedding for {file_path}")
                return True
            else:
                logger.error(f"Failed to store embedding: {operation_info}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing embedding: {e}")
            return False
    
    async def search_similar(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        score_threshold: float = 0.7,
        filters: Dict[str, Any] = None
    ) -> List[Tuple[str, float, Dict]]:
        """Search for similar files using vector similarity"""
        if not self.client:
            return []
            
        try:
            # Build filter if provided
            search_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, dict) and "min" in value:
                        # Range filter
                        conditions.append(
                            FieldCondition(
                                key=key,
                                range=Range(
                                    gte=value.get("min"),
                                    lte=value.get("max")
                                )
                            )
                        )
                    else:
                        # Exact match filter
                        conditions.append(
                            FieldCondition(key=key, match={"value": value})
                        )
                
                if conditions:
                    search_filter = Filter(must=conditions)
            
            # Perform search
            search_result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding.tolist(),
                    limit=top_k,
                    query_filter=search_filter,
                    score_threshold=score_threshold,
                    with_payload=True
                )
            )
            
            # Format results
            results = []
            for hit in search_result:
                if hit.payload:
                    results.append((
                        hit.payload.get("file_path", ""),
                        hit.score,
                        hit.payload
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar files: {e}")
            return []
    
    async def batch_store_embeddings(
        self,
        file_embeddings: List[Tuple[str, np.ndarray, Dict]]
    ) -> int:
        """Store multiple embeddings efficiently"""
        if not self.client:
            return 0
            
        try:
            points = []
            for file_path, embedding, metadata in file_embeddings:
                point_id = self.generate_file_id(file_path)
                
                payload = {
                    "file_path": file_path,
                    "indexed_at": datetime.now().isoformat(),
                    "embedding_model": "nomic-embed-text"
                }
                
                if metadata:
                    payload.update(metadata)
                
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding.tolist(),
                        payload=payload
                    )
                )
            
            # Batch upsert
            operation_info = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.upsert(
                    collection_name=self.collection_name,
                    points=points,
                    wait=True
                )
            )
            
            if operation_info.status == UpdateStatus.COMPLETED:
                logger.info(f"Stored {len(points)} embeddings in batch")
                return len(points)
            else:
                logger.error(f"Batch storage failed: {operation_info}")
                return 0
                
        except Exception as e:
            logger.error(f"Error in batch storage: {e}")
            return 0
    
    async def delete_embedding(self, file_path: str) -> bool:
        """Delete embedding for a file"""
        if not self.client:
            return False
            
        try:
            point_id = self.generate_file_id(file_path)
            
            operation_info = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=[point_id]
                )
            )
            
            return operation_info.status == UpdateStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Error deleting embedding: {e}")
            return False
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        if not self.client:
            return {"status": "disconnected"}
            
        try:
            info = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.get_collection(self.collection_name)
            )
            
            stats = {
                "status": "connected",
                "collection": self.collection_name,
                "vectors_count": info.points_count,
                "vectors_config": {
                    "size": info.config.params.vectors.size,
                    "distance": info.config.params.vectors.distance
                }
            }
            
            # Add optional fields if available
            if hasattr(info, 'disk_data_size'):
                stats["disk_size_mb"] = info.disk_data_size / (1024 * 1024)
            if hasattr(info, 'memory_size'):
                stats["memory_size_mb"] = info.memory_size / (1024 * 1024)
            if hasattr(info, 'indexed_vectors_count'):
                stats["indexed"] = info.indexed_vectors_count
            elif hasattr(info, 'indexed_count'):
                stats["indexed"] = info.indexed_count
                
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"status": "error", "message": str(e)}
    
    async def optimize_collection(self):
        """Optimize collection for better search performance"""
        if not self.client:
            return False
            
        try:
            # Create index for faster search
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="file_path",
                    field_type="keyword"
                )
            )
            
            # Optimize segments
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.update_collection(
                    collection_name=self.collection_name,
                    optimizer_config={
                        "deleted_threshold": 0.2,
                        "vacuum_min_vector_number": 1000,
                        "max_segment_number": 5
                    }
                )
            )
            
            logger.info("Collection optimization completed")
            return True
            
        except Exception as e:
            logger.error(f"Error optimizing collection: {e}")
            return False
    
    def close(self):
        """Close connections and cleanup"""
        if self.executor:
            self.executor.shutdown(wait=True)
        logger.info("Qdrant vector manager closed")