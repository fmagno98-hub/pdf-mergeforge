from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

from pdf_merger_desktop.pdf_service import (
    MergeCancelled,
    PdfValidationError,
    merge_pdfs,
    validate_pdf,
)


def make_pdf(path: Path, widths: list[float]) -> Path:
    writer = PdfWriter()
    for width in widths:
        writer.add_blank_page(width=width, height=200)
    with path.open("wb") as stream:
        writer.write(stream)
    return path


def test_merge_two_keeps_order_and_temp_is_cleaned(tmp_path: Path) -> None:
    first = make_pdf(tmp_path / "uno.pdf", [101, 102])
    second = make_pdf(tmp_path / "due.pdf", [201])
    output, pages = merge_pdfs([first, second], tmp_path / "cartella con spazi" / "risultato")
    assert pages == 3
    assert output.suffix == ".pdf"
    assert [float(page.mediabox.width) for page in PdfReader(output).pages] == [101, 102, 201]
    assert not list(output.parent.glob("*.tmp"))


def test_single_pdf_safe_copy_unicode(tmp_path: Path) -> None:
    source = make_pdf(tmp_path / "sorgente.pdf", [123])
    before = source.read_bytes()
    output, pages = merge_pdfs([source], tmp_path / "Unicode-à" / "cópia.pdf")
    assert pages == 1 and output.exists() and source.read_bytes() == before


@pytest.mark.parametrize(
    "name,content", [("missing.pdf", None), ("bad.pdf", b"not pdf"), ("empty.pdf", b"")]
)
def test_invalid_inputs(tmp_path: Path, name: str, content: bytes | None) -> None:
    path = tmp_path / name
    if content is not None:
        path.write_bytes(content)
    assert not validate_pdf(path).is_valid


def test_output_cannot_equal_source(tmp_path: Path) -> None:
    source = make_pdf(tmp_path / "same.pdf", [100])
    with pytest.raises(PdfValidationError):
        merge_pdfs([source], source)


def test_cancel_cleans_temporary(tmp_path: Path) -> None:
    source = make_pdf(tmp_path / "input.pdf", [100])
    with pytest.raises(MergeCancelled):
        merge_pdfs([source], tmp_path / "out.pdf", cancelled=lambda: True)
    assert not list(tmp_path.glob("*.tmp")) and not (tmp_path / "out.pdf").exists()


def test_error_cleans_temporary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = make_pdf(tmp_path / "input.pdf", [100])

    def fail(*args, **kwargs):
        raise OSError("disk error")

    monkeypatch.setattr(PdfWriter, "write", fail)
    with pytest.raises(OSError):
        merge_pdfs([source], tmp_path / "out.pdf")
    assert not list(tmp_path.glob("*.tmp"))
