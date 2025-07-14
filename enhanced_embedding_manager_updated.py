"""
Enhanced Embedding Manager with Qdrant Integration
Combines SQLite fallback with Qdrant vector search
"""

import os
import logging
import asyncio
from typing import List, Tuple, Dict, Optional, Any
import numpy as np

from embedding_manager import EmbeddingManager
from qdrant_vector_manager import QdrantVectorManager

logger = logging.getLogger(__name__)

class EnhancedEmbeddingManager(EmbeddingManager):
    """Enhanced embedding manager with Qdrant support"""
    
    def __init__(self, embeddings_path: str, ollama_url: str = None):
        # Initialize base embedding manager
        super().__init__(embeddings_path, ollama_url)
        
        # Initialize Qdrant manager
        try:
            self.qdrant_manager = QdrantVectorManager(
                embedding_dim=768  # nomic-embed-text dimension
            )
            self.use_qdrant = True
            logger.info("Qdrant vector database initialized")
        except Exception as e:
            logger.warning(f"Qdrant initialization failed, using SQLite only: {e}")
            self.qdrant_manager = None
            self.use_qdrant = False
    
    async def store_embedding_async(
        self,
        file_path: str,
        content_hash: str,
        embedding: np.ndarray,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Store embedding in both SQLite and Qdrant"""
        # Store in SQLite (synchronous)
        sqlite_success = self.store_embedding(file_path, content_hash, embedding)
        
        # Store in Qdrant if available
        qdrant_success = True
        if self.use_qdrant and self.qdrant_manager:
            try:
                # Add content hash to metadata
                if metadata is None:
                    metadata = {}
                metadata["content_hash"] = content_hash
                
                qdrant_success = await self.qdrant_manager.store_embedding(
                    file_path, embedding, metadata
                )
            except Exception as e:
                logger.error(f"Qdrant storage failed: {e}")
                qdrant_success = False
        
        return sqlite_success and qdrant_success
    
    async def semantic_search_async(
        self,
        query_text: str,
        top_k: int = 50,
        score_threshold: float = 0.7,
        filters: Dict[str, Any] = None
    ) -> List[Tuple[str, float, Dict]]:
        """Enhanced semantic search using Qdrant when available"""
        # Generate query embedding
        query_embedding = self.generate_embedding(query_text)
        if query_embedding is None:
            return []
        
        # Try Qdrant first if available
        if self.use_qdrant and self.qdrant_manager:
            try:
                results = await self.qdrant_manager.search_similar(
                    query_embedding,
                    top_k=top_k,
                    score_threshold=score_threshold,
                    filters=filters
                )
                
                if results:
                    return results
                    
            except Exception as e:
                logger.error(f"Qdrant search failed: {e}")
        
        # Fallback to SQLite search
        sqlite_results = self.semantic_search(query_text, top_k)
        
        # Convert SQLite results to match Qdrant format
        enhanced_results = []
        for file_path, score in sqlite_results:
            enhanced_results.append((
                file_path,
                score,
                {"source": "sqlite", "file_path": file_path}
            ))
        
        return enhanced_results
    
    async def migrate_to_qdrant(self, batch_size: int = 100) -> int:
        """Migrate existing SQLite embeddings to Qdrant"""
        if not self.use_qdrant or not self.qdrant_manager:
            logger.error("Qdrant not available for migration")
            return 0
        
        try:
            # Get all embeddings from SQLite
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT file_path, content_hash, embedding 
                FROM embeddings
                ORDER BY created_at DESC
            """)
            
            migrated_count = 0
            batch = []
            
            for row in cursor:
                file_path = row[0]
                content_hash = row[1]
                embedding_bytes = row[2]
                
                # Convert bytes to numpy array
                embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                
                # Add to batch
                batch.append((
                    file_path,
                    embedding,
                    {"content_hash": content_hash, "migrated": True}
                ))
                
                # Process batch when full
                if len(batch) >= batch_size:
                    count = await self.qdrant_manager.batch_store_embeddings(batch)
                    migrated_count += count
                    batch = []
                    
                    if migrated_count % 1000 == 0:
                        logger.info(f"Migrated {migrated_count} embeddings...")
            
            # Process remaining batch
            if batch:
                count = await self.qdrant_manager.batch_store_embeddings(batch)
                migrated_count += count
            
            logger.info(f"Migration completed: {migrated_count} embeddings migrated to Qdrant")
            return migrated_count
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return 0
        finally:
            conn.close()
    
    async def get_vector_stats(self) -> Dict[str, Any]:
        """Get combined statistics from both storage systems"""
        stats = {
            "sqlite": self.get_stats(),
            "qdrant": None
        }
        
        if self.use_qdrant and self.qdrant_manager:
            stats["qdrant"] = await self.qdrant_manager.get_collection_stats()
        
        return stats
    
    async def optimize_storage(self):
        """Optimize both storage systems"""
        # Optimize SQLite
        self.cleanup_old_embeddings(days=30)
        
        # Optimize Qdrant
        if self.use_qdrant and self.qdrant_manager:
            await self.qdrant_manager.optimize_collection()
    
    def close(self):
        """Close all connections"""
        super().close()
        
        if self.qdrant_manager:
            self.qdrant_manager.close()