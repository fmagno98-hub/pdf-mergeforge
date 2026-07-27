from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class PdfFileItem:
    path: Path
    normalized_path: str
    name: str
    size_bytes: int
    page_count: int
    is_valid: bool
    error: str = ""
