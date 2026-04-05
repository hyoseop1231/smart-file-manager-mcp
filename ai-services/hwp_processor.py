#!/usr/bin/env python3
"""
HWP/HWPX File Processor for Smart File Manager
Handles both legacy HWP (binary) and modern HWPX (XML-based) formats
"""

import os
import re
import shutil
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import logging
from typing import Tuple, Optional, Dict, Any
import tempfile
import subprocess

# Try to import pyhwp for HWP support
try:
    import hwp5  # pyhwp package exposes the `hwp5` module
    HWP_SUPPORT = True
except ImportError:
    try:
        import pyhwp.hwp5 as hwp5  # Fallback for older layouts
        HWP_SUPPORT = True
    except ImportError:
        hwp5 = None
        HWP_SUPPORT = False

try:
    import olefile
    OLEFILE_SUPPORT = True
except ImportError:
    olefile = None
    OLEFILE_SUPPORT = False

HWP5TXT_PATH = shutil.which("hwp5txt")
SUMMARY_STREAM = "\x05HwpSummaryInformation"
SUMMARY_FIELD_MAP = {
    2: "title",
    3: "subject",
    4: "author",
    5: "keywords",
    6: "comments",
    8: "last_saved_by",
    9: "revision",
}

logger = logging.getLogger(__name__)

class HWPProcessor:
    """
    Processor for Korean HWP and HWPX document formats
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supported_extensions = ['.hwp', '.hwpx']
        
        # Log library availability
        if not HWP_SUPPORT and not HWP5TXT_PATH:
            self.logger.warning("pyhwp library not available. HWP file processing will be limited.")
    
    def is_supported_file(self, file_path: str) -> bool:
        """Check if file is supported HWP/HWPX format"""
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    def get_file_type(self, file_path: str) -> str:
        """Get specific file type (hwp or hwpx)"""
        suffix = Path(file_path).suffix.lower()
        if suffix == '.hwp':
            return 'hwp'
        elif suffix == '.hwpx':
            return 'hwpx'
        else:
            return 'unknown'
    
    def extract_text(self, file_path: str) -> Tuple[str, bool, Dict[str, Any]]:
        """
        Extract text content from HWP/HWPX file
        
        Returns:
            tuple: (extracted_text, success, metadata)
        """
        if not self.is_supported_file(file_path):
            return "", False, {"error": "Unsupported file format"}
        
        file_type = self.get_file_type(file_path)
        
        try:
            if file_type == 'hwp':
                return self._extract_hwp_text(file_path)
            elif file_type == 'hwpx':
                return self._extract_hwpx_text(file_path)
            else:
                return "", False, {"error": "Unknown file type"}
        except Exception as e:
            self.logger.error(f"Error processing {file_type.upper()} file {file_path}: {e}")
            return "", False, {"error": str(e)}
    
    def _extract_hwp_text(self, file_path: str) -> Tuple[str, bool, Dict[str, Any]]:
        """Extract text from legacy HWP (binary) format"""
        summary_info = self._extract_hwp_summary_metadata(file_path)

        if HWP5TXT_PATH:
            text, success, metadata = self._extract_via_hwp5txt(file_path)
            metadata = self._merge_summary_info(metadata, summary_info)
            if success:
                return text, True, metadata

        # Fallback: try LibreOffice conversion
        text, success, metadata = self._extract_via_libreoffice(file_path, 'hwp')
        metadata = self._merge_summary_info(metadata, summary_info)
        return text, success, metadata
    
    def _extract_hwpx_text(self, file_path: str) -> Tuple[str, bool, Dict[str, Any]]:
        """Extract text from modern HWPX (XML-based) format"""
        try:
            self.logger.info(f"Processing HWPX file: {file_path}")
            
            text_parts = []
            metadata = {
                "format": "hwpx",
                "processor": "xml_parser",
                "content_files": [],
                "xml_elements": 0
            }
            
            with zipfile.ZipFile(file_path, 'r') as zf:
                # List all files in HWPX
                file_list = zf.namelist()
                self.logger.debug(f"HWPX contents: {file_list}")
                
                # Possible content file locations
                content_files = [
                    'Contents/content.xml',
                    'content.xml',
                    'Contents/section0.xml',
                    'Contents/header.xml',
                    'word/document.xml',  # Office compatibility
                    'Contents/content.hml'  # Alternative format
                ]
                
                files_processed = 0
                for content_file in content_files:
                    if content_file in file_list:
                        self.logger.debug(f"Processing content file: {content_file}")
                        metadata["content_files"].append(content_file)
                        
                        try:
                            content = zf.read(content_file)
                            file_text = self._parse_xml_content(content)
                            if file_text:
                                text_parts.append(file_text)
                                files_processed += 1
                        except Exception as e:
                            self.logger.warning(f"Error processing {content_file}: {e}")
                            continue
                
                # Also try to extract from any other XML files
                for file_name in file_list:
                    if (file_name.endswith('.xml') and 
                        file_name not in content_files and
                        not file_name.startswith('_rels/') and
                        not file_name.startswith('[Content_Types]')):
                        
                        try:
                            content = zf.read(file_name)
                            file_text = self._parse_xml_content(content)
                            if file_text and len(file_text) > 50:  # Only significant content
                                text_parts.append(file_text)
                                metadata["content_files"].append(file_name)
                                files_processed += 1
                        except:
                            continue
            
            # Combine and clean text
            full_text = self._clean_extracted_text("\n".join(text_parts))
            metadata["files_processed"] = files_processed
            
            if full_text.strip():
                self.logger.info(f"✅ HWPX text extraction successful: {len(full_text)} characters from {files_processed} files")
                metadata["success"] = True
                metadata["character_count"] = len(full_text)
                return full_text, True, metadata
            else:
                self.logger.warning(f"⚠️ HWPX file appears to be empty: {file_path}")
                return "", False, {"error": "No text content found", **metadata}
                
        except Exception as e:
            self.logger.error(f"❌ HWPX processing failed: {e}")
            # Fallback to LibreOffice
            return self._extract_via_libreoffice(file_path, 'hwpx')
    
    def _parse_xml_content(self, xml_content: bytes) -> str:
        """Parse XML content and extract text"""
        try:
            root = ET.fromstring(xml_content)
            text_parts = []
            
            # Extract all text nodes
            for elem in root.iter():
                # Get element text
                if elem.text and elem.text.strip():
                    text_parts.append(elem.text.strip())
                
                # Get tail text (text after element)
                if elem.tail and elem.tail.strip():
                    text_parts.append(elem.tail.strip())
            
            return " ".join(text_parts)
            
        except ET.ParseError as e:
            self.logger.debug(f"XML parsing error: {e}")
            # Try as raw text if XML parsing fails
            try:
                text = xml_content.decode('utf-8', errors='ignore')
                # Simple tag removal
                import re
                text = re.sub(r'<[^>]+>', ' ', text)
                return text
            except:
                return ""
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        import re
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        
        # Remove common artifacts
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        return text.strip()

    def _extract_via_hwp5txt(self, file_path: str) -> Tuple[str, bool, Dict[str, Any]]:
        """Extract HWP text using the bundled hwp5txt CLI."""
        if not HWP5TXT_PATH:
            return "", False, {"error": "hwp5txt command not available", "format": "hwp"}

        try:
            self.logger.info(f"Processing HWP file via hwp5txt: {file_path}")
            result = subprocess.run(
                [HWP5TXT_PATH, file_path],
                capture_output=True,
                text=True,
                timeout=60,
            )
            text = self._clean_extracted_text(result.stdout)
            warnings = self._extract_warning_lines(result.stderr)
            metadata = {
                "format": "hwp",
                "processor": "hwp5txt",
                "success": bool(text),
                "character_count": len(text),
            }
            if warnings:
                metadata["warnings"] = warnings

            if text:
                self.logger.info(f"✅ HWP text extraction successful via hwp5txt: {len(text)} characters")
                return text, True, metadata

            error = self._clean_extracted_text(result.stderr) or "No text content found"
            self.logger.warning(f"⚠️ hwp5txt produced no text for {file_path}")
            return "", False, {**metadata, "error": error}
        except subprocess.TimeoutExpired:
            self.logger.error("hwp5txt extraction timed out")
            return "", False, {"error": "hwp5txt timed out", "format": "hwp", "processor": "hwp5txt"}
        except FileNotFoundError:
            return "", False, {"error": "hwp5txt command not found", "format": "hwp", "processor": "hwp5txt"}
        except Exception as e:
            self.logger.error(f"❌ HWP processing failed with hwp5txt: {e}")
            return "", False, {"error": str(e), "format": "hwp", "processor": "hwp5txt"}

    def _extract_hwp_summary_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract summary info from the HWP OLE container when available."""
        if not OLEFILE_SUPPORT:
            return {}

        try:
            with olefile.OleFileIO(file_path) as ole:
                if not ole.exists(SUMMARY_STREAM):
                    return {}
                properties = ole.getproperties(SUMMARY_STREAM)
        except Exception as e:
            self.logger.debug(f"HWP summary metadata extraction failed: {e}")
            return {}

        summary_info: Dict[str, Any] = {}
        for prop_id, field_name in SUMMARY_FIELD_MAP.items():
            value = properties.get(prop_id)
            cleaned = self._normalize_summary_value(value)
            if cleaned:
                summary_info[field_name] = cleaned

        if summary_info:
            summary_info["processor"] = "ole_summary"
        return summary_info

    def _normalize_summary_value(self, value: Any) -> str:
        if value in (None, ""):
            return ""
        if hasattr(value, "isoformat"):
            try:
                return value.isoformat()
            except Exception:
                pass
        if isinstance(value, (int, float)):
            return str(value)
        text = str(value).replace("\x00", "")
        text = text.split("\x1f", 1)[0]
        text = re.sub(r"[\x00-\x1f\x7f-\x9f]+", " ", text)
        return " ".join(text.split()).strip()

    def _merge_summary_info(self, metadata: Dict[str, Any], summary_info: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(metadata)
        if summary_info:
            merged["summary_info"] = summary_info
            for key in ("title", "subject", "author", "keywords", "comments", "last_saved_by", "revision"):
                value = summary_info.get(key)
                if value and key not in merged:
                    merged[key] = value
        return merged

    def _extract_warning_lines(self, stderr: str) -> list[str]:
        if not stderr:
            return []
        warnings = []
        for line in stderr.splitlines():
            cleaned = self._clean_extracted_text(line)
            if cleaned and cleaned not in warnings:
                warnings.append(cleaned)
        return warnings[:20]
    
    def _extract_via_libreoffice(self, file_path: str, file_type: str) -> Tuple[str, bool, Dict[str, Any]]:
        """
        Fallback method using LibreOffice to convert to text
        """
        try:
            self.logger.info(f"Attempting LibreOffice extraction for {file_type.upper()}: {file_path}")
            
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Convert to text using LibreOffice
                cmd = [
                    'libreoffice',
                    '--headless',
                    '--convert-to', 'txt',
                    '--outdir', str(temp_path),
                    file_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    # Find the output text file
                    input_name = Path(file_path).stem
                    output_file = temp_path / f"{input_name}.txt"
                    
                    if output_file.exists():
                        text = output_file.read_text(encoding='utf-8', errors='ignore')
                        text = self._clean_extracted_text(text)
                        
                        if text.strip():
                            metadata = {
                                "format": file_type,
                                "processor": "libreoffice",
                                "success": True,
                                "character_count": len(text)
                            }
                            self.logger.info(f"✅ LibreOffice extraction successful: {len(text)} characters")
                            return text, True, metadata
                
                self.logger.warning(f"LibreOffice conversion failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            self.logger.error("LibreOffice conversion timed out")
        except FileNotFoundError:
            self.logger.warning("LibreOffice not found. Install LibreOffice for better HWP support")
        except Exception as e:
            self.logger.error(f"LibreOffice extraction error: {e}")
        
        return "", False, {"error": "All extraction methods failed", "format": file_type}
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive file information"""
        file_path = Path(file_path)
        
        info = {
            'file_name': file_path.name,
            'file_type': self.get_file_type(str(file_path)),
            'file_size': file_path.stat().st_size if file_path.exists() else 0,
            'supported': self.is_supported_file(str(file_path)),
            'hwp_lib_available': HWP_SUPPORT,
            'hwp_cli_available': bool(HWP5TXT_PATH),
            'ole_summary_available': OLEFILE_SUPPORT,
            'can_process': True
        }
        
        # Add capability assessment
        if info['file_type'] == 'hwp':
            if HWP5TXT_PATH:
                info['recommended_processor'] = 'hwp5txt'
                info['extraction_confidence'] = 'high'
            elif HWP_SUPPORT:
                info['recommended_processor'] = 'pyhwp'
                info['extraction_confidence'] = 'high'
            else:
                info['recommended_processor'] = 'libreoffice'
                info['extraction_confidence'] = 'medium'
        elif info['file_type'] == 'hwpx':
            info['recommended_processor'] = 'xml_parser'
            info['extraction_confidence'] = 'high'
        
        return info
    
    def test_processing(self, file_path: str) -> Dict[str, Any]:
        """Test file processing and return detailed results"""
        if not Path(file_path).exists():
            return {"error": "File does not exist", "file_path": file_path}
        
        info = self.get_file_info(file_path)
        
        if not info['supported']:
            return {"error": "File format not supported", "info": info}
        
        # Attempt text extraction
        text, success, metadata = self.extract_text(file_path)
        
        result = {
            "file_info": info,
            "extraction_success": success,
            "extraction_metadata": metadata,
            "text_length": len(text) if text else 0,
            "text_preview": text[:500] + "..." if len(text) > 500 else text
        }
        
        return result


def test_hwp_processor():
    """Test function for HWP processor"""
    processor = HWPProcessor()
    
    print("🔍 HWP/HWPX Processor Test")
    print(f"📚 pyhwp library support: {'✅' if HWP_SUPPORT else '❌'}")
    print("-" * 50)
    
    # Test with actual files if they exist
    test_files = [
        "/watch_directories/Desktop/test.hwp",
        "/watch_directories/Desktop/test.hwpx",
        "/Users/hyoseop1231/Desktop/test.hwp",
        "/Users/hyoseop1231/Desktop/test.hwpx"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n📄 Testing: {test_file}")
            result = processor.test_processing(test_file)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"\n❌ File not found: {test_file}")


if __name__ == "__main__":
    import json
    test_hwp_processor()
