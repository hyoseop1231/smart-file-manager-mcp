#!/usr/bin/env python3
"""
Content Extractor for Smart File Manager
Unified text extraction from various file formats including HWP/HWPX
"""

import os
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import mimetypes
import chardet

# Import specialized processors
from hwp_processor import HWPProcessor

logger = logging.getLogger(__name__)

class ContentExtractor:
    """
    Unified content extraction system supporting multiple file formats
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize specialized processors
        self.hwp_processor = HWPProcessor()
        
        # Define supported file types and their processors
        self.extractors = {
            # Korean document formats
            '.hwp': self._extract_hwp,
            '.hwpx': self._extract_hwp,

            # Office/document formats
            '.pdf': self._extract_pdf,
            '.doc': self._extract_office_via_libreoffice,
            '.docx': self._extract_office_via_libreoffice,
            '.ppt': self._extract_office_via_libreoffice,
            '.pptx': self._extract_office_via_libreoffice,
            '.xls': self._extract_office_via_libreoffice,
            '.xlsx': self._extract_xlsx,
            
            # Standard document formats
            '.txt': self._extract_text,
            '.md': self._extract_text,
            '.csv': self._extract_text,
            '.json': self._extract_text,
            '.xml': self._extract_text,
            '.log': self._extract_text,
            
            # Code files
            '.py': self._extract_text,
            '.js': self._extract_text,
            '.java': self._extract_text,
            '.cpp': self._extract_text,
            '.c': self._extract_text,
            '.go': self._extract_text,
            '.php': self._extract_text,
            '.rb': self._extract_text,
            '.sh': self._extract_text,
            '.sql': self._extract_text,
            '.html': self._extract_html,
            '.css': self._extract_text,
            
            # Configuration files
            '.yml': self._extract_text,
            '.yaml': self._extract_text,
            '.toml': self._extract_text,
            '.ini': self._extract_text,
            '.conf': self._extract_text,
            '.config': self._extract_text,
        }
        
        # File size limits (in bytes)
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.max_text_file_size = 10 * 1024 * 1024  # 10MB for text files
    
    def can_extract(self, file_path: str) -> bool:
        """Check if file can be processed"""
        file_path = Path(file_path)
        
        if not file_path.exists() or not file_path.is_file():
            return False
        
        extension = file_path.suffix.lower()
        return extension in self.extractors
    
    def extract_content(self, file_path: str) -> Tuple[str, bool, Dict[str, Any]]:
        """
        Extract text content from file
        
        Returns:
            tuple: (text_content, success, metadata)
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
        
        # Get file extension
        extension = file_path.suffix.lower()
        
        if extension not in self.extractors:
            return "", False, {
                "error": "Unsupported file format",
                "extension": extension,
                "supported_formats": list(self.extractors.keys())
            }
        
        # Extract content using appropriate method
        try:
            extractor = self.extractors[extension]
            text, success, metadata = extractor(str(file_path))
            
            # Add common metadata
            metadata.update({
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_size": file_size,
                "extension": extension,
                "extractor_used": extractor.__name__
            })
            
            if success and text:
                self.logger.info(f"✅ Content extracted from {file_path.name}: {len(text)} characters")
            else:
                self.logger.warning(f"⚠️ Failed to extract content from {file_path.name}")
            
            return text, success, metadata
            
        except Exception as e:
            self.logger.error(f"❌ Content extraction error for {file_path}: {e}")
            return "", False, {"error": str(e), "extractor": extractor.__name__}
    
    def _extract_hwp(self, file_path: str) -> Tuple[str, bool, Dict[str, Any]]:
        """Extract content from HWP/HWPX files"""
        return self.hwp_processor.extract_text(file_path)

    def _extract_pdf(self, file_path: str) -> Tuple[str, bool, Dict[str, Any]]:
        """Extract content from PDF files."""
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            return self._extract_office_via_libreoffice(file_path)

        try:
            reader = PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_parts.append(page_text.strip())

            metadata = {
                "processor": "pypdf2",
                "page_count": len(reader.pages),
                "success": True,
            }
            pdf_meta = {}
            raw_meta = getattr(reader, "metadata", None) or {}
            for key, value in dict(raw_meta).items():
                cleaned_key = str(key).lstrip("/")
                cleaned_value = str(value).strip()
                if cleaned_value:
                    pdf_meta[cleaned_key] = cleaned_value
            if pdf_meta:
                metadata["pdf_metadata"] = pdf_meta

            text = self._clean_text("\n\n".join(text_parts))
            if text:
                metadata["character_count"] = len(text)
                return text, True, metadata

            summary_parts = [f"PDF document with {len(reader.pages)} pages"]
            for field in ("Title", "Author", "Subject", "Keywords"):
                value = pdf_meta.get(field)
                if value:
                    summary_parts.append(f"{field}: {value}")
            summary_text = self._clean_text(". ".join(summary_parts))
            metadata["character_count"] = len(summary_text)
            return summary_text, bool(summary_text), metadata
        except Exception as e:
            return "", False, {"error": str(e), "processor": "pypdf2"}

    def _extract_xlsx(self, file_path: str) -> Tuple[str, bool, Dict[str, Any]]:
        """Extract content from XLSX files with openpyxl."""
        try:
            import openpyxl
        except ImportError:
            return self._extract_office_via_libreoffice(file_path)

        try:
            workbook = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            text_parts = []
            sheet_names = []

            for sheet in workbook.worksheets:
                sheet_names.append(sheet.title)
                rows = []
                for row in sheet.iter_rows(values_only=True):
                    values = [str(cell).strip() for cell in row if cell not in (None, "")]
                    if values:
                        rows.append(" | ".join(values))
                if rows:
                    text_parts.append(f"[Sheet: {sheet.title}]\n" + "\n".join(rows))

            metadata = {
                "processor": "openpyxl",
                "sheet_count": len(sheet_names),
                "sheet_names": sheet_names,
                "success": True,
            }

            text = self._clean_text("\n\n".join(text_parts))
            if text:
                metadata["character_count"] = len(text)
                return text, True, metadata

            summary_text = self._clean_text(
                f"Excel workbook with {len(sheet_names)} sheets. " +
                (f"Sheets: {', '.join(sheet_names)}" if sheet_names else "")
            )
            metadata["character_count"] = len(summary_text)
            return summary_text, bool(summary_text), metadata
        except Exception as e:
            return self._extract_office_via_libreoffice(file_path, error_hint=str(e))

    def _extract_office_via_libreoffice(self, file_path: str, error_hint: str = "") -> Tuple[str, bool, Dict[str, Any]]:
        """Fallback office extractor using LibreOffice text conversion."""
        file_path_obj = Path(file_path)
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                cmd = [
                    "libreoffice",
                    "--headless",
                    "--convert-to", "txt:Text",
                    "--outdir", temp_dir,
                    file_path,
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                output_file = Path(temp_dir) / f"{file_path_obj.stem}.txt"
                if result.returncode == 0 and output_file.exists():
                    text = self._clean_text(output_file.read_text(encoding="utf-8", errors="ignore"))
                    metadata = {
                        "processor": "libreoffice",
                        "source_format": file_path_obj.suffix.lower(),
                        "success": bool(text),
                        "character_count": len(text),
                    }
                    if text:
                        return text, True, metadata

                stderr = (result.stderr or "").strip()
                error = stderr or error_hint or "LibreOffice conversion failed"
                return "", False, {
                    "error": error,
                    "processor": "libreoffice",
                    "source_format": file_path_obj.suffix.lower(),
                }
        except subprocess.TimeoutExpired:
            return "", False, {
                "error": "LibreOffice conversion timed out",
                "processor": "libreoffice",
                "source_format": file_path_obj.suffix.lower(),
            }
        except FileNotFoundError:
            return "", False, {
                "error": "LibreOffice not available",
                "processor": "libreoffice",
                "source_format": file_path_obj.suffix.lower(),
            }
        except Exception as e:
            return "", False, {
                "error": error_hint or str(e),
                "processor": "libreoffice",
                "source_format": file_path_obj.suffix.lower(),
            }
    
    def _extract_text(self, file_path: str) -> Tuple[str, bool, Dict[str, Any]]:
        """Extract content from plain text files"""
        try:
            file_path = Path(file_path)
            file_size = file_path.stat().st_size
            
            # Size check for text files
            if file_size > self.max_text_file_size:
                return "", False, {
                    "error": f"Text file too large: {file_size} bytes (max: {self.max_text_file_size})"
                }
            
            # Detect encoding
            with open(file_path, 'rb') as f:
                raw_data = f.read()
            
            encoding_info = chardet.detect(raw_data)
            encoding = encoding_info.get('encoding', 'utf-8')
            confidence = encoding_info.get('confidence', 0.0)
            
            # Try to decode with detected encoding
            try:
                text = raw_data.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                # Fallback to utf-8 with error handling
                text = raw_data.decode('utf-8', errors='ignore')
                encoding = 'utf-8 (fallback)'
                confidence = 0.0
            
            # Clean text
            text = self._clean_text(text)
            
            metadata = {
                "encoding": encoding,
                "encoding_confidence": confidence,
                "character_count": len(text),
                "line_count": text.count('\n') + 1 if text else 0,
                "success": True
            }
            
            return text, True, metadata
            
        except Exception as e:
            return "", False, {"error": str(e)}
    
    def _extract_html(self, file_path: str) -> Tuple[str, bool, Dict[str, Any]]:
        """Extract content from HTML files"""
        try:
            # First extract as text
            text, success, metadata = self._extract_text(file_path)
            
            if not success:
                return text, success, metadata
            
            # Simple HTML tag removal
            import re
            
            # Remove script and style content
            text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', text)
            
            # Clean up HTML entities
            import html
            text = html.unescape(text)
            
            # Clean whitespace
            text = self._clean_text(text)
            
            metadata.update({
                "html_processed": True,
                "final_character_count": len(text)
            })
            
            return text, True, metadata
            
        except Exception as e:
            return "", False, {"error": str(e)}
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        import re
        
        # Remove control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs -> single space
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple newlines -> double newline
        
        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def get_supported_extensions(self) -> list:
        """Get list of supported file extensions"""
        return list(self.extractors.keys())
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information and extraction capabilities"""
        file_path = Path(file_path)
        
        info = {
            'file_name': file_path.name,
            'file_path': str(file_path),
            'exists': file_path.exists(),
            'is_file': file_path.is_file() if file_path.exists() else False,
            'file_size': file_path.stat().st_size if file_path.exists() else 0,
            'extension': file_path.suffix.lower(),
            'can_extract': self.can_extract(str(file_path)),
            'supported_extensions': self.get_supported_extensions()
        }
        
        # Add MIME type if available
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            info['mime_type'] = mime_type
        
        # Add extractor information
        if info['can_extract']:
            extension = file_path.suffix.lower()
            extractor = self.extractors.get(extension)
            if extractor:
                info['extractor_method'] = extractor.__name__
        
        # Special handling for HWP files
        if extension in ['.hwp', '.hwpx']:
            hwp_info = self.hwp_processor.get_file_info(str(file_path))
            info.update({'hwp_info': hwp_info})
        
        return info
    
    def extract_sample(self, file_path: str, max_chars: int = 1000) -> Tuple[str, bool, Dict[str, Any]]:
        """Extract a sample of content for preview purposes"""
        text, success, metadata = self.extract_content(file_path)
        
        if success and text and len(text) > max_chars:
            # Extract sample from beginning and end
            sample_size = max_chars // 2
            sample_text = text[:sample_size] + "\n...\n" + text[-sample_size:]
            metadata.update({
                "is_sample": True,
                "sample_size": max_chars,
                "total_length": len(text)
            })
            return sample_text, True, metadata
        
        return text, success, metadata
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get content extractor statistics"""
        return {
            "supported_extensions": len(self.extractors),
            "extension_list": list(self.extractors.keys()),
            "max_file_size_mb": self.max_file_size // (1024 * 1024),
            "max_text_file_size_mb": self.max_text_file_size // (1024 * 1024),
            "hwp_support": self.hwp_processor.get_file_info("dummy.hwp").get('hwp_lib_available', False),
            "processors": {
                "hwp_processor": "HWPProcessor",
                "text_processor": "Built-in",
                "html_processor": "Built-in"
            }
        }


def test_content_extractor():
    """Test function for content extractor"""
    extractor = ContentExtractor()
    
    print("🔍 Content Extractor Test")
    print("📊 Statistics:")
    stats = extractor.get_statistics()
    import json
    print(json.dumps(stats, indent=2))
    print("-" * 50)
    
    # Test with sample files
    test_files = [
        "/watch_directories/Desktop/test.hwp",
        "/watch_directories/Desktop/test.hwpx", 
        "/watch_directories/Desktop/test.txt",
        "/etc/hosts",  # System text file that usually exists
        __file__  # This python file
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n📄 Testing: {test_file}")
            
            # Get file info
            info = extractor.get_file_info(test_file)
            print(f"   Can extract: {'✅' if info['can_extract'] else '❌'}")
            print(f"   Size: {info['file_size']:,} bytes")
            print(f"   Extension: {info['extension']}")
            
            if info['can_extract']:
                # Extract sample
                sample, success, metadata = extractor.extract_sample(test_file, 200)
                if success:
                    print(f"   ✅ Sample extracted ({len(sample)} chars)")
                    print(f"   Preview: {repr(sample[:100])}...")
                else:
                    print(f"   ❌ Extraction failed: {metadata.get('error', 'Unknown error')}")
        else:
            print(f"\n❌ File not found: {test_file}")


if __name__ == "__main__":
    test_content_extractor()
