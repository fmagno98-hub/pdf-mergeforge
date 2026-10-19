import shutil
from pathlib import Path

import pytest
from pypdf import PdfWriter

from pdf_merger_desktop.services.ghostscript_service import GhostscriptInstallation
from pdf_merger_desktop.services.pdfa_conversion_service import (
    PdfAConversionError,
    export_pdfa_1b,
)
from pdf_merger_desktop.services.pdfa_validation_service import PdfABaselineValidationResult
from pdf_merger_desktop.services.verapdf_service import ExternalValidationResult


def make_pdf(path: Path) -> Path:
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with path.open("wb") as stream:
        writer.write(stream)
    return path


def fake_installation(tmp_path: Path) -> GhostscriptInstallation:
    root = tmp_path / "gs10.7.1"
    exe = root / "bin" / "gswin64c.exe"
    exe.parent.mkdir(parents=True)
    exe.touch()
    (root / "lib").mkdir()
    (root / "lib" / "PDFA_def.ps").write_text(
        "/ICCProfile (srgb.icc) % Customise\ndef\n", encoding="latin-1"
    )
    (root / "iccprofiles").mkdir()
    (root / "iccprofiles" / "srgb.icc").touch()
    return GhostscriptInstallation(exe, (10, 7, 1), "10.7.1", "test")


def test_export_is_atomic_and_preserves_order(tmp_path: Path, monkeypatch) -> None:
    first = make_pdf(tmp_path / "first.pdf")
    second = make_pdf(tmp_path / "second.pdf")
    destination = tmp_path / "final.pdf"
    destination.write_bytes(b"old")
    install = fake_installation(tmp_path)

    def run(command, cancelled, timeout):
        source = Path(command[-1])
        output = Path(
            next(arg.split("=", 1)[1] for arg in command if arg.startswith("-sOutputFile="))
        )
        shutil.copy2(source, output)
        return 0, "", ""

    monkeypatch.setattr(
        "pdf_merger_desktop.services.pdfa_conversion_service.validate_pdfa_baseline",
        lambda path, pages: PdfABaselineValidationResult(True, ("ok",)),
    )
    monkeypatch.setattr(
        "pdf_merger_desktop.services.pdfa_conversion_service.discover_verapdf", lambda path: None
    )
    monkeypatch.setattr(
        "pdf_merger_desktop.services.pdfa_conversion_service.validate_with_verapdf",
        lambda *args: ExternalValidationResult(False, None),
    )
    result = export_pdfa_1b(
        [first, second], destination, discover_gs=lambda _saved: install, run_process=run
    )
    assert result.pages == 2 and destination.read_bytes() != b"old"
    assert not list(tmp_path.glob(".*-pdfa-*"))


def test_failed_process_preserves_existing_output(tmp_path: Path) -> None:
    source = make_pdf(tmp_path / "source.pdf")
    destination = tmp_path / "final.pdf"
    destination.write_bytes(b"keep")
    install = fake_installation(tmp_path)
    with pytest.raises(PdfAConversionError):
        export_pdfa_1b(
            [source],
            destination,
            discover_gs=lambda _saved: install,
            run_process=lambda *args: (1, "", "conversion failed"),
        )
    assert destination.read_bytes() == b"keep"
