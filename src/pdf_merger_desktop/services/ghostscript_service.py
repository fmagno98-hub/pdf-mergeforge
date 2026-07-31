import os
import re
import shutil
import subprocess
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path


class GhostscriptError(RuntimeError):
    """Base class for user-safe Ghostscript failures."""


class GhostscriptNotFoundError(GhostscriptError):
    pass


class GhostscriptInvalidInstallationError(GhostscriptError):
    pass


class GhostscriptResourceError(GhostscriptError):
    pass


@dataclass(frozen=True, slots=True)
class GhostscriptInstallation:
    executable_path: Path
    version: tuple[int, ...]
    version_text: str
    discovery_source: str

    @property
    def root(self) -> Path:
        return self.executable_path.parent.parent


@dataclass(frozen=True, slots=True)
class GhostscriptResources:
    pdfa_definition: Path
    rgb_profile: Path


def _creation_flags() -> int:
    return int(getattr(subprocess, "CREATE_NO_WINDOW", 0)) if os.name == "nt" else 0


def parse_version(value: str) -> tuple[int, ...] | None:
    match = re.search(r"(?<!\d)(\d+(?:\.\d+)+)(?!\d)", value)
    return tuple(int(part) for part in match.group(1).split(".")) if match else None


def validate_executable(
    path: Path,
    source: str = "manual",
    *,
    run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    timeout: float = 5.0,
) -> GhostscriptInstallation:
    candidate = path.expanduser().resolve()
    if candidate.name.casefold() != "gswin64c.exe" or not candidate.is_file():
        raise GhostscriptInvalidInstallationError("Select the 64-bit gswin64c.exe executable.")
    try:
        result = run(
            [str(candidate), "--version"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            shell=False,
            creationflags=_creation_flags(),
        )
    except subprocess.TimeoutExpired as exc:
        raise GhostscriptInvalidInstallationError("Ghostscript version check timed out.") from exc
    except OSError as exc:
        raise GhostscriptInvalidInstallationError("Ghostscript could not be started.") from exc
    version_text = f"{result.stdout}\n{result.stderr}".strip()
    version = parse_version(version_text)
    if result.returncode != 0 or version is None:
        raise GhostscriptInvalidInstallationError("Ghostscript returned an invalid version.")
    return GhostscriptInstallation(candidate, version, ".".join(map(str, version)), source)


def _program_files_candidates(roots: Iterable[Path]) -> list[Path]:
    found: list[Path] = []
    for root in roots:
        gs_root = root / "gs"
        if gs_root.is_dir():
            found.extend(gs_root.glob("gs*/bin/gswin64c.exe"))
    return found


def discover_ghostscript(
    saved_path: str | Path | None = None,
    *,
    which: Callable[[str], str | None] = shutil.which,
    program_files: Iterable[Path] | None = None,
    validator: Callable[[Path, str], GhostscriptInstallation] = validate_executable,
) -> GhostscriptInstallation:
    candidates: list[tuple[Path, str]] = []
    if saved_path:
        candidates.append((Path(saved_path), "saved setting"))
    path_match = which("gswin64c.exe")
    if path_match:
        candidates.append((Path(path_match), "PATH"))
    default_roots = filter(
        None,
        map(
            lambda value: Path(value) if value else None,
            (os.getenv("PROGRAMFILES"), os.getenv("PROGRAMW6432")),
        ),
    )
    roots = list(default_roots if program_files is None else program_files)
    candidates.extend((path, "Program Files") for path in _program_files_candidates(roots))
    valid: list[GhostscriptInstallation] = []
    seen: set[str] = set()
    for path, source in candidates:
        key = str(path).casefold()
        if key in seen:
            continue
        seen.add(key)
        try:
            valid.append(validator(path, source))
        except GhostscriptInvalidInstallationError:
            continue
    if not valid:
        raise GhostscriptNotFoundError("A separate 64-bit Ghostscript installation was not found.")
    return max(valid, key=lambda item: item.version)


def locate_pdfa_resources(installation: GhostscriptInstallation) -> GhostscriptResources:
    root = installation.root
    definitions = [root / "lib" / "PDFA_def.ps", root / "Resource" / "Init" / "PDFA_def.ps"]
    profiles = [
        root / "iccprofiles" / "srgb.icc",
        root / "iccprofiles" / "default_rgb.icc",
        root / "Resource" / "ColorSpace" / "srgb.icc",
        root / "lib" / "srgb.icc",
    ]
    definition = next((path for path in definitions if path.is_file()), None)
    profile = next((path for path in profiles if path.is_file()), None)
    if not definition or not profile:
        raise GhostscriptResourceError(
            "Ghostscript was detected, but the required PDF/A resources could not be located."
        )
    return GhostscriptResources(definition, profile)


def prepare_pdfa_definition(
    resources: GhostscriptResources, work_directory: Path
) -> GhostscriptResources:
    """Create an ephemeral definition that points at the external ICC profile.

    Ghostscript's installed sample normally refers to ``srgb.icc`` by a relative
    name. Under modern ``SAFER`` rules that lookup can fail even when an include
    directory is supplied. The runtime copy is never distributed and is deleted
    with the conversion workspace.
    """
    try:
        definition = resources.pdfa_definition.read_text(encoding="latin-1")
    except OSError as exc:
        raise GhostscriptResourceError("The Ghostscript PDF/A definition is not readable.") from exc
    profile = resources.rgb_profile.as_posix().replace("(", r"\(").replace(")", r"\)")
    patched, replacements = re.subn(
        r"/ICCProfile\s*\([^)]*\)\s*(?:%[^\r\n]*)?\s*def",
        f"/ICCProfile ({profile}) def",
        definition,
        count=1,
    )
    if replacements != 1:
        raise GhostscriptResourceError(
            "The installed Ghostscript PDF/A definition has an unsupported format."
        )
    runtime_definition = work_directory / "PDFA_def-runtime.ps"
    runtime_definition.write_text(patched, encoding="latin-1")
    return GhostscriptResources(runtime_definition, resources.rgb_profile)


def build_pdfa_command(
    installation: GhostscriptInstallation,
    resources: GhostscriptResources,
    source_pdf: Path,
    output_pdf: Path,
) -> list[str]:
    return [
        str(installation.executable_path),
        "-dPDFA=1",
        "-dPDFACompatibilityPolicy=2",
        "-dBATCH",
        "-dNOPAUSE",
        "-dSAFER",
        f"--permit-file-read={resources.rgb_profile}",
        "-dCompatibilityLevel=1.4",
        "-sDEVICE=pdfwrite",
        "-sColorConversionStrategy=RGB",
        "-dProcessColorModel=/DeviceRGB",
        "-dEmbedAllFonts=true",
        "-dSubsetFonts=true",
        f"-I{resources.rgb_profile.parent}",
        f"-sOutputICCProfile={resources.rgb_profile}",
        f"-sOutputFile={output_pdf}",
        str(resources.pdfa_definition),
        str(source_pdf),
    ]
