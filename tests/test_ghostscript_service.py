import subprocess
from pathlib import Path

import pytest

from pdf_merger_desktop.services.ghostscript_service import (
    GhostscriptInstallation,
    GhostscriptInvalidInstallationError,
    GhostscriptNotFoundError,
    GhostscriptResources,
    build_pdfa_command,
    discover_ghostscript,
    parse_version,
    validate_executable,
)


def installation(path: Path, version: tuple[int, ...], source: str) -> GhostscriptInstallation:
    return GhostscriptInstallation(path, version, ".".join(map(str, version)), source)


def test_parse_semantic_version() -> None:
    assert parse_version("GPL Ghostscript 10.10.0") == (10, 10, 0)
    assert parse_version("invalid") is None


def test_discovery_prefers_newest_numeric_version(tmp_path: Path) -> None:
    saved = tmp_path / "saved" / "gswin64c.exe"
    path = tmp_path / "path" / "gswin64c.exe"
    saved.parent.mkdir()
    path.parent.mkdir()
    saved.touch()
    path.touch()

    def validator(candidate: Path, source: str) -> GhostscriptInstallation:
        version = (10, 9) if candidate == saved else (10, 10)
        return installation(candidate, version, source)

    result = discover_ghostscript(
        saved, which=lambda _name: str(path), program_files=[], validator=validator
    )
    assert result.version == (10, 10) and result.discovery_source == "PATH"


def test_discovery_ignores_stale_saved_path(tmp_path: Path) -> None:
    good = tmp_path / "gswin64c.exe"
    good.touch()

    def validator(candidate: Path, source: str) -> GhostscriptInstallation:
        if not candidate.exists():
            raise GhostscriptInvalidInstallationError("missing")
        return installation(candidate, (10, 7, 1), source)

    assert (
        discover_ghostscript(
            tmp_path / "gone.exe",
            which=lambda _name: str(good),
            program_files=[],
            validator=validator,
        ).executable_path
        == good
    )


def test_discovery_reports_not_found() -> None:
    with pytest.raises(GhostscriptNotFoundError):
        discover_ghostscript(which=lambda _name: None, program_files=[])


def test_validate_executable_uses_argument_list_and_no_shell(tmp_path: Path) -> None:
    exe = tmp_path / "Unicode à" / "gswin64c.exe"
    exe.parent.mkdir()
    exe.touch()
    captured = {}

    def run(args, **kwargs):
        captured.update(args=args, **kwargs)
        return subprocess.CompletedProcess(args, 0, "10.07.1\n", "")

    result = validate_executable(exe, run=run)
    assert result.version == (10, 7, 1)
    assert captured["args"] == [str(exe.resolve()), "--version"]
    assert captured["shell"] is False


def test_validate_rejects_wrong_name_and_timeout(tmp_path: Path) -> None:
    wrong = tmp_path / "ghost.exe"
    wrong.touch()
    with pytest.raises(GhostscriptInvalidInstallationError):
        validate_executable(wrong)
    exe = tmp_path / "gswin64c.exe"
    exe.touch()
    with pytest.raises(GhostscriptInvalidInstallationError):
        validate_executable(
            exe, run=lambda *a, **k: (_ for _ in ()).throw(subprocess.TimeoutExpired("gs", 1))
        )


def test_command_is_strict_pdfa_argument_list(tmp_path: Path) -> None:
    exe = tmp_path / "Program Files" / "gs" / "bin" / "gswin64c.exe"
    resources = GhostscriptResources(tmp_path / "PDFA_def.ps", tmp_path / "sRGB profile.icc")
    source = tmp_path / "input with spaces.pdf"
    output = tmp_path / "uscita à.pdf"
    command = build_pdfa_command(installation(exe, (10, 7, 1), "test"), resources, source, output)
    assert command[0] == str(exe)
    assert "-dPDFA=1" in command and "-dPDFACompatibilityPolicy=2" in command
    assert "-sDEVICE=pdfwrite" in command and "-dCompatibilityLevel=1.4" in command
    assert str(source) == command[-1] and str(resources.pdfa_definition) == command[-2]
    assert f"-sOutputFile={output}" in command
