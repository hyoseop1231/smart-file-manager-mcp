#!/usr/bin/env python3
"""
Minimal test API to diagnose search issue
"""

from fastapi import FastAPI
from db_connection_pool import get_db_connection
import os

app = FastAPI()

@app.get("/test")
async def test_search():
    db_path = os.environ.get("DB_PATH", "/tmp/smart-file-manager/db/file-index.db")
    
    results = []
    debug_info = {}
    
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Simple query
            cursor.execute("SELECT id, path, name FROM files LIMIT 3")
            rows = cursor.fetchall()
            
            debug_info["rows_count"] = len(rows)
            debug_info["rows_type"] = str(type(rows))
            
            if rows:
                debug_info["first_row_type"] = str(type(rows[0]))
                debug_info["first_row_repr"] = str(rows[0])
                
                # Process rows
                for row in rows:
                    result = {
                        "id": row.get("id"),
                        "path": row.get("path"),
                        "name": row.get("name")
                    }
                    results.append(result)
            
            return {
                "success": True,
                "results": results,
                "debug": debug_info
            }
    
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)