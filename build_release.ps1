$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
& $python -m pytest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python -m ruff check .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python (Join-Path $root "scripts\check_external_tools_not_bundled.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& (Join-Path $root "build_onedir.bat")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& (Join-Path $root "build_onefile.bat")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python (Join-Path $root "scripts\prepare_github_repo.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python (Join-Path $root "scripts\create_release.py")
exit $LASTEXITCODE
