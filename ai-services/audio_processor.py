#!/usr/bin/env python3
"""
Audio Content Processor for Smart File Manager v4.0
Metadata extraction, STT, and audio analysis
"""

import os
import logging
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
import mimetypes

logger = logging.getLogger(__name__)


class AudioProcessor:
    """
    Comprehensive audio content processor
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
        
        # Check for ffmpeg availability (for metadata and conversion)
        self.ffmpeg_available = self._check_ffmpeg()
        
        # Audio metadata library
        self.metadata_engine = None
        self._init_metadata_engine()
        
        # Supported audio formats
        self.supported_extensions = [
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', 
            '.opus', '.aiff', '.au', '.ra', '.amr', '.3ga'
        ]
        
        # Processing limits
        self.max_audio_size = 100 * 1024 * 1024  # 100MB
        self.max_stt_duration = 7200  # 2 hours for STT
    
    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.logger.info("✅ FFmpeg available for audio processing")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        self.logger.warning("⚠️ FFmpeg not available for audio processing")
        return False
    
    def _init_metadata_engine(self):
        """Initialize audio metadata extraction engine"""
        # Try mutagen first (best metadata support)
        try:
            import mutagen
            self.metadata_engine = {
                'type': 'mutagen',
                'module': mutagen
            }
            self.logger.info("✅ Audio metadata engine (Mutagen) initialized")
            return
        except ImportError:
            pass
        
        # Try eyed3 for MP3 files
        try:
            import eyed3
            self.metadata_engine = {
                'type': 'eyed3',
                'module': eyed3
            }
            self.logger.info("✅ Audio metadata engine (EyeD3) initialized")
            return
        except ImportError:
            pass
        
        self.logger.warning("⚠️ No audio metadata library available. Install with: pip install mutagen or pip install eyed3")
    
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
        Extract content from audio file
        
        Returns:
            tuple: (extracted_text, success, metadata)
        """
        file_path = Path(file_path)
        
        try:
            # Extract audio metadata
            audio_metadata = self._extract_audio_metadata(file_path)
            
            # Perform speech-to-text
            stt_text = ""
            stt_confidence = 0
            if self.enable_stt and self.stt_engine and self._should_process_stt(audio_metadata):
                stt_text, stt_confidence = self._extract_speech_text(file_path)
            
            # Combine all extracted text
            combined_text = []
            if stt_text.strip():
                combined_text.append(f"Spoken Content: {stt_text}")
            
            # Add metadata as searchable text
            metadata_text = self._metadata_to_text(audio_metadata)
            if metadata_text.strip():
                combined_text.append(f"Audio Info: {metadata_text}")
            
            final_text = "\n\n".join(combined_text)
            
            # Compile metadata
            metadata = {
                "audio_metadata": audio_metadata,
                "processing_results": {
                    "stt_enabled": self.enable_stt,
                    "stt_text_length": len(stt_text),
                    "stt_confidence": stt_confidence,
                    "metadata_extracted": len(audio_metadata) > 0
                },
                "success": True
            }
            
            success = len(final_text.strip()) > 0 or len(audio_metadata) > 0
            
            return final_text, success, metadata
            
        except Exception as e:
            return "", False, {"error": str(e), "audio_processing_failed": True}
    
    def _extract_audio_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract comprehensive audio metadata"""
        metadata = {}
        
        # Try specialized metadata extraction first
        if self.metadata_engine:
            try:
                if self.metadata_engine['type'] == 'mutagen':
                    metadata.update(self._extract_mutagen_metadata(file_path))
                elif self.metadata_engine['type'] == 'eyed3':
                    metadata.update(self._extract_eyed3_metadata(file_path))
            except Exception as e:
                self.logger.debug(f"Specialized metadata extraction failed: {e}")
        
        # Fallback to ffprobe if available
        if self.ffmpeg_available and not metadata:
            try:
                metadata.update(self._extract_ffprobe_metadata(file_path))
            except Exception as e:
                self.logger.debug(f"FFprobe metadata extraction failed: {e}")
        
        # Basic file information as fallback
        if not metadata:
            metadata = self._basic_audio_metadata(file_path)
        
        return metadata
    
    def _extract_mutagen_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata using Mutagen"""
        mutagen = self.metadata_engine['module']
        
        try:
            audio_file = mutagen.File(str(file_path))
            if audio_file is None:
                return {}
            
            metadata = {}
            
            # Basic audio properties
            if hasattr(audio_file, 'info'):
                info = audio_file.info
                metadata.update({
                    'duration': getattr(info, 'length', 0),
                    'bitrate': getattr(info, 'bitrate', 0),
                    'sample_rate': getattr(info, 'sample_rate', 0),
                    'channels': getattr(info, 'channels', 0),
                    'codec': getattr(info, 'codec', ''),
                    'format': str(type(info).__name__)
                })
            
            # Tag information
            if hasattr(audio_file, 'tags') and audio_file.tags:
                tags = audio_file.tags
                
                # Common tag mappings
                tag_mappings = {
                    'title': ['TIT2', 'TITLE', '\xa9nam'],
                    'artist': ['TPE1', 'ARTIST', '\xa9ART'],
                    'album': ['TALB', 'ALBUM', '\xa9alb'],
                    'date': ['TDRC', 'DATE', '\xa9day'],
                    'genre': ['TCON', 'GENRE', '\xa9gen'],
                    'track': ['TRCK', 'TRACKNUMBER', 'trkn'],
                    'albumartist': ['TPE2', 'ALBUMARTIST', 'aART'],
                    'composer': ['TCOM', 'COMPOSER', '\xa9wrt'],
                    'comment': ['COMM', 'COMMENT', '\xa9cmt']
                }
                
                for field, possible_keys in tag_mappings.items():
                    for key in possible_keys:
                        if key in tags:
                            value = tags[key]
                            if isinstance(value, list) and value:
                                value = value[0]
                            if hasattr(value, 'text'):
                                value = str(value.text[0]) if value.text else str(value)
                            metadata[field] = str(value)
                            break
            
            return metadata
            
        except Exception as e:
            self.logger.debug(f"Mutagen metadata extraction failed: {e}")
            return {}
    
    def _extract_eyed3_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata using EyeD3 (MP3 only)"""
        if file_path.suffix.lower() != '.mp3':
            return {}
        
        try:
            eyed3 = self.metadata_engine['module']
            audio_file = eyed3.load(str(file_path))
            
            if audio_file is None:
                return {}
            
            metadata = {}
            
            # Audio info
            if audio_file.info:
                info = audio_file.info
                metadata.update({
                    'duration': info.time_secs,
                    'bitrate': info.bit_rate[1] if info.bit_rate else 0,
                    'sample_rate': info.sample_freq,
                    'mode': info.mode,
                    'format': 'MP3'
                })
            
            # Tag info
            if audio_file.tag:
                tag = audio_file.tag
                metadata.update({
                    'title': tag.title or '',
                    'artist': tag.artist or '',
                    'album': tag.album or '',
                    'date': str(tag.release_date) if tag.release_date else '',
                    'genre': tag.genre.name if tag.genre else '',
                    'track': f"{tag.track_num[0]}/{tag.track_num[1]}" if tag.track_num else '',
                    'albumartist': tag.album_artist or '',
                    'composer': tag.composer or ''
                })
            
            return metadata
            
        except Exception as e:
            self.logger.debug(f"EyeD3 metadata extraction failed: {e}")
            return {}
    
    def _extract_ffprobe_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata using ffprobe"""
        try:
            import json
            
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(file_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                probe_data = json.loads(result.stdout)
                return self._parse_ffprobe_audio_data(probe_data)
            else:
                return {}
                
        except Exception as e:
            self.logger.debug(f"FFprobe metadata extraction failed: {e}")
            return {}
    
    def _parse_ffprobe_audio_data(self, probe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ffprobe JSON output for audio"""
        metadata = {}
        
        # Format information
        if 'format' in probe_data:
            format_info = probe_data['format']
            metadata.update({
                'duration': float(format_info.get('duration', 0)),
                'size': int(format_info.get('size', 0)),
                'bit_rate': int(format_info.get('bit_rate', 0)),
                'format_name': format_info.get('format_name', '')
            })
            
            # Tags
            if 'tags' in format_info:
                tags = format_info['tags']
                # Normalize tag names
                tag_map = {
                    'title': tags.get('title', ''),
                    'artist': tags.get('artist', ''),
                    'album': tags.get('album', ''),
                    'date': tags.get('date', ''),
                    'genre': tags.get('genre', ''),
                    'track': tags.get('track', ''),
                    'albumartist': tags.get('album_artist', ''),
                    'composer': tags.get('composer', ''),
                    'comment': tags.get('comment', '')
                }
                metadata.update({k: v for k, v in tag_map.items() if v})
        
        # Stream information (first audio stream)
        if 'streams' in probe_data:
            for stream in probe_data['streams']:
                if stream.get('codec_type') == 'audio':
                    metadata.update({
                        'codec': stream.get('codec_name', ''),
                        'sample_rate': int(stream.get('sample_rate', 0)),
                        'channels': int(stream.get('channels', 0)),
                        'channel_layout': stream.get('channel_layout', ''),
                        'bit_rate': int(stream.get('bit_rate', 0))
                    })
                    break
        
        return metadata
    
    def _basic_audio_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract basic metadata without specialized tools"""
        stat = file_path.stat()
        return {
            "file_size": stat.st_size,
            "modified_time": stat.st_mtime,
            "format": file_path.suffix.lower().lstrip('.'),
            "container": file_path.suffix.lower().lstrip('.')
        }
    
    def _should_process_stt(self, metadata: Dict[str, Any]) -> bool:
        """Determine if audio should be processed with STT"""
        duration = metadata.get('duration', 0)
        
        # Skip very long audio files
        if duration > self.max_stt_duration:
            return False
        
        # Skip if it's music (has artist/album tags) unless it's very short
        if duration > 60 and metadata.get('artist') and metadata.get('album'):
            return False
        
        return True
    
    def _extract_speech_text(self, audio_path: Path) -> Tuple[str, float]:
        """Extract speech text from audio file"""
        if not self.stt_engine:
            return "", 0.0
        
        try:
            # Convert audio to compatible format if needed
            processed_audio_path = self._prepare_audio_for_stt(audio_path)
            if not processed_audio_path:
                return "", 0.0
            
            # Perform speech-to-text
            if self.stt_engine['type'] == 'whisper':
                return self._stt_with_whisper(processed_audio_path)
            elif self.stt_engine['type'] == 'speech_recognition':
                return self._stt_with_speech_recognition(processed_audio_path)
            else:
                return "", 0.0
                
        except Exception as e:
            self.logger.debug(f"STT processing failed: {e}")
            return "", 0.0
    
    def _prepare_audio_for_stt(self, audio_path: Path) -> Optional[str]:
        """Convert audio to format suitable for STT"""
        # If it's already WAV, use as-is
        if audio_path.suffix.lower() == '.wav':
            return str(audio_path)
        
        if not self.ffmpeg_available:
            # If no ffmpeg, try with original file
            return str(audio_path)
        
        try:
            # Create processed audio cache directory
            audio_dir = self.cache_dir / "stt_audio"
            audio_dir.mkdir(exist_ok=True)
            
            # Generate processed filename
            file_hash = hashlib.md5(str(audio_path).encode()).hexdigest()[:12]
            processed_name = f"{file_hash}_{audio_path.stem}.wav"
            processed_path = audio_dir / processed_name
            
            # Convert audio if not exists
            if not processed_path.exists():
                cmd = [
                    'ffmpeg', '-i', str(audio_path),
                    '-acodec', 'pcm_s16le',  # WAV format
                    '-ar', '16000',  # 16kHz sample rate (good for speech)
                    '-ac', '1',  # Mono
                    '-y',  # Overwrite
                    str(processed_path)
                ]
                
                result = subprocess.run(cmd, capture_output=True, timeout=300)
                
                if result.returncode != 0:
                    self.logger.debug(f"Audio conversion failed: {result.stderr}")
                    return str(audio_path)  # Try with original
            
            return str(processed_path)
            
        except Exception as e:
            self.logger.debug(f"Audio preprocessing error: {e}")
            return str(audio_path)  # Fallback to original
    
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
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=1)
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
    
    def _metadata_to_text(self, metadata: Dict[str, Any]) -> str:
        """Convert audio metadata to searchable text"""
        text_parts = []
        
        # Music tags
        for field in ['title', 'artist', 'album', 'genre', 'albumartist', 'composer']:
            if field in metadata and metadata[field]:
                text_parts.append(f"{field.title()}: {metadata[field]}")
        
        # Technical info
        if 'duration' in metadata:
            duration_min = int(metadata['duration'] // 60)
            duration_sec = int(metadata['duration'] % 60)
            text_parts.append(f"Duration: {duration_min}:{duration_sec:02d}")
        
        if 'bitrate' in metadata and metadata['bitrate']:
            text_parts.append(f"Bitrate: {metadata['bitrate']} kbps")
        
        if 'sample_rate' in metadata and metadata['sample_rate']:
            text_parts.append(f"Sample Rate: {metadata['sample_rate']} Hz")
        
        if 'codec' in metadata and metadata['codec']:
            text_parts.append(f"Codec: {metadata['codec']}")
        
        return " | ".join(text_parts)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get processor capabilities"""
        return {
            "metadata_engine": self.metadata_engine['type'] if self.metadata_engine else None,
            "ffmpeg_available": self.ffmpeg_available,
            "stt_available": self.stt_engine is not None,
            "stt_engine": self.stt_engine['type'] if self.stt_engine else None,
            "supported_formats": self.supported_extensions,
            "max_file_size_mb": self.max_audio_size // (1024 * 1024),
            "max_stt_duration_hours": self.max_stt_duration // 3600
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processor statistics"""
        return {
            "processor_type": "audio",
            "supported_extensions": len(self.supported_extensions),
            "extension_list": self.supported_extensions,
            "features_enabled": {
                "metadata_extraction": self.metadata_engine is not None,
                "stt": self.enable_stt and self.stt_engine is not None,
                "format_conversion": self.ffmpeg_available
            },
            "capabilities": self.get_capabilities()
        }
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions"""
        return self.supported_extensions


def test_audio_processor():
    """Test audio processor functionality"""
    processor = AudioProcessor(enable_stt=True)
    
    print("🎵 Audio Processor Test")
    print("=" * 40)
    
    # Display capabilities
    caps = processor.get_capabilities()
    print("🔧 Capabilities:")
    for key, value in caps.items():
        print(f"   {key}: {value}")
    
    # Test with sample audio files
    test_files = [
        "/watch_directories/Desktop/test.mp3",
        "/watch_directories/Music/sample.wav",
        "/watch_directories/Downloads/audio.flac",
        "/watch_directories/Desktop/voice_memo.m4a"
    ]
    
    print("\n🔍 Testing audio processing:")
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n🎧 Processing: {test_file}")
            
            text, success, metadata = processor.extract_content(test_file)
            
            if success:
                print(f"   ✅ Processing successful")
                print(f"   📝 Text extracted: {len(text)} characters")
                
                audio_meta = metadata.get('audio_metadata', {})
                print(f"   ⏱️ Duration: {audio_meta.get('duration', 0):.1f} seconds")
                print(f"   🎨 Format: {audio_meta.get('format', 'unknown')}")
                print(f"   🎤 Artist: {audio_meta.get('artist', 'unknown')}")
                print(f"   💿 Album: {audio_meta.get('album', 'unknown')}")
                
                if text.strip():
                    preview = text[:200] + "..." if len(text) > 200 else text
                    print(f"   📄 Content preview: {repr(preview)}")
                
                # Show processing results
                proc_results = metadata.get('processing_results', {})
                if proc_results.get('stt_enabled'):
                    print(f"   🎤 STT confidence: {proc_results.get('stt_confidence', 0):.2f}")
                
            else:
                print(f"   ❌ Processing failed: {metadata.get('error', 'Unknown error')}")
        else:
            print(f"\n❌ File not found: {test_file}")


if __name__ == "__main__":
    test_audio_processor()