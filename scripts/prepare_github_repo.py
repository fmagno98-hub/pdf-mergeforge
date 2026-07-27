"""Incrementally synchronize a clean, publishable GitHub repository."""

import hashlib
import shutil
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "github-ready" / "pdf-mergeforge"
IGNORED_DIRECTORIES = {
    ".deps",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tmp",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "github-ready",
    "test-output",
    "test-temp",
    "wheels",
}
IGNORED_FILES = ("*.exe", "*.log", "*.pdf", "*.pyc", "*.tmp", "*.zip")


def digest(path: Path) -> bytes:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.digest()


def is_publishable(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if any(part in IGNORED_DIRECTORIES for part in relative.parts[:-1]):
        return False
    return not any(fnmatch(path.name, pattern) for pattern in IGNORED_FILES)


def synchronize() -> tuple[int, int, int]:
    TARGET.mkdir(parents=True, exist_ok=True)
    desired: set[Path] = set()
    copied = unchanged = 0

    for source in ROOT.rglob("*"):
        if not source.is_file() or not is_publishable(source):
            continue
        relative = source.relative_to(ROOT)
        destination = TARGET / relative
        desired.add(relative)
        if destination.exists() and digest(source) == digest(destination):
            unchanged += 1
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied += 1

    removed = 0
    for destination in TARGET.rglob("*"):
        if destination.is_file() and destination.relative_to(TARGET) not in desired:
            destination.unlink()
            removed += 1
    for directory in sorted(TARGET.rglob("*"), reverse=True):
        if directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()

    return copied, unchanged, removed


if __name__ == "__main__":
    copied, unchanged, removed = synchronize()
    print(
        "GitHub repository synchronized: "
        f"{copied} updated, {unchanged} unchanged, {removed} removed"
    )
