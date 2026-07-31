from pathlib import Path

from pdf_merger_desktop.file_item import PdfFileItem
from pdf_merger_desktop.main_window import MainWindow


def test_pdfa_button_tracks_valid_input_state(qtbot, tmp_path: Path) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.pdfa_button.text() == "Export as PDF/A-1b"
    assert not window.pdfa_button.isEnabled()

    source = tmp_path / "valid.pdf"
    source.write_bytes(b"%PDF-placeholder")
    window.items = [
        PdfFileItem(source, str(source).casefold(), source.name, source.stat().st_size, 1, True)
    ]
    window._render()
    assert window.pdfa_button.isEnabled()

    window.merging = True
    window._refresh_buttons()
    assert not window.pdfa_button.isEnabled()
    window.merging = False
