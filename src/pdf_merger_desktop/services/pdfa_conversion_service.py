import os
import shutil
import subprocess
import time
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from ..pdf_service import MergeCancelled, merge_pdfs
from .ghostscript_service import (
    GhostscriptInstallation,
    build_pdfa_command,
    discover_ghostscript,
    locate_pdfa_resources,
    prepare_pdfa_definition,
)
from .pdfa_validation_service import PdfABaselineValidationResult, validate_pdfa_baseline
from .verapdf_service import ExternalValidationResult, discover_verapdf, validate_with_verapdf


class PdfAConversionError(RuntimeError):
    pass


class PdfAConversionCancelled(MergeCancelled):
    pass


@dataclass(frozen=True, slots=True)
class PdfAConversionResult:
    output_path: Path
    pages: int
    ghostscript: GhostscriptInstallation
    baseline: PdfABaselineValidationResult
    external: ExternalValidationResult
    warnings: tuple[str, ...]


def _creation_flags() -> int:
    return int(getattr(subprocess, "CREATE_NO_WINDOW", 0)) if os.name == "nt" else 0


def _run_process(
    command: list[str],
    cancelled: Callable[[], bool],
    timeout: float,
    popen: Callable[..., subprocess.Popen[str]] = subprocess.Popen,
) -> tuple[int, str, str]:
    process = popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=False,
        creationflags=_creation_flags(),
    )
    started = time.monotonic()
    while process.poll() is None:
        if cancelled():
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
            raise PdfAConversionCancelled("PDF/A export was cancelled.")
        if time.monotonic() - started > timeout:
            process.kill()
            process.wait()
            raise PdfAConversionError("Ghostscript conversion timed out.")
        time.sleep(0.05)
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr


def export_pdfa_1b(
    paths: Sequence[Path],
    destination: Path,
    *,
    saved_ghostscript: str | Path | None = None,
    saved_verapdf: str | Path | None = None,
    progress: Callable[[str], None] | None = None,
    cancelled: Callable[[], bool] = lambda: False,
    discover_gs: Callable[..., GhostscriptInstallation] = discover_ghostscript,
    run_process: Callable[
        [list[str], Callable[[], bool], float], tuple[int, str, str]
    ] = _run_process,
) -> PdfAConversionResult:
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if progress:
        progress("Validating and merging input PDFs")
    work = destination.parent / f".{destination.stem}-pdfa-{uuid.uuid4().hex}"
    # On Windows the directory inherits the destination folder's user ACL; an
    # unpredictable name prevents collisions without applying POSIX-only modes.
    work.mkdir()
    try:
        merged, pages = merge_pdfs(paths, work / "merged.pdf", cancelled=cancelled)
        if cancelled():
            raise PdfAConversionCancelled("PDF/A export was cancelled.")
        if progress:
            progress("Detecting Ghostscript")
        ghostscript = discover_gs(saved_ghostscript)
        resources = prepare_pdfa_definition(locate_pdfa_resources(ghostscript), work)
        candidate = work / "candidate-pdfa-1b.pdf"
        command = build_pdfa_command(ghostscript, resources, merged, candidate)
        if progress:
            progress("Converting to PDF/A-1b")
        code, _stdout, stderr = run_process(command, cancelled, 300.0)
        if code != 0:
            detail = stderr.strip().splitlines()[-1] if stderr.strip() else "unknown error"
            raise PdfAConversionError(f"Ghostscript conversion failed: {detail}")
        if not candidate.is_file() or candidate.stat().st_size == 0:
            raise PdfAConversionError("Ghostscript did not create a usable PDF/A output.")
        if progress:
            progress("Checking generated document")
        baseline = validate_pdfa_baseline(candidate, pages)
        if not baseline.passed:
            raise PdfAConversionError("PDF/A baseline checks failed: " + "; ".join(baseline.errors))
        if progress:
            progress("Validating with veraPDF")
        external = validate_with_verapdf(
            discover_verapdf(saved_verapdf), candidate, work / "verapdf-report.json"
        )
        if external.available and external.compliant is None:
            raise PdfAConversionError(
                "veraPDF validation was inconclusive: "
                + "; ".join(external.parse_errors or ("the structured report was invalid",))
            )
        if external.available and external.compliant is False:
            raise PdfAConversionError(
                "veraPDF reported that the document is not PDF/A-1b compliant."
                + (
                    " Failed rules: " + ", ".join(external.failed_rules[:5])
                    if external.failed_rules
                    else ""
                )
            )
        if cancelled():
            raise PdfAConversionCancelled("PDF/A export was cancelled.")
        if progress:
            progress("Finalising output")
        os.replace(candidate, destination)
        warnings = (
            ()
            if external.available
            else (
                "Baseline checks passed, but the document was not independently "
                "validated with veraPDF.",
            )
        )
        return PdfAConversionResult(destination, pages, ghostscript, baseline, external, warnings)
    finally:
        shutil.rmtree(work, ignore_errors=True)
