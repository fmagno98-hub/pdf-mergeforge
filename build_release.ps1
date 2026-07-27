$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
& $python -m pytest
& $python -m ruff check .
& (Join-Path $root "build_onedir.bat")
& (Join-Path $root "build_onefile.bat")
& $python (Join-Path $root "scripts\create_release.py")
