# PDF MergeForge

![PDF MergeForge](assets/pdf-mergeforge-banner.png)

**Merge PDFs completely on your own computer - no uploads, no subscription, no
provider fees, and no loss of document privacy.**

PDF MergeForge is a fast, portable Windows 10/11 x64 application for ordering,
validating, and safely combining PDF files. It does not need an account, API key,
cloud service, Internet connection, analytics provider, or paid PDF platform.

![PDF MergeForge desktop interface](assets/pdf-mergeforge-app.png)

![PDF MergeForge brand](assets/pdf-mergeforge-brand.png)

## Features

- Add multiple PDFs or drag them into the window.
- Brand-matched dark interface with high-contrast controls and clear empty, active,
  progress, success, error, and disabled states.
- Natural A-Z/Z-A sorting, multi-selection, internal drag reordering, Move up/down.
- PDF structure, page-count, encryption, existence, and duplicate validation.
- Responsive background merge, cooperative cancellation, atomic temporary-file output.
- Open the completed PDF or reveal it in Explorer.
- Local-only settings and technical logs in `%LOCALAPPDATA%\PDF MergeForge\logs`.

## Download

1. Open the latest GitHub Release.
2. Download `PDF-MergeForge-v1.0.0-Windows-x64.exe`.
3. Double-click the downloaded file.
4. No installation is required.

**That single `.exe` is the only file an end user needs.** It already contains the
Python runtime, the GUI toolkit, the PDF engine, and the application assets. Do not
download the source-code ZIP unless you want to inspect or develop the project.

Windows SmartScreen may warn because the executable is not digitally signed. The one-file build can also take a few seconds to start. Windows 10/11 x64 only.

## Development

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python run_app.py
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\ruff check .
```

Build a diagnostic directory with `build_onedir.bat`, then the portable executable with `build_onefile.bat`. `build_release.ps1` runs quality checks, both builds, and prepares the release files.

The source is under `src/pdf_merger_desktop`, tests under `tests`, and packaging scripts/specifications are in the repository root. Cancellation takes effect between source PDFs and immediately before writing; a very large current PDF page sequence may take time to finish.

## Why local PDF merging matters

Many online PDF services require users to upload contracts, forms, reports, personal
records, or other confidential documents to a third-party server. Some add usage
limits, subscriptions, provider fees, advertising, or account requirements.

PDF MergeForge takes a simpler approach:

- Your documents stay on your Windows computer.
- The merge is performed by the `pypdf` library bundled inside the executable.
- No document is uploaded, transmitted, synchronized, or remotely analysed.
- There are no subscriptions, per-document charges, API fees, or usage limits.
- The application remains usable without an Internet connection.

See [PRIVACY.md](PRIVACY.md) for the exact local data flow and storage behaviour.

## Privacy, security, licensing, and responsibility

Source PDFs are opened read-only and are never uploaded or modified. Password-protected PDFs are rejected; the app does not bypass protection. The program has no automatic updater. Report bugs with the GitHub issue template, excluding sensitive PDFs and logs unless reviewed. MIT licensed.

The source code is licensed under the [MIT License](LICENSE), Copyright (c) 2026
Francesco, creator of PDF MergeForge. The official name, logo, icon, banner, and
artwork are separately protected under [BRAND_LICENSE.md](BRAND_LICENSE.md).

The software is provided **as-is, without warranty**. Use it at your own risk. Users
are responsible for backups, selecting the correct files and destination, verifying
the resulting PDF, and complying with applicable laws and document rights. The
legally controlling warranty and liability disclaimer is in `LICENSE`.

Third-party components and their license notices are documented in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
