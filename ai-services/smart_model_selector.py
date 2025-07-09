#!/usr/bin/env python3
"""
Smart Model Selector for File Analysis
Chooses appropriate LLM based on file type, size, and content complexity
"""
import os
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SmartModelSelector:
    def __init__(self):
        # Available models
        self.models = {
            "text_light": "llama3.2:3b",        # Fast for simple text analysis
            "text_large": "qwen3:30b-a3b",      # Complex text analysis
            "vision": "llava:13b",              # Image analysis
            "embedding": "nomic-embed-text",    # Semantic embeddings
            "gemma": "gemma3:27b-it-qat"        # Alternative large model
        }
        
        # File size thresholds (bytes)
        self.size_thresholds = {
            "small": 1024 * 100,      # 100KB
            "medium": 1024 * 1024,    # 1MB  
            "large": 1024 * 1024 * 10 # 10MB
        }
        
        # File type categories
        self.file_categories = {
            "text": [".txt", ".md", ".log", ".csv", ".json", ".xml", ".yml", ".yaml"],
            "document": [".pdf", ".doc", ".docx", ".rtf", ".odt"],
            "code": [".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".css", ".html", ".php", ".rb", ".go", ".rs"],
            "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".tiff"],
            "video": [".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mkv"],
            "audio": [".mp3", ".wav", ".flac", ".m4a", ".ogg", ".wma"],
            "archive": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
            "data": [".db", ".sqlite", ".sql", ".xlsx", ".xls", ".ppt", ".pptx"]
        }
        
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive file information"""
        try:
            path = Path(file_path)
            if not path.exists():
                return None
                
            stat = path.stat()
            mime_type, _ = mimetypes.guess_type(file_path)
            
            return {
                "path": file_path,
                "name": path.name,
                "extension": path.suffix.lower(),
                "size": stat.st_size,
                "mime_type": mime_type,
                "is_text": mime_type and mime_type.startswith("text/") if mime_type else False,
                "is_binary": self._is_binary(file_path),
                "category": self._get_file_category(path.suffix.lower())
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return None
    
    def _is_binary(self, file_path: str) -> bool:
        """Check if file is binary"""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\x00' in chunk
        except:
            return True
    
    def _get_file_category(self, extension: str) -> str:
        """Get file category based on extension"""
        for category, extensions in self.file_categories.items():
            if extension in extensions:
                return category
        return "other"
    
    def _get_size_category(self, size: int) -> str:
        """Get file size category"""
        if size < self.size_thresholds["small"]:
            return "small"
        elif size < self.size_thresholds["medium"]:
            return "medium"
        elif size < self.size_thresholds["large"]:
            return "large"
        else:
            return "huge"
    
    def select_model_for_file(self, file_path: str, task_type: str = "analyze") -> Dict[str, Any]:
        """Select appropriate model for file analysis"""
        file_info = self.get_file_info(file_path)
        if not file_info:
            return {"model": self.models["text_light"], "strategy": "fallback"}
        
        category = file_info["category"]
        size_category = self._get_size_category(file_info["size"])
        
        # Image files -> Vision model
        if category == "image":
            return {
                "model": self.models["vision"],
                "strategy": "vision_analysis",
                "embedding_model": self.models["embedding"],
                "use_embedding": True
            }
        
        # Code files -> Specialized analysis
        elif category == "code":
            if size_category in ["small", "medium"]:
                return {
                    "model": self.models["text_large"],  # Better for code understanding
                    "strategy": "code_analysis",
                    "embedding_model": self.models["embedding"],
                    "use_embedding": True
                }
            else:
                return {
                    "model": self.models["text_light"],  # Large files need speed
                    "strategy": "code_summary",
                    "embedding_model": self.models["embedding"],
                    "use_embedding": True
                }
        
        # Documents -> Content-based selection
        elif category == "document":
            if size_category == "small":
                return {
                    "model": self.models["text_large"],  # Detailed analysis for small docs
                    "strategy": "document_analysis",
                    "embedding_model": self.models["embedding"],
                    "use_embedding": True
                }
            else:
                return {
                    "model": self.models["text_light"],  # Fast processing for large docs
                    "strategy": "document_summary",
                    "embedding_model": self.models["embedding"],
                    "use_embedding": True
                }
        
        # Text files -> Size-based selection
        elif category == "text":
            if size_category == "small":
                return {
                    "model": self.models["text_large"],  # Thorough analysis
                    "strategy": "text_analysis",
                    "embedding_model": self.models["embedding"],
                    "use_embedding": True
                }
            else:
                return {
                    "model": self.models["text_light"],  # Fast processing
                    "strategy": "text_summary",
                    "embedding_model": self.models["embedding"],
                    "use_embedding": True
                }
        
        # Binary/Data files -> Metadata only
        elif category in ["archive", "data", "video", "audio"]:
            return {
                "model": self.models["text_light"],  # Minimal processing
                "strategy": "metadata_only",
                "embedding_model": self.models["embedding"],
                "use_embedding": False  # No content to embed
            }
        
        # Default fallback
        else:
            return {
                "model": self.models["text_light"],
                "strategy": "basic_analysis",
                "embedding_model": self.models["embedding"],
                "use_embedding": file_info["size"] < self.size_thresholds["medium"]
            }
    
    def select_embedding_strategy(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Select embedding strategy based on file characteristics"""
        category = file_info["category"]
        size = file_info["size"]
        
        if category == "image":
            return {
                "strategy": "image_description",
                "chunk_size": None,
                "model": self.models["embedding"]
            }
        
        elif category in ["text", "document", "code"]:
            if size < self.size_thresholds["small"]:
                return {
                    "strategy": "full_content",
                    "chunk_size": None,
                    "model": self.models["embedding"]
                }
            elif size < self.size_thresholds["medium"]:
                return {
                    "strategy": "chunked",
                    "chunk_size": 1000,
                    "model": self.models["embedding"]
                }
            else:
                return {
                    "strategy": "summary_only",
                    "chunk_size": 500,
                    "model": self.models["embedding"]
                }
        
        else:
            return {
                "strategy": "metadata_only",
                "chunk_size": None,
                "model": self.models["embedding"]
            }
    
    def get_processing_plan(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive processing plan for a file"""
        file_info = self.get_file_info(file_path)
        if not file_info:
            return None
        
        model_selection = self.select_model_for_file(file_path)
        embedding_strategy = self.select_embedding_strategy(file_info)
        
        return {
            "file_info": file_info,
            "model_selection": model_selection,
            "embedding_strategy": embedding_strategy,
            "processing_priority": self._get_processing_priority(file_info),
            "estimated_time": self._estimate_processing_time(file_info, model_selection)
        }
    
    def _get_processing_priority(self, file_info: Dict[str, Any]) -> str:
        """Get processing priority based on file characteristics"""
        category = file_info["category"]
        size = file_info["size"]
        
        if category in ["text", "document", "code"] and size < self.size_thresholds["medium"]:
            return "high"
        elif category == "image":
            return "medium"
        else:
            return "low"
    
    def _estimate_processing_time(self, file_info: Dict[str, Any], model_selection: Dict[str, Any]) -> str:
        """Estimate processing time"""
        category = file_info["category"]
        size = file_info["size"]
        model = model_selection["model"]
        
        if model == self.models["text_large"]:
            base_time = 5  # seconds
        elif model == self.models["vision"]:
            base_time = 10
        else:
            base_time = 2
        
        if size > self.size_thresholds["large"]:
            base_time *= 3
        elif size > self.size_thresholds["medium"]:
            base_time *= 2
        
        return f"~{base_time}s"
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all models"""
        return {
            "available_models": self.models,
            "file_categories": list(self.file_categories.keys()),
            "size_thresholds": self.size_thresholds,
            "recommendations": {
                "small_text": self.models["text_large"],
                "large_text": self.models["text_light"],
                "code": self.models["text_large"],
                "images": self.models["vision"],
                "embeddings": self.models["embedding"]
            }
        }

# Example usage and testing
if __name__ == "__main__":
    selector = SmartModelSelector()
    
    # Test file
    test_file = "/tmp/test.py"
    plan = selector.get_processing_plan(test_file)
    
    if plan:
        print("Processing Plan:")
        print(f"  File: {plan['file_info']['name']}")
        print(f"  Category: {plan['file_info']['category']}")
        print(f"  Size: {plan['file_info']['size']} bytes")
        print(f"  Model: {plan['model_selection']['model']}")
        print(f"  Strategy: {plan['model_selection']['strategy']}")
        print(f"  Embedding: {plan['embedding_strategy']['strategy']}")
        print(f"  Priority: {plan['processing_priority']}")
        print(f"  Est. Time: {plan['estimated_time']}")
    else:
        print("Could not create processing plan")