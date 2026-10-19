# Contributing to PDF MergeForge

Use Python 3.12, create a local virtual environment, and install
`requirements-dev.txt`. Run `pytest` and `ruff check .` before opening a pull request.
Use `build_release.bat` to run the release checks, build both Windows formats,
synchronize the publishable repository, and prepare checksummed release artifacts.

Do not commit personal PDFs, logs, build output, credentials, generated executables,
`vendor-stage`, `.deps`, or downloaded wheels.
