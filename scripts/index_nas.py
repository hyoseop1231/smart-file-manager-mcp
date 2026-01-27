#!/usr/bin/env python3
"""Index NAS files for Smart File Manager - Filtered"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ai-services"))

from pathlib import Path
import sqlite3
import hashlib
from datetime import datetime

# Skip patterns
SKIP_DIRS = {
    "venv", ".venv", "node_modules", "__pycache__", ".git", ".trash",
    "site-packages", ".cache", ".npm", ".pyenv"
}

IMPORTANT_EXTENSIONS = {
    # Documents
    ".pdf", ".doc", ".docx", ".hwp", ".hwpx", ".ppt", ".pptx", ".xls", ".xlsx",
    ".txt", ".md", ".rtf",
    # Images
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".bmp", ".tiff",
    # Videos
    ".mp4", ".mov", ".avi", ".mkv", ".webm",
    # Audio
    ".mp3", ".wav", ".flac", ".m4a", ".aac",
    # Archives
    ".zip", ".tar", ".gz", ".rar", ".7z",
    # Code (optional)
    ".py", ".js", ".ts", ".json", ".yaml", ".yml"
}

def should_skip_dir(dir_name):
    return dir_name in SKIP_DIRS or dir_name.startswith(".")

def is_important_file(file_path):
    ext = Path(file_path).suffix.lower()
    return ext in IMPORTANT_EXTENSIONS

def index_nas():
    nas_path = "/home/hyoseop1231/nas_khs"
    db_path = "/tmp/smart-file-manager/db/file-index.db"
    
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Create table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY,
            path TEXT UNIQUE,
            name TEXT,
            extension TEXT,
            size INTEGER,
            modified TEXT,
            category TEXT,
            indexed_at TEXT
        )
    """)
    conn.commit()
    
    print(f"🚀 Indexing NAS: {nas_path}")
    print(f"📁 Skipping: {SKIP_DIRS}")
    
    total = 0
    indexed = 0
    
    for root, dirs, files in os.walk(nas_path):
        # Filter out skip directories
        dirs[:] = [d for d in dirs if not should_skip_dir(d)]
        
        for fname in files:
            total += 1
            fpath = os.path.join(root, fname)
            
            if not is_important_file(fpath):
                continue
            
            try:
                stat = os.stat(fpath)
                ext = Path(fpath).suffix.lower()
                
                # Determine category
                if ext in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".bmp", ".tiff"}:
                    category = "image"
                elif ext in {".mp4", ".mov", ".avi", ".mkv", ".webm"}:
                    category = "video"
                elif ext in {".mp3", ".wav", ".flac", ".m4a", ".aac"}:
                    category = "audio"
                elif ext in {".pdf", ".doc", ".docx", ".hwp", ".hwpx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt", ".md", ".rtf"}:
                    category = "document"
                elif ext in {".zip", ".tar", ".gz", ".rar", ".7z"}:
                    category = "archive"
                else:
                    category = "other"
                
                cur.execute("""
                    INSERT OR REPLACE INTO files (path, name, extension, size, modified, category, indexed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (fpath, fname, ext, stat.st_size, datetime.fromtimestamp(stat.st_mtime).isoformat(), category, datetime.now().isoformat()))
                
                indexed += 1
                
                if indexed % 100 == 0:
                    print(f"✅ Indexed: {indexed} files (scanned {total})")
                    conn.commit()
                    
            except Exception as e:
                pass
    
    conn.commit()
    
    # Stats
    cur.execute("SELECT category, COUNT(*) FROM files GROUP BY category")
    stats = cur.fetchall()
    
    print(f"\n📊 Indexing Complete!")
    print(f"   Total scanned: {total}")
    print(f"   Indexed: {indexed}")
    print(f"\n📁 By Category:")
    for cat, count in stats:
        print(f"   {cat}: {count}")
    
    conn.close()

if __name__ == "__main__":
    index_nas()
