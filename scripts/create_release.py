import hashlib
import shutil
from datetime import date
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / "dist" / "PDF-MergeForge-v1.1.0-Windows-x64.exe"
release = root / "github-ready" / "release"
release.mkdir(parents=True, exist_ok=True)
target = release / "PDF-MergeForge-v1.1.0-Windows-x64.exe"
shutil.copy2(source, target)
digest = hashlib.sha256(target.read_bytes()).hexdigest()
(release / "SHA256SUMS.txt").write_text(f"{digest}  {target.name}\n", encoding="utf-8")
(release / "RELEASE_NOTES.md").write_text(
    f"""# PDF MergeForge 1.1.0

Released {date.today().isoformat()} for Windows 10/11 x64.

Portable, completely local PDF merging plus optional PDF/A-1b export. Download only
`{target.name}` and double-click it; no installation, account, subscription, paid
provider, API, cloud upload, or Internet connection is required.

The executable bundles the Python runtime, PySide6, pypdf, application code, and
assets. It also bundles separately licensed veraPDF 1.30.2 and Eclipse Temurin JRE 17
for independent local validation. Ghostscript remains external and is required only to
create PDF/A-1b files. Source PDFs remain on the user's computer and are never transmitted.

Licensing: PDF MergeForge source code is MIT; veraPDF is MPL 2.0+; Eclipse Temurin is
GPLv2 with the Classpath Exception. See THIRD_PARTY_NOTICES.md and the bundled notices.

The software is provided as-is, without warranty, and is used at the user's own risk.
The unsigned executable may trigger Windows SmartScreen, and one-file startup may
take a few seconds.
""",
    encoding="utf-8",
)
