import ntpath
from pathlib import Path


def normalized_windows_path(path: str | Path) -> str:
    """Return a stable, case-insensitive Windows comparison key."""
    return ntpath.normcase(ntpath.normpath(str(Path(path).resolve())))


def ensure_pdf_suffix(path: str | Path) -> Path:
    result = Path(path)
    return (
        result if result.suffix.casefold() == ".pdf" else result.with_suffix(result.suffix + ".pdf")
    )
