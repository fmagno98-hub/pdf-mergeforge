# PDF MergeForge 1.2.0

Released 2026-10-19 for Windows 10/11 x64.

PDF MergeForge 1.2.0 can limit a merged PDF to the first number of pages you choose.
The limit works for both ordinary PDFs and PDF/A-1b exports, while source files stay
unchanged.

## What's new

- Enable **Limit output length** and choose a positive page count.
- See the expected output length before starting the merge.
- Apply the same limit to normal PDF and PDF/A-1b output.
- Keep the selected limit between app sessions.
- Continue to use the app fully offline without uploading documents.

The limit follows the order displayed in the file list. If two PDFs contain two pages each and are
merged with a three-page limit, the output contains both pages from the first PDF and
the first page from the second PDF. A limit greater than the combined length keeps all
pages.

## Download and run

1. Download `PDF-MergeForge-v1.2.0-Windows-x64.exe` from the GitHub Release.
2. Double-click it. No installation is required for normal merging.
3. Add and order PDFs, optionally enable **Limit output length**, then choose the output.
4. Install 64-bit Ghostscript only if you need PDF/A-1b creation.

The executable includes Python, PySide6, pypdf, veraPDF 1.30.2, and Eclipse Temurin
JRE 17. Ghostscript remains external. The unsigned executable may trigger Windows
SmartScreen, and one-file startup can take a few seconds.

## Verification and licensing

The release includes `SHA256SUMS.txt` for the executable and source archive. PDF
MergeForge source code is MIT licensed. veraPDF is MPL 2.0 or later, Eclipse Temurin
is GPLv2 with the Classpath Exception, and Ghostscript uses its own Artifex terms.
See `THIRD_PARTY_NOTICES.md` and `licenses/` for complete notices.

Keep original documents and visually inspect important output. PDF/A conversion can
change rendering or invalidate signatures. The software is provided as-is and is used
at your own risk.
