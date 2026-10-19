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


def test_page_limit_control_updates_output_summary(qtbot, tmp_path: Path) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    source = tmp_path / "valid.pdf"
    source.write_bytes(b"%PDF-placeholder")
    window.items = [
        PdfFileItem(source, str(source).casefold(), source.name, source.stat().st_size, 5, True)
    ]

    window.page_limit_spin.setValue(3)
    window.page_limit_check.setChecked(True)
    window._refresh()
    assert window._current_page_limit() == 3
    assert window.summary_pages.text() == "5 total pages - 3 in output"

    window.page_limit_check.setChecked(False)
    assert window._current_page_limit() is None
    assert window.summary_pages.text() == "5 total pages"
