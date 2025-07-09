#!/usr/bin/env python3
"""
Background indexer service for periodic file indexing
"""
import os
import time
import sqlite3
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import schedule
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileIndexer:
    def __init__(self, db_path: str, embeddings_path: str, metadata_path: str):
        self.db_path = db_path
        self.embeddings_path = embeddings_path
        self.metadata_path = metadata_path
        self.indexed_dirs = [
            "/Users/hyoseop1231/Documents",
            "/Users/hyoseop1231/Downloads", 
            "/Users/hyoseop1231/Desktop",
            "/Users/hyoseop1231/Pictures",
            "/Users/hyoseop1231/Movies",
            "/Users/hyoseop1231/Music"
        ]
        
        # Initialize directories
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        os.makedirs(embeddings_path, exist_ok=True)
        os.makedirs(metadata_path, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Files table with full-text search
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                extension TEXT,
                size INTEGER,
                modified_time REAL,
                content_hash TEXT,
                embedding_id TEXT,
                metadata_json TEXT,
                indexed_at REAL,
                UNIQUE(path)
            )
        ''')
        
        # Create FTS5 virtual table for full-text search
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
                path, name, content, metadata,
                content=files
            )
        ''')
        
        # Index for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_name ON files(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_extension ON files(extension)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_modified ON files(modified_time)')
        
        # Embeddings reference table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                id TEXT PRIMARY KEY,
                file_id INTEGER,
                model TEXT,
                vector_path TEXT,
                created_at REAL,
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
        ''')
        
        # Query cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS query_cache (
                query_hash TEXT PRIMARY KEY,
                query TEXT,
                results TEXT,
                created_at REAL,
                expires_at REAL
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def _calculate_file_hash(self, file_path: str, max_size: int = 1024 * 1024) -> str:
        """Calculate hash of file content (first 1MB for large files)"""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                data = f.read(max_size)
                hasher.update(data)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {e}")
            return ""
            
    def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from file"""
        metadata = {
            "name": file_path.name,
            "extension": file_path.suffix.lower(),
            "size": file_path.stat().st_size,
            "modified": file_path.stat().st_mtime,
            "parent_dir": str(file_path.parent),
            "is_hidden": file_path.name.startswith('.')
        }
        
        # Add file type categorization
        extension = metadata["extension"]
        if extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']:
            metadata["category"] = "image"
        elif extension in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            metadata["category"] = "video"
        elif extension in ['.mp3', '.wav', '.flac', '.aac', '.ogg']:
            metadata["category"] = "audio"
        elif extension in ['.pdf', '.doc', '.docx', '.txt', '.md']:
            metadata["category"] = "document"
        elif extension in ['.py', '.js', '.java', '.cpp', '.c', '.go']:
            metadata["category"] = "code"
        elif extension in ['.zip', '.tar', '.gz', '.rar', '.7z']:
            metadata["category"] = "archive"
        else:
            metadata["category"] = "other"
            
        return metadata
        
    def _should_index_file(self, file_path: Path) -> bool:
        """Check if file should be indexed"""
        # Skip hidden files and directories
        if any(part.startswith('.') for part in file_path.parts):
            return False
            
        # Skip system files
        skip_patterns = ['__pycache__', 'node_modules', '.git', '.DS_Store']
        if any(pattern in str(file_path) for pattern in skip_patterns):
            return False
            
        # Skip very large files (>1GB)
        try:
            if file_path.stat().st_size > 1024 * 1024 * 1024:
                return False
        except:
            return False
            
        return True
        
    def index_directory(self, directory: str):
        """Index all files in a directory"""
        logger.info(f"Indexing directory: {directory}")
        
        if not os.path.exists(directory):
            logger.warning(f"Directory does not exist: {directory}")
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        indexed_count = 0
        skipped_count = 0
        
        try:
            for root, dirs, files in os.walk(directory):
                # Filter out hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file_name in files:
                    file_path = Path(root) / file_name
                    
                    if not self._should_index_file(file_path):
                        skipped_count += 1
                        continue
                        
                    try:
                        # Extract metadata
                        metadata = self._extract_metadata(file_path)
                        
                        # Calculate content hash
                        content_hash = self._calculate_file_hash(str(file_path))
                        
                        # Check if file already indexed and unchanged
                        cursor.execute(
                            "SELECT content_hash FROM files WHERE path = ?",
                            (str(file_path),)
                        )
                        existing = cursor.fetchone()
                        
                        if existing and existing[0] == content_hash:
                            # File unchanged, skip
                            continue
                            
                        # Insert or update file record
                        cursor.execute('''
                            INSERT OR REPLACE INTO files 
                            (path, name, extension, size, modified_time, 
                             content_hash, metadata_json, indexed_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            str(file_path),
                            metadata["name"],
                            metadata["extension"],
                            metadata["size"],
                            metadata["modified"],
                            content_hash,
                            json.dumps(metadata),
                            time.time()
                        ))
                        
                        indexed_count += 1
                        
                        if indexed_count % 100 == 0:
                            conn.commit()
                            logger.info(f"Indexed {indexed_count} files...")
                            
                    except Exception as e:
                        logger.error(f"Error indexing file {file_path}: {e}")
                        
            conn.commit()
            logger.info(f"Indexing complete. Indexed: {indexed_count}, Skipped: {skipped_count}")
            
        finally:
            conn.close()
            
    def clean_cache(self):
        """Clean expired cache entries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM query_cache WHERE expires_at < ?",
            (time.time(),)
        )
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted > 0:
            logger.info(f"Cleaned {deleted} expired cache entries")
            
    def run_indexing(self):
        """Run full indexing process"""
        logger.info("Starting indexing process...")
        start_time = time.time()
        
        # Index each directory
        for directory in self.indexed_dirs:
            self.index_directory(directory)
            
        # Clean expired cache
        self.clean_cache()
        
        elapsed = time.time() - start_time
        logger.info(f"Indexing completed in {elapsed:.2f} seconds")
        
    def get_stats(self) -> Dict[str, Any]:
        """Get indexing statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total files
        cursor.execute("SELECT COUNT(*) FROM files")
        stats["total_files"] = cursor.fetchone()[0]
        
        # Files by category
        cursor.execute("""
            SELECT 
                json_extract(metadata_json, '$.category') as category,
                COUNT(*) as count
            FROM files
            GROUP BY category
        """)
        stats["by_category"] = dict(cursor.fetchall())
        
        # Total size
        cursor.execute("SELECT SUM(size) FROM files")
        total_size = cursor.fetchone()[0] or 0
        stats["total_size_gb"] = round(total_size / (1024**3), 2)
        
        # Recent files
        cursor.execute("""
            SELECT COUNT(*) FROM files 
            WHERE indexed_at > ?
        """, (time.time() - 86400,))  # Last 24 hours
        stats["indexed_last_24h"] = cursor.fetchone()[0]
        
        conn.close()
        return stats


def main():
    # Configuration from environment
    db_path = os.environ.get("DB_PATH", "/db/file-index.db")
    embeddings_path = os.environ.get("EMBEDDINGS_PATH", "/embeddings")
    metadata_path = os.environ.get("METADATA_PATH", "/metadata")
    index_interval = int(os.environ.get("INDEX_INTERVAL", 7200))  # 2 hours default
    
    # Create indexer
    indexer = FileIndexer(db_path, embeddings_path, metadata_path)
    
    # Run initial indexing
    indexer.run_indexing()
    
    # Log initial stats
    stats = indexer.get_stats()
    logger.info(f"Initial indexing stats: {json.dumps(stats, indent=2)}")
    
    # Schedule periodic indexing
    schedule.every(index_interval).seconds.do(indexer.run_indexing)
    
    logger.info(f"Indexer started. Will run every {index_interval} seconds.")
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    main()