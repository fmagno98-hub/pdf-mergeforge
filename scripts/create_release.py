import hashlib
import shutil
from datetime import date
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / "dist" / "PDF MergeForge.exe"
release = root / "github-ready" / "release"
release.mkdir(parents=True, exist_ok=True)
target = release / "PDF-MergeForge-v1.0.0-Windows-x64.exe"
shutil.copy2(source, target)
digest = hashlib.sha256(target.read_bytes()).hexdigest()
(release / "SHA256SUMS.txt").write_text(f"{digest}  {target.name}\n", encoding="utf-8")
(release / "RELEASE_NOTES.md").write_text(
    f"""# PDF MergeForge 1.0.0

Released {date.today().isoformat()} for Windows 10/11 x64.

Portable, completely local PDF merging with drag and drop, ordering, validation,
safe output, progress, cancellation, and Explorer integration. Download only
`{target.name}` and double-click it; no installation, account, subscription, paid
provider, API, cloud upload, or Internet connection is required.

The executable bundles the Python runtime, PySide6, pypdf, application code, and
assets. Source PDFs remain on the user's computer and are never transmitted.

The software is provided as-is, without warranty, and is used at the user's own risk.
The unsigned executable may trigger Windows SmartScreen, and one-file startup may
take a few seconds.
""",
    encoding="utf-8",
)
