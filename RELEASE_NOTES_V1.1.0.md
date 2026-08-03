# PDF MergeForge 1.1.0

PDF MergeForge 1.1.0 adds completely local PDF/A-1b creation and independent
validation while keeping ordinary PDF merging simple and offline.

## For users

1. Download `PDF-MergeForge-v1.1.0-Windows-x64.exe` from the GitHub Release.
2. Double-click it; no installation is required for normal PDF merging.
3. To create PDF/A-1b, install 64-bit Ghostscript from its official website. PDF
   MergeForge detects it automatically or lets you locate `gswin64c.exe`.
4. veraPDF 1.30.2 and Eclipse Temurin JRE 17 are already incorporated in the EXE.
   No separate Java or veraPDF installation is needed.

PDF/A processing remains local: pypdf merges, the separately installed Ghostscript
creates PDF/A-1b, baseline checks inspect the result, and bundled veraPDF validates it
against profile `1b`. No PDF or validation report is uploaded.

One possible use case is preparing a combined archival document before submitting it
through an official Agenzia delle Entrate workflow. Technical PDF/A-1b conformance does
not guarantee acceptance: users must follow the current rules of the specific service,
including any signature, size, naming, or profile requirements.

## Licensing

- PDF MergeForge source code: MIT License.
- veraPDF 1.30.2: Mozilla Public License 2.0 or later.
- Eclipse Temurin JRE 17: GPLv2 with the Classpath Exception.
- Ghostscript: not included; its separate installation is governed by Artifex terms.

See `THIRD_PARTY_NOTICES.md` and `licenses/` for notices and source links. PDF/A
conversion can alter rendering and invalidate signatures; keep original documents and
verify important output. The software is provided as-is and used at your own risk.
