import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from pdf_merger_desktop.services.verapdf_service import (
    VeraPdfInstallation,
    VeraPdfInvalidInstallationError,
    VeraPdfReportError,
    build_launcher_command,
    discover_verapdf,
    parse_verapdf_json,
    parse_verapdf_report,
    validate_launcher,
    validate_with_verapdf,
)


def completed(code=0, stdout="veraPDF 1.28.2", stderr=""):
    return SimpleNamespace(returncode=code, stdout=stdout, stderr=stderr)


def launcher(tmp_path: Path, name="verapdf.bat") -> Path:
    path = tmp_path / "vera PDF ü" / name
    path.parent.mkdir()
    path.touch()
    return path


def test_batch_command_uses_cmd_argument_list_and_separate_unicode_pdf(tmp_path: Path) -> None:
    bat = launcher(tmp_path)
    pdf = tmp_path / "dati ü con spazi.pdf"
    command = build_launcher_command(bat, ["--flavour", "1b", "--format", "json", str(pdf)])
    assert command[0].casefold().endswith("cmd.exe")
    assert command[1:4] == ["/d", "/s", "/c"]
    assert command[4] == "call"
    assert command[-1] == str(pdf) and command[-4:-1] == ["1b", "--format", "json"]


def test_validate_launcher_accepts_version_and_records_source(tmp_path: Path) -> None:
    bat = launcher(tmp_path)
    seen = []
    result = validate_launcher(
        bat, "saved setting", runner=lambda command, timeout: seen.append(command) or completed()
    )
    assert result.version == "1.28.2" and result.discovery_source == "saved setting"
    assert result.installation_directory == bat.parent.resolve()
    assert seen[0][-1] == "--version"


@pytest.mark.parametrize("result", [completed(1), completed(stdout="unknown tool")])
def test_validate_launcher_rejects_bad_result(tmp_path: Path, result) -> None:
    with pytest.raises(VeraPdfInvalidInstallationError):
        validate_launcher(launcher(tmp_path), "manual", runner=lambda *_: result)


def test_validate_launcher_reports_timeout(tmp_path: Path) -> None:
    def timeout(*_):
        raise subprocess.TimeoutExpired("verapdf", 10)

    with pytest.raises(VeraPdfInvalidInstallationError, match="timed out"):
        validate_launcher(launcher(tmp_path), "manual", runner=timeout)


def test_discovery_ignores_stale_saved_path_and_uses_common(tmp_path: Path) -> None:
    good = launcher(tmp_path)
    calls = []

    def validator(path, source):
        calls.append((path, source))
        if path != good:
            raise VeraPdfInvalidInstallationError("bad")
        return VeraPdfInstallation(path, "1.28.2", path.parent, source)

    found = discover_verapdf(
        tmp_path / "missing" / "verapdf.bat", validator=validator, common_candidates=[good]
    )
    assert found and found.launcher_path == good
    assert calls[0][1] == "saved setting"


def test_discovery_returns_none_without_installation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("shutil.which", lambda _: None)
    assert discover_verapdf(common_candidates=[], include_bundled=False) is None


@pytest.mark.parametrize("value,expected", [("true", True), ("false", False)])
def test_parse_verapdf_xml_compliance(value: str, expected: bool) -> None:
    xml = f'<report><validationReport isCompliant="{value}"/></report>'
    assert parse_verapdf_report(xml) is expected


@pytest.mark.parametrize("xml", ["not xml", "<report/>", '<validationReport isCompliant="maybe"/>'])
def test_parse_verapdf_rejects_malformed_xml(xml: str) -> None:
    with pytest.raises(VeraPdfReportError):
        parse_verapdf_report(xml)


def test_parse_json_compliant_and_noncompliant_rules() -> None:
    assert parse_verapdf_json(json.dumps({"jobs": [{"validationReport": {"isCompliant": True}}]}))[
        0
    ]
    compliant, rules = parse_verapdf_json(
        json.dumps(
            {
                "jobs": [
                    {"validationReport": {"isCompliant": False, "details": [{"ruleId": "6.2.2"}]}}
                ]
            }
        )
    )
    assert not compliant and rules == ("6.2.2",)


@pytest.mark.parametrize("text", ["", "not-json", "{}", '{"jobs": []}'])
def test_parse_json_rejects_inconclusive_reports(text: str) -> None:
    with pytest.raises(VeraPdfReportError):
        parse_verapdf_json(text)


def test_validation_uses_profile_json_local_path_and_parses_report(tmp_path: Path) -> None:
    bat = launcher(tmp_path)
    pdf = tmp_path / "local only ü.pdf"
    pdf.touch()
    install = VeraPdfInstallation(bat, "1.28.2", bat.parent, "test")
    report = json.dumps({"jobs": [{"validationReport": {"isCompliant": True}}]})
    seen = []
    result = validate_with_verapdf(
        install,
        pdf,
        tmp_path / "report.json",
        runner=lambda command, timeout: seen.append(command) or completed(stdout=report),
    )
    assert result.validation_executed and result.compliant
    assert seen[0][-5:] == ["--flavour", "1b", "--format", "json", str(pdf.resolve())]
    assert result.report_path and result.report_path.read_text(encoding="utf-8") == report


def test_validation_absent_is_not_an_error(tmp_path: Path) -> None:
    result = validate_with_verapdf(None, tmp_path / "x.pdf", tmp_path / "report.json")
    assert not result.available and not result.validation_executed and result.compliant is None
