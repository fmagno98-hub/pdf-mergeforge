import json
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class VeraPdfError(RuntimeError):
    pass


class VeraPdfInvalidInstallationError(VeraPdfError):
    pass


class VeraPdfReportError(VeraPdfError):
    pass


@dataclass(frozen=True, slots=True)
class VeraPdfInstallation:
    launcher_path: Path
    version: str
    installation_directory: Path
    discovery_source: str

    @property
    def executable_path(self) -> Path:  # backwards-compatible public name
        return self.launcher_path


@dataclass(frozen=True, slots=True)
class ExternalValidationResult:
    available: bool
    compliant: bool | None
    validator_version: str = ""
    summary: str = ""
    report_path: Path | None = None
    validation_executed: bool = False
    profile: str = "PDF/A-1b"
    report_format: str = "json"
    failed_rules: tuple[str, ...] = ()
    parse_errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


def _flags() -> int:
    return int(getattr(subprocess, "CREATE_NO_WINDOW", 0)) if os.name == "nt" else 0


def _cmd_exe() -> str:
    trusted = Path(os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe"))
    if trusted.name.casefold() != "cmd.exe" or not trusted.is_absolute():
        trusted = Path(r"C:\Windows\System32\cmd.exe")
    return str(trusted)


def build_launcher_command(launcher: Path, arguments: Iterable[str]) -> list[str]:
    launcher = launcher.resolve()
    if launcher.suffix.casefold() == ".bat":
        # subprocess receives an argument list and shell=False. cmd.exe is needed only
        # because Windows batch files are scripts, not executable PE files.
        # CALL lets cmd.exe execute a quoted batch path containing spaces without
        # constructing an interpolated command string.
        return [_cmd_exe(), "/d", "/s", "/c", "call", str(launcher), *map(str, arguments)]
    return [str(launcher), *map(str, arguments)]


def _run(command: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        shell=False,
        creationflags=_flags(),
    )


def _version(text: str) -> str | None:
    match = re.search(
        r"veraPDF(?:\s+(?:CLI|version))?\s*[:v-]*\s*(\d+(?:\.\d+)+(?:[-.\w]+)?)", text, re.I
    )
    return match.group(1) if match else None


def validate_launcher(
    candidate: Path, source: str, *, runner: Callable[[list[str], float], Any] = _run
) -> VeraPdfInstallation:
    candidate = candidate.expanduser().resolve()
    if not candidate.is_file() or candidate.name.casefold() not in {"verapdf.bat", "verapdf.exe"}:
        raise VeraPdfInvalidInstallationError("Select the official verapdf.bat launcher.")
    try:
        result = runner(build_launcher_command(candidate, ["--version"]), 10.0)
    except subprocess.TimeoutExpired as exc:
        raise VeraPdfInvalidInstallationError("veraPDF version check timed out.") from exc
    except OSError as exc:
        raise VeraPdfInvalidInstallationError("veraPDF could not be started.") from exc
    version = _version((result.stdout or "") + "\n" + (result.stderr or ""))
    if result.returncode != 0 or not version:
        raise VeraPdfInvalidInstallationError(
            "The selected launcher did not return a valid veraPDF version."
        )
    return VeraPdfInstallation(candidate, version, candidate.parent, source)


def _common_candidates() -> Iterable[Path]:
    roots = [
        os.environ.get("LOCALAPPDATA"),
        os.environ.get("PROGRAMFILES"),
        os.environ.get("PROGRAMFILES(X86)"),
    ]
    for raw in roots:
        if not raw:
            continue
        root = Path(raw)
        for relative in ("veraPDF/verapdf.bat", "veraPDF/verapdf/verapdf.bat"):
            yield root / relative
        if root.exists():
            yield from root.glob("veraPDF*/verapdf.bat")


def discover_verapdf(
    saved_path: str | Path | None = None,
    *,
    validator: Callable[[Path, str], VeraPdfInstallation] = validate_launcher,
    common_candidates: Iterable[Path] | None = None,
) -> VeraPdfInstallation | None:
    candidates: list[tuple[Path, str]] = []
    if saved_path:
        candidates.append((Path(saved_path), "saved setting"))
    match = shutil.which("verapdf.bat")
    if match:
        candidates.append((Path(match), "PATH"))
    for path in common_candidates if common_candidates is not None else _common_candidates():
        candidates.append((path, "common installation folder"))
    seen: set[str] = set()
    for path, source in candidates:
        key = str(path).casefold()
        if key in seen:
            continue
        seen.add(key)
        try:
            return validator(path, source)
        except VeraPdfInvalidInstallationError:
            continue
    return None


def _walk(value: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def parse_verapdf_json(text: str) -> tuple[bool, tuple[str, ...]]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise VeraPdfReportError("veraPDF returned malformed JSON.") from exc
    pairs = list(_walk(data))
    compliance = [
        value
        for key, value in pairs
        if key.casefold() in {"iscompliant", "compliant"} and isinstance(value, bool)
    ]
    jobs = [
        value
        for key, value in pairs
        if key.casefold() in {"jobs", "validationreports"} and isinstance(value, list)
    ]
    if not compliance or (jobs and len(jobs[0]) == 0):
        raise VeraPdfReportError("veraPDF did not return a conclusive validation job.")
    failed: list[str] = []
    for key, value in pairs:
        if key.casefold() in {"ruleid", "specification", "testnumber", "clause"} and isinstance(
            value, str | int
        ):
            failed.append(str(value))
    return all(compliance), tuple(dict.fromkeys(failed))[:10]


def parse_verapdf_report(xml_text: str) -> bool:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise VeraPdfReportError("veraPDF returned malformed XML.") from exc
    reports = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "validationReport"]
    values = [node.get("isCompliant") for node in reports]
    if not values or any(value not in {"true", "false"} for value in values):
        raise VeraPdfReportError("veraPDF did not return a conclusive validation job.")
    return all(value == "true" for value in values)


def validate_with_verapdf(
    installation: VeraPdfInstallation | None,
    pdf: Path,
    report_path: Path,
    timeout: float = 120.0,
    *,
    runner: Callable[[list[str], float], Any] = _run,
) -> ExternalValidationResult:
    if installation is None:
        return ExternalValidationResult(False, None, summary="veraPDF was not detected.")
    pdf = pdf.resolve()
    command = build_launcher_command(
        installation.launcher_path, ["--flavour", "1b", "--format", "json", str(pdf)]
    )
    try:
        result = runner(command, timeout)
    except subprocess.TimeoutExpired as exc:
        raise VeraPdfError("veraPDF validation timed out.") from exc
    except OSError as exc:
        raise VeraPdfError("veraPDF was detected but could not be started.") from exc
    if result.returncode != 0:
        detail = (result.stderr or "").strip().splitlines()
        raise VeraPdfError(
            "veraPDF could not complete validation" + (f": {detail[-1]}" if detail else ".")
        )
    report_path = report_path.with_suffix(".json")
    report_path.write_text(result.stdout, encoding="utf-8")
    try:
        compliant, failed = parse_verapdf_json(result.stdout)
    except VeraPdfReportError as exc:
        return ExternalValidationResult(
            True,
            None,
            installation.version,
            "Validation was inconclusive.",
            report_path,
            True,
            parse_errors=(str(exc),),
        )
    return ExternalValidationResult(
        True,
        compliant,
        installation.version,
        "Compliant with PDF/A-1b" if compliant else "Not compliant with PDF/A-1b",
        report_path,
        True,
        failed_rules=failed,
    )
