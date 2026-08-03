import os
import uuid
from collections.abc import Callable, Sequence
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from .file_item import PdfFileItem
from .utilities.paths import ensure_pdf_suffix, normalized_windows_path


class PdfValidationError(ValueError):
    pass


class MergeCancelled(RuntimeError):
    pass


def validate_pdf(path: str | Path) -> PdfFileItem:
    source = Path(path).resolve()
    key = normalized_windows_path(source)
    try:
        if source.suffix.casefold() != ".pdf":
            raise PdfValidationError("The file extension is not .pdf")
        if not source.is_file():
            raise PdfValidationError("File not found")
        if source.stat().st_size == 0:
            raise PdfValidationError("The file is empty")
        with source.open("rb") as stream:
            if stream.read(5) != b"%PDF-":
                raise PdfValidationError("The file is not a PDF")
            stream.seek(0)
            reader = PdfReader(stream, strict=False)
            if reader.is_encrypted:
                raise PdfValidationError("Password-protected PDFs are not supported")
            pages = len(reader.pages)
            if pages < 1:
                raise PdfValidationError("The PDF has no pages")
        return PdfFileItem(source, key, source.name, source.stat().st_size, pages, True)
    except (OSError, PdfValidationError, Exception) as exc:
        # pypdf exposes several version-specific exception classes; all are converted
        # to a user-safe model here and logged by the GUI boundary.
        return PdfFileItem(
            source,
            key,
            source.name,
            source.stat().st_size if source.is_file() else 0,
            0,
            False,
            str(exc),
        )


def validate_sources(paths: Sequence[Path], output: Path) -> list[PdfFileItem]:
    output_key = normalized_windows_path(output)
    items = [validate_pdf(path) for path in paths]
    if any(normalized_windows_path(path) == output_key for path in paths):
        raise PdfValidationError("The output cannot overwrite a source PDF")
    invalid = [item for item in items if not item.is_valid]
    if invalid:
        raise PdfValidationError(f"{invalid[0].name}: {invalid[0].error}")
    return items


def merge_pdfs(
    paths: Sequence[str | Path],
    output: str | Path,
    progress: Callable[[int, int, str], None] | None = None,
    cancelled: Callable[[], bool] | None = None,
) -> tuple[Path, int]:
    sources = [Path(path).resolve() for path in paths]
    destination = ensure_pdf_suffix(Path(output).resolve())
    destination.parent.mkdir(parents=True, exist_ok=True)
    items = validate_sources(sources, destination)
    temporary = destination.parent / f".{destination.stem}-{uuid.uuid4().hex}.tmp"
    with temporary.open("xb"):
        pass
    total_pages = 0
    try:
        writer = PdfWriter()
        for index, (source, item) in enumerate(zip(sources, items, strict=True), 1):
            if cancelled and cancelled():
                raise MergeCancelled("Operation cancelled")
            if progress:
                progress(index, len(sources), item.name)
            reader = PdfReader(source, strict=False)
            for page in reader.pages:
                writer.add_page(page)
                total_pages += 1
        if cancelled and cancelled():
            raise MergeCancelled("Operation cancelled")
        with temporary.open("wb") as stream:
            writer.write(stream)
            stream.flush()
            os.fsync(stream.fileno())
        if temporary.stat().st_size == 0 or len(PdfReader(temporary).pages) != total_pages:
            raise PdfValidationError("The temporary output could not be verified")
        os.replace(temporary, destination)
        return destination, total_pages
    finally:
        temporary.unlink(missing_ok=True)
