"""
Bridge module for MAFM (Multi-Agent File Manager) integration with Ollama
"""
import os
import sys
import json
from typing import List, Dict, Any
from pathlib import Path
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import asyncio
from ollama_bridge import ollama_service

class MAFMSearcher:
    def __init__(self):
        self.initialized = False
        self.vector_db = None
        self.embedding_model = None
        
    def initialize(self):
        """Initialize with Ollama"""
        if not self.initialized:
            try:
                # Ensure Ollama models are available
                ollama_service.ensure_all_models()
                self.initialized = True
                print("✅ MAFM initialized with Ollama")
            except Exception as e:
                print(f"Failed to initialize MAFM: {e}")
                self.initialized = False
    
    async def search(self, query: str, directories: List[str], limit: int = 10) -> Dict[str, Any]:
        """
        Perform semantic search using MAFM
        
        Args:
            query: Natural language search query
            directories: List of directories to search
            limit: Maximum number of results
            
        Returns:
            Dictionary with search results
        """
        try:
            # Initialize if needed
            if not self.initialized:
                self.initialize()
            
            all_results = []
            
            # Generate query embedding
            print(f"🔍 '{query}' 검색을 위한 임베딩 생성 중...")
            query_embedding = await ollama_service.generate_embedding(query)
            
            if not query_embedding:
                # Fallback to simple search
                for directory in directories:
                    all_results.extend(self._fallback_search(query, directory, limit))
            else:
                # Semantic search with embeddings
                file_embeddings = []
                file_paths = []
                
                # Collect files and generate embeddings
                print("📁 파일 스캔 및 임베딩 생성 중...")
                for directory in directories:
                    for root, _, files in os.walk(directory):
                        for file in files[:100]:  # Limit for performance
                            file_path = os.path.join(root, file)
                            file_paths.append(file_path)
                            
                            # Generate embedding for filename and content preview
                            file_text = f"{file} {self._get_file_preview(file_path)}"
                            file_embedding = await ollama_service.generate_embedding(file_text)
                            file_embeddings.append(file_embedding)
                
                # Calculate similarities
                if file_embeddings:
                    print("🧮 유사도 계산 중...")
                    query_vec = np.array(query_embedding).reshape(1, -1)
                    file_vecs = np.array(file_embeddings)
                    
                    similarities = cosine_similarity(query_vec, file_vecs)[0]
                    
                    # Get top results
                    top_indices = np.argsort(similarities)[-limit:][::-1]
                    
                    for idx in top_indices:
                        if similarities[idx] > 0.3:  # Threshold
                            result = {
                                "path": file_paths[idx],
                                "score": float(similarities[idx]),
                                "type": self._get_file_type(file_paths[idx]),
                                "size": self._get_file_size(file_paths[idx]),
                                "preview": self._get_file_preview(file_paths[idx])
                            }
                            all_results.append(result)
            
            # Sort by score and limit results
            all_results.sort(key=lambda x: x['score'], reverse=True)
            all_results = all_results[:limit]
            
            return {
                "status": "success",
                "query": query,
                "results": all_results,
                "total_found": len(all_results),
                "search_directories": directories
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "query": query,
                "results": []
            }
    
    def _fallback_search(self, query: str, directory: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback search implementation when MAFM is not available"""
        results = []
        query_lower = query.lower()
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if query_lower in file.lower():
                        file_path = os.path.join(root, file)
                        results.append({
                            "path": file_path,
                            "score": 0.5,  # Fixed score for simple matching
                            "type": self._get_file_type(file_path),
                            "size": self._get_file_size(file_path),
                            "preview": self._get_file_preview(file_path)
                        })
                        
                        if len(results) >= limit:
                            return results
        except Exception as e:
            print(f"Error in fallback search: {e}")
            
        return results
    
    def _get_file_type(self, path: str) -> str:
        """Get file type from extension"""
        ext = Path(path).suffix.lower()
        type_map = {
            '.txt': 'text',
            '.pdf': 'pdf',
            '.doc': 'document',
            '.docx': 'document',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.png': 'image',
            '.mp4': 'video',
            '.mp3': 'audio',
            '.zip': 'archive',
            '.tar': 'archive',
            '.gz': 'archive'
        }
        return type_map.get(ext, 'other')
    
    def _get_file_size(self, path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(path)
        except:
            return 0
    
    def _get_file_preview(self, path: str) -> str:
        """Get a preview of file content"""
        try:
            if self._get_file_type(path) == 'text':
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(200)
                    return content[:150] + "..." if len(content) > 150 else content
        except:
            pass
        return ""

# Global instance
mafm_searcher = MAFMSearcher()