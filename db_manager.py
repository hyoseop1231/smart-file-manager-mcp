"""
Database manager for fast file queries
"""
import sqlite3
import json
import time
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str, cache_ttl: int = 3600):
        self.db_path = db_path
        self.cache_ttl = cache_ttl  # Cache time-to-live in seconds
        
    def _escape_fts_query(self, query: str) -> str:
        """Escape special characters for FTS5 queries"""
        # Replace special FTS5 characters with quoted versions
        special_chars = ['"', "'", ".", "(", ")", "[", "]", ":", "*", "?", "!", "-", "+"]
        escaped = query
        
        # If query contains special characters, wrap the whole thing in quotes
        if any(char in escaped for char in special_chars):
            escaped = f'"{escaped}"'
        
        return escaped
        
    def search_files(self, query: str, directories: Optional[List[str]] = None, 
                    limit: int = 10) -> List[Dict[str, Any]]:
        """Search files using indexed database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Check cache first
            query_hash = hashlib.md5(f"{query}{directories}{limit}".encode()).hexdigest()
            
            cursor.execute("""
                SELECT results FROM query_cache 
                WHERE query_hash = ? AND expires_at > ?
            """, (query_hash, time.time()))
            
            cached = cursor.fetchone()
            if cached:
                logger.info(f"Cache hit for query: {query}")
                return json.loads(cached['results'])
            
            # Build search query
            sql_parts = []
            params = []
            
            # Use FTS5 for text search
            if query:
                # Escape special characters for FTS5
                escaped_query = self._escape_fts_query(query)
                sql_parts.append("""
                    SELECT f.*, 
                           highlight(files_fts, 1, '<mark>', '</mark>') as highlighted_name,
                           snippet(files_fts, 2, '<mark>', '</mark>', '...', 20) as snippet,
                           rank as fts_rank
                    FROM files f
                    JOIN files_fts ON f.path = files_fts.path
                    WHERE files_fts MATCH ?
                """)
                params.append(escaped_query)
            else:
                sql_parts.append("SELECT * FROM files f WHERE 1=1")
            
            # Filter by directories
            if directories:
                placeholders = ','.join(['?' for _ in directories])
                sql_parts.append(f"AND f.path IN ({placeholders})")
                params.extend(directories)
            
            # Add ordering and limit
            sql_parts.append("ORDER BY f.modified_time DESC")
            sql_parts.append(f"LIMIT {limit}")
            
            # Execute search
            sql = ' '.join(sql_parts)
            cursor.execute(sql, params)
            
            results = []
            for row in cursor.fetchall():
                result = {
                    'path': row['path'],
                    'name': row['name'],
                    'size': row['size'],
                    'modified': row['modified_time'],
                    'metadata': json.loads(row['metadata_json']) if row['metadata_json'] else {},
                    'score': 1.0  # Can be improved with relevance scoring
                }
                
                # Add highlights if available
                if 'highlighted_name' in row.keys():
                    result['highlighted_name'] = row['highlighted_name']
                if 'snippet' in row.keys():
                    result['snippet'] = row['snippet']
                    
                results.append(result)
            
            # Cache results
            cursor.execute("""
                INSERT OR REPLACE INTO query_cache 
                (query_hash, query, results, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                query_hash,
                query,
                json.dumps(results),
                time.time(),
                time.time() + self.cache_ttl
            ))
            
            conn.commit()
            return results
            
        except Exception as e:
            logger.error(f"Database search error: {e}")
            raise
        finally:
            conn.close()
            
    def get_file_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file information by path"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM files WHERE path = ?
            """, (file_path,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'path': row['path'],
                    'name': row['name'],
                    'size': row['size'],
                    'modified': row['modified_time'],
                    'metadata': json.loads(row['metadata_json']) if row['metadata_json'] else {},
                    'indexed_at': row['indexed_at']
                }
            return None
            
        finally:
            conn.close()
            
    def search_by_category(self, category: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search files by category"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM files 
                WHERE json_extract(metadata_json, '$.category') = ?
                ORDER BY modified_time DESC
                LIMIT ?
            """, (category, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'path': row['path'],
                    'name': row['name'],
                    'size': row['size'],
                    'modified': row['modified_time'],
                    'metadata': json.loads(row['metadata_json']) if row['metadata_json'] else {}
                })
                
            return results
            
        finally:
            conn.close()
            
    def search_by_extension(self, extensions: List[str], limit: int = 50) -> List[Dict[str, Any]]:
        """Search files by extension"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            placeholders = ','.join(['?' for _ in extensions])
            cursor.execute(f"""
                SELECT * FROM files 
                WHERE extension IN ({placeholders})
                ORDER BY modified_time DESC
                LIMIT ?
            """, extensions + [limit])
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'path': row['path'],
                    'name': row['name'],
                    'size': row['size'],
                    'modified': row['modified_time'],
                    'metadata': json.loads(row['metadata_json']) if row['metadata_json'] else {}
                })
                
            return results
            
        finally:
            conn.close()
            
    def get_recent_files(self, hours: int = 24, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recently modified files"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            since = time.time() - (hours * 3600)
            
            cursor.execute("""
                SELECT * FROM files 
                WHERE modified_time > ?
                ORDER BY modified_time DESC
                LIMIT ?
            """, (since, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'path': row['path'],
                    'name': row['name'],
                    'size': row['size'],
                    'modified': row['modified_time'],
                    'metadata': json.loads(row['metadata_json']) if row['metadata_json'] else {}
                })
                
            return results
            
        finally:
            conn.close()
            
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            stats = {}
            
            # Total files
            cursor.execute("SELECT COUNT(*) FROM files")
            stats["total_files"] = cursor.fetchone()[0]
            
            # By category
            cursor.execute("""
                SELECT 
                    json_extract(metadata_json, '$.category') as category,
                    COUNT(*) as count,
                    SUM(size) as total_size
                FROM files
                GROUP BY category
            """)
            
            stats["by_category"] = {}
            for row in cursor.fetchall():
                stats["by_category"][row[0]] = {
                    "count": row[1],
                    "size_gb": round(row[2] / (1024**3), 2) if row[2] else 0
                }
                
            # Cache stats
            cursor.execute("SELECT COUNT(*) FROM query_cache WHERE expires_at > ?", (time.time(),))
            stats["active_cache_entries"] = cursor.fetchone()[0]
            
            return stats
            
        finally:
            conn.close()
    
    def find_duplicates(self) -> List[Dict[str, Any]]:
        """Find duplicate files based on size and name"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT name, size, COUNT(*) as count, GROUP_CONCAT(path) as paths
                FROM files 
                WHERE size > 0
                GROUP BY name, size
                HAVING COUNT(*) > 1
                ORDER BY size DESC, count DESC
            """)
            
            duplicates = []
            for row in cursor.fetchall():
                paths = row['paths'].split(',')
                duplicates.append({
                    'name': row['name'],
                    'size': row['size'],
                    'count': row['count'],
                    'paths': paths,
                    'potential_savings': row['size'] * (row['count'] - 1)
                })
            
            return duplicates
            
        finally:
            conn.close()
    
    def get_large_files(self, min_size_mb: int = 100) -> List[Dict[str, Any]]:
        """Get files larger than specified size"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            min_size_bytes = min_size_mb * 1024 * 1024
            cursor.execute("""
                SELECT * FROM files 
                WHERE size > ?
                ORDER BY size DESC
                LIMIT 100
            """, (min_size_bytes,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'path': row['path'],
                    'name': row['name'],
                    'size': row['size'],
                    'size_mb': round(row['size'] / (1024*1024), 2),
                    'modified': row['modified_time'],
                    'metadata': json.loads(row['metadata_json']) if row['metadata_json'] else {}
                })
            
            return results
            
        finally:
            conn.close()
    
    def get_old_files(self, days: int = 365) -> List[Dict[str, Any]]:
        """Get files older than specified days"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cutoff_time = time.time() - (days * 24 * 3600)
            cursor.execute("""
                SELECT * FROM files 
                WHERE modified_time < ?
                ORDER BY modified_time ASC
                LIMIT 100
            """, (cutoff_time,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'path': row['path'],
                    'name': row['name'],
                    'size': row['size'],
                    'modified': row['modified_time'],
                    'days_old': int((time.time() - row['modified_time']) / (24 * 3600)),
                    'metadata': json.loads(row['metadata_json']) if row['metadata_json'] else {}
                })
            
            return results
            
        finally:
            conn.close()
    
    def get_temp_files(self) -> List[Dict[str, Any]]:
        """Get temporary files that can be cleaned up"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            temp_patterns = ['%.tmp', '%.temp', '%~$%', '%.bak', '%.old', '%.log']
            temp_dirs = ['%/tmp/%', '%/temp/%', '%/.cache/%', '%/Downloads/%']
            
            conditions = []
            params = []
            
            # Add pattern conditions
            for pattern in temp_patterns:
                conditions.append("name LIKE ?")
                params.append(pattern)
            
            # Add directory conditions
            for dir_pattern in temp_dirs:
                conditions.append("path LIKE ?")
                params.append(dir_pattern)
            
            sql = f"""
                SELECT * FROM files 
                WHERE ({' OR '.join(conditions)})
                ORDER BY size DESC
                LIMIT 100
            """
            
            cursor.execute(sql, params)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'path': row['path'],
                    'name': row['name'],
                    'size': row['size'],
                    'modified': row['modified_time'],
                    'metadata': json.loads(row['metadata_json']) if row['metadata_json'] else {}
                })
            
            return results
            
        finally:
            conn.close()
    
    def get_empty_files(self) -> List[Dict[str, Any]]:
        """Get empty files (0 bytes)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM files 
                WHERE size = 0
                ORDER BY modified_time DESC
                LIMIT 100
            """)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'path': row['path'],
                    'name': row['name'],
                    'size': row['size'],
                    'modified': row['modified_time'],
                    'metadata': json.loads(row['metadata_json']) if row['metadata_json'] else {}
                })
            
            return results
            
        finally:
            conn.close()