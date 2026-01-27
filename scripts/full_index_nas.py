#!/usr/bin/env python3
"""Full NAS Indexing with AI Analysis + Embeddings"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ai-services"))

from enhanced_indexer_v4 import EnhancedFileIndexer

# Skip patterns
SKIP_DIRS = {"venv", ".venv", "node_modules", "__pycache__", ".git", ".trash", "site-packages", ".cache"}

def main():
    print("🚀 Full NAS Indexing (AI + Embeddings)")
    print("=" * 50)
    
    # Initialize with AI enabled
    indexer = EnhancedFileIndexer(
        db_path="/tmp/smart-file-manager/db/file-index.db",
        embeddings_path="/tmp/smart-file-manager/embeddings",
        metadata_path="/tmp/smart-file-manager/metadata",
        enable_ai_vision=True,
        enable_stt=True
    )
    
    # Override indexed directories
    indexer.indexed_dirs = ["/home/hyoseop1231/nas_khs"]
    
    # Set skip patterns
    original_should_index = indexer._should_index_file
    def filtered_should_index(file_path):
        path_str = str(file_path)
        for skip in SKIP_DIRS:
            if f"/{skip}/" in path_str:
                return False
        return original_should_index(file_path)
    indexer._should_index_file = filtered_should_index
    
    # Run full indexing
    nas_path = "/home/hyoseop1231/nas_khs"
    print(f"📁 Target: {nas_path}")
    print(f"🚫 Skipping: {SKIP_DIRS}")
    print()
    
    indexer.index_directory(nas_path, force_reindex=False)
    
    # Show final stats
    print("\n" + "=" * 50)
    print("📊 Final Statistics:")
    stats = indexer.get_stats()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for k, v in value.items():
                print(f"      {k}: {v}")
        else:
            print(f"   {key}: {value}")

if __name__ == "__main__":
    main()
