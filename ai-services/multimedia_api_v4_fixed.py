#!/usr/bin/env python3
"""
Fixed multimedia search endpoint
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import os
import time
import json
import logging
from db_connection_pool import get_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Fixed Multimedia Search API")

# Request model
class MultimediaSearchRequest(BaseModel):
    query: Optional[str] = Field(default="", description="Search query")
    media_types: Optional[List[str]] = Field(default=None, description="Filter by media types: image, video, audio")
    categories: Optional[List[str]] = Field(default=None, description="Filter by categories")
    limit: Optional[int] = Field(default=20, description="Maximum results")
    include_ai_analysis: Optional[bool] = Field(default=False, description="Include AI analysis in results")

@app.post("/search/multimedia/fixed")
async def search_multimedia_content_fixed(request: MultimediaSearchRequest):
    """Fixed multimedia content search"""
    logger.info(f"Fixed search called: query='{request.query}', limit={request.limit}")
    
    db_path = os.environ.get("DB_PATH", "/tmp/smart-file-manager/db/file-index.db")
    start_time = time.time()
    
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Build search query
            sql_parts = []
            params = []
            
            if request.query and request.query.strip():
                # FTS search
                escaped_query = request.query.replace("'", "''")
                sql_parts.append("""
                    SELECT f.*, 
                           highlight(files_fts, 0, '<mark>', '</mark>') as highlighted_name,
                           highlight(files_fts, 1, '<mark>', '</mark>') as highlighted_path,
                           bm25(files_fts) as relevance_score
                    FROM files f
                    JOIN files_fts ON f.id = files_fts.rowid
                    WHERE files_fts MATCH ?
                """)
                params.append(escaped_query)
            else:
                # Simple query without FTS
                sql_parts.append("SELECT *, NULL as highlighted_name, NULL as highlighted_path, 1.0 as relevance_score FROM files f WHERE 1=1")
            
            # Add filters
            if request.media_types:
                placeholders = ','.join(['?' for _ in request.media_types])
                sql_parts.append(f"AND f.media_type IN ({placeholders})")
                params.extend(request.media_types)
            
            if request.categories:
                placeholders = ','.join(['?' for _ in request.categories])
                sql_parts.append(f"AND f.category IN ({placeholders})")
                params.extend(request.categories)
            
            # Order and limit
            sql_parts.append("ORDER BY relevance_score DESC, f.modified_time DESC")
            sql_parts.append(f"LIMIT {request.limit}")
            
            # Execute query
            sql = ' '.join(sql_parts)
            logger.info(f"Executing SQL: {sql}")
            logger.info(f"With params: {params}")
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            logger.info(f"Found {len(rows)} rows")
            
            # Process results
            results = []
            for row in rows:
                # Convert Row to dict
                if hasattr(row, 'keys'):
                    row_dict = dict(row)
                else:
                    # Fallback for tuple results
                    columns = [desc[0] for desc in cursor.description]
                    row_dict = dict(zip(columns, row))
                
                # Parse processing status
                processing_status = {}
                try:
                    ps = row_dict.get('processing_status')
                    if ps and isinstance(ps, str) and ps.strip() and ps != 'null':
                        processing_status = json.loads(ps)
                except:
                    pass
                
                # Build result
                result = {
                    'id': row_dict.get('id'),
                    'path': row_dict.get('path'),
                    'name': row_dict.get('name'),
                    'size': row_dict.get('size', 0),
                    'modified_time': row_dict.get('modified_time', 0),
                    'media_type': row_dict.get('media_type'),
                    'category': row_dict.get('category'),
                    'has_multimedia_content': bool(row_dict.get('multimedia_content')),
                    'has_ai_analysis': bool(row_dict.get('ai_analysis')),
                    'has_thumbnail': bool(row_dict.get('thumbnail_path')),
                    'processing_status': processing_status,
                    'score': float(row_dict.get('relevance_score', 1.0))
                }
                
                # Add highlights if available
                if row_dict.get('highlighted_name'):
                    result['highlighted_name'] = row_dict['highlighted_name']
                if row_dict.get('highlighted_path'):
                    result['highlighted_path'] = row_dict['highlighted_path']
                
                # Include AI analysis if requested
                if request.include_ai_analysis and row_dict.get('ai_analysis'):
                    result['ai_analysis'] = row_dict['ai_analysis']
                
                results.append(result)
            
            duration = time.time() - start_time
            
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
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Search error: {error_msg}\n{error_trace}")
        return {
            "success": False,
            "count": 0,
            "results": [],
            "error": error_msg
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)