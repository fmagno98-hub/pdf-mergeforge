# Changelog

## 1.1.0 - local release candidate

### Added

- PDF/A-1b export using a separately installed Ghostscript executable.
- Ghostscript discovery, validation, manual selection, and missing-dependency guidance.
- Strict external conversion, deterministic cleanup, cancellation, and atomic output.
- PDF/A baseline validation for version, encryption, page count, XMP, and OutputIntent.
- Optional independent veraPDF PDF/A-1b validation.
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
