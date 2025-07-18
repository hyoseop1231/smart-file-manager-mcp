#!/usr/bin/env python3
"""
Multimedia Content Processor for Smart File Manager v4.0
Unified processing for images, videos, and audio files
"""

import os
import logging
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
from abc import ABC, abstractmethod

# Import specialized processors
from image_processor import ImageProcessor
from video_processor import VideoProcessor  
from audio_processor import AudioProcessor

logger = logging.getLogger(__name__)


class BaseMediaProcessor(ABC):
    """Base class for media processors"""
    
    @abstractmethod
    def can_process(self, file_path: str) -> bool:
        """Check if this processor can handle the file type"""
        pass
    
    @abstractmethod
    def extract_content(self, file_path: str) -> Tuple[str, bool, Dict[str, Any]]:
        """Extract content and metadata from file"""
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions"""
        pass


class MultimediaProcessor:
    """
    Unified multimedia content processor
    Routes files to appropriate specialized processors
    """
    
    def __init__(self, 
                 enable_ocr: bool = True,
                 enable_ai_vision: bool = False,
                 enable_stt: bool = True,
                 cache_dir: str = "/tmp/multimedia_cache"):
        
        self.logger = logging.getLogger(__name__)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize specialized processors
        self.processors = {}
        
        try:
            self.processors['image'] = ImageProcessor(
                enable_ocr=enable_ocr,
                enable_ai_vision=enable_ai_vision,
                cache_dir=cache_dir
            )
            self.logger.info("✅ Image processor initialized")
        except Exception as e:
            self.logger.warning(f"⚠️ Image processor initialization failed: {e}")
        
        try:
            self.processors['video'] = VideoProcessor(
                enable_stt=enable_stt,
                cache_dir=cache_dir
            )
            self.logger.info("✅ Video processor initialized")
        except Exception as e:
            self.logger.warning(f"⚠️ Video processor initialization failed: {e}")
        
        try:
            self.processors['audio'] = AudioProcessor(
                enable_stt=enable_stt,
                cache_dir=cache_dir
            )
            self.logger.info("✅ Audio processor initialized")
        except Exception as e:
            self.logger.warning(f"⚠️ Audio processor initialization failed: {e}")
        
        # File size limits
        self.max_file_size = 500 * 1024 * 1024  # 500MB
        self.max_image_size = 50 * 1024 * 1024   # 50MB for images
        self.max_video_size = 1024 * 1024 * 1024 # 1GB for videos
        self.max_audio_size = 100 * 1024 * 1024  # 100MB for audio
        
        # Supported file types mapping
        self.file_type_map = {
            # Images
            '.jpg': 'image', '.jpeg': 'image', '.png': 'image', '.gif': 'image',
            '.bmp': 'image', '.svg': 'image', '.webp': 'image', '.tiff': 'image',
            '.tga': 'image', '.ico': 'image', '.heic': 'image', '.heif': 'image',
            
            # Videos  
            '.mp4': 'video', '.avi': 'video', '.mkv': 'video', '.mov': 'video',
            '.wmv': 'video', '.flv': 'video', '.webm': 'video', '.m4v': 'video',
            '.3gp': 'video', '.ogv': 'video', '.mpg': 'video', '.mpeg': 'video',
            
            # Audio
            '.mp3': 'audio', '.wav': 'audio', '.flac': 'audio', '.aac': 'audio',
            '.ogg': 'audio', '.wma': 'audio', '.m4a': 'audio', '.opus': 'audio',
            '.aiff': 'audio', '.au': 'audio', '.ra': 'audio'
        }
    
    def can_process(self, file_path: str) -> bool:
        """Check if file can be processed by any multimedia processor"""
        file_path = Path(file_path)
        
        if not file_path.exists() or not file_path.is_file():
            return False
        
        extension = file_path.suffix.lower()
        return extension in self.file_type_map
    
    def get_file_type(self, file_path: str) -> Optional[str]:
        """Determine media type (image/video/audio) from file"""
        extension = Path(file_path).suffix.lower()
        return self.file_type_map.get(extension)
    
    def extract_content(self, file_path: str) -> Tuple[str, bool, Dict[str, Any]]:
        """
        Extract content from multimedia file
        
        Returns:
            tuple: (extracted_text, success, metadata)
        """
        file_path = Path(file_path)
        
        # Basic validation
        if not file_path.exists():
            return "", False, {"error": "File does not exist"}
        
        if not file_path.is_file():
            return "", False, {"error": "Path is not a file"}
        
        # Check file size
        try:
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                return "", False, {
                    "error": f"File too large: {file_size} bytes (max: {self.max_file_size})",
                    "file_size": file_size
                }
        except Exception as e:
            return "", False, {"error": f"Cannot access file: {e}"}
        
        # Determine file type
        media_type = self.get_file_type(str(file_path))
        if not media_type:
            return "", False, {
                "error": "Unsupported media format",
                "extension": file_path.suffix.lower(),
                "supported_formats": list(self.file_type_map.keys())
            }
        
        # Check if appropriate processor is available
        if media_type not in self.processors:
            return "", False, {
                "error": f"No processor available for {media_type} files",
                "media_type": media_type
            }
        
        # Apply type-specific size limits
        type_limits = {
            'image': self.max_image_size,
            'video': self.max_video_size,
            'audio': self.max_audio_size
        }
        
        if file_size > type_limits.get(media_type, self.max_file_size):
            return "", False, {
                "error": f"{media_type.title()} file too large: {file_size} bytes (max: {type_limits[media_type]})",
                "media_type": media_type,
                "file_size": file_size
            }
        
        # Process with appropriate processor
        try:
            processor = self.processors[media_type]
            text, success, metadata = processor.extract_content(str(file_path))
            
            # Add common metadata
            metadata.update({
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_size": file_size,
                "media_type": media_type,
                "processor_used": f"{media_type}_processor"
            })
            
            if success:
                self.logger.info(f"✅ {media_type.title()} content extracted from {file_path.name}: {len(text)} characters")
            else:
                self.logger.warning(f"⚠️ Failed to extract {media_type} content from {file_path.name}")
            
            return text, success, metadata
            
        except Exception as e:
            self.logger.error(f"❌ {media_type.title()} processing error for {file_path}: {e}")
            return "", False, {
                "error": str(e), 
                "media_type": media_type,
                "processor": f"{media_type}_processor"
            }
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive file information and processing capabilities"""
        file_path = Path(file_path)
        
        info = {
            'file_name': file_path.name,
            'file_path': str(file_path),
            'exists': file_path.exists(),
            'is_file': file_path.is_file() if file_path.exists() else False,
            'file_size': file_path.stat().st_size if file_path.exists() else 0,
            'extension': file_path.suffix.lower(),
            'media_type': self.get_file_type(str(file_path)),
            'can_process': self.can_process(str(file_path)),
            'supported_media_types': list(set(self.file_type_map.values())),
            'available_processors': list(self.processors.keys())
        }
        
        # Add MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            info['mime_type'] = mime_type
        
        # Add processor-specific capabilities
        media_type = info['media_type']
        if media_type and media_type in self.processors:
            processor = self.processors[media_type]
            try:
                processor_info = processor.get_capabilities()
                info[f'{media_type}_capabilities'] = processor_info
            except:
                pass
        
        return info
    
    def extract_preview(self, file_path: str, max_chars: int = 500) -> Tuple[str, bool, Dict[str, Any]]:
        """Extract a preview/sample of content for quick display"""
        text, success, metadata = self.extract_content(file_path)
        
        if success and text and len(text) > max_chars:
            # Create preview from extracted content
            preview_text = text[:max_chars] + "..."
            metadata.update({
                "is_preview": True,
                "preview_length": max_chars,
                "total_content_length": len(text)
            })
            return preview_text, True, metadata
        
        return text, success, metadata
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processor statistics"""
        stats = {
            "supported_media_types": list(set(self.file_type_map.values())),
            "supported_extensions": len(self.file_type_map),
            "extension_breakdown": {},
            "max_file_sizes": {
                "general": self.max_file_size // (1024 * 1024),  # MB
                "image": self.max_image_size // (1024 * 1024),
                "video": self.max_video_size // (1024 * 1024),
                "audio": self.max_audio_size // (1024 * 1024)
            },
            "processors_available": len(self.processors),
            "processor_details": {}
        }
        
        # Count extensions by type
        for ext, media_type in self.file_type_map.items():
            if media_type not in stats["extension_breakdown"]:
                stats["extension_breakdown"][media_type] = []
            stats["extension_breakdown"][media_type].append(ext)
        
        # Get processor-specific stats
        for media_type, processor in self.processors.items():
            try:
                processor_stats = processor.get_statistics()
                stats["processor_details"][media_type] = processor_stats
            except:
                stats["processor_details"][media_type] = {"status": "error"}
        
        return stats
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of all supported file extensions"""
        return list(self.file_type_map.keys())


def test_multimedia_processor():
    """Test function for multimedia processor"""
    processor = MultimediaProcessor()
    
    print("🎬 Multimedia Processor Test")
    print("=" * 50)
    
    # Display statistics
    stats = processor.get_statistics()
    print("📊 Processor Statistics:")
    print(f"   Supported media types: {stats['supported_media_types']}")
    print(f"   Total extensions: {stats['supported_extensions']}")
    print(f"   Available processors: {stats['processors_available']}")
    
    # Test files to look for
    test_files = [
        "/watch_directories/Desktop/test.jpg",
        "/watch_directories/Desktop/test.mp4",
        "/watch_directories/Desktop/test.mp3",
        "/watch_directories/Pictures/sample.png",
        "/watch_directories/Movies/sample.mov",
        "/watch_directories/Music/sample.wav"
    ]
    
    print("\n🔍 Testing file processing:")
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n📄 Testing: {test_file}")
            
            # Get file info
            info = processor.get_file_info(test_file)
            print(f"   Media type: {info['media_type']}")
            print(f"   Can process: {'✅' if info['can_process'] else '❌'}")
            print(f"   Size: {info['file_size']:,} bytes")
            
            if info['can_process']:
                # Extract preview
                preview, success, metadata = processor.extract_preview(test_file, 200)
                if success:
                    print(f"   ✅ Preview extracted ({len(preview)} chars)")
                    if preview.strip():
                        print(f"   Content: {repr(preview[:100])}...")
                else:
                    print(f"   ❌ Processing failed: {metadata.get('error', 'Unknown error')}")
        else:
            print(f"\n❌ File not found: {test_file}")
    
    return processor


if __name__ == "__main__":
    test_multimedia_processor()