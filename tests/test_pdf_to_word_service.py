from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from pypdf import PdfWriter

from pdf_merger_desktop.pdf_to_word_service import (
    _image_dimensions,
    _image_xml,
    _text_xml,
    convert_pdfs_to_docx,
)


def test_convert_pdf_to_docx_creates_valid_docx(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=400, height=400)
    with source.open("wb") as stream:
        writer.write(stream)
    output, pages, images = convert_pdfs_to_docx(
        [source], tmp_path / "converted.docx", preserve_layout=True
    )
    assert output.exists() and pages == 1 and images == 0
    with ZipFile(output) as archive:
        assert "word/document.xml" in archive.namelist()
        document_xml = archive.read("word/document.xml").decode("utf-8")
        assert 'w:pgSz w:w="11905" w:h="16837"' in document_xml


def test_image_dimensions_and_xml_preserve_aspect_ratio() -> None:
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8 + (1200).to_bytes(4, "big") + (600).to_bytes(4, "big")
    assert _image_dimensions(png) == (1200, 600)
    xml = _image_xml("rId2", "figure.png", 1, 1200, 600)
    root = ET.fromstring(
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">'
        + xml
        + "</w:document>"
    )
    extent = next(node for node in root.iter() if node.tag.endswith("extent"))
    assert extent.attrib == {"cx": "5669280", "cy": "2834640"}
    small_xml = _image_xml("rId3", "small.png", 2, 120, 60)
    assert 'cx="1143000" cy="571500"' in small_xml


def test_text_xml_keeps_extracted_line_breaks() -> None:
    xml = _text_xml("first line\nsecond line")
    assert "<w:br/>" in xml
    assert "first line" in xml and "second line" in xml
