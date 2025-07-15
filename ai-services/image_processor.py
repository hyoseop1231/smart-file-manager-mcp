#!/usr/bin/env python3
"""
Image Content Processor for Smart File Manager v4.0
OCR, EXIF, AI analysis, and thumbnail generation
"""

import os
import io
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
from PIL import Image, ExifTags
import mimetypes

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Comprehensive image content processor
    """
    
    def __init__(self, 
                 enable_ocr: bool = True,
                 enable_ai_vision: bool = False,
                 cache_dir: str = "/tmp/multimedia_cache"):
        
        self.logger = logging.getLogger(__name__)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # OCR capabilities
        self.enable_ocr = enable_ocr
        self.ocr_engine = None
        if enable_ocr:
            self._init_ocr()
        
        # AI Vision capabilities  
        self.enable_ai_vision = enable_ai_vision
        self.vision_model = None
        if enable_ai_vision:
            self._init_ai_vision()
        
        # Supported image formats
        self.supported_extensions = [
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', 
            '.tiff', '.tga', '.ico', '.heic', '.heif'
        ]
        
        # Processing limits
        self.max_image_size = 50 * 1024 * 1024  # 50MB
        self.max_ocr_dimensions = (4000, 4000)  # Max resolution for OCR
        self.thumbnail_size = (300, 300)
    
    def _init_ocr(self):
        """Initialize OCR engine (pytesseract)"""
        try:
            import pytesseract
            from PIL import Image
            
            # Test OCR availability
            test_image = Image.new('RGB', (100, 50), color='white')
            pytesseract.image_to_string(test_image)
            
            self.ocr_engine = pytesseract
            self.logger.info("✅ OCR engine (Tesseract) initialized")
            
        except ImportError:
            self.logger.warning("⚠️ pytesseract not available. Install with: pip install pytesseract")
        except Exception as e:
            self.logger.warning(f"⚠️ OCR initialization failed: {e}")
    
    def _init_ai_vision(self):
        """Initialize AI vision model (CLIP)"""
        try:
            import torch
            import clip
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model, preprocess = clip.load("ViT-B/32", device=device)
            
            self.vision_model = {
                'model': model,
                'preprocess': preprocess,
                'device': device
            }
            self.logger.info(f"✅ AI Vision model (CLIP) initialized on {device}")
            
        except ImportError:
            self.logger.warning("⚠️ CLIP model not available. Install with: pip install torch torchvision clip-by-openai")
        except Exception as e:
            self.logger.warning(f"⚠️ AI Vision initialization failed: {e}")
    
    def can_process(self, file_path: str) -> bool:
        """Check if file can be processed"""
        extension = Path(file_path).suffix.lower()
        return extension in self.supported_extensions
    
    def extract_content(self, file_path: str) -> Tuple[str, bool, Dict[str, Any]]:
        """
        Extract content from image file
        
        Returns:
            tuple: (extracted_text, success, metadata)
        """
        file_path = Path(file_path)
        
        try:
            # Open and validate image
            with Image.open(file_path) as img:
                # Extract EXIF metadata
                exif_data = self._extract_exif(img)
                
                # Extract text via OCR
                ocr_text = ""
                ocr_confidence = 0
                if self.enable_ocr and self.ocr_engine:
                    ocr_text, ocr_confidence = self._extract_ocr_text(img)
                
                # AI image analysis
                ai_description = ""
                ai_confidence = 0
                if self.enable_ai_vision and self.vision_model:
                    ai_description, ai_confidence = self._analyze_with_ai(img)
                
                # Generate thumbnail
                thumbnail_path = self._generate_thumbnail(file_path, img)
                
                # Combine all extracted text
                combined_text = []
                if ocr_text.strip():
                    combined_text.append(f"OCR Text: {ocr_text}")
                if ai_description.strip():
                    combined_text.append(f"Image Description: {ai_description}")
                
                # Add EXIF text content
                exif_text = self._exif_to_text(exif_data)
                if exif_text.strip():
                    combined_text.append(f"EXIF Data: {exif_text}")
                
                final_text = "\n\n".join(combined_text)
                
                # Compile metadata
                metadata = {
                    "image_format": img.format,
                    "image_mode": img.mode,
                    "dimensions": img.size,
                    "width": img.size[0],
                    "height": img.size[1],
                    "has_transparency": img.mode in ('RGBA', 'LA') or 'transparency' in img.info,
                    "exif_data": exif_data,
                    "thumbnail_path": thumbnail_path,
                    "processing_results": {
                        "ocr_enabled": self.enable_ocr,
                        "ocr_text_length": len(ocr_text),
                        "ocr_confidence": ocr_confidence,
                        "ai_vision_enabled": self.enable_ai_vision,
                        "ai_description_length": len(ai_description),
                        "ai_confidence": ai_confidence
                    },
                    "success": True
                }
                
                success = len(final_text.strip()) > 0 or len(exif_data) > 0
                
                return final_text, success, metadata
                
        except Exception as e:
            return "", False, {"error": str(e), "image_processing_failed": True}
    
    def _extract_exif(self, img: Image.Image) -> Dict[str, Any]:
        """Extract EXIF metadata from image"""
        exif_data = {}
        
        try:
            if hasattr(img, '_getexif') and img._getexif() is not None:
                exif = img._getexif()
                for tag_id, value in exif.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    try:
                        # Convert bytes to string if needed
                        if isinstance(value, bytes):
                            value = value.decode('utf-8', errors='ignore')
                        exif_data[tag] = value
                    except:
                        # Skip problematic EXIF values
                        continue
        except Exception as e:
            self.logger.debug(f"EXIF extraction failed: {e}")
        
        return exif_data
    
    def _extract_ocr_text(self, img: Image.Image) -> Tuple[str, float]:
        """Extract text from image using OCR"""
        if not self.ocr_engine:
            return "", 0.0
        
        try:
            # Resize image if too large for OCR
            if img.size[0] > self.max_ocr_dimensions[0] or img.size[1] > self.max_ocr_dimensions[1]:
                img.thumbnail(self.max_ocr_dimensions, Image.Resampling.LANCZOS)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Extract text with confidence
            try:
                # Get detailed OCR data with confidence scores
                ocr_data = self.ocr_engine.image_to_data(img, output_type=self.ocr_engine.Output.DICT)
                
                # Filter out low-confidence text
                texts = []
                confidences = []
                for i, conf in enumerate(ocr_data['conf']):
                    if int(conf) > 30:  # Confidence threshold
                        text = ocr_data['text'][i].strip()
                        if text:
                            texts.append(text)
                            confidences.append(int(conf))
                
                combined_text = ' '.join(texts)
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                return combined_text, avg_confidence / 100.0  # Convert to 0-1 scale
                
            except:
                # Fallback to simple text extraction
                text = self.ocr_engine.image_to_string(img, lang='kor+eng')
                return text.strip(), 0.5  # Default confidence
                
        except Exception as e:
            self.logger.debug(f"OCR failed: {e}")
            return "", 0.0
    
    def _analyze_with_ai(self, img: Image.Image) -> Tuple[str, float]:
        """Analyze image with AI vision model"""
        if not self.vision_model:
            return "", 0.0
        
        try:
            import torch
            
            model = self.vision_model['model']
            preprocess = self.vision_model['preprocess']
            device = self.vision_model['device']
            
            # Preprocess image
            image_tensor = preprocess(img).unsqueeze(0).to(device)
            
            # Define descriptive text prompts
            text_prompts = [
                "a photo of",
                "a picture showing",
                "an image containing",
                "a document with",
                "a screenshot of",
                "a diagram of",
                "text and numbers",
                "people and faces",
                "objects and items",
                "nature and landscape"
            ]
            
            with torch.no_grad():
                # Encode image
                image_features = model.encode_image(image_tensor)
                
                # Encode text prompts
                text_tokens = torch.cat([torch.tensor(model.encode(prompt)).unsqueeze(0) for prompt in text_prompts]).to(device)
                text_features = model.encode_text(text_tokens)
                
                # Calculate similarities
                similarities = torch.cosine_similarity(image_features, text_features)
                
                # Get best match
                best_idx = similarities.argmax().item()
                best_confidence = similarities[best_idx].item()
                
                description = text_prompts[best_idx]
                
                return description, best_confidence
                
        except Exception as e:
            self.logger.debug(f"AI vision analysis failed: {e}")
            return "", 0.0
    
    def _generate_thumbnail(self, file_path: Path, img: Image.Image) -> Optional[str]:
        """Generate thumbnail for image"""
        try:
            # Create thumbnail cache directory
            thumb_dir = self.cache_dir / "thumbnails"
            thumb_dir.mkdir(exist_ok=True)
            
            # Generate thumbnail filename
            file_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:12]
            thumb_name = f"{file_hash}_{file_path.stem}.jpg"
            thumb_path = thumb_dir / thumb_name
            
            # Generate thumbnail if not exists
            if not thumb_path.exists():
                thumb_img = img.copy()
                thumb_img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                
                # Convert to RGB if needed
                if thumb_img.mode != 'RGB':
                    thumb_img = thumb_img.convert('RGB')
                
                thumb_img.save(thumb_path, "JPEG", quality=85)
            
            return str(thumb_path)
            
        except Exception as e:
            self.logger.debug(f"Thumbnail generation failed: {e}")
            return None
    
    def _exif_to_text(self, exif_data: Dict[str, Any]) -> str:
        """Convert EXIF data to searchable text"""
        if not exif_data:
            return ""
        
        # Important EXIF fields to include in text
        text_fields = []
        
        # Camera information
        if 'Make' in exif_data:
            text_fields.append(f"Camera: {exif_data['Make']}")
        if 'Model' in exif_data:
            text_fields.append(f"Model: {exif_data['Model']}")
        
        # Date information
        if 'DateTime' in exif_data:
            text_fields.append(f"Date: {exif_data['DateTime']}")
        
        # GPS information
        if 'GPSInfo' in exif_data:
            text_fields.append("GPS location available")
        
        # Image settings
        if 'Software' in exif_data:
            text_fields.append(f"Software: {exif_data['Software']}")
        
        return " | ".join(text_fields)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get processor capabilities"""
        return {
            "ocr_available": self.ocr_engine is not None,
            "ai_vision_available": self.vision_model is not None,
            "thumbnail_generation": True,
            "exif_extraction": True,
            "supported_formats": self.supported_extensions,
            "max_file_size_mb": self.max_image_size // (1024 * 1024),
            "max_ocr_dimensions": self.max_ocr_dimensions
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processor statistics"""
        return {
            "processor_type": "image",
            "supported_extensions": len(self.supported_extensions),
            "extension_list": self.supported_extensions,
            "features_enabled": {
                "ocr": self.enable_ocr and self.ocr_engine is not None,
                "ai_vision": self.enable_ai_vision and self.vision_model is not None,
                "exif_extraction": True,
                "thumbnail_generation": True
            },
            "capabilities": self.get_capabilities()
        }
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions"""
        return self.supported_extensions


def test_image_processor():
    """Test image processor functionality"""
    processor = ImageProcessor(enable_ocr=True, enable_ai_vision=False)
    
    print("🖼️ Image Processor Test")
    print("=" * 40)
    
    # Display capabilities
    caps = processor.get_capabilities()
    print("🔧 Capabilities:")
    for key, value in caps.items():
        print(f"   {key}: {value}")
    
    # Test with sample image files
    test_files = [
        "/watch_directories/Desktop/test.jpg",
        "/watch_directories/Desktop/test.png", 
        "/watch_directories/Pictures/sample.jpeg",
        "/Users/hyoseop1231/Desktop/screenshot.png"
    ]
    
    print("\n🔍 Testing image processing:")
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n📸 Processing: {test_file}")
            
            text, success, metadata = processor.extract_content(test_file)
            
            if success:
                print(f"   ✅ Processing successful")
                print(f"   📝 Text extracted: {len(text)} characters")
                print(f"   📏 Dimensions: {metadata.get('dimensions', 'unknown')}")
                print(f"   🎨 Format: {metadata.get('image_format', 'unknown')}")
                
                if text.strip():
                    preview = text[:200] + "..." if len(text) > 200 else text
                    print(f"   📄 Content preview: {repr(preview)}")
                
                # Show processing results
                proc_results = metadata.get('processing_results', {})
                if proc_results.get('ocr_enabled'):
                    print(f"   🔍 OCR confidence: {proc_results.get('ocr_confidence', 0):.2f}")
                
            else:
                print(f"   ❌ Processing failed: {metadata.get('error', 'Unknown error')}")
        else:
            print(f"\n❌ File not found: {test_file}")


if __name__ == "__main__":
    test_image_processor()