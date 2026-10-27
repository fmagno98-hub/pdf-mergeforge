# Changelog

## 1.3.0 - 2026-10-26

### Added

- Added a **Convert to Word** button and `Ctrl+W` shortcut.
- Added local PDF-to-DOCX extraction of selectable text and embedded images. Conversion no longer launches Microsoft Word or rasterizes entire pages.
- Added a layout-text option that keeps extracted text editable while approximating its original spacing.
- Converted common PDF bullet and numbered markers to native Word lists and applied embedded font metadata to extracted text.
- Added page progress, cancellation, and atomic output for Word conversion.
- Documents without a text layer are clearly marked instead of being uploaded or processed online.

### Licensing

- Kept PDF MergeForge source code under MIT.
- Kept the MIT source license and avoided adding copyleft dependencies; the converter uses pypdf and the Python standard library.
## 1.2.0 - 2026-10-19

### Added

- You can now limit normal and PDF/A output to the first selected number of pages.
  Enable **Limit output length**, choose the page count, and merge as usual. The live
  summary shows the resulting length, the preference is remembered, and source PDFs
  remain unchanged.

### Changed

- Release metadata, packaging names, security support information, privacy details,
  and GitHub release documentation now target version 1.2.0.

## 1.1.0 - local release candidate

### Added

- PDF/A-1b export using a separately installed Ghostscript executable.
- Ghostscript discovery, validation, manual selection, and missing-dependency guidance.
- Strict external conversion, deterministic cleanup, cancellation, and atomic output.
- PDF/A baseline validation for version, encryption, page count, XMP, and OutputIntent.
- Optional independent veraPDF PDF/A-1b validation.
- Windows-aware veraPDF discovery, safe `verapdf.bat` execution, structured JSON report
  parsing, explicit validation states, External tools controls, and Validate now.
- Single-file candidate bundling veraPDF Greenfield CLI 1.30.2 and Eclipse Temurin JRE
  17.0.15+6 with licence notices and automatic local discovery; Ghostscript stays external.
- PDF/A documentation, troubleshooting, and packaging safeguards.

### Changed

- Prepared local application and build metadata for version 1.1.0.
- Updated bundled pypdf declaration to 6.14.2.

### Fixed

- Allow the detected external sRGB profile through modern Ghostscript `SAFER` rules and
  create an ephemeral PDF/A definition with its absolute path, ensuring that the
  generated PDF/A-1b contains a real OutputIntent.

## 1.0.0 - 2026-07-27

- Branded release of PDF MergeForge with application icon, in-app logo, repository artwork,
  safe PDF merging, reordering, validation, cancellation, and portable packaging.
- Redesigned the complete desktop interface around the navy, cyan, and forge-orange brand
  system, with stronger hierarchy, accessibility, trust indicators, and responsive cards.
