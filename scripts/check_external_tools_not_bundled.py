from pathlib import Path

root = Path(__file__).resolve().parents[1]
forbidden = {"gswin64c.exe", "gsdll64.dll", "pdfa_def.ps", "verapdf.jar", "java.exe"}
folders = [root / "assets", root / "src", root / "dist", root / "dist-candidate-v1.1.0"]
violations = [
    path
    for folder in folders
    if folder.exists()
    for path in folder.rglob("*")
    if path.is_file() and path.name.casefold() in forbidden
]
if violations:
    raise SystemExit("Forbidden external-tool payloads found:\n" + "\n".join(map(str, violations)))
print("Packaging safeguard passed: no Ghostscript, veraPDF, or Java payloads bundled.")
