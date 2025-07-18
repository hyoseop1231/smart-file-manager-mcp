#!/usr/bin/env python3
"""
Enhanced File Indexer v4.0 for Smart File Manager
Full multimedia content extraction and AI analysis
"""

import os
import time
import sqlite3
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import schedule
import numpy as np

# Import enhanced processors
from content_extractor import ContentExtractor
from multimedia_processor import MultimediaProcessor

# Conditional imports for AI services
try:
    from ai_vision_service import AIVisionService
    AI_VISION_AVAILABLE = True
except ImportError:
    AIVisionService = None
    AI_VISION_AVAILABLE = False

try:
    from speech_recognition_service import SpeechRecognitionService
    STT_AVAILABLE = True
except ImportError:
    SpeechRecognitionService = None
    STT_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedFileIndexer:
    """
    Enhanced file indexer with full multimedia support and AI analysis
    """
    
    def __init__(self, 
                 db_path: str, 
                 embeddings_path: str, 
                 metadata_path: str,
                 enable_ai_vision: bool = True,
                 enable_stt: bool = True):
        
        self.db_path = db_path
        self.embeddings_path = embeddings_path
        self.metadata_path = metadata_path
        
        # Initialize content processors
        self.content_extractor = ContentExtractor()  # For text files
        self.multimedia_processor = MultimediaProcessor(
            enable_ai_vision=enable_ai_vision,
            enable_stt=enable_stt,
            cache_dir=metadata_path
        )
        
        # Initialize AI services with availability checks
        self.ai_vision = None
        self.speech_recognition = None
        
        if enable_ai_vision and AI_VISION_AVAILABLE:
            try:
                self.ai_vision = AIVisionService(cache_dir=metadata_path)
                logger.info("✅ AI Vision service initialized")
            except Exception as e:
                logger.warning(f"⚠️ AI Vision service failed to initialize: {e}")
        elif enable_ai_vision and not AI_VISION_AVAILABLE:
            logger.warning("⚠️ AI Vision service not available (dependencies missing)")
        
        if enable_stt and STT_AVAILABLE:
            try:
                self.speech_recognition = SpeechRecognitionService(cache_dir=metadata_path)
                logger.info("✅ Speech Recognition service initialized")
            except Exception as e:
                logger.warning(f"⚠️ Speech Recognition service failed to initialize: {e}")
        elif enable_stt and not STT_AVAILABLE:
            logger.warning("⚠️ Speech Recognition service not available (dependencies missing)")
        
        # Get directories from environment or use defaults
        self.indexed_dirs = [
            os.environ.get("HOME_DOCUMENTS", "/watch_directories/Documents"),
            os.environ.get("HOME_DOWNLOADS", "/watch_directories/Downloads"), 
            os.environ.get("HOME_DESKTOP", "/watch_directories/Desktop"),
            os.environ.get("HOME_PICTURES", "/watch_directories/Pictures"),
            os.environ.get("HOME_MOVIES", "/watch_directories/Movies"),
            os.environ.get("HOME_MUSIC", "/watch_directories/Music")
        ]
        
        # Initialize directories
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        os.makedirs(embeddings_path, exist_ok=True)
        os.makedirs(metadata_path, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # File type categories with multimedia support
        self.file_categories = {
            # Text/Document files - use content_extractor
            'text': ['.txt', '.md', '.csv', '.json', '.xml', '.log', '.py', '.js', '.java', 
                    '.cpp', '.c', '.go', '.php', '.rb', '.sh', '.sql', '.html', '.css', 
                    '.yml', '.yaml', '.toml', '.ini', '.conf', '.config'],
            'document': ['.pdf', '.doc', '.docx'],
            'korean_document': ['.hwp', '.hwpx'],
            
            # Multimedia files - use multimedia_processor
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', 
                     '.tiff', '.tga', '.ico', '.heic', '.heif'],
            'video': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', 
                     '.m4v', '.3gp', '.ogv', '.mpg', '.mpeg', '.ts', '.mts'],
            'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', 
                     '.opus', '.aiff', '.au', '.ra', '.amr', '.3ga'],
            
            # Archive files - basic metadata only
            'archive': ['.zip', '.tar', '.gz', '.rar', '.7z', '.bz2'],
            
            # Other files
            'other': []
        }
    
    def _init_database(self):
        """Initialize SQLite database with enhanced schema for multimedia"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enhanced files table with multimedia support
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                extension TEXT,
                size INTEGER,
                modified_time REAL,
                content_hash TEXT,
                
                -- Text content (from any source)
                text_content TEXT,
                content_extracted BOOLEAN DEFAULT 0,
                extraction_metadata TEXT,
                
                -- Multimedia specific fields
                multimedia_content TEXT,           -- Text extracted from multimedia
                multimedia_metadata TEXT,          -- Tech metadata (resolution, duration, etc.)
                ai_analysis TEXT,                  -- AI analysis results
                thumbnail_path TEXT,               -- Path to thumbnail/preview
                processing_status TEXT,            -- Processing status and results
                
                -- Classification and metadata
                media_type TEXT,                   -- image, video, audio, document, etc.
                category TEXT,                     -- More specific categorization
                metadata_json TEXT,                -- Original metadata
                
                -- Indexing info
                embedding_id TEXT,
                indexed_at REAL,
                last_analyzed REAL,                -- Last AI analysis timestamp
                
                UNIQUE(path)
            )
        ''')
        
        # Enhanced FTS5 virtual table including multimedia content
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
                name, path, text_content, multimedia_content, ai_analysis,
                content='files',
                content_rowid='id'
            )
        ''')
        
        # Update triggers for new fields
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS files_ai AFTER INSERT ON files BEGIN
                INSERT INTO files_fts(rowid, name, path, text_content, multimedia_content, ai_analysis) 
                VALUES (new.id, new.name, new.path, new.text_content, new.multimedia_content, new.ai_analysis);
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS files_ad AFTER DELETE ON files BEGIN
                DELETE FROM files_fts WHERE rowid = old.id;
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS files_au AFTER UPDATE ON files BEGIN
                UPDATE files_fts SET 
                    name = new.name, 
                    path = new.path, 
                    text_content = new.text_content,
                    multimedia_content = new.multimedia_content,
                    ai_analysis = new.ai_analysis
                WHERE rowid = new.id;
            END
        ''')
        
        # Enhanced indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_name ON files(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_extension ON files(extension)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_modified ON files(modified_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_media_type ON files(media_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_category ON files(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_processing_status ON files(processing_status)')
        
        # Query cache table (existing)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS query_cache (
                query_hash TEXT PRIMARY KEY,
                query TEXT,
                results TEXT,
                created_at REAL,
                expires_at REAL
            )
        ''')
        
        # AI analysis cache table (new)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_analysis_cache (
                file_id INTEGER,
                analysis_type TEXT,
                analysis_data TEXT,
                confidence REAL,
                created_at REAL,
                expires_at REAL,
                PRIMARY KEY (file_id, analysis_type),
                FOREIGN KEY (file_id) REFERENCES files (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Enhanced database schema initialized")
    
    def determine_file_category(self, file_path: Path) -> tuple[str, str]:
        """
        Determine file category and media type
        
        Returns:
            tuple: (category, media_type)
        """
        extension = file_path.suffix.lower()
        
        for category, extensions in self.file_categories.items():
            if extension in extensions:
                # Determine media type
                if category in ['image', 'video', 'audio']:
                    media_type = 'multimedia'
                elif category in ['text', 'document', 'korean_document']:
                    media_type = 'text'
                elif category == 'archive':
                    media_type = 'archive'
                else:
                    media_type = 'other'
                
                return category, media_type
        
        return 'other', 'other'
    
    def index_file(self, file_path: str) -> bool:
        """
        Index a single file with enhanced multimedia support
        """
        file_path = Path(file_path)
        
        if not self._should_index_file(file_path):
            return False
        
        try:
            # Extract basic metadata
            metadata = self._extract_metadata(file_path)
            
            # Determine category and media type
            category, media_type = self.determine_file_category(file_path)
            metadata["category"] = category
            metadata["media_type"] = media_type
            
            # Calculate content hash
            content_hash = self._calculate_file_hash(str(file_path))
            
            # Check if file already indexed and unchanged
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT content_hash, last_analyzed FROM files WHERE path = ?",
                (str(file_path),)
            )
            existing = cursor.fetchone()
            
            if existing and existing[0] == content_hash:
                # File unchanged, skip unless it needs AI analysis
                last_analyzed = existing[1] or 0
                needs_ai_analysis = (time.time() - last_analyzed) > 86400  # 24 hours
                
                if not needs_ai_analysis:
                    conn.close()
                    return True  # Skip processing
            
            # Initialize content fields
            text_content = ""
            multimedia_content = ""
            ai_analysis = ""
            thumbnail_path = ""
            processing_status = {"status": "pending", "steps": []}
            
            content_extracted = False
            extraction_metadata = {}
            multimedia_metadata = {}
            ai_analysis_data = {}
            
            # Process based on media type
            if media_type == "text":
                # Use content_extractor for text files
                processing_status["steps"].append("text_extraction")
                
                try:
                    text, success, extract_meta = self.content_extractor.extract_content(str(file_path))
                    if success and text:
                        text_content = text
                        content_extracted = True
                        extraction_metadata = extract_meta
                        processing_status["steps"].append("text_extraction_success")
                    else:
                        processing_status["steps"].append("text_extraction_failed")
                        extraction_metadata = extract_meta
                except Exception as e:
                    logger.warning(f"Text extraction error for {file_path}: {e}")
                    processing_status["steps"].append(f"text_extraction_error: {str(e)}")
            
            elif media_type == "multimedia":
                # Use multimedia_processor for multimedia files
                processing_status["steps"].append("multimedia_processing")
                
                try:
                    mm_text, mm_success, mm_meta = self.multimedia_processor.extract_content(str(file_path))
                    if mm_success:
                        multimedia_content = mm_text
                        multimedia_metadata = mm_meta
                        content_extracted = True
                        processing_status["steps"].append("multimedia_processing_success")
                        
                        # Extract thumbnail path if available
                        if "thumbnail_path" in mm_meta:
                            thumbnail_path = mm_meta["thumbnail_path"]
                        elif "thumbnail_paths" in mm_meta and mm_meta["thumbnail_paths"]:
                            thumbnail_path = mm_meta["thumbnail_paths"][0]  # First thumbnail
                        
                    else:
                        processing_status["steps"].append("multimedia_processing_failed")
                        multimedia_metadata = mm_meta
                        
                except Exception as e:
                    logger.warning(f"Multimedia processing error for {file_path}: {e}")
                    processing_status["steps"].append(f"multimedia_processing_error: {str(e)}")
                
                # Additional AI analysis for images
                if category == "image" and self.ai_vision:
                    processing_status["steps"].append("ai_vision_analysis")
                    
                    try:
                        ai_desc, ai_conf, ai_meta = self.ai_vision.analyze_image(str(file_path))
                        if ai_desc:
                            ai_analysis = ai_desc
                            ai_analysis_data = {
                                "description": ai_desc,
                                "confidence": ai_conf,
                                "analysis_metadata": ai_meta
                            }
                            processing_status["steps"].append("ai_vision_success")
                        else:
                            processing_status["steps"].append("ai_vision_failed")
                    except Exception as e:
                        logger.warning(f"AI vision analysis error for {file_path}: {e}")
                        processing_status["steps"].append(f"ai_vision_error: {str(e)}")
            
            # Combine all text content for FTS
            combined_text_content = ""
            if text_content.strip():
                combined_text_content = text_content
            if multimedia_content.strip():
                combined_text_content = multimedia_content if not combined_text_content else f"{combined_text_content}\n\n{multimedia_content}"
            
            # Update processing status
            processing_status["status"] = "completed"
            processing_status["completed_at"] = time.time()
            
            # Insert or update file record
            current_time = time.time()
            
            cursor.execute('''
                INSERT OR REPLACE INTO files 
                (path, name, extension, size, modified_time, content_hash,
                 text_content, multimedia_content, ai_analysis,
                 content_extracted, extraction_metadata, multimedia_metadata,
                 thumbnail_path, processing_status, media_type, category,
                 metadata_json, indexed_at, last_analyzed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(file_path),
                metadata["name"],
                metadata["extension"],
                metadata["size"],
                metadata["modified"],
                content_hash,
                combined_text_content,  # Combined for FTS
                multimedia_content,
                ai_analysis,
                content_extracted,
                json.dumps(extraction_metadata),
                json.dumps(multimedia_metadata),
                thumbnail_path,
                json.dumps(processing_status),
                media_type,
                category,
                json.dumps(metadata),
                current_time,
                current_time
            ))
            
            # Cache AI analysis if available
            if ai_analysis_data:
                self._cache_ai_analysis(cursor, cursor.lastrowid, "image_analysis", ai_analysis_data)
            
            conn.commit()
            conn.close()
            
            logger.debug(f"✅ File indexed: {file_path.name} ({category}/{media_type})")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing file {file_path}: {e}")
            return False
    
    def _cache_ai_analysis(self, cursor, file_id: int, analysis_type: str, analysis_data: Dict[str, Any]):
        """Cache AI analysis results"""
        try:
            current_time = time.time()
            expires_at = current_time + (7 * 24 * 3600)  # 7 days
            
            cursor.execute('''
                INSERT OR REPLACE INTO ai_analysis_cache
                (file_id, analysis_type, analysis_data, confidence, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                file_id,
                analysis_type,
                json.dumps(analysis_data),
                analysis_data.get("confidence", 0.0),
                current_time,
                expires_at
            ))
        except Exception as e:
            logger.debug(f"Failed to cache AI analysis: {e}")
    
    def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract basic file metadata"""
        stat = file_path.stat()
        
        metadata = {
            "name": file_path.name,
            "extension": file_path.suffix.lower(),
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "path": str(file_path),
            "parent_dir": str(file_path.parent)
        }
        
        return metadata
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file content"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.debug(f"Hash calculation failed for {file_path}: {e}")
            return ""
    
    def _should_index_file(self, file_path: Path) -> bool:
        """Check if file should be indexed"""
        # Skip hidden files and directories
        if any(part.startswith('.') for part in file_path.parts):
            return False
            
        # Skip system files
        skip_patterns = ['__pycache__', 'node_modules', '.git', '.DS_Store', 'Thumbs.db']
        if any(pattern in str(file_path) for pattern in skip_patterns):
            return False
            
        # Skip very large files (>2GB)
        try:
            if file_path.stat().st_size > 2 * 1024 * 1024 * 1024:
                return False
        except:
            return False
        
        # Check if it's a supported file type
        category, media_type = self.determine_file_category(file_path)
        if category == 'other' and media_type == 'other':
            return False
            
        return True
    
    def index_directory(self, directory: str, force_reindex: bool = False):
        """Index all files in a directory with progress tracking"""
        logger.info(f"Indexing directory: {directory}")
        
        if not os.path.exists(directory):
            logger.warning(f"Directory does not exist: {directory}")
            return
        
        indexed_count = 0
        skipped_count = 0
        multimedia_count = 0
        
        try:
            # Count total files first for progress tracking
            total_files = sum(1 for root, dirs, files in os.walk(directory) 
                            for file_name in files 
                            if self._should_index_file(Path(root) / file_name))
            
            logger.info(f"Found {total_files} files to process")
            
            for root, dirs, files in os.walk(directory):
                # Filter out hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file_name in files:
                    file_path = Path(root) / file_name
                    
                    if not self._should_index_file(file_path):
                        skipped_count += 1
                        continue
                    
                    try:
                        success = self.index_file(str(file_path))
                        if success:
                            indexed_count += 1
                            
                            # Track multimedia files
                            category, media_type = self.determine_file_category(file_path)
                            if media_type == "multimedia":
                                multimedia_count += 1
                            
                            # Progress logging
                            if indexed_count % 100 == 0:
                                progress = (indexed_count / total_files) * 100
                                logger.info(f"Progress: {indexed_count}/{total_files} ({progress:.1f}%) - {multimedia_count} multimedia files")
                        else:
                            skipped_count += 1
                            
                    except Exception as e:
                        logger.error(f"Error indexing file {file_path}: {e}")
                        skipped_count += 1
            
            logger.info(f"Indexing complete. Indexed: {indexed_count}, Multimedia: {multimedia_count}, Skipped: {skipped_count}")
            
        except Exception as e:
            logger.error(f"Directory indexing failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            stats = {}
            
            # Total files
            cursor.execute("SELECT COUNT(*) FROM files")
            stats["total_files"] = cursor.fetchone()[0]
            
            # By media type
            cursor.execute("""
                SELECT media_type, COUNT(*) as count, SUM(size) as total_size
                FROM files
                GROUP BY media_type
            """)
            
            stats["by_media_type"] = {}
            for row in cursor.fetchall():
                media_type, count, total_size = row
                stats["by_media_type"][media_type or "unknown"] = {
                    "count": count,
                    "size_gb": round((total_size or 0) / (1024**3), 2)
                }
            
            # By category
            cursor.execute("""
                SELECT category, COUNT(*) as count, SUM(size) as total_size
                FROM files
                GROUP BY category
            """)
            
            stats["by_category"] = {}
            for row in cursor.fetchall():
                category, count, total_size = row
                stats["by_category"][category or "unknown"] = {
                    "count": count,
                    "size_gb": round((total_size or 0) / (1024**3), 2)
                }
            
            # Content extraction stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN content_extracted = 1 THEN 1 ELSE 0 END) as extracted,
                    SUM(CASE WHEN multimedia_content IS NOT NULL AND multimedia_content != '' THEN 1 ELSE 0 END) as multimedia_extracted,
                    SUM(CASE WHEN ai_analysis IS NOT NULL AND ai_analysis != '' THEN 1 ELSE 0 END) as ai_analyzed,
                    SUM(CASE WHEN thumbnail_path IS NOT NULL AND thumbnail_path != '' THEN 1 ELSE 0 END) as with_thumbnails
                FROM files
            """)
            
            content_stats = cursor.fetchone()
            stats["content_extraction"] = {
                "total_files": content_stats[0],
                "content_extracted": content_stats[1],
                "multimedia_content": content_stats[2],
                "ai_analyzed": content_stats[3],
                "with_thumbnails": content_stats[4]
            }
            
            # Processing status
            cursor.execute("""
                SELECT 
                    JSON_EXTRACT(processing_status, '$.status') as status,
                    COUNT(*) as count
                FROM files
                WHERE processing_status IS NOT NULL
                GROUP BY JSON_EXTRACT(processing_status, '$.status')
            """)
            
            stats["processing_status"] = {}
            for row in cursor.fetchall():
                status, count = row
                stats["processing_status"][status or "unknown"] = count
            
            # Cache stats
            cursor.execute("SELECT COUNT(*) FROM query_cache WHERE expires_at > ?", (time.time(),))
            stats["active_query_cache"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ai_analysis_cache WHERE expires_at > ?", (time.time(),))
            stats["active_ai_cache"] = cursor.fetchone()[0]
            
            return stats
            
        finally:
            conn.close()
    
    def get_multimedia_stats(self) -> Dict[str, Any]:
        """Get detailed multimedia processing statistics"""
        return {
            "multimedia_processor": self.multimedia_processor.get_statistics() if self.multimedia_processor else {},
            "ai_vision": self.ai_vision.get_statistics() if self.ai_vision else {},
            "speech_recognition": self.speech_recognition.get_statistics() if self.speech_recognition else {},
            "supported_extensions": {
                "images": self.file_categories["image"],
                "videos": self.file_categories["video"],
                "audio": self.file_categories["audio"]
            }
        }


def test_enhanced_indexer():
    """Test enhanced indexer with multimedia support"""
    indexer = EnhancedFileIndexer(
        db_path="/tmp/test_enhanced_indexer.db",
        embeddings_path="/tmp/test_embeddings",
        metadata_path="/tmp/test_metadata",
        enable_ai_vision=True,
        enable_stt=True
    )
    
    print("🚀 Enhanced File Indexer v4.0 Test")
    print("=" * 50)
    
    # Display capabilities
    mm_stats = indexer.get_multimedia_stats()
    print("📊 Multimedia Capabilities:")
    for service, stats in mm_stats.items():
        if isinstance(stats, dict) and stats:
            print(f"   {service}: {len(stats)} features")
        elif isinstance(stats, list):
            print(f"   {service}: {len(stats)} items")
    
    # Test file indexing
    test_files = [
        "/watch_directories/Desktop/test.jpg",
        "/watch_directories/Desktop/test.mp4", 
        "/watch_directories/Desktop/test.mp3",
        "/watch_directories/Desktop/test.txt",
        "/watch_directories/Desktop/test.hwp"
    ]
    
    print("\n🔍 Testing file indexing:")
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n📄 Indexing: {test_file}")
            
            success = indexer.index_file(test_file)
            
            if success:
                category, media_type = indexer.determine_file_category(Path(test_file))
                print(f"   ✅ Indexed successfully")
                print(f"   📂 Category: {category}")
                print(f"   🎯 Media Type: {media_type}")
            else:
                print(f"   ❌ Indexing failed")
        else:
            print(f"\n❌ File not found: {test_file}")
    
    # Display final stats
    print(f"\n📊 Final Statistics:")
    stats = indexer.get_stats()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"   {key}: {len(value)} categories")
        else:
            print(f"   {key}: {value}")


if __name__ == "__main__":
    test_enhanced_indexer()