#!/usr/bin/env python3
"""
LLM-based File Organizer using Ollama
Combines MAFM multi-agent search with Local-File-Organizer auto-categorization
"""
import os
import json
import shutil
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import aiohttp
import logging
from datetime import datetime
import mimetypes
from smart_model_selector import SmartModelSelector

logger = logging.getLogger(__name__)

class LLMOrganizer:
    def __init__(self, ollama_url: str = None):
        # Use environment variable or default to host's Ollama
        if ollama_url is None:
            ollama_url = os.environ.get("OLLAMA_API_URL", "http://host.docker.internal:11434/api/generate")
        # Ensure we have the base URL without /api/generate for other calls
        if "/api/generate" in ollama_url:
            self.ollama_base_url = ollama_url.replace("/api/generate", "")
        else:
            self.ollama_base_url = ollama_url
        self.ollama_url = ollama_url
        self.text_model = "llama3.2:3b"  # For text analysis (lightweight & fast)
        self.vision_model = "llava:13b"   # For image analysis
        self.large_model = "qwen3:30b-a3b"  # For complex analysis when needed
        self.embedding_model = "nomic-embed-text"  # For semantic embeddings
        
        # Smart model selector
        self.model_selector = SmartModelSelector()
        
        # File categories based on Local-File-Organizer
        self.categories = self._get_categories()
        
    def _choose_model(self, task_complexity: str = "simple") -> str:
        """Choose appropriate model based on task complexity"""
        if task_complexity == "complex":
            return self.large_model  # qwen3:30b-a3b for complex analysis
        else:
            return self.text_model   # llama3.2:3b for simple/fast analysis
    
    def _get_categories(self):
        """Get file categories"""
        return {
            "Documents": {
                "Financial": ["invoice", "budget", "expense", "tax", "payment"],
                "Meetings_and_Notes": ["meeting", "notes", "agenda", "minutes"],
                "Reports": ["report", "analysis", "summary", "research"],
                "Personal": ["resume", "cv", "letter", "personal"]
            },
            "Media": {
                "Photos": ["photo", "image", "picture", "selfie"],
                "Videos": ["video", "movie", "clip", "recording"],
                "Audio": ["audio", "music", "podcast", "recording"]
            },
            "Development": {
                "Code": ["code", "script", "program", "source"],
                "Documentation": ["readme", "docs", "api", "guide"],
                "Projects": ["project", "repository", "package"]
            },
            "Data": {
                "Spreadsheets": ["excel", "spreadsheet", "data", "csv"],
                "Databases": ["database", "sql", "db", "data"],
                "Archives": ["backup", "archive", "compressed"]
            }
        }
        
    async def analyze_file_with_llm(self, file_path: str) -> Dict[str, Any]:
        """Analyze file content using Ollama LLM"""
        try:
            file_type = self._get_file_type(file_path)
            
            if file_type == "image":
                return await self._analyze_image(file_path)
            elif file_type == "text":
                return await self._analyze_text(file_path)
            else:
                return await self._analyze_metadata(file_path)
                
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return self._fallback_analysis(file_path)
            
    async def _analyze_text(self, file_path: str) -> Dict[str, Any]:
        """Analyze text file content"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(2000)  # Read first 2000 chars
                
            prompt = f"""Analyze this file content and provide:
1. A descriptive filename (without extension)
2. The most appropriate category from: {list(self.categories.keys())}
3. A subcategory if applicable
4. Keywords for search

Content: {content[:1000]}...

Respond in JSON format:
{{"filename": "...", "category": "...", "subcategory": "...", "keywords": ["..."], "description": "..."}}"""

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.ollama_url,
                    json={
                        "model": self.text_model,
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
            
    async def _analyze_image(self, file_path: str) -> Dict[str, Any]:
        """Analyze image file using vision model"""
        try:
            import base64
            
            with open(file_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
                
            prompt = """Describe this image and suggest:
1. A descriptive filename
2. Category (Photos, Screenshots, Documents, etc.)
3. Keywords for search

Respond in JSON format."""

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.ollama_url,
                    json={
                        "model": self.vision_model,
                        "prompt": prompt,
                        "images": [image_data],
                        "stream": False,
                        "format": "json"
                    }
                ) as resp:
                    result = await resp.json()
                    return json.loads(result.get("response", "{}"))
                    
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            return self._fallback_analysis(file_path)
            
    def _get_file_type(self, file_path: str) -> str:
        """Determine file type category"""
        mime_type, _ = mimetypes.guess_type(file_path)
        
        if mime_type:
            if mime_type.startswith('image/'):
                return 'image'
            elif mime_type.startswith('text/') or mime_type in ['application/pdf', 'application/msword']:
                return 'text'
            elif mime_type.startswith('video/'):
                return 'video'
            elif mime_type.startswith('audio/'):
                return 'audio'
                
        # Fallback to extension
        ext = Path(file_path).suffix.lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            return 'image'
        elif ext in ['.txt', '.md', '.pdf', '.doc', '.docx']:
            return 'text'
        elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
            return 'video'
        elif ext in ['.mp3', '.wav', '.flac']:
            return 'audio'
            
        return 'other'
        
    def _fallback_analysis(self, file_path: str) -> Dict[str, Any]:
        """Fallback analysis based on filename and extension"""
        path = Path(file_path)
        name = path.stem
        ext = path.suffix
        
        # Simple keyword extraction from filename
        keywords = [w.lower() for w in name.replace('_', ' ').replace('-', ' ').split()]
        
        # Guess category from extension
        category = "Documents"
        if ext in ['.jpg', '.png', '.gif']:
            category = "Media"
        elif ext in ['.py', '.js', '.java']:
            category = "Development"
            
        return {
            "filename": name,
            "category": category,
            "keywords": keywords,
            "description": f"File: {name}{ext}"
        }
        
    async def organize_directory(self, source_dir: str, target_dir: str, 
                               method: str = "content", dry_run: bool = False) -> Dict[str, Any]:
        """Organize files in directory using LLM analysis"""
        source_path = Path(source_dir)
        target_path = Path(target_dir) if target_dir else source_path / "Organized"
        
        if not source_path.exists():
            raise ValueError(f"Source directory {source_dir} does not exist")
            
        results = {
            "analyzed": 0,
            "organized": 0,
            "failed": 0,
            "operations": []
        }
        
        # Collect all files
        files = []
        for root, _, filenames in os.walk(source_path):
            for filename in filenames:
                if not filename.startswith('.'):
                    files.append(Path(root) / filename)
                    
        logger.info(f"Found {len(files)} files to organize")
        
        # Analyze and organize files
        for file_path in files:
            try:
                # Analyze file with LLM
                analysis = await self.analyze_file_with_llm(str(file_path))
                results["analyzed"] += 1
                
                # Determine target location
                category = analysis.get("category", "Uncategorized")
                subcategory = analysis.get("subcategory", "")
                new_filename = self._sanitize_filename(
                    analysis.get("filename", file_path.stem)
                ) + file_path.suffix
                
                # Build target path
                if subcategory:
                    target_file_path = target_path / category / subcategory / new_filename
                else:
                    target_file_path = target_path / category / new_filename
                    
                operation = {
                    "source": str(file_path),
                    "target": str(target_file_path),
                    "analysis": analysis
                }
                
                if not dry_run:
                    # Create directory and move/copy file
                    target_file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if method == "move":
                        shutil.move(str(file_path), str(target_file_path))
                    else:
                        shutil.copy2(str(file_path), str(target_file_path))
                        
                    results["organized"] += 1
                    
                results["operations"].append(operation)
                
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                results["failed"] += 1
                
        return results
        
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem"""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
            
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
            
        return filename.strip()
        
    async def smart_search(self, query: str, directories: List[str]) -> List[Dict[str, Any]]:
        """Smart search using LLM to understand query intent"""
        logger.info(f"Smart search initiated for query: {query}")
        
        # First try direct fallback for immediate results
        try:
            keywords = self._extract_keywords_fallback(query)
            logger.info(f"Extracted keywords: {keywords}")
            
            # Try simple search first
            simple_results = await self._perform_smart_search({"keywords": keywords}, directories)
            if simple_results:
                logger.info(f"Direct search returned {len(simple_results)} results")
                return simple_results
        except Exception as e:
            logger.error(f"Direct search error: {e}")
        
        # Then try LLM analysis
        prompt = f"""Analyze this search query and extract:
1. File types to search for (e.g., [".pdf", ".docx", ".txt"])
2. Keywords to match (important words from the query)
3. Likely categories (document, image, video, audio, code, archive, other)
4. Date range if mentioned

Query: {query}

Respond ONLY with valid JSON like this example:
{{
    "file_types": [".pdf", ".docx"],
    "keywords": ["project", "report"],
    "categories": ["document"],
    "date_range": null
}}"""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.ollama_url,
                    json={
                        "model": self.text_model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        search_params = json.loads(result.get("response", "{}"))
                        logger.info(f"LLM search params: {search_params}")
                        
                        # Use search parameters to find files
                        llm_results = await self._perform_smart_search(search_params, directories)
                        if llm_results:
                            return llm_results
                    else:
                        logger.warning(f"LLM request failed with status {resp.status}")
                        
        except Exception as e:
            logger.error(f"LLM search error: {e}")
            
        # Final fallback - return simple results or empty
        try:
            keywords = self._extract_keywords_fallback(query)
            return await self._perform_smart_search({"keywords": keywords}, directories)
        except Exception as e2:
            logger.error(f"Final fallback search error: {e2}")
            return []
            
    async def _perform_smart_search(self, params: Dict[str, Any], 
                                  directories: List[str]) -> List[Dict[str, Any]]:
        """Perform search based on LLM-analyzed parameters"""
        logger.info(f"Performing smart search with params: {params}")
        
        # Import db_manager locally to avoid circular import
        from db_manager import DatabaseManager
        
        try:
            db_manager = DatabaseManager(os.environ.get("DB_PATH", "/data/db/file-index.db"))
            
            # Extract search parameters from LLM analysis
            keywords = params.get("keywords", [])
            file_types = params.get("file_types", [])
            categories = params.get("categories", [])
            
            logger.info(f"Search parameters - Keywords: {keywords}, Types: {file_types}, Categories: {categories}")
            
            results = []
            
            # Try multiple search strategies
            if keywords:
                # Strategy 1: Search with all keywords combined
                combined_query = " ".join(keywords)
                logger.info(f"Searching with combined query: {combined_query}")
                combined_results = db_manager.search_files(combined_query, directories, limit=30)
                results.extend(combined_results)
                
                # Strategy 2: Search with each keyword separately
                for keyword in keywords:
                    logger.info(f"Searching with individual keyword: {keyword}")
                    keyword_results = db_manager.search_files(keyword, directories, limit=20)
                    results.extend(keyword_results)
                    
            # If we have file types, also search by extension
            if file_types:
                for file_type in file_types:
                    ext_query = file_type.replace(".", "")
                    logger.info(f"Searching by extension: {ext_query}")
                    ext_results = db_manager.search_files(ext_query, directories, limit=20)
                    results.extend(ext_results)
                    
            # Remove duplicates based on path
            seen_paths = set()
            unique_results = []
            for result in results:
                if result and result.get('path') and result['path'] not in seen_paths:
                    seen_paths.add(result['path'])
                    unique_results.append(result)
                    
            # Apply filters
            filtered_results = unique_results
            
            # Filter by file types if specified
            if file_types:
                temp_results = []
                for result in filtered_results:
                    ext = result.get("metadata", {}).get("extension", "").lower()
                    if any(ft.lower() in ext for ft in file_types):
                        temp_results.append(result)
                filtered_results = temp_results
                
            # Filter by categories if specified
            if categories:
                temp_results = []
                for result in filtered_results:
                    cat = result.get("metadata", {}).get("category", "").lower()
                    if any(c.lower() in cat for c in categories):
                        temp_results.append(result)
                filtered_results = temp_results
                
            logger.info(f"Search completed: {len(filtered_results)} results found")
            return filtered_results[:50]  # Limit to top 50 results
            
        except Exception as e:
            logger.error(f"Smart search error: {e}")
            return []
    
    def _extract_keywords_fallback(self, query: str) -> List[str]:
        """Extract keywords from query when LLM is unavailable"""
        import re
        
        # Remove common stop words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            '그', '이', '저', '것', '는', '은', '이', '가', '을', '를', '에', '서', '로', '와', '과',
            '파일', '문서', '찾아', '검색', '보여', '주세요', '해주세요', '있는', '없는'
        }
        
        # Clean and split query
        query = query.lower()
        query = re.sub(r'[^\w\s]', ' ', query)  # Remove punctuation
        words = query.split()
        
        # Filter out stop words and short words
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # If no keywords found, return original words
        if not keywords:
            keywords = [word for word in words if len(word) > 1]
            
        return keywords[:5]  # Limit to top 5 keywords