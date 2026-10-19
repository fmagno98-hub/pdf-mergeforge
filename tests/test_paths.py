from pathlib import Path

from pdf_merger_desktop.utilities.paths import ensure_pdf_suffix, normalized_windows_path


def test_windows_duplicate_detection(tmp_path: Path) -> None:
    path = tmp_path / "Example.PDF"
    assert normalized_windows_path(path) == normalized_windows_path(str(path).upper())


def test_pdf_suffix() -> None:
    assert ensure_pdf_suffix("merged").name == "merged.pdf"
    assert ensure_pdf_suffix("already.PDF").name == "already.PDF"
