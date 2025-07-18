"""
Embedding Manager for Smart File Manager
임베딩 벡터 관리 및 의미 검색 기능
"""

import numpy as np
import sqlite3
import logging
from typing import List, Dict, Optional, Tuple
import requests
import json
import os

logger = logging.getLogger(__name__)

class EmbeddingManager:
    """벡터 임베딩 관리 클래스"""
    
    def __init__(self, embeddings_path: str = "/data/embeddings", db_path: str = None,
                 ollama_url: str = "http://host.docker.internal:11434"):
        # Support both embeddings_path (directory) and db_path (full file path) for compatibility
        if db_path is None:
            self.db_path = os.path.join(embeddings_path, "embeddings.db")
        else:
            self.db_path = db_path
        self.ollama_url = ollama_url
        self.model_name = "nomic-embed-text"
        self._init_db()
    
    def _init_db(self):
        """임베딩 데이터베이스 초기화"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    content_hash TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_path ON embeddings(file_path);
            """)
            
            conn.commit()
            conn.close()
            logger.info("Embedding database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize embedding database: {e}")
    
    def generate_embedding(self, text: str) -> Optional[np.ndarray]:
        """텍스트에서 임베딩 벡터 생성"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": self.model_name,
                    "prompt": text
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                embedding = np.array(data.get("embedding", []))
                return embedding if len(embedding) > 0 else None
            else:
                logger.error(f"Ollama embedding failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def store_embedding(self, file_path: str, content_hash: str, embedding: np.ndarray):
        """임베딩을 데이터베이스에 저장"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            embedding_blob = embedding.tobytes()
            
            cursor.execute("""
                INSERT OR REPLACE INTO embeddings 
                (file_path, content_hash, embedding, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (file_path, content_hash, embedding_blob))
            
            conn.commit()
            conn.close()
            logger.debug(f"Stored embedding for {file_path}")
            
        except Exception as e:
            logger.error(f"Error storing embedding: {e}")
    
    def get_embedding(self, file_path: str) -> Optional[np.ndarray]:
        """파일 경로로 임베딩 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT embedding FROM embeddings WHERE file_path = ?",
                (file_path,)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return np.frombuffer(result[0], dtype=np.float64)
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving embedding: {e}")
            return None
    
    def semantic_search(self, query_text: str, top_k: int = 50) -> List[Tuple[str, float]]:
        """의미 검색 수행"""
        try:
            # 쿼리 임베딩 생성
            query_embedding = self.generate_embedding(query_text)
            if query_embedding is None:
                return []
            
            # 모든 임베딩과 유사도 계산
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT file_path, embedding FROM embeddings")
            results = cursor.fetchall()
            conn.close()
            
            similarities = []
            for file_path, embedding_blob in results:
                try:
                    embedding = np.frombuffer(embedding_blob, dtype=np.float64)
                    similarity = self._cosine_similarity(query_embedding, embedding)
                    similarities.append((file_path, similarity))
                except Exception as e:
                    logger.warning(f"Error processing embedding for {file_path}: {e}")
            
            # 유사도 순으로 정렬
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """코사인 유사도 계산"""
        try:
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            return dot_product / (norm_a * norm_b)
        except Exception:
            return 0.0
    
    def update_embeddings_batch(self, files_data: List[Dict]) -> int:
        """배치로 임베딩 업데이트"""
        updated_count = 0
        
        for file_data in files_data:
            try:
                file_path = file_data.get("path")
                content = file_data.get("content", "")
                content_hash = file_data.get("hash")
                
                if not file_path or not content_hash:
                    continue
                
                # 기존 임베딩 확인
                existing = self.get_embedding(file_path)
                if existing is not None:
                    continue  # 이미 존재하면 스킵
                
                # 새 임베딩 생성
                embedding = self.generate_embedding(content[:2000])  # 처음 2000자만 사용
                if embedding is not None:
                    self.store_embedding(file_path, content_hash, embedding)
                    updated_count += 1
                    
            except Exception as e:
                logger.error(f"Error updating embedding for {file_data.get('path')}: {e}")
        
        return updated_count
    
    def cleanup_orphaned_embeddings(self, valid_file_paths: List[str]) -> int:
        """고아 임베딩 정리"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            placeholders = ",".join(["?" for _ in valid_file_paths])
            cursor.execute(
                f"DELETE FROM embeddings WHERE file_path NOT IN ({placeholders})",
                valid_file_paths
            )
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up {deleted_count} orphaned embeddings")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up embeddings: {e}")
            return 0
    
    def get_stats(self) -> Dict:
        """임베딩 통계 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM embeddings")
            total_embeddings = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM embeddings 
                WHERE updated_at > datetime('now', '-24 hours')
            """)
            recent_embeddings = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_embeddings": total_embeddings,
                "recent_embeddings": recent_embeddings,
                "model_name": self.model_name
            }
            
        except Exception as e:
            logger.error(f"Error getting embedding stats: {e}")
            return {}

# 전역 인스턴스
embedding_manager = None

def get_embedding_manager() -> EmbeddingManager:
    """임베딩 매니저 싱글톤 인스턴스 반환"""
    global embedding_manager
    if embedding_manager is None:
        embedding_manager = EmbeddingManager()
    return embedding_manager