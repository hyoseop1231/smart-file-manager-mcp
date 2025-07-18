#!/usr/bin/env python3
"""
Direct database test to diagnose fetchall() issue
"""

import sqlite3
import json
import os

db_path = os.environ.get("DB_PATH", "/tmp/smart-file-manager/db/file-index.db")
print(f"Testing database at: {db_path}")

try:
    # Test 1: Direct connection without any row factory
    print("\n=== Test 1: Direct connection (no row factory) ===")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, path, name FROM files LIMIT 3")
    rows = cursor.fetchall()
    print(f"Type of rows: {type(rows)}")
    print(f"Number of rows: {len(rows)}")
    for i, row in enumerate(rows):
        print(f"Row {i}: type={type(row)}, value={row}")
    
    # Test 2: With sqlite3.Row factory
    print("\n=== Test 2: With sqlite3.Row factory ===")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, path, name FROM files LIMIT 3")
    rows = cursor.fetchall()
    print(f"Type of rows: {type(rows)}")
    print(f"Number of rows: {len(rows)}")
    for i, row in enumerate(rows):
        print(f"Row {i}: type={type(row)}")
        # Convert Row to dict to see contents
        row_dict = dict(row)
        print(f"  As dict: {row_dict}")
        print(f"  Keys: {list(row_dict.keys())}")
        print(f"  id={row_dict.get('id')}, path={row_dict.get('path')[:50] if row_dict.get('path') else None}...")
    
    # Test 3: Check cursor.description
    print("\n=== Test 3: Cursor description ===")
    cursor.execute("SELECT id, path, name FROM files LIMIT 1")
    print(f"cursor.description: {cursor.description}")
    columns = [desc[0] for desc in cursor.description]
    print(f"Column names: {columns}")
    
    # Test 4: Check table structure
    print("\n=== Test 4: Table structure ===")
    cursor.execute("PRAGMA table_info(files)")
    table_info = cursor.fetchall()
    print("Table schema:")
    for col in table_info:
        print(f"  {dict(col)}")
    
    # Test 5: Count total files
    print("\n=== Test 5: Total file count ===")
    cursor.execute("SELECT COUNT(*) FROM files")
    count = cursor.fetchone()[0]
    print(f"Total files in database: {count}")
    
    # Test 6: Check FTS table
    print("\n=== Test 6: FTS table check ===")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%fts%'")
    fts_tables = cursor.fetchall()
    print(f"FTS tables: {[row[0] for row in fts_tables]}")
    
    # Test 7: Simple FTS search
    print("\n=== Test 7: Simple FTS search ===")
    try:
        cursor.execute("SELECT * FROM files_fts WHERE files_fts MATCH 'test' LIMIT 2")
        fts_rows = cursor.fetchall()
        print(f"FTS search found {len(fts_rows)} rows")
        if fts_rows:
            print(f"First FTS row: {dict(fts_rows[0])}")
    except Exception as e:
        print(f"FTS search error: {e}")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()