import hashlib
import shutil
from pathlib import Path

VERSION = "1.2.0"
root = Path(__file__).resolve().parents[1]
source = root / "dist" / f"PDF-MergeForge-v{VERSION}-Windows-x64.exe"
release = root.parent / "release" / f"v{VERSION}"
release.mkdir(parents=True, exist_ok=True)
target = release / source.name
shutil.copy2(source, target)
notes_source = root / f"RELEASE_NOTES_V{VERSION}.md"
shutil.copy2(notes_source, release / notes_source.name)

repository_source = root / "github-ready" / "pdf-mergeforge"
source_archive = Path(
    shutil.make_archive(
        str(release / f"PDF-MergeForge-v{VERSION}-source"),
        "zip",
        root_dir=repository_source.parent,
        base_dir=repository_source.name,
    )
)

artifacts = (target, source_archive)
checksums = "".join(
    f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in artifacts
)
(release / "SHA256SUMS.txt").write_text(checksums, encoding="utf-8")
print(f"Release prepared at {release}")
