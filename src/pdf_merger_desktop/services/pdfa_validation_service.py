import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


class PdfAValidationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PdfABaselineValidationResult:
    passed: bool
    checks: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


def validate_pdfa_baseline(path: Path, expected_pages: int) -> PdfABaselineValidationResult:
    checks: list[str] = []
    errors: list[str] = []
    try:
        if not path.is_file() or path.stat().st_size == 0:
            raise PdfAValidationError("The PDF/A output is missing or empty.")
        header = path.read_bytes()[:8]
        match = re.match(rb"%PDF-(\d)\.(\d)", header)
        if not match or tuple(map(int, match.groups())) > (1, 4):
            errors.append("The PDF header is not compatible with PDF/A-1.")
        else:
            checks.append("PDF version is 1.4 or earlier")
        reader = PdfReader(path, strict=False)
        if reader.is_encrypted:
            errors.append("PDF/A documents must not be encrypted.")
        else:
            checks.append("Document is not encrypted")
        if len(reader.pages) != expected_pages:
            errors.append("The PDF/A page count does not match the merged source.")
        else:
            checks.append("Page count matches")
        root = reader.trailer.get("/Root")
        if root is None:
            errors.append("The PDF catalog is missing.")
            metadata = None
            intents = None
        else:
            root = root.get_object()
            metadata = root.get("/Metadata")
            intents = root.get("/OutputIntents")
        if not intents:
            errors.append("A PDF/A OutputIntent is missing.")
        else:
            checks.append("OutputIntent is present")
        xmp = metadata.get_object().get_data().decode("utf-8", errors="replace") if metadata else ""
        if not xmp:
            errors.append("XMP metadata is missing.")
        else:
            part = re.search(r"(?:pdfaid:part[^>]*>|pdfaid:part=['\"])(\s*1)", xmp, re.I)
            conformance = re.search(
                r"(?:pdfaid:conformance[^>]*>|pdfaid:conformance=['\"])(\s*B)", xmp, re.I
            )
            if not part:
                errors.append("XMP does not declare PDF/A part 1.")
            else:
                checks.append("XMP declares PDF/A part 1")
            if not conformance:
                errors.append("XMP does not declare conformance level B.")
            else:
                checks.append("XMP declares conformance level B")
    except PdfAValidationError:
        raise
    except Exception as exc:
        raise PdfAValidationError("The generated PDF/A could not be read.") from exc
    return PdfABaselineValidationResult(not errors, tuple(checks), errors=tuple(errors))
