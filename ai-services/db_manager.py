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
from db_connection_pool import get_db_connection
from performance_monitor import get_performance_monitor

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str, cache_ttl: int = 3600):
        self.db_path = db_path
        self.cache_ttl = cache_ttl  # Cache time-to-live in seconds
        self._setup_database()
        
    def _get_connection(self):
        """Get optimized database connection"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA foreign_keys=ON")
        # Use dictionary factory for consistent access
        def dict_factory(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d
        conn.row_factory = dict_factory
        return conn
        
    def _setup_database(self):
        """Setup database with optimizations"""
        conn = self._get_connection()
        try:
            # Enable WAL mode
            conn.execute("PRAGMA journal_mode=WAL")
            conn.commit()
        except Exception as e:
            logger.warning(f"Database setup warning: {e}")
        finally:
            conn.close()
        
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
        monitor = get_performance_monitor()
        start_time = time.time()
        
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                
                monitor.increment_counter("db_queries")
                
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
                
                # Use FTS5 for text search (including file content)
                if query:
                    # Escape special characters for FTS5
                    escaped_query = self._escape_fts_query(query)
                    sql_parts.append("""
                        SELECT f.*, 
                               highlight(files_fts, 0, '<mark>', '</mark>') as highlighted_name,
                               highlight(files_fts, 1, '<mark>', '</mark>') as highlighted_path,
                               highlight(files_fts, 2, '<mark>', '</mark>') as highlighted_content,
                               snippet(files_fts, 2, '<mark>', '</mark>', '...', 30) as content_snippet,
                               bm25(files_fts) as relevance_score
                        FROM files f
                        JOIN files_fts ON f.id = files_fts.rowid
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
                if query:
                    # Order by relevance score when searching
                    sql_parts.append("ORDER BY relevance_score DESC, f.modified_time DESC")
                else:
                    # Order by modification time when browsing
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
                        'modified_time': row['modified_time'],
                        'modified': row['modified_time'],  # Keep for compatibility
                        'metadata': json.loads(row['metadata_json']) if row['metadata_json'] else {},
                        'content_extracted': bool(row.get('content_extracted', False)),
                        'has_text_content': bool(row.get('text_content')),
                        'score': 1.0  # Default score
                    }
                    
                    # Add relevance score if available (from FTS search)
                    if 'relevance_score' in row and row['relevance_score'] is not None:
                        result['score'] = abs(float(row['relevance_score']))  # BM25 can be negative
                    
                    # Add highlights if available
                    if 'highlighted_name' in row and row['highlighted_name']:
                        result['highlighted_name'] = row['highlighted_name']
                    else:
                        result['highlighted_name'] = row['name']
                        
                    if 'highlighted_path' in row and row['highlighted_path']:
                        result['highlighted_path'] = row['highlighted_path']
                    else:
                        result['highlighted_path'] = row['path']
                        
                    if 'highlighted_content' in row and row['highlighted_content']:
                        result['highlighted_content'] = row['highlighted_content']
                    
                    # Add content snippet for search results
                    if 'content_snippet' in row and row['content_snippet']:
                        result['snippet'] = row['content_snippet']
                    elif 'snippet' in row and row['snippet']:
                        result['snippet'] = row['snippet']
                    
                    # Add extraction metadata if available
                    if 'extraction_metadata' in row and row['extraction_metadata']:
                        try:
                            extraction_meta = json.loads(row['extraction_metadata'])
                            result['extraction_info'] = extraction_meta
                        except:
                            pass
                        
                    results.append(result)
                
                # Cache results only if we found something
                if results:
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
            
    def get_file_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file information by path"""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
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
            
            
    def search_by_category(self, category: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search files by category"""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
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
            
            
    def search_by_extension(self, extensions: List[str], limit: int = 50) -> List[Dict[str, Any]]:
        """Search files by extension"""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
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
            
            
    def get_recent_files(self, hours: int = 24, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recently modified files"""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
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
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
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
            
    
    def get_large_files(self, min_size_mb: int = 100) -> List[Dict[str, Any]]:
        """Get files larger than specified size"""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
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
            
    
    def get_old_files(self, days: int = 365) -> List[Dict[str, Any]]:
        """Get files older than specified days"""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
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
    
    def search_korean_documents(self, query: str = "", limit: int = 50) -> List[Dict[str, Any]]:
        """Search specifically Korean documents (HWP/HWPX files) with content support"""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
            if query:
                # Text-based search in Korean documents
                escaped_query = self._escape_fts_query(query)
                cursor.execute("""
                    SELECT f.*, 
                           highlight(files_fts, 0, '<mark>', '</mark>') as highlighted_name,
                           highlight(files_fts, 2, '<mark>', '</mark>') as highlighted_content,
                           snippet(files_fts, 2, '<mark>', '</mark>', '...', 50) as content_snippet,
                           bm25(files_fts) as relevance_score
                    FROM files f
                    JOIN files_fts ON f.id = files_fts.rowid
                    WHERE files_fts MATCH ? 
                    AND json_extract(f.metadata_json, '$.category') = 'korean_document'
                    ORDER BY relevance_score DESC, f.modified_time DESC
                    LIMIT ?
                """, (escaped_query, limit))
            else:
                # Browse all Korean documents
                cursor.execute("""
                    SELECT * FROM files 
                    WHERE json_extract(metadata_json, '$.category') = 'korean_document'
                    ORDER BY modified_time DESC 
                    LIMIT ?
                """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                result = {
                    'path': row['path'],
                    'name': row['name'],
                    'size': row['size'],
                    'modified_time': row['modified_time'],
                    'modified': row['modified_time'],
                    'metadata': json.loads(row['metadata_json']) if row['metadata_json'] else {},
                    'content_extracted': bool(row['content_extracted'] if 'content_extracted' in row.keys() else False),
                    'has_text_content': bool(row['text_content'] if 'text_content' in row.keys() else False),
                    'category': 'korean_document',
                    'score': 1.0
                }
                
                # Add search-specific fields if available
                if query:
                    if 'relevance_score' in row and row['relevance_score'] is not None:
                        result['score'] = abs(float(row['relevance_score']))
                    if 'highlighted_name' in row and row['highlighted_name']:
                        result['highlighted_name'] = row['highlighted_name']
                    if 'highlighted_content' in row and row['highlighted_content']:
                        result['highlighted_content'] = row['highlighted_content']
                    if 'content_snippet' in row and row['content_snippet']:
                        result['snippet'] = row['content_snippet']
                
                results.append(result)
            
            return results
            
    
    def get_temp_files(self) -> List[Dict[str, Any]]:
        """Get temporary files that can be cleaned up"""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
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
            
    
    def get_empty_files(self) -> List[Dict[str, Any]]:
        """Get empty files (0 bytes)"""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
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