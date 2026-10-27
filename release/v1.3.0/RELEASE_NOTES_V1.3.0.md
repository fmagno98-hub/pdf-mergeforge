# PDF MergeForge 1.3.0

Build refreshed 2026-10-27 for Windows 10/11 x64.

## What is new

- Added **Convert to Word** for one or more ordered PDF files.
- The conversion is fully local and works without accounts, APIs, uploads, online services, Microsoft Word automation, or Ghostscript.
- Extracted text is written to an editable `.docx`; common bullets and numbering become native Word lists.
- Embedded TrueType font metadata is used to match the dominant font family, weight, and size. Images keep their proportions; whole pages are never inserted as images.
- Scanned pages without a text layer are marked clearly because OCR is not bundled.
- Added progress reporting, cancellation, atomic output, and the `Ctrl+W` shortcut.

## Download and run

Download `PDF-MergeForge-v1.3.0-Windows-x64.exe` from the GitHub Release and double-click it. No installation is required. Ghostscript remains external and is only needed for PDF/A-1b export.

## Licensing

PDF MergeForge source code remains MIT licensed. The PDF-to-Word implementation uses the Python standard library and pypdf; pypdf remains BSD-3-Clause. No additional conversion engine or copyleft dependency was added. See `THIRD_PARTY_NOTICES.md` for bundled component terms.

The executable is unsigned, so Windows SmartScreen may show a warning. Keep original documents and inspect important output, especially PDFs with complex layouts or scans.
