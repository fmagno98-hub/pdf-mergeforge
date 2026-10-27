# Licensing and distribution

PDF MergeForge is a larger distribution containing separately licensed components.
The repository name remains `pdf-mergeforge`, and its own Python source code remains
available under the MIT License.

## PDF MergeForge

- Code: `src/pdf_merger_desktop`, build scripts, and tests.
- Licence: MIT, as stated in the root `LICENSE`.
- Warranty: provided as-is, without warranty; use is at the user's own risk.

The MIT licence does not replace or override third-party licences.

## pypdf

pypdf performs ordinary local merging and PDF structure access. It is installed as a
Python dependency and packaged by PyInstaller. Its upstream licence and notices remain
controlling for pypdf.

Source: https://github.com/py-pdf/pypdf

## Ghostscript

Ghostscript performs PDF/A-1b conversion. It is **not** copied into the repository,
onedir package, or onefile EXE. Users install 64-bit Ghostscript separately and accept
the applicable Artifex AGPL or commercial terms. PDF MergeForge only discovers and
invokes the local `gswin64c.exe` process.

Download and licensing: https://ghostscript.com/releases/gsdnld.html

## veraPDF

The Windows release bundles the unmodified veraPDF Greenfield CLI 1.30.2 as a separate
component under the Mozilla Public License 2.0 or later. It validates the Ghostscript
output against PDF/A-1b using a structured JSON report. PDF MergeForge does not claim
ownership of or relicense veraPDF under MIT.

- Binary source: official veraPDF 1.30.2 installer.
- Downloads: https://software.verapdf.org/rel/1.30/
- Application source: https://github.com/veraPDF/veraPDF-apps
- Library source: https://github.com/veraPDF/veraPDF-library
- Validation profiles: https://github.com/veraPDF/veraPDF-validation-profiles
- Licence text: `licenses/MPL-2.0.txt`
- Notice: `licenses/VERAPDF-NOTICE.txt`

## Eclipse Temurin

veraPDF runs through the bundled unmodified Eclipse Temurin JRE 17.0.15+6. Temurin is
a separate component under GPL version 2 with the Classpath Exception. Its complete
runtime `legal` directory is incorporated into the Windows binary payload.

- Runtime source: https://github.com/adoptium/jdk17u.git
- Build source: https://github.com/adoptium/temurin-build.git
- Notices: `licenses/TEMURIN-NOTICE.txt` and `licenses/TEMURIN-SOURCE-NOTICE.txt`

## Local processing

pypdf, Ghostscript, and veraPDF receive local filesystem paths. PDF MergeForge does
not upload documents, validation reports, or filenames to the projects above or to any
other server. Download links open only after an explicit user action.

This document is a technical description of the distribution, not legal advice.
