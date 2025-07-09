#!/usr/bin/env python3
"""
Enhanced LLM Organizer with Smart Model Selection and Embedding Integration
"""
import os
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import aiohttp
from smart_model_selector import SmartModelSelector

logger = logging.getLogger(__name__)

class EnhancedLLMOrganizer:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model_selector = SmartModelSelector()
        
    async def analyze_file_with_smart_selection(self, file_path: str) -> Dict[str, Any]:
        """Analyze file using smart model selection"""
        try:
            # Get processing plan
            plan = self.model_selector.get_processing_plan(file_path)
            if not plan:
                return self._fallback_analysis(file_path)
            
            file_info = plan["file_info"]
            model_selection = plan["model_selection"]
            embedding_strategy = plan["embedding_strategy"]
            
            logger.info(f"Processing {file_info['name']} with {model_selection['model']} ({model_selection['strategy']})")
            
            # Choose analysis method based on strategy
            if model_selection["strategy"] == "vision_analysis":
                result = await self._analyze_with_vision(file_path, model_selection["model"])
            elif model_selection["strategy"] == "metadata_only":
                result = await self._analyze_metadata_only(file_path)
            else:
                result = await self._analyze_with_text_model(file_path, model_selection)
            
            # Add embedding if needed
            if model_selection.get("use_embedding", False):
                embedding_result = await self._create_embedding(file_path, embedding_strategy)
                result["embedding"] = embedding_result
            
            # Add processing metadata
            result["processing_info"] = {
                "model_used": model_selection["model"],
                "strategy": model_selection["strategy"],
                "file_category": file_info["category"],
                "file_size": file_info["size"],
                "processing_time": plan["estimated_time"]
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced analysis error for {file_path}: {e}")
            return self._fallback_analysis(file_path)
    
    async def _analyze_with_vision(self, file_path: str, model: str) -> Dict[str, Any]:
        """Analyze image file with vision model"""
        try:
            import base64
            
            with open(file_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
            
            prompt = """Analyze this image and provide:
1. Description of what you see
2. Suggested category (Photos, Screenshots, Documents, Artwork, etc.)
3. Keywords for search
4. Recommended folder organization

Respond in JSON format:
{"filename": "...", "category": "...", "subcategory": "...", "keywords": ["..."], "description": "..."}"""
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                        "images": [image_data]
                    }
                ) as resp:
                    result = await resp.json()
                    return json.loads(result.get("response", "{}"))
                    
        except Exception as e:
            logger.error(f"Vision analysis error: {e}")
            return self._fallback_analysis(file_path)
    
    async def _analyze_with_text_model(self, file_path: str, model_selection: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze text file with appropriate text model"""
        try:
            # Read file content based on strategy
            content = await self._read_file_content(file_path, model_selection["strategy"])
            
            if not content:
                return self._fallback_analysis(file_path)
            
            # Create analysis prompt based on file type
            file_info = self.model_selector.get_file_info(file_path)
            prompt = self._create_analysis_prompt(content, file_info, model_selection["strategy"])
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model_selection["model"],
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    }
                ) as resp:
                    result = await resp.json()
                    return json.loads(result.get("response", "{}"))
                    
        except Exception as e:
            logger.error(f"Text analysis error: {e}")
            return self._fallback_analysis(file_path)
    
    async def _analyze_metadata_only(self, file_path: str) -> Dict[str, Any]:
        """Analyze file metadata only (for binary files)"""
        try:
            file_info = self.model_selector.get_file_info(file_path)
            path = Path(file_path)
            
            return {
                "filename": path.name,
                "category": file_info["category"].title(),
                "subcategory": file_info["extension"].upper().replace(".", ""),
                "keywords": [file_info["category"], file_info["extension"].replace(".", "")],
                "description": f"{file_info['category']} file ({file_info['extension']}), {file_info['size']} bytes"
            }
            
        except Exception as e:
            logger.error(f"Metadata analysis error: {e}")
            return self._fallback_analysis(file_path)
    
    async def _read_file_content(self, file_path: str, strategy: str) -> str:
        """Read file content based on strategy"""
        try:
            if strategy == "text_summary" or strategy == "document_summary":
                # Read first 2000 chars for large files
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read(2000)
            elif strategy == "code_summary":
                # Read first 1000 chars for code files
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read(1000)
            else:
                # Read full content for detailed analysis
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read(5000)  # Limit to prevent token overflow
                    
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return ""
    
    def _create_analysis_prompt(self, content: str, file_info: Dict[str, Any], strategy: str) -> str:
        """Create appropriate analysis prompt"""
        category = file_info["category"]
        
        if category == "code":
            return f"""Analyze this code file and provide:
1. Programming language
2. Main functionality
3. Suggested organization (by language, project, etc.)
4. Keywords for search

Content preview:
{content[:1000]}

Respond in JSON format:
{{"filename": "...", "category": "Code", "subcategory": "...", "keywords": ["..."], "description": "..."}}"""
        
        elif category == "document":
            return f"""Analyze this document and provide:
1. Document type and purpose
2. Main topics covered
3. Suggested organization
4. Keywords for search

Content preview:
{content[:1000]}

Respond in JSON format:
{{"filename": "...", "category": "Documents", "subcategory": "...", "keywords": ["..."], "description": "..."}}"""
        
        else:
            return f"""Analyze this file and provide:
1. Content type and purpose
2. Main topics or functionality
3. Suggested organization
4. Keywords for search

Content preview:
{content[:1000]}

Respond in JSON format:
{{"filename": "...", "category": "...", "subcategory": "...", "keywords": ["..."], "description": "..."}}"""
    
    async def _create_embedding(self, file_path: str, embedding_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Create semantic embedding for file"""
        try:
            strategy = embedding_strategy["strategy"]
            
            if strategy == "metadata_only":
                # Only embed filename and basic metadata
                file_info = self.model_selector.get_file_info(file_path)
                embed_text = f"{file_info['name']} {file_info['category']} {file_info['extension']}"
            elif strategy == "image_description":
                # For images, embed the description from vision analysis
                embed_text = "Image file requiring vision analysis"
            else:
                # For text files, embed content
                content = await self._read_file_content(file_path, strategy)
                embed_text = content[:500]  # Limit for embedding
            
            # Create embedding
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={
                        "model": embedding_strategy["model"],
                        "prompt": embed_text
                    }
                ) as resp:
                    result = await resp.json()
                    return {
                        "embedding": result.get("embedding", []),
                        "text": embed_text[:200],  # Store sample for reference
                        "strategy": strategy
                    }
                    
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return {"embedding": [], "text": "", "strategy": "failed"}
    
    def _fallback_analysis(self, file_path: str) -> Dict[str, Any]:
        """Fallback analysis when other methods fail"""
        path = Path(file_path)
        return {
            "filename": path.name,
            "category": "Other",
            "subcategory": "Unknown",
            "keywords": [path.suffix.replace(".", "")],
            "description": f"File: {path.name}",
            "processing_info": {
                "model_used": "fallback",
                "strategy": "metadata_only",
                "file_category": "unknown",
                "file_size": 0,
                "processing_time": "instant"
            }
        }
    
    async def batch_analyze_files(self, file_paths: List[str], max_concurrent: int = 5) -> List[Dict[str, Any]]:
        """Analyze multiple files concurrently with smart prioritization"""
        # Get processing plans for all files
        plans = []
        for file_path in file_paths:
            plan = self.model_selector.get_processing_plan(file_path)
            if plan:
                plans.append((file_path, plan))
        
        # Sort by priority (high priority first)
        plans.sort(key=lambda x: {"high": 3, "medium": 2, "low": 1}[x[1]["processing_priority"]], reverse=True)
        
        # Process in batches
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_file(file_path: str) -> Dict[str, Any]:
            async with semaphore:
                return await self.analyze_file_with_smart_selection(file_path)
        
        # Create tasks for all files
        tasks = [process_file(file_path) for file_path, _ in plans]
        
        # Execute with progress logging
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            results.append(result)
            if i % 10 == 0:
                logger.info(f"Processed {i+1}/{len(tasks)} files")
        
        return results
    
    def get_model_recommendations(self, file_paths: List[str]) -> Dict[str, Any]:
        """Get model usage recommendations for a list of files"""
        recommendations = {}
        model_usage = {}
        
        for file_path in file_paths:
            plan = self.model_selector.get_processing_plan(file_path)
            if plan:
                model = plan["model_selection"]["model"]
                category = plan["file_info"]["category"]
                
                if model not in model_usage:
                    model_usage[model] = {"count": 0, "categories": set()}
                
                model_usage[model]["count"] += 1
                model_usage[model]["categories"].add(category)
        
        # Convert sets to lists for JSON serialization
        for model in model_usage:
            model_usage[model]["categories"] = list(model_usage[model]["categories"])
        
        return {
            "total_files": len(file_paths),
            "model_usage": model_usage,
            "recommendations": {
                "primary_model": max(model_usage.keys(), key=lambda x: model_usage[x]["count"]) if model_usage else None,
                "suggested_concurrent": min(5, len(file_paths) // 10 + 1)
            }
        }

# Testing function
async def test_enhanced_organizer():
    organizer = EnhancedLLMOrganizer()
    
    # Test with a sample file
    test_file = "/tmp/test_sample.txt"
    
    # Create test file
    with open(test_file, 'w') as f:
        f.write("This is a test document for analyzing the smart file manager system.")
    
    # Analyze
    result = await organizer.analyze_file_with_smart_selection(test_file)
    print("Analysis Result:")
    print(json.dumps(result, indent=2))
    
    # Clean up
    os.remove(test_file)

if __name__ == "__main__":
    asyncio.run(test_enhanced_organizer())