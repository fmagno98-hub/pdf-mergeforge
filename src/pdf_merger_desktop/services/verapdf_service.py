import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class VeraPdfInstallation:
    executable_path: Path
    version: str


@dataclass(frozen=True, slots=True)
class ExternalValidationResult:
    available: bool
    compliant: bool | None
    validator_version: str = ""
    summary: str = ""
    report_path: Path | None = None


def discover_verapdf(saved_path: str | Path | None = None) -> VeraPdfInstallation | None:
    candidates = [Path(saved_path)] if saved_path else []
    for name in ("verapdf.bat", "verapdf.exe"):
        match = shutil.which(name)
        if match:
            candidates.append(Path(match))
    for path in candidates:
        if not path.is_file() or path.name.casefold() not in {"verapdf.bat", "verapdf.exe"}:
            continue
        try:
            result = subprocess.run(
                [str(path.resolve()), "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
                shell=False,
                creationflags=int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
                if os.name == "nt"
                else 0,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        match = re.search(r"veraPDF\s+([\w.-]+)", result.stdout + result.stderr, re.I)
        if result.returncode == 0 and match:
            return VeraPdfInstallation(path.resolve(), match.group(1))
    return None


def parse_verapdf_report(xml_text: str) -> bool:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise RuntimeError("veraPDF returned a malformed validation report.") from exc
    report = next((node for node in root.iter() if node.tag.endswith("validationReport")), None)
    if report is None or report.get("isCompliant") not in {"true", "false"}:
        raise RuntimeError("veraPDF did not return a PDF/A validation result.")
    return report.get("isCompliant") == "true"


def validate_with_verapdf(
    installation: VeraPdfInstallation | None,
    pdf: Path,
    report_path: Path,
    timeout: float = 120.0,
) -> ExternalValidationResult:
    if installation is None:
        return ExternalValidationResult(False, None, summary="veraPDF is not installed.")
    try:
        result = subprocess.run(
            [str(installation.executable_path), "--format", "xml", "--flavour", "1b", str(pdf)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            shell=False,
            creationflags=int(getattr(subprocess, "CREATE_NO_WINDOW", 0)) if os.name == "nt" else 0,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("veraPDF validation timed out.") from exc
    if result.returncode != 0:
        raise RuntimeError("veraPDF could not validate the generated document.")
    report_path.write_text(result.stdout, encoding="utf-8")
    compliant = parse_verapdf_report(result.stdout)
    return ExternalValidationResult(
        True,
        compliant,
        installation.version,
        "Compliant with PDF/A-1b" if compliant else "Not compliant with PDF/A-1b",
        report_path,
    )
