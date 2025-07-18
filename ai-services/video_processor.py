#!/usr/bin/env python3
"""
Video Content Processor for Smart File Manager v4.0
Metadata extraction, subtitle processing, STT, and thumbnail generation
"""

import os
import json
import logging
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
import mimetypes

logger = logging.getLogger(__name__)


class VideoProcessor:
    """
    Comprehensive video content processor
    """
    
    def __init__(self, 
                 enable_stt: bool = True,
                 cache_dir: str = "/tmp/multimedia_cache"):
        
        self.logger = logging.getLogger(__name__)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Speech-to-text capabilities
        self.enable_stt = enable_stt
        self.stt_engine = None
        if enable_stt:
            self._init_stt()
        
        # Check for ffmpeg availability
        self.ffmpeg_available = self._check_ffmpeg()
        
        # Supported video formats
        self.supported_extensions = [
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', 
            '.m4v', '.3gp', '.ogv', '.mpg', '.mpeg', '.ts', '.mts'
        ]
        
        # Subtitle file extensions
        self.subtitle_extensions = ['.srt', '.vtt', '.ass', '.ssa', '.sub', '.idx']
        
        # Processing limits
        self.max_video_size = 1024 * 1024 * 1024  # 1GB
        self.max_stt_duration = 3600  # 1 hour for STT
        self.thumbnail_count = 3  # Number of thumbnails to generate
    
    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.logger.info("✅ FFmpeg available")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        self.logger.warning("⚠️ FFmpeg not available. Install ffmpeg for full video processing capabilities")
        return False
    
    def _init_stt(self):
        """Initialize speech-to-text engine"""
        try:
            # Try OpenAI Whisper first
            import whisper
            
            # Load small model for efficiency
            model = whisper.load_model("base")
            self.stt_engine = {
                'type': 'whisper',
                'model': model
            }
            self.logger.info("✅ Speech-to-text engine (Whisper) initialized")
            
        except ImportError:
            try:
                # Fallback to speech_recognition library
                import speech_recognition as sr
                
                recognizer = sr.Recognizer()
                self.stt_engine = {
                    'type': 'speech_recognition',
                    'recognizer': recognizer
                }
                self.logger.info("✅ Speech-to-text engine (SpeechRecognition) initialized")
                
            except ImportError:
                self.logger.warning("⚠️ No STT library available. Install with: pip install openai-whisper or pip install SpeechRecognition")
    
    def can_process(self, file_path: str) -> bool:
        """Check if file can be processed"""
        extension = Path(file_path).suffix.lower()
        return extension in self.supported_extensions
    
    def extract_content(self, file_path: str) -> Tuple[str, bool, Dict[str, Any]]:
        """
        Extract content from video file
        
        Returns:
            tuple: (extracted_text, success, metadata)
        """
        file_path = Path(file_path)
        
        try:
            # Extract video metadata
            video_metadata = self._extract_video_metadata(file_path)
            
            # Look for subtitle files
            subtitle_text = self._find_and_extract_subtitles(file_path)
            
            # Generate thumbnails/keyframes
            thumbnail_paths = self._generate_thumbnails(file_path)
            
            # Extract audio and perform STT
            stt_text = ""
            stt_confidence = 0
            if self.enable_stt and self.stt_engine and self._should_process_stt(video_metadata):
                stt_text, stt_confidence = self._extract_audio_text(file_path)
            
            # Combine all extracted text
            combined_text = []
            if subtitle_text.strip():
                combined_text.append(f"Subtitles: {subtitle_text}")
            if stt_text.strip():
                combined_text.append(f"Spoken Content: {stt_text}")
            
            # Add metadata as searchable text
            metadata_text = self._metadata_to_text(video_metadata)
            if metadata_text.strip():
                combined_text.append(f"Video Info: {metadata_text}")
            
            final_text = "\n\n".join(combined_text)
            
            # Compile metadata
            metadata = {
                "video_metadata": video_metadata,
                "subtitle_files": self._find_subtitle_files(file_path),
                "thumbnail_paths": thumbnail_paths,
                "processing_results": {
                    "stt_enabled": self.enable_stt,
                    "stt_text_length": len(stt_text),
                    "stt_confidence": stt_confidence,
                    "subtitle_text_length": len(subtitle_text),
                    "thumbnails_generated": len(thumbnail_paths)
                },
                "success": True
            }
            
            success = len(final_text.strip()) > 0 or len(video_metadata) > 0
            
            return final_text, success, metadata
            
        except Exception as e:
            return "", False, {"error": str(e), "video_processing_failed": True}
    
    def _extract_video_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract video metadata using ffprobe"""
        if not self.ffmpeg_available:
            return self._basic_video_metadata(file_path)
        
        try:
            # Use ffprobe to get detailed metadata
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(file_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                probe_data = json.loads(result.stdout)
                return self._parse_ffprobe_data(probe_data)
            else:
                self.logger.warning(f"ffprobe failed for {file_path}: {result.stderr}")
                return self._basic_video_metadata(file_path)
                
        except Exception as e:
            self.logger.debug(f"Metadata extraction failed: {e}")
            return self._basic_video_metadata(file_path)
    
    def _basic_video_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract basic metadata without ffmpeg"""
        stat = file_path.stat()
        return {
            "file_size": stat.st_size,
            "modified_time": stat.st_mtime,
            "format": file_path.suffix.lower().lstrip('.'),
            "container": file_path.suffix.lower().lstrip('.')
        }
    
    def _parse_ffprobe_data(self, probe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ffprobe JSON output"""
        metadata = {}
        
        # Format information
        if 'format' in probe_data:
            format_info = probe_data['format']
            metadata.update({
                'duration': float(format_info.get('duration', 0)),
                'size': int(format_info.get('size', 0)),
                'bit_rate': int(format_info.get('bit_rate', 0)),
                'format_name': format_info.get('format_name', ''),
                'container': format_info.get('format_name', '').split(',')[0]
            })
            
            # Tags (title, artist, etc.)
            if 'tags' in format_info:
                metadata['tags'] = format_info['tags']
        
        # Stream information
        if 'streams' in probe_data:
            video_streams = []
            audio_streams = []
            
            for stream in probe_data['streams']:
                if stream.get('codec_type') == 'video':
                    video_info = {
                        'codec': stream.get('codec_name', ''),
                        'width': stream.get('width', 0),
                        'height': stream.get('height', 0),
                        'frame_rate': stream.get('r_frame_rate', ''),
                        'pixel_format': stream.get('pix_fmt', ''),
                        'bit_rate': stream.get('bit_rate', 0)
                    }
                    video_streams.append(video_info)
                    
                elif stream.get('codec_type') == 'audio':
                    audio_info = {
                        'codec': stream.get('codec_name', ''),
                        'sample_rate': stream.get('sample_rate', 0),
                        'channels': stream.get('channels', 0),
                        'bit_rate': stream.get('bit_rate', 0),
                        'language': stream.get('tags', {}).get('language', '')
                    }
                    audio_streams.append(audio_info)
            
            metadata['video_streams'] = video_streams
            metadata['audio_streams'] = audio_streams
            
            # Primary video/audio info
            if video_streams:
                primary_video = video_streams[0]
                metadata.update({
                    'width': primary_video['width'],
                    'height': primary_video['height'],
                    'video_codec': primary_video['codec'],
                    'resolution': f"{primary_video['width']}x{primary_video['height']}"
                })
            
            if audio_streams:
                primary_audio = audio_streams[0]
                metadata.update({
                    'audio_codec': primary_audio['codec'],
                    'sample_rate': primary_audio['sample_rate'],
                    'channels': primary_audio['channels']
                })
        
        return metadata
    
    def _find_subtitle_files(self, video_path: Path) -> List[str]:
        """Find subtitle files associated with video"""
        subtitle_files = []
        base_name = video_path.stem
        parent_dir = video_path.parent
        
        # Look for subtitle files with same name
        for ext in self.subtitle_extensions:
            subtitle_file = parent_dir / f"{base_name}{ext}"
            if subtitle_file.exists():
                subtitle_files.append(str(subtitle_file))
        
        return subtitle_files
    
    def _find_and_extract_subtitles(self, video_path: Path) -> str:
        """Find and extract text from subtitle files"""
        subtitle_files = self._find_subtitle_files(video_path)
        
        if not subtitle_files:
            return ""
        
        # Extract text from all subtitle files
        all_subtitle_text = []
        
        for subtitle_file in subtitle_files:
            try:
                text = self._extract_subtitle_text(subtitle_file)
                if text.strip():
                    all_subtitle_text.append(text)
            except Exception as e:
                self.logger.debug(f"Failed to extract subtitles from {subtitle_file}: {e}")
        
        return "\n\n".join(all_subtitle_text)
    
    def _extract_subtitle_text(self, subtitle_file: str) -> str:
        """Extract text content from subtitle file"""
        subtitle_path = Path(subtitle_file)
        
        try:
            # Detect encoding
            with open(subtitle_path, 'rb') as f:
                raw_data = f.read()
            
            # Try common encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            content = None
            
            for encoding in encodings:
                try:
                    content = raw_data.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                # Fallback with error handling
                content = raw_data.decode('utf-8', errors='ignore')
            
            # Parse subtitle content based on format
            extension = subtitle_path.suffix.lower()
            
            if extension == '.srt':
                return self._parse_srt_content(content)
            elif extension == '.vtt':
                return self._parse_vtt_content(content)
            else:
                # Generic text extraction
                return self._clean_subtitle_text(content)
                
        except Exception as e:
            self.logger.debug(f"Subtitle extraction failed: {e}")
            return ""
    
    def _parse_srt_content(self, content: str) -> str:
        """Parse SRT subtitle format"""
        import re
        
        # Remove SRT formatting (timestamps, indices)
        # Pattern: number, timestamp, text, blank line
        lines = content.split('\n')
        text_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines, numbers, and timestamps
            if (not line or 
                line.isdigit() or 
                '-->' in line or
                re.match(r'^\d{2}:\d{2}:\d{2}', line)):
                continue
            
            # Remove HTML tags if present
            line = re.sub(r'<[^>]+>', '', line)
            if line:
                text_lines.append(line)
        
        return ' '.join(text_lines)
    
    def _parse_vtt_content(self, content: str) -> str:
        """Parse WebVTT subtitle format"""
        import re
        
        lines = content.split('\n')
        text_lines = []
        in_cue = False
        
        for line in lines:
            line = line.strip()
            
            # Skip WEBVTT header
            if line.startswith('WEBVTT'):
                continue
                
            # Skip cue identifiers and timestamps
            if '-->' in line or re.match(r'^\d+$', line):
                in_cue = True
                continue
                
            # Empty line ends cue
            if not line:
                in_cue = False
                continue
                
            # Extract text content
            if line and not line.startswith('NOTE'):
                # Remove WebVTT tags
                line = re.sub(r'<[^>]+>', '', line)
                if line:
                    text_lines.append(line)
        
        return ' '.join(text_lines)
    
    def _clean_subtitle_text(self, content: str) -> str:
        """Generic subtitle text cleaning"""
        import re
        
        # Remove HTML/XML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Remove common subtitle artifacts
        content = re.sub(r'\d{2}:\d{2}:\d{2}[,\.]\d{3}', '', content)  # Timestamps
        content = re.sub(r'-->', '', content)  # Arrow separators
        content = re.sub(r'^\d+$', '', content, flags=re.MULTILINE)  # Line numbers
        
        # Clean whitespace
        content = re.sub(r'\n\s*\n', '\n', content)  # Multiple newlines
        content = re.sub(r'[ \t]+', ' ', content)  # Multiple spaces
        
        return content.strip()
    
    def _should_process_stt(self, metadata: Dict[str, Any]) -> bool:
        """Determine if video should be processed with STT"""
        duration = metadata.get('duration', 0)
        
        # Skip very long videos
        if duration > self.max_stt_duration:
            return False
        
        # Skip if no audio streams
        audio_streams = metadata.get('audio_streams', [])
        if not audio_streams:
            return False
        
        return True
    
    def _extract_audio_text(self, video_path: Path) -> Tuple[str, float]:
        """Extract audio from video and convert to text"""
        if not self.stt_engine:
            return "", 0.0
        
        try:
            # Extract audio to temporary file
            audio_path = self._extract_audio(video_path)
            if not audio_path:
                return "", 0.0
            
            # Perform speech-to-text
            if self.stt_engine['type'] == 'whisper':
                return self._stt_with_whisper(audio_path)
            elif self.stt_engine['type'] == 'speech_recognition':
                return self._stt_with_speech_recognition(audio_path)
            else:
                return "", 0.0
                
        except Exception as e:
            self.logger.debug(f"STT processing failed: {e}")
            return "", 0.0
    
    def _extract_audio(self, video_path: Path) -> Optional[str]:
        """Extract audio track from video"""
        if not self.ffmpeg_available:
            return None
        
        try:
            # Create audio cache directory
            audio_dir = self.cache_dir / "audio"
            audio_dir.mkdir(exist_ok=True)
            
            # Generate audio filename
            file_hash = hashlib.md5(str(video_path).encode()).hexdigest()[:12]
            audio_name = f"{file_hash}_{video_path.stem}.wav"
            audio_path = audio_dir / audio_name
            
            # Extract audio if not exists
            if not audio_path.exists():
                cmd = [
                    'ffmpeg', '-i', str(video_path),
                    '-vn',  # No video
                    '-acodec', 'pcm_s16le',  # WAV format
                    '-ar', '16000',  # 16kHz sample rate
                    '-ac', '1',  # Mono
                    '-y',  # Overwrite
                    str(audio_path)
                ]
                
                result = subprocess.run(cmd, capture_output=True, timeout=300)
                
                if result.returncode != 0:
                    self.logger.debug(f"Audio extraction failed: {result.stderr}")
                    return None
            
            return str(audio_path)
            
        except Exception as e:
            self.logger.debug(f"Audio extraction error: {e}")
            return None
    
    def _stt_with_whisper(self, audio_path: str) -> Tuple[str, float]:
        """Perform STT using Whisper"""
        try:
            model = self.stt_engine['model']
            result = model.transcribe(audio_path, language='ko')  # Auto-detect or force Korean
            
            text = result.get('text', '').strip()
            
            # Calculate average confidence from segments
            segments = result.get('segments', [])
            if segments:
                confidences = [seg.get('confidence', 0) for seg in segments if 'confidence' in seg]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
            else:
                avg_confidence = 0.5
            
            return text, avg_confidence
            
        except Exception as e:
            self.logger.debug(f"Whisper STT failed: {e}")
            return "", 0.0
    
    def _stt_with_speech_recognition(self, audio_path: str) -> Tuple[str, float]:
        """Perform STT using SpeechRecognition library"""
        try:
            import speech_recognition as sr
            
            recognizer = self.stt_engine['recognizer']
            
            # Load audio file
            with sr.AudioFile(audio_path) as source:
                audio = recognizer.record(source)
            
            # Try Google Speech Recognition (requires internet)
            try:
                text = recognizer.recognize_google(audio, language='ko-KR')
                return text, 0.7  # Default confidence
            except sr.UnknownValueException:
                return "", 0.0
            except sr.RequestError:
                # Fallback to offline recognition if available
                try:
                    text = recognizer.recognize_sphinx(audio)
                    return text, 0.5
                except:
                    return "", 0.0
                    
        except Exception as e:
            self.logger.debug(f"SpeechRecognition STT failed: {e}")
            return "", 0.0
    
    def _generate_thumbnails(self, video_path: Path) -> List[str]:
        """Generate thumbnail images from video"""
        if not self.ffmpeg_available:
            return []
        
        try:
            # Create thumbnail cache directory
            thumb_dir = self.cache_dir / "video_thumbnails"
            thumb_dir.mkdir(exist_ok=True)
            
            file_hash = hashlib.md5(str(video_path).encode()).hexdigest()[:12]
            thumbnail_paths = []
            
            # Generate thumbnails at different time points
            for i in range(self.thumbnail_count):
                thumb_name = f"{file_hash}_{video_path.stem}_{i}.jpg"
                thumb_path = thumb_dir / thumb_name
                
                if not thumb_path.exists():
                    # Calculate timestamp (10%, 50%, 90% of video)
                    percentage = [0.1, 0.5, 0.9][i]
                    
                    cmd = [
                        'ffmpeg', '-i', str(video_path),
                        '-ss', f'{percentage}%',
                        '-vframes', '1',
                        '-q:v', '2',  # High quality
                        '-y',  # Overwrite
                        str(thumb_path)
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, timeout=30)
                    
                    if result.returncode == 0:
                        thumbnail_paths.append(str(thumb_path))
                else:
                    thumbnail_paths.append(str(thumb_path))
            
            return thumbnail_paths
            
        except Exception as e:
            self.logger.debug(f"Thumbnail generation failed: {e}")
            return []
    
    def _metadata_to_text(self, metadata: Dict[str, Any]) -> str:
        """Convert video metadata to searchable text"""
        text_parts = []
        
        # Basic info
        if 'duration' in metadata:
            duration_min = int(metadata['duration'] // 60)
            text_parts.append(f"Duration: {duration_min} minutes")
        
        if 'resolution' in metadata:
            text_parts.append(f"Resolution: {metadata['resolution']}")
        
        if 'video_codec' in metadata:
            text_parts.append(f"Video: {metadata['video_codec']}")
        
        if 'audio_codec' in metadata:
            text_parts.append(f"Audio: {metadata['audio_codec']}")
        
        # Tags
        if 'tags' in metadata:
            tags = metadata['tags']
            for key, value in tags.items():
                if key.lower() in ['title', 'artist', 'album', 'genre', 'comment']:
                    text_parts.append(f"{key}: {value}")
        
        return " | ".join(text_parts)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get processor capabilities"""
        return {
            "ffmpeg_available": self.ffmpeg_available,
            "stt_available": self.stt_engine is not None,
            "stt_engine": self.stt_engine['type'] if self.stt_engine else None,
            "subtitle_support": True,
            "thumbnail_generation": self.ffmpeg_available,
            "metadata_extraction": self.ffmpeg_available,
            "supported_formats": self.supported_extensions,
            "subtitle_formats": self.subtitle_extensions,
            "max_file_size_gb": self.max_video_size // (1024**3),
            "max_stt_duration_hours": self.max_stt_duration // 3600
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processor statistics"""
        return {
            "processor_type": "video",
            "supported_extensions": len(self.supported_extensions),
            "extension_list": self.supported_extensions,
            "subtitle_extensions": self.subtitle_extensions,
            "features_enabled": {
                "metadata_extraction": self.ffmpeg_available,
                "stt": self.enable_stt and self.stt_engine is not None,
                "subtitle_extraction": True,
                "thumbnail_generation": self.ffmpeg_available
            },
            "capabilities": self.get_capabilities()
        }
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions"""
        return self.supported_extensions


def test_video_processor():
    """Test video processor functionality"""
    processor = VideoProcessor(enable_stt=True)
    
    print("🎬 Video Processor Test")
    print("=" * 40)
    
    # Display capabilities
    caps = processor.get_capabilities()
    print("🔧 Capabilities:")
    for key, value in caps.items():
        print(f"   {key}: {value}")
    
    # Test with sample video files
    test_files = [
        "/watch_directories/Desktop/test.mp4",
        "/watch_directories/Movies/sample.avi",
        "/watch_directories/Downloads/video.mkv"
    ]
    
    print("\n🔍 Testing video processing:")
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n🎥 Processing: {test_file}")
            
            text, success, metadata = processor.extract_content(test_file)
            
            if success:
                print(f"   ✅ Processing successful")
                print(f"   📝 Text extracted: {len(text)} characters")
                
                video_meta = metadata.get('video_metadata', {})
                print(f"   📏 Resolution: {video_meta.get('resolution', 'unknown')}")
                print(f"   ⏱️ Duration: {video_meta.get('duration', 0):.1f} seconds")
                print(f"   🎨 Video codec: {video_meta.get('video_codec', 'unknown')}")
                
                if text.strip():
                    preview = text[:200] + "..." if len(text) > 200 else text
                    print(f"   📄 Content preview: {repr(preview)}")
                
                # Show processing results
                proc_results = metadata.get('processing_results', {})
                print(f"   🎬 Thumbnails: {proc_results.get('thumbnails_generated', 0)}")
                if proc_results.get('stt_enabled'):
                    print(f"   🎤 STT confidence: {proc_results.get('stt_confidence', 0):.2f}")
                
            else:
                print(f"   ❌ Processing failed: {metadata.get('error', 'Unknown error')}")
        else:
            print(f"\n❌ File not found: {test_file}")


if __name__ == "__main__":
    test_video_processor()