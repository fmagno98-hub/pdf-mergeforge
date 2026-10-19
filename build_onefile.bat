@echo off
setlocal
"%~dp0.venv\Scripts\python.exe" -m PyInstaller --clean --noconfirm "%~dp0PDF_MergeForge_onefile.spec"
