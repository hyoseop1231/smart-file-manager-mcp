"""
Bridge module for Local-File-Organizer integration with Ollama
"""
import os
import sys
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import json
import asyncio
from ollama_bridge import ollama_service

class FileOrganizer:
    def __init__(self):
        self.model_initialized = False
        
    def initialize_models(self):
        """Initialize AI models if needed"""
        if not self.model_initialized:
            try:
                # Models will be initialized when needed
                self.model_initialized = True
            except Exception as e:
                print(f"Failed to initialize models: {e}")
                self.model_initialized = False
    
    async def organize_files(
        self, 
        source_dir: str, 
        target_dir: Optional[str], 
        method: str, 
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Organize files using AI-powered categorization
        
        Args:
            source_dir: Source directory path
            target_dir: Target directory path (optional)
            method: Organization method ('content', 'date', 'type')
            dry_run: If True, only preview changes without executing
            
        Returns:
            Dictionary with organization results
        """
        try:
            # Validate source directory
            if not os.path.exists(source_dir):
                return {
                    "status": "error",
                    "error": f"Source directory not found: {source_dir}"
                }
            
            # Set default target directory
            if not target_dir:
                target_dir = f"{source_dir}_organized"
            
            # Collect files
            file_paths = self._collect_files(source_dir)
            
            if not file_paths:
                return {
                    "status": "no_files",
                    "message": "No files found to organize"
                }
            
            # Organize based on method
            if method == "content":
                organized = await self._organize_by_content(file_paths, target_dir, dry_run)
            elif method == "date":
                organized = self._organize_by_date(file_paths, target_dir, dry_run)
            elif method == "type":
                organized = self._organize_by_type(file_paths, target_dir, dry_run)
            else:
                return {
                    "status": "error",
                    "error": f"Unknown organization method: {method}"
                }
            
            return organized
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _collect_files(self, directory: str) -> List[str]:
        """Collect all files from directory"""
        files = []
        try:
            if collect_file_paths:
                # Use original function if available
                return collect_file_paths(directory)
            else:
                # Fallback implementation
                for root, _, filenames in os.walk(directory):
                    for filename in filenames:
                        files.append(os.path.join(root, filename))
        except Exception as e:
            print(f"Error collecting files: {e}")
        return files
    
    async def _organize_by_content(self, file_paths: List[str], target_dir: str, dry_run: bool) -> Dict[str, Any]:
        """Organize files by content using AI analysis with Ollama"""
        # AI 기반 카테고리
        ai_categories = {}
        
        print(f"🤖 Ollama를 사용하여 {len(file_paths)}개 파일 분석 중...")
        
        # Analyze each file with AI
        for i, file_path in enumerate(file_paths):
            print(f"  분석 중... ({i+1}/{len(file_paths)})", end='\r')
            
            try:
                # Use Ollama to categorize
                result = await ollama_service.categorize_file(file_path)
                suggested_folder = result.get("suggested_folder", "기타")
                
                if suggested_folder not in ai_categories:
                    ai_categories[suggested_folder] = []
                ai_categories[suggested_folder].append(os.path.basename(file_path))
            except Exception as e:
                print(f"\n  ⚠️ {file_path} 분석 실패: {e}")
                if "기타" not in ai_categories:
                    ai_categories["기타"] = []
                ai_categories["기타"].append(os.path.basename(file_path))
        
        print("\n✅ 파일 분석 완료!")
        
        # Execute organization if not dry run
        if not dry_run:
            for category, files in ai_categories.items():
                if files:
                    cat_dir = os.path.join(target_dir, category)
                    os.makedirs(cat_dir, exist_ok=True)
                    
                    for file in files:
                        src = None
                        # Find the full path of the file
                        for fp in file_paths:
                            if os.path.basename(fp) == file:
                                src = fp
                                break
                        
                        if src:
                            dst = os.path.join(cat_dir, file)
                            try:
                                shutil.copy2(src, dst)
                            except Exception as e:
                                print(f"Error copying {file}: {e}")
        
        return {
            "status": "preview" if dry_run else "completed",
            "method": "content",
            "organized_files": ai_categories,
            "total_files": sum(len(files) for files in ai_categories.values()),
            "target_directory": target_dir,
            "ai_powered": True
        }
    
    def _organize_by_date(self, file_paths: List[str], target_dir: str, dry_run: bool) -> Dict[str, Any]:
        """Organize files by creation/modification date"""
        date_groups = {}
        
        for file_path in file_paths:
            try:
                # Get file modification time
                mtime = os.path.getmtime(file_path)
                date = datetime.fromtimestamp(mtime)
                year_month = f"{date.year}년_{date.month:02d}월"
                
                if year_month not in date_groups:
                    date_groups[year_month] = []
                date_groups[year_month].append(os.path.basename(file_path))
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
        
        # Execute organization if not dry run
        if not dry_run:
            for date_folder, files in date_groups.items():
                date_dir = os.path.join(target_dir, date_folder)
                os.makedirs(date_dir, exist_ok=True)
                
                for file in files:
                    src = os.path.join(os.path.dirname(file_paths[0]), file)
                    dst = os.path.join(date_dir, file)
                    try:
                        shutil.copy2(src, dst)
                    except Exception as e:
                        print(f"Error copying {file}: {e}")
        
        return {
            "status": "preview" if dry_run else "completed",
            "method": "date",
            "organized_files": date_groups,
            "total_files": sum(len(files) for files in date_groups.values()),
            "target_directory": target_dir
        }
    
    def _organize_by_type(self, file_paths: List[str], target_dir: str, dry_run: bool) -> Dict[str, Any]:
        """Organize files by file type/extension"""
        type_groups = {}
        
        type_map = {
            "문서": [".txt", ".doc", ".docx", ".pdf", ".odt", ".rtf"],
            "스프레드시트": [".xls", ".xlsx", ".csv", ".ods"],
            "프레젠테이션": [".ppt", ".pptx", ".odp"],
            "이미지": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
            "비디오": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"],
            "오디오": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma"],
            "코드": [".py", ".js", ".java", ".cpp", ".c", ".html", ".css", ".ts", ".go"],
            "압축파일": [".zip", ".tar", ".gz", ".rar", ".7z", ".bz2"],
            "데이터": [".json", ".xml", ".yaml", ".yml", ".sql", ".db"]
        }
        
        for file_path in file_paths:
            ext = Path(file_path).suffix.lower()
            file_type = "기타"
            
            for type_name, extensions in type_map.items():
                if ext in extensions:
                    file_type = type_name
                    break
            
            if file_type not in type_groups:
                type_groups[file_type] = []
            type_groups[file_type].append(os.path.basename(file_path))
        
        # Execute organization if not dry run
        if not dry_run:
            for type_folder, files in type_groups.items():
                type_dir = os.path.join(target_dir, type_folder)
                os.makedirs(type_dir, exist_ok=True)
                
                for file in files:
                    src = os.path.join(os.path.dirname(file_paths[0]), file)
                    dst = os.path.join(type_dir, file)
                    try:
                        shutil.copy2(src, dst)
                    except Exception as e:
                        print(f"Error copying {file}: {e}")
        
        return {
            "status": "preview" if dry_run else "completed",
            "method": "type",
            "organized_files": type_groups,
            "total_files": sum(len(files) for files in type_groups.values()),
            "target_directory": target_dir
        }
    
    def _categorize_file(self, file_path: str) -> str:
        """Categorize a single file based on its type and content"""
        ext = Path(file_path).suffix.lower()
        
        # Simple categorization based on extension
        if ext in [".txt", ".doc", ".docx", ".pdf", ".odt", ".rtf"]:
            return "documents"
        elif ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"]:
            return "images"
        elif ext in [".py", ".js", ".java", ".cpp", ".c", ".html", ".css"]:
            return "code"
        elif ext in [".json", ".xml", ".csv", ".xlsx", ".sql"]:
            return "data"
        elif ext in [".mp4", ".avi", ".mkv", ".mp3", ".wav"]:
            return "media"
        elif ext in [".zip", ".tar", ".gz", ".rar"]:
            return "archives"
        else:
            return "others"

# Global instance
file_organizer = FileOrganizer()