from pathlib import Path

root = Path(SPECPATH)
icon_path = root / "assets" / "app.ico"
icon = str(icon_path) if icon_path.exists() else None

a = Analysis(
    [str(root / "run_app.py")],
    pathex=[str(root / "src")],
    binaries=[],
    datas=[
        (str(root / "assets"), "assets"),
        (str(root / "vendor-stage" / "verapdf"), "vendor/verapdf"),
        (str(root / "vendor-stage" / "jre"), "vendor/jre"),
        (str(root / "licenses"), "licenses"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["ghostscript"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PDF-MergeForge-v1.1.0-Windows-x64",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=icon,
)
