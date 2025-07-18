#!/usr/bin/env python3
"""
Background scheduler for Smart File Manager
Handles periodic indexing and maintenance tasks
"""
import os
import time
import schedule
import logging
import asyncio
import threading
from datetime import datetime
from enhanced_indexer_v4 import EnhancedFileIndexer as FileIndexer
from db_manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SmartFileScheduler:
    def __init__(self):
        # Configuration from environment
        self.db_path = os.environ.get("DB_PATH", "/tmp/smart-file-manager/db/file-index.db")
        self.embeddings_path = os.environ.get("EMBEDDINGS_PATH", "/tmp/smart-file-manager/embeddings")
        self.metadata_path = os.environ.get("METADATA_PATH", "/tmp/smart-file-manager/metadata")
        
        # Indexing intervals (in seconds)
        self.full_index_interval = int(os.environ.get("FULL_INDEX_INTERVAL", 7200))  # 2 hours
        self.quick_index_interval = int(os.environ.get("QUICK_INDEX_INTERVAL", 1800))  # 30 minutes
        self.cleanup_interval = int(os.environ.get("CLEANUP_INTERVAL", 86400))  # 24 hours
        
        # Initialize components
        self.file_indexer = FileIndexer(self.db_path, self.embeddings_path, self.metadata_path)
        self.db_manager = DatabaseManager(self.db_path)
        
        # Track indexing state
        self.is_indexing = False
        self.last_full_index = None
        self.last_quick_index = None
        
        logger.info(f"Scheduler initialized with intervals:")
        logger.info(f"  Full indexing: {self.full_index_interval}s ({self.full_index_interval/3600:.1f}h)")
        logger.info(f"  Quick indexing: {self.quick_index_interval}s ({self.quick_index_interval/60:.1f}m)")
        logger.info(f"  Cleanup: {self.cleanup_interval}s ({self.cleanup_interval/3600:.1f}h)")
        
    def run_full_indexing(self):
        """Run full indexing of all directories"""
        if self.is_indexing:
            logger.info("Indexing already in progress, skipping...")
            return
            
        logger.info("🔄 Starting full indexing...")
        self.is_indexing = True
        start_time = time.time()
        
        try:
            # Run indexing
            self.file_indexer.run_indexing()
            
            # Log statistics
            stats = self.file_indexer.get_stats()
            elapsed = time.time() - start_time
            
            logger.info(f"✅ Full indexing completed in {elapsed:.1f}s")
            logger.info(f"📊 Stats: {stats}")
            
            self.last_full_index = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ Full indexing failed: {e}")
        finally:
            self.is_indexing = False
            
    def run_quick_indexing(self):
        """Run quick indexing of recently modified files"""
        if self.is_indexing:
            logger.info("Full indexing in progress, skipping quick indexing...")
            return
            
        logger.info("🚀 Starting quick indexing...")
        self.is_indexing = True
        start_time = time.time()
        
        try:
            # Quick indexing: only files modified in last 2 hours
            recent_files = self.db_manager.get_recent_files(hours=2, limit=1000)
            
            if recent_files:
                indexed_count = 0
                for file_info in recent_files:
                    try:
                        file_path = file_info.get('path')
                        if file_path and os.path.exists(file_path):
                            # Re-index the file to update metadata
                            self.file_indexer.index_file(file_path)
                            indexed_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to index {file_path}: {e}")
                
                elapsed = time.time() - start_time
                logger.info(f"✅ Quick indexing completed in {elapsed:.1f}s")
                logger.info(f"📊 Indexed {indexed_count} recent files")
            else:
                logger.info("📭 No recent files to index")
                
            self.last_quick_index = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ Quick indexing failed: {e}")
        finally:
            self.is_indexing = False
            
    def run_cleanup(self):
        """Run database cleanup and optimization"""
        logger.info("🧹 Starting database cleanup...")
        start_time = time.time()
        
        try:
            # Clean expired cache entries
            self.file_indexer.clean_cache()
            
            # Run basic SQLite optimization
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # VACUUM to reclaim unused space
            cursor.execute("VACUUM")
            
            # Analyze to update statistics
            cursor.execute("ANALYZE")
            
            conn.close()
            
            elapsed = time.time() - start_time
            logger.info(f"✅ Database cleanup completed in {elapsed:.1f}s")
            
        except Exception as e:
            logger.error(f"❌ Database cleanup failed: {e}")
            
    def get_status(self):
        """Get scheduler status"""
        return {
            "is_indexing": self.is_indexing,
            "last_full_index": self.last_full_index.isoformat() if self.last_full_index else None,
            "last_quick_index": self.last_quick_index.isoformat() if self.last_quick_index else None,
            "intervals": {
                "full_index": self.full_index_interval,
                "quick_index": self.quick_index_interval,
                "cleanup": self.cleanup_interval
            }
        }
        
    def setup_schedule(self):
        """Setup scheduled tasks"""
        # Full indexing schedule
        schedule.every(self.full_index_interval).seconds.do(self.run_full_indexing)
        
        # Quick indexing schedule
        schedule.every(self.quick_index_interval).seconds.do(self.run_quick_indexing)
        
        # Cleanup schedule
        schedule.every(self.cleanup_interval).seconds.do(self.run_cleanup)
        
        logger.info("📅 Scheduled tasks configured:")
        logger.info(f"  Full indexing: every {self.full_index_interval}s")
        logger.info(f"  Quick indexing: every {self.quick_index_interval}s")
        logger.info(f"  Cleanup: every {self.cleanup_interval}s")
        
    def run(self):
        """Main scheduler loop"""
        self.setup_schedule()
        
        # Run initial full indexing
        logger.info("🚀 Running initial full indexing...")
        self.run_full_indexing()
        
        # Main loop
        logger.info("🔄 Starting scheduler loop...")
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("🛑 Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Scheduler error: {e}")
                time.sleep(60)  # Wait before retrying

def main():
    """Main function"""
    scheduler = SmartFileScheduler()
    scheduler.run()

if __name__ == "__main__":
    main()