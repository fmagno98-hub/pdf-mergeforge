"""Prepare a versioned Windows release binary and its SHA-256 checksum."""

import hashlib
import shutil
from pathlib import Path

VERSION = "1.3.0"
root = Path(__file__).resolve().parents[1]
release = root / "release" / f"v{VERSION}"
release.mkdir(parents=True, exist_ok=True)
source = root / "dist" / f"PDF-MergeForge-v{VERSION}-Windows-x64.exe"
target = release / source.name
shutil.copy2(source, target)
notes_source = root / f"RELEASE_NOTES_V{VERSION}.md"
shutil.copy2(notes_source, release / notes_source.name)
checksum = hashlib.sha256(target.read_bytes()).hexdigest()
(release / "SHA256SUMS.txt").write_text(
    f"{checksum}  {target.name}\n", encoding="utf-8"
)
print(f"Release prepared at {release}")
