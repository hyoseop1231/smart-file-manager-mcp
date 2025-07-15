#!/usr/bin/env python3
"""
AI Vision Service for Smart File Manager v4.0
Advanced image analysis using computer vision models
"""

import os
import logging
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
from PIL import Image

# Conditional imports for AI models
try:
    import torch
    TORCH_AVAILABLE = True
    TorchTensor = torch.Tensor
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    # Type hint placeholder when torch is not available
    from typing import Any
    TorchTensor = Any

logger = logging.getLogger(__name__)


class AIVisionService:
    """
    AI-powered image analysis service
    """
    
    def __init__(self, 
                 cache_dir: str = "/tmp/multimedia_cache",
                 device: str = "auto"):
        
        self.logger = logging.getLogger(__name__)
        self.cache_dir = Path(cache_dir) / "ai_vision"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Device selection
        if not TORCH_AVAILABLE:
            self.device = "cpu"
            self.logger.warning("Torch not available, AI vision features disabled")
        elif device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        # Available models
        self.models = {}
        self.current_model = None
        
        # Initialize models only if torch is available
        if TORCH_AVAILABLE:
            self._init_clip_model()
            self._init_blip_model()
        else:
            self.logger.info("AI models skipped - torch not available")
        
        # Analysis categories
        self.image_categories = [
            "document", "screenshot", "photo", "artwork", "diagram", 
            "chart", "map", "text_image", "people", "nature", "object",
            "meme", "illustration", "technical_drawing", "user_interface"
        ]
        
        # Content detection prompts
        self.content_prompts = {
            "has_text": "text, words, letters, writing, document",
            "has_people": "person, people, face, human, portrait",
            "has_objects": "objects, items, things, tools, furniture",
            "is_screenshot": "screenshot, computer screen, software interface",
            "is_document": "document, paper, form, letter, invoice",
            "is_chart": "chart, graph, plot, diagram, visualization",
            "is_photo": "photograph, camera, real life, outdoor, indoor",
            "is_artwork": "art, painting, drawing, illustration, creative"
        }
    
    def _init_clip_model(self):
        """Initialize CLIP model for image-text understanding"""
        try:
            import clip
            
            # Load CLIP model
            model, preprocess = clip.load("ViT-B/32", device=self.device)
            
            self.models['clip'] = {
                'model': model,
                'preprocess': preprocess,
                'type': 'multimodal',
                'capabilities': ['image_classification', 'text_similarity', 'zero_shot']
            }
            
            self.current_model = 'clip'
            self.logger.info(f"✅ CLIP model loaded on {self.device}")
            
        except ImportError:
            self.logger.warning("⚠️ CLIP not available. Install with: pip install git+https://github.com/openai/CLIP.git")
        except Exception as e:
            self.logger.warning(f"⚠️ CLIP initialization failed: {e}")
    
    def _init_blip_model(self):
        """Initialize BLIP model for image captioning"""
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            
            # Load BLIP model (smaller version for efficiency)
            processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
            
            if self.device == "cuda":
                model = model.to(self.device)
            
            self.models['blip'] = {
                'model': model,
                'processor': processor,
                'type': 'captioning',
                'capabilities': ['image_captioning', 'description_generation']
            }
            
            self.logger.info(f"✅ BLIP model loaded on {self.device}")
            
        except ImportError:
            self.logger.warning("⚠️ BLIP not available. Install with: pip install transformers")
        except Exception as e:
            self.logger.warning(f"⚠️ BLIP initialization failed: {e}")
    
    def analyze_image(self, image_path: str) -> Tuple[str, float, Dict[str, Any]]:
        """
        Comprehensive image analysis
        
        Returns:
            tuple: (description, confidence, analysis_data)
        """
        if not TORCH_AVAILABLE:
            return "AI vision analysis not available (torch not installed)", 0.0, {
                "error": "torch_not_available",
                "fallback": "basic_analysis"
            }
        
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            
            # Check cache first
            cache_key = self._get_cache_key(image_path)
            cached_result = self._load_cached_analysis(cache_key)
            if cached_result:
                return cached_result
            
            # Perform analysis
            analysis_results = {}
            
            # CLIP-based analysis
            if 'clip' in self.models:
                clip_results = self._analyze_with_clip(image)
                analysis_results['clip'] = clip_results
            
            # BLIP-based captioning
            if 'blip' in self.models:
                blip_results = self._analyze_with_blip(image)
                analysis_results['blip'] = blip_results
            
            # Combine results
            description, confidence, metadata = self._combine_analysis_results(analysis_results)
            
            # Cache results
            self._cache_analysis(cache_key, description, confidence, metadata)
            
            return description, confidence, metadata
            
        except Exception as e:
            self.logger.error(f"Image analysis failed: {e}")
            return "", 0.0, {"error": str(e)}
    
    def _analyze_with_clip(self, image: Image.Image) -> Dict[str, Any]:
        """Analyze image using CLIP model"""
        if 'clip' not in self.models:
            return {}
        
        try:
            model = self.models['clip']['model']
            preprocess = self.models['clip']['preprocess']
            
            # Preprocess image
            image_tensor = preprocess(image).unsqueeze(0).to(self.device)
            
            results = {}
            
            # Category classification
            category_scores = self._classify_image_category(image_tensor, model)
            results['category'] = category_scores
            
            # Content detection
            content_detection = self._detect_image_content(image_tensor, model)
            results['content'] = content_detection
            
            # Generate descriptive text
            descriptive_text = self._generate_clip_description(image_tensor, model)
            results['description'] = descriptive_text
            
            return results
            
        except Exception as e:
            self.logger.debug(f"CLIP analysis failed: {e}")
            return {}
    
    def _classify_image_category(self, image_tensor: TorchTensor, model) -> Dict[str, float]:
        """Classify image into predefined categories"""
        import clip
        
        try:
            # Prepare category prompts
            category_texts = [f"a {category}" for category in self.image_categories]
            text_tokens = clip.tokenize(category_texts).to(self.device)
            
            with torch.no_grad():
                # Get features
                image_features = model.encode_image(image_tensor)
                text_features = model.encode_text(text_tokens)
                
                # Calculate similarities
                similarities = torch.cosine_similarity(image_features, text_features)
                
                # Convert to probabilities
                probabilities = torch.softmax(similarities * 100, dim=0)
                
                # Create results dictionary
                category_scores = {}
                for i, category in enumerate(self.image_categories):
                    category_scores[category] = float(probabilities[i])
                
                return category_scores
                
        except Exception as e:
            self.logger.debug(f"Category classification failed: {e}")
            return {}
    
    def _detect_image_content(self, image_tensor: TorchTensor, model) -> Dict[str, float]:
        """Detect specific content types in image"""
        import clip
        
        try:
            content_scores = {}
            
            for content_type, prompt in self.content_prompts.items():
                # Create positive and negative prompts
                positive_prompt = f"an image with {prompt}"
                negative_prompt = f"an image without {prompt}"
                
                text_tokens = clip.tokenize([positive_prompt, negative_prompt]).to(self.device)
                
                with torch.no_grad():
                    image_features = model.encode_image(image_tensor)
                    text_features = model.encode_text(text_tokens)
                    
                    similarities = torch.cosine_similarity(image_features, text_features)
                    
                    # Calculate confidence (positive vs negative)
                    positive_score = float(similarities[0])
                    negative_score = float(similarities[1])
                    
                    # Normalize to 0-1 probability
                    confidence = (positive_score - negative_score + 2) / 4  # Rough normalization
                    content_scores[content_type] = max(0, min(1, confidence))
            
            return content_scores
            
        except Exception as e:
            self.logger.debug(f"Content detection failed: {e}")
            return {}
    
    def _generate_clip_description(self, image_tensor: TorchTensor, model) -> Dict[str, Any]:
        """Generate descriptive text using CLIP"""
        import clip
        
        try:
            # Predefined descriptive prompts
            descriptive_prompts = [
                "a detailed photo of",
                "a screenshot showing",
                "a document containing",
                "an illustration of",
                "a diagram explaining",
                "a chart displaying",
                "artwork depicting",
                "a technical drawing of",
                "an interface showing",
                "text that says"
            ]
            
            text_tokens = clip.tokenize(descriptive_prompts).to(self.device)
            
            with torch.no_grad():
                image_features = model.encode_image(image_tensor)
                text_features = model.encode_text(text_tokens)
                
                similarities = torch.cosine_similarity(image_features, text_features)
                
                # Get best matches
                top_indices = torch.argsort(similarities, descending=True)[:3]
                
                descriptions = []
                for idx in top_indices:
                    prompt = descriptive_prompts[idx]
                    confidence = float(similarities[idx])
                    descriptions.append({
                        "text": prompt,
                        "confidence": confidence
                    })
                
                return {
                    "descriptions": descriptions,
                    "best_match": descriptions[0] if descriptions else None
                }
                
        except Exception as e:
            self.logger.debug(f"CLIP description generation failed: {e}")
            return {}
    
    def _analyze_with_blip(self, image: Image.Image) -> Dict[str, Any]:
        """Analyze image using BLIP model"""
        if 'blip' not in self.models:
            return {}
        
        try:
            model = self.models['blip']['model']
            processor = self.models['blip']['processor']
            
            # Process image
            inputs = processor(image, return_tensors="pt")
            if self.device == "cuda":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate caption
            with torch.no_grad():
                out = model.generate(**inputs, max_length=50, num_beams=5)
                caption = processor.decode(out[0], skip_special_tokens=True)
            
            # Generate conditional captions with prompts
            conditional_captions = {}
            prompts = [
                "a picture of",
                "this image shows", 
                "the content includes",
                "this appears to be"
            ]
            
            for prompt in prompts:
                try:
                    inputs = processor(image, prompt, return_tensors="pt")
                    if self.device == "cuda":
                        inputs = {k: v.to(self.device) for k, v in inputs.items()}
                    
                    with torch.no_grad():
                        out = model.generate(**inputs, max_length=50)
                        conditional_caption = processor.decode(out[0], skip_special_tokens=True)
                        conditional_captions[prompt] = conditional_caption
                except:
                    continue
            
            return {
                "caption": caption,
                "conditional_captions": conditional_captions,
                "model": "blip"
            }
            
        except Exception as e:
            self.logger.debug(f"BLIP analysis failed: {e}")
            return {}
    
    def _combine_analysis_results(self, analysis_results: Dict[str, Any]) -> Tuple[str, float, Dict[str, Any]]:
        """Combine results from different models"""
        combined_text = []
        max_confidence = 0.0
        metadata = {"analysis_results": analysis_results}
        
        # BLIP caption
        if 'blip' in analysis_results and 'caption' in analysis_results['blip']:
            caption = analysis_results['blip']['caption']
            combined_text.append(f"Image Caption: {caption}")
            max_confidence = max(max_confidence, 0.8)  # BLIP is generally reliable
        
        # CLIP category
        if 'clip' in analysis_results and 'category' in analysis_results['clip']:
            categories = analysis_results['clip']['category']
            top_category = max(categories.items(), key=lambda x: x[1])
            if top_category[1] > 0.3:  # Confidence threshold
                combined_text.append(f"Category: {top_category[0]}")
                max_confidence = max(max_confidence, top_category[1])
        
        # CLIP content detection
        if 'clip' in analysis_results and 'content' in analysis_results['clip']:
            content = analysis_results['clip']['content']
            detected_content = [k for k, v in content.items() if v > 0.6]
            if detected_content:
                combined_text.append(f"Contains: {', '.join(detected_content)}")
        
        # CLIP descriptions
        if 'clip' in analysis_results and 'description' in analysis_results['clip']:
            desc_data = analysis_results['clip']['description']
            if 'best_match' in desc_data and desc_data['best_match']:
                best_desc = desc_data['best_match']
                combined_text.append(f"Visual Description: {best_desc['text']}")
                max_confidence = max(max_confidence, best_desc['confidence'])
        
        final_text = " | ".join(combined_text)
        return final_text, max_confidence, metadata
    
    def _get_cache_key(self, image_path: str) -> str:
        """Generate cache key for image"""
        # Include file modification time in cache key
        stat = Path(image_path).stat()
        content = f"{image_path}_{stat.st_mtime}_{stat.st_size}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _load_cached_analysis(self, cache_key: str) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Load cached analysis results"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                return data['description'], data['confidence'], data['metadata']
        except:
            pass
        
        return None
    
    def _cache_analysis(self, cache_key: str, description: str, confidence: float, metadata: Dict[str, Any]):
        """Cache analysis results"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            cache_data = {
                'description': description,
                'confidence': confidence,
                'metadata': metadata,
                'timestamp': Path().stat().st_ctime if Path().exists() else 0
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except:
            pass  # Cache failure is not critical
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get service capabilities"""
        return {
            "available_models": list(self.models.keys()),
            "current_device": self.device,
            "supported_capabilities": [
                cap for model_info in self.models.values() 
                for cap in model_info.get('capabilities', [])
            ],
            "image_categories": self.image_categories,
            "content_detection": list(self.content_prompts.keys())
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        # Count cached analyses
        cache_count = len(list(self.cache_dir.glob("*.json"))) if self.cache_dir.exists() else 0
        
        return {
            "service_type": "ai_vision",
            "models_loaded": len(self.models),
            "model_details": {
                name: info.get('capabilities', []) 
                for name, info in self.models.items()
            },
            "device": self.device,
            "cache_entries": cache_count,
            "supported_categories": len(self.image_categories)
        }


def test_ai_vision_service():
    """Test AI vision service"""
    service = AIVisionService()
    
    print("🤖 AI Vision Service Test")
    print("=" * 40)
    
    # Display capabilities
    caps = service.get_capabilities()
    print("🔧 Capabilities:")
    for key, value in caps.items():
        if isinstance(value, list) and len(value) > 5:
            print(f"   {key}: {len(value)} items")
        else:
            print(f"   {key}: {value}")
    
    # Test with sample images
    test_files = [
        "/watch_directories/Desktop/screenshot.png",
        "/watch_directories/Pictures/photo.jpg",
        "/watch_directories/Desktop/document.png"
    ]
    
    print("\n🔍 Testing image analysis:")
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n🖼️ Analyzing: {test_file}")
            
            description, confidence, metadata = service.analyze_image(test_file)
            
            if description:
                print(f"   ✅ Analysis successful")
                print(f"   📝 Description: {description}")
                print(f"   🎯 Confidence: {confidence:.3f}")
                
                # Show model-specific results
                analysis = metadata.get('analysis_results', {})
                for model_name, results in analysis.items():
                    print(f"   🤖 {model_name.upper()} results:")
                    if isinstance(results, dict):
                        for key, value in list(results.items())[:3]:  # Show first 3 items
                            if isinstance(value, dict) and len(value) > 3:
                                print(f"      {key}: {len(value)} items")
                            else:
                                print(f"      {key}: {str(value)[:100]}...")
            else:
                print(f"   ❌ Analysis failed: {metadata.get('error', 'Unknown error')}")
        else:
            print(f"\n❌ File not found: {test_file}")


if __name__ == "__main__":
    test_ai_vision_service()