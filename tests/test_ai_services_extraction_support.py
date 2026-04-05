from pathlib import Path
import sys
import unicodedata
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from PIL import Image


AI_SERVICES_DIR = Path(__file__).resolve().parents[1] / "ai-services"
if str(AI_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICES_DIR))

sys.modules.setdefault("schedule", SimpleNamespace())

import content_extractor as content_extractor_module
from content_extractor import ContentExtractor
from hwp_processor import HWPProcessor
from enhanced_indexer_v4 import EnhancedFileIndexer
from image_processor import ImageProcessor
from multimedia_processor import MultimediaProcessor


def test_content_extractor_supports_office_extensions() -> None:
    extractor = ContentExtractor()

    for ext in (".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"):
        assert ext in extractor.extractors


def test_extract_xlsx_reads_sheet_values(tmp_path: Path) -> None:
    openpyxl = pytest.importorskip("openpyxl")

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Projects"
    sheet["A1"] = "과제명"
    sheet["B1"] = "KITECH"
    sheet["A2"] = "책임자"
    sheet["B2"] = "김효섭"

    file_path = tmp_path / "sample.xlsx"
    workbook.save(file_path)

    extractor = ContentExtractor()
    text, success, metadata = extractor.extract_content(str(file_path))

    assert success is True
    assert "Projects" in text
    assert "과제명" in text
    assert "김효섭" in text
    assert metadata["processor"] == "openpyxl"


def test_hwp_processor_uses_hwp5txt_and_merges_summary() -> None:
    processor = HWPProcessor()

    fake_result = SimpleNamespace(returncode=0, stdout="본문 내용\n두번째 줄", stderr="warning line\n")
    with patch("hwp_processor.HWP5TXT_PATH", "/usr/local/bin/hwp5txt"), \
         patch("hwp_processor.subprocess.run", return_value=fake_result), \
         patch.object(processor, "_extract_hwp_summary_metadata", return_value={"title": "문서 제목", "author": "김효섭"}):
        text, success, metadata = processor._extract_hwp_text("/tmp/sample.hwp")

    assert success is True
    assert "본문 내용" in text
    assert metadata["processor"] == "hwp5txt"
    assert metadata["title"] == "문서 제목"
    assert metadata["summary_info"]["author"] == "김효섭"


def test_image_processor_treats_metadata_only_images_as_extracted(tmp_path: Path) -> None:
    file_path = tmp_path / "diagram.bmp"
    Image.new("RGB", (320, 200), color="white").save(file_path)

    processor = ImageProcessor(enable_ocr=False, enable_ai_vision=False)
    text, success, metadata = processor.extract_content(str(file_path))

    assert success is True
    assert "Resolution 320x200" in text
    assert metadata["image_format"] == "BMP"


def test_multimedia_processor_supports_audio_video_extensions() -> None:
    processor = MultimediaProcessor(enable_ocr=False, enable_ai_vision=False, enable_stt=False)

    assert processor.get_file_type("sample.amr") == "audio"
    assert processor.get_file_type("sample.3ga") == "audio"
    assert processor.get_file_type("sample.ts") == "video"
    assert processor.get_file_type("sample.mts") == "video"


def test_extract_pdf_uses_pdf_reader_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakePage:
        def extract_text(self) -> str:
            return "PDF 본문"

    class FakePdfReader:
        def __init__(self, file_path: str) -> None:
            self.pages = [FakePage()]
            self.metadata = {"/Title": "보고서", "/Author": "김효섭"}

    monkeypatch.setitem(sys.modules, "PyPDF2", SimpleNamespace(PdfReader=FakePdfReader))

    extractor = ContentExtractor()
    text, success, metadata = extractor._extract_pdf("/tmp/sample.pdf")

    assert success is True
    assert "PDF 본문" in text
    assert metadata["page_count"] == 1
    assert metadata["pdf_metadata"]["Title"] == "보고서"


def test_force_reindex_reprocesses_unchanged_files(tmp_path: Path) -> None:
    file_path = tmp_path / "note.txt"
    file_path.write_text("hello world", encoding="utf-8")

    indexer = EnhancedFileIndexer(
        db_path=str(tmp_path / "db" / "file-index.db"),
        embeddings_path=str(tmp_path / "embeddings"),
        metadata_path=str(tmp_path / "metadata"),
        enable_ai_vision=False,
        enable_stt=False,
    )

    calls = {"count": 0}

    def fake_extract_content(_: str):
        calls["count"] += 1
        return "hello world", True, {"processor": "test"}

    with patch.object(indexer.content_extractor, "extract_content", side_effect=fake_extract_content):
        assert indexer.index_file(str(file_path)) is True
        assert indexer.index_file(str(file_path)) is True
        assert indexer.index_file(str(file_path), force_reindex=True) is True

    assert calls["count"] == 2


def test_extract_metadata_stores_normalized_name_and_path(tmp_path: Path) -> None:
    nfd_name = unicodedata.normalize("NFD", "가나다.txt")
    file_path = tmp_path / nfd_name
    file_path.write_text("sample", encoding="utf-8")

    indexer = EnhancedFileIndexer(
        db_path=str(tmp_path / "db2" / "file-index.db"),
        embeddings_path=str(tmp_path / "embeddings2"),
        metadata_path=str(tmp_path / "metadata2"),
        enable_ai_vision=False,
        enable_stt=False,
    )

    metadata = indexer._extract_metadata(file_path)

    assert metadata["path"] == str(file_path)
    assert metadata["normalized_path"] == unicodedata.normalize("NFC", str(file_path))
    assert metadata["name"] == "가나다.txt"
    assert metadata["raw_name"] == nfd_name
