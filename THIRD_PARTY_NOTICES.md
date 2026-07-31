# Third-party notices

PDF MergeForge bundles open-source components inside its portable executable:

- **PySide6 6.9.1 / Qt for Python** - LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only.
- **pypdf 6.14.2** - BSD-3-Clause license.
- **PyInstaller 6.14.2 bootloader** - GPL license with the PyInstaller bootloader
  exception permitting distribution of bundled applications.

These components remain subject to their respective licenses. Their inclusion does
not change the MIT license covering PDF MergeForge source code or the separate brand
asset terms in `BRAND_LICENSE.md`.

## Ghostscript

PDF MergeForge can optionally invoke a separately installed copy of Ghostscript to
create PDF/A-1b documents. Ghostscript is not included, copied, modified, or
redistributed with PDF MergeForge. It is a separate product distributed under its own
licensing terms, including GNU AGPL and commercial licensing options from Artifex.
The MIT License of PDF MergeForge does not apply to Ghostscript.

- Product: https://ghostscript.com/
- Official downloads: https://ghostscript.com/releases/gsdnld.html
- Licensing: https://ghostscript.com/licensing/

## veraPDF

The single-file candidate bundles veraPDF Greenfield CLI 1.30.2 for independent PDF/A
validation and Eclipse Temurin JRE 17.0.15+6 to run it. These are separate third-party
components and remain subject to their own licences. The MIT
License of PDF MergeForge does not apply to veraPDF.

- Product and downloads: https://software.verapdf.org/
- Documentation: https://docs.verapdf.org/

veraPDF is distributed under MPL 2.0 or later. Eclipse Temurin is distributed under
GPLv2 with the Classpath Exception. Complete notices, source links, the Temurin `legal`
directory, and the relevant licence text are included in `licenses` and in the bundled
runtime. Ghostscript is not bundled.
