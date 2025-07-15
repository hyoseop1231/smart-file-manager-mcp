#!/usr/bin/env python3
"""
Speech Recognition Service for Smart File Manager v4.0
Advanced speech-to-text using multiple engines
"""

import os
import logging
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
import tempfile

logger = logging.getLogger(__name__)


class SpeechRecognitionService:
    """
    Unified speech-to-text service with multiple engine support
    """
    
    def __init__(self, 
                 cache_dir: str = "/tmp/multimedia_cache",
                 preferred_engine: str = "auto"):
        
        self.logger = logging.getLogger(__name__)
        self.cache_dir = Path(cache_dir) / "speech_recognition"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Available engines
        self.engines = {}
        self.current_engine = None
        
        # Initialize engines in order of preference
        engine_priority = ["whisper", "speech_recognition", "vosk"]
        
        if preferred_engine != "auto" and preferred_engine in engine_priority:
            engine_priority = [preferred_engine] + [e for e in engine_priority if e != preferred_engine]
        
        for engine_name in engine_priority:
            if self._init_engine(engine_name):
                if self.current_engine is None:
                    self.current_engine = engine_name
        
        # Language support
        self.supported_languages = {
            "ko": "Korean",
            "en": "English", 
            "ja": "Japanese",
            "zh": "Chinese",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "auto": "Auto-detect"
        }
        
        # Processing limits
        self.max_audio_duration = 3600  # 1 hour
        self.chunk_duration = 300  # 5 minutes per chunk for long audio
    
    def _init_engine(self, engine_name: str) -> bool:
        """Initialize specific STT engine"""
        try:
            if engine_name == "whisper":
                return self._init_whisper()
            elif engine_name == "speech_recognition":
                return self._init_speech_recognition()
            elif engine_name == "vosk":
                return self._init_vosk()
            else:
                return False
        except Exception as e:
            self.logger.debug(f"Failed to initialize {engine_name}: {e}")
            return False
    
    def _init_whisper(self) -> bool:
        """Initialize OpenAI Whisper"""
        try:
            import whisper
            
            # Load model (base is good balance of speed/accuracy)
            model = whisper.load_model("base")
            
            self.engines['whisper'] = {
                'model': model,
                'module': whisper,
                'capabilities': ['multilingual', 'timestamps', 'high_accuracy'],
                'supported_languages': ['ko', 'en', 'ja', 'zh', 'es', 'fr', 'de', 'auto'],
                'max_duration': 3600
            }
            
            self.logger.info("✅ Whisper engine initialized")
            return True
            
        except ImportError:
            self.logger.debug("Whisper not available. Install with: pip install openai-whisper")
            return False
    
    def _init_speech_recognition(self) -> bool:
        """Initialize SpeechRecognition library"""
        try:
            import speech_recognition as sr
            
            recognizer = sr.Recognizer()
            
            self.engines['speech_recognition'] = {
                'recognizer': recognizer,
                'module': sr,
                'capabilities': ['google_api', 'offline_sphinx'],
                'supported_languages': ['ko', 'en', 'ja', 'zh', 'es', 'fr', 'de'],
                'max_duration': 300  # Google API has time limits
            }
            
            self.logger.info("✅ SpeechRecognition engine initialized")
            return True
            
        except ImportError:
            self.logger.debug("SpeechRecognition not available. Install with: pip install SpeechRecognition")
            return False
    
    def _init_vosk(self) -> bool:
        """Initialize Vosk offline speech recognition"""
        try:
            import vosk
            import json
            
            # Check if Korean model is available
            model_path = "/tmp/vosk-model-ko"  # User should download model
            
            if os.path.exists(model_path):
                model = vosk.Model(model_path)
                
                self.engines['vosk'] = {
                    'model': model,
                    'module': vosk,
                    'capabilities': ['offline', 'real_time', 'korean_optimized'],
                    'supported_languages': ['ko'],
                    'max_duration': 7200  # No API limits
                }
                
                self.logger.info("✅ Vosk engine initialized")
                return True
            else:
                self.logger.debug("Vosk model not found. Download Korean model to /tmp/vosk-model-ko")
                return False
                
        except ImportError:
            self.logger.debug("Vosk not available. Install with: pip install vosk")
            return False
    
    def transcribe_audio(self, 
                        audio_path: str, 
                        language: str = "auto",
                        engine: Optional[str] = None) -> Tuple[str, float, Dict[str, Any]]:
        """
        Transcribe audio to text
        
        Args:
            audio_path: Path to audio file
            language: Language code ('ko', 'en', 'auto', etc.)
            engine: Specific engine to use (None for auto-select)
            
        Returns:
            tuple: (transcribed_text, confidence, metadata)
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            return "", 0.0, {"error": "Audio file not found"}
        
        # Check cache first
        cache_key = self._get_cache_key(str(audio_path), language, engine)
        cached_result = self._load_cached_transcription(cache_key)
        if cached_result:
            return cached_result
        
        # Select engine
        selected_engine = engine or self.current_engine
        if not selected_engine or selected_engine not in self.engines:
            return "", 0.0, {"error": "No speech recognition engine available"}
        
        # Check audio duration and split if necessary
        audio_duration = self._get_audio_duration(audio_path)
        if audio_duration > self.max_audio_duration:
            return "", 0.0, {"error": f"Audio too long: {audio_duration}s (max: {self.max_audio_duration}s)"}
        
        try:
            # Process audio
            if audio_duration > self.chunk_duration:
                # Process in chunks for long audio
                text, confidence, metadata = self._transcribe_chunked(audio_path, language, selected_engine)
            else:
                # Process entire file
                text, confidence, metadata = self._transcribe_single(audio_path, language, selected_engine)
            
            # Cache successful results
            if text.strip():
                self._cache_transcription(cache_key, text, confidence, metadata)
            
            return text, confidence, metadata
            
        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            return "", 0.0, {"error": str(e), "engine": selected_engine}
    
    def _transcribe_single(self, audio_path: Path, language: str, engine: str) -> Tuple[str, float, Dict[str, Any]]:
        """Transcribe single audio file"""
        if engine == "whisper":
            return self._transcribe_with_whisper(audio_path, language)
        elif engine == "speech_recognition":
            return self._transcribe_with_speech_recognition(audio_path, language)
        elif engine == "vosk":
            return self._transcribe_with_vosk(audio_path, language)
        else:
            return "", 0.0, {"error": f"Unknown engine: {engine}"}
    
    def _transcribe_chunked(self, audio_path: Path, language: str, engine: str) -> Tuple[str, float, Dict[str, Any]]:
        """Transcribe long audio by splitting into chunks"""
        try:
            # Split audio into chunks
            chunks = self._split_audio(audio_path, self.chunk_duration)
            
            all_texts = []
            all_confidences = []
            chunk_results = []
            
            for i, chunk_path in enumerate(chunks):
                try:
                    text, confidence, metadata = self._transcribe_single(chunk_path, language, engine)
                    
                    if text.strip():
                        all_texts.append(text)
                        all_confidences.append(confidence)
                        chunk_results.append({
                            "chunk": i,
                            "text": text,
                            "confidence": confidence
                        })
                    
                    # Clean up chunk file
                    os.unlink(chunk_path)
                    
                except Exception as e:
                    self.logger.warning(f"Chunk {i} transcription failed: {e}")
                    continue
            
            # Combine results
            combined_text = " ".join(all_texts)
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
            
            metadata = {
                "engine": engine,
                "language": language,
                "chunks_processed": len(chunk_results),
                "total_chunks": len(chunks),
                "chunk_results": chunk_results,
                "processing_method": "chunked"
            }
            
            return combined_text, avg_confidence, metadata
            
        except Exception as e:
            return "", 0.0, {"error": f"Chunked transcription failed: {e}"}
    
    def _transcribe_with_whisper(self, audio_path: Path, language: str) -> Tuple[str, float, Dict[str, Any]]:
        """Transcribe using Whisper"""
        try:
            model = self.engines['whisper']['model']
            
            # Set language parameter
            lang_param = None if language == "auto" else language
            
            # Transcribe
            result = model.transcribe(str(audio_path), language=lang_param)
            
            text = result.get('text', '').strip()
            detected_language = result.get('language', 'unknown')
            
            # Calculate confidence from segments
            segments = result.get('segments', [])
            if segments:
                confidences = [seg.get('confidence', 0) for seg in segments if 'confidence' in seg]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.7
            else:
                avg_confidence = 0.7  # Default for Whisper
            
            metadata = {
                "engine": "whisper",
                "detected_language": detected_language,
                "segments_count": len(segments),
                "has_timestamps": bool(segments),
                "model_size": "base"
            }
            
            return text, avg_confidence, metadata
            
        except Exception as e:
            return "", 0.0, {"error": f"Whisper transcription failed: {e}"}
    
    def _transcribe_with_speech_recognition(self, audio_path: Path, language: str) -> Tuple[str, float, Dict[str, Any]]:
        """Transcribe using SpeechRecognition library"""
        try:
            sr = self.engines['speech_recognition']['module']
            recognizer = self.engines['speech_recognition']['recognizer']
            
            # Load audio
            with sr.AudioFile(str(audio_path)) as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = recognizer.record(source)
            
            # Language mapping
            lang_codes = {
                "ko": "ko-KR",
                "en": "en-US", 
                "ja": "ja-JP",
                "zh": "zh-CN",
                "es": "es-ES",
                "fr": "fr-FR",
                "de": "de-DE"
            }
            
            google_lang = lang_codes.get(language, "en-US") if language != "auto" else None
            
            # Try Google Speech Recognition first
            try:
                text = recognizer.recognize_google(audio, language=google_lang)
                confidence = 0.8  # Google API is generally reliable
                method = "google_api"
                
            except (sr.UnknownValueException, sr.RequestError):
                # Fallback to offline Sphinx
                try:
                    text = recognizer.recognize_sphinx(audio)
                    confidence = 0.6  # Sphinx is less reliable
                    method = "sphinx_offline"
                except:
                    return "", 0.0, {"error": "All SpeechRecognition methods failed"}
            
            metadata = {
                "engine": "speech_recognition",
                "method": method,
                "language_code": google_lang or "auto"
            }
            
            return text, confidence, metadata
            
        except Exception as e:
            return "", 0.0, {"error": f"SpeechRecognition failed: {e}"}
    
    def _transcribe_with_vosk(self, audio_path: Path, language: str) -> Tuple[str, float, Dict[str, Any]]:
        """Transcribe using Vosk"""
        try:
            vosk = self.engines['vosk']['module']
            model = self.engines['vosk']['model']
            
            # Vosk works with WAV files, convert if needed
            wav_path = self._convert_to_wav(audio_path)
            
            # Create recognizer
            rec = vosk.KaldiRecognizer(model, 16000)
            
            # Process audio
            import wave
            wf = wave.open(str(wav_path), 'rb')
            
            results = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    if 'text' in result and result['text'].strip():
                        results.append(result['text'])
            
            # Final result
            final_result = json.loads(rec.FinalResult())
            if 'text' in final_result and final_result['text'].strip():
                results.append(final_result['text'])
            
            wf.close()
            
            # Clean up converted file if created
            if wav_path != audio_path:
                os.unlink(wav_path)
            
            combined_text = " ".join(results)
            confidence = 0.7  # Vosk default confidence
            
            metadata = {
                "engine": "vosk",
                "language": "korean",
                "segments_count": len(results),
                "offline": True
            }
            
            return combined_text, confidence, metadata
            
        except Exception as e:
            return "", 0.0, {"error": f"Vosk transcription failed: {e}"}
    
    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get audio duration in seconds"""
        try:
            # Use ffprobe to get duration
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', str(audio_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                return float(data.get('format', {}).get('duration', 0))
            else:
                # Fallback: estimate from file size (very rough)
                file_size = audio_path.stat().st_size
                # Assume ~128kbps average bitrate
                estimated_duration = file_size / (128 * 1024 / 8)  
                return estimated_duration
                
        except Exception:
            # Last resort: assume reasonable duration
            return 300  # 5 minutes default
    
    def _split_audio(self, audio_path: Path, chunk_duration: int) -> List[Path]:
        """Split audio into chunks"""
        chunks = []
        
        try:
            audio_duration = self._get_audio_duration(audio_path)
            num_chunks = int(audio_duration // chunk_duration) + 1
            
            for i in range(num_chunks):
                start_time = i * chunk_duration
                
                # Create temporary chunk file
                chunk_path = Path(tempfile.mktemp(suffix=".wav"))
                
                cmd = [
                    'ffmpeg', '-i', str(audio_path),
                    '-ss', str(start_time),
                    '-t', str(chunk_duration),
                    '-acodec', 'pcm_s16le',
                    '-ar', '16000',
                    '-ac', '1',
                    '-y',  # Overwrite
                    str(chunk_path)
                ]
                
                result = subprocess.run(cmd, capture_output=True, timeout=60)
                
                if result.returncode == 0 and chunk_path.exists():
                    chunks.append(chunk_path)
                else:
                    break  # Stop if chunk creation fails
            
            return chunks
            
        except Exception as e:
            self.logger.warning(f"Audio splitting failed: {e}")
            return [audio_path]  # Return original file
    
    def _convert_to_wav(self, audio_path: Path) -> Path:
        """Convert audio to WAV format for compatibility"""
        if audio_path.suffix.lower() == '.wav':
            return audio_path
        
        try:
            wav_path = Path(tempfile.mktemp(suffix=".wav"))
            
            cmd = [
                'ffmpeg', '-i', str(audio_path),
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                '-y',
                str(wav_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=120)
            
            if result.returncode == 0:
                return wav_path
            else:
                return audio_path  # Return original if conversion fails
                
        except Exception:
            return audio_path
    
    def _get_cache_key(self, audio_path: str, language: str, engine: Optional[str]) -> str:
        """Generate cache key for transcription"""
        stat = Path(audio_path).stat()
        content = f"{audio_path}_{language}_{engine}_{stat.st_mtime}_{stat.st_size}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _load_cached_transcription(self, cache_key: str) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Load cached transcription"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data['text'], data['confidence'], data['metadata']
        except:
            pass
        
        return None
    
    def _cache_transcription(self, cache_key: str, text: str, confidence: float, metadata: Dict[str, Any]):
        """Cache transcription results"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            cache_data = {
                'text': text,
                'confidence': confidence,
                'metadata': metadata,
                'timestamp': Path().stat().st_ctime if Path().exists() else 0
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except:
            pass  # Cache failure is not critical
    
    def get_available_engines(self) -> List[str]:
        """Get list of available engines"""
        return list(self.engines.keys())
    
    def get_engine_info(self, engine_name: str) -> Dict[str, Any]:
        """Get information about specific engine"""
        if engine_name in self.engines:
            return self.engines[engine_name]
        return {}
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get service capabilities"""
        return {
            "available_engines": list(self.engines.keys()),
            "current_engine": self.current_engine,
            "supported_languages": self.supported_languages,
            "max_audio_duration": self.max_audio_duration,
            "chunk_duration": self.chunk_duration,
            "engine_capabilities": {
                name: info.get('capabilities', [])
                for name, info in self.engines.items()
            }
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        # Count cached transcriptions
        cache_count = len(list(self.cache_dir.glob("*.json"))) if self.cache_dir.exists() else 0
        
        return {
            "service_type": "speech_recognition",
            "engines_loaded": len(self.engines),
            "engine_details": {
                name: {
                    "capabilities": info.get('capabilities', []),
                    "max_duration": info.get('max_duration', 0),
                    "languages": info.get('supported_languages', [])
                }
                for name, info in self.engines.items()
            },
            "cache_entries": cache_count,
            "supported_languages": len(self.supported_languages)
        }


def test_speech_recognition_service():
    """Test speech recognition service"""
    service = SpeechRecognitionService()
    
    print("🎤 Speech Recognition Service Test")
    print("=" * 50)
    
    # Display capabilities
    caps = service.get_capabilities()
    print("🔧 Capabilities:")
    for key, value in caps.items():
        if isinstance(value, dict):
            print(f"   {key}: {len(value)} items")
        elif isinstance(value, list):
            print(f"   {key}: {value}")
        else:
            print(f"   {key}: {value}")
    
    # Test with sample audio files
    test_files = [
        "/watch_directories/Desktop/voice_memo.wav",
        "/watch_directories/Music/speech.mp3",
        "/watch_directories/Downloads/interview.m4a"
    ]
    
    print("\n🔍 Testing speech recognition:")
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n🎧 Processing: {test_file}")
            
            text, confidence, metadata = service.transcribe_audio(test_file, language="ko")
            
            if text:
                print(f"   ✅ Transcription successful")
                print(f"   📝 Text length: {len(text)} characters")
                print(f"   🎯 Confidence: {confidence:.3f}")
                print(f"   🔧 Engine: {metadata.get('engine', 'unknown')}")
                
                if text.strip():
                    preview = text[:200] + "..." if len(text) > 200 else text
                    print(f"   📄 Text preview: {repr(preview)}")
                
            else:
                print(f"   ❌ Transcription failed: {metadata.get('error', 'Unknown error')}")
        else:
            print(f"\n❌ File not found: {test_file}")


if __name__ == "__main__":
    test_speech_recognition_service()