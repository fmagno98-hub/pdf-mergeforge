from pathlib import Path

root = Path(__file__).resolve().parents[1]
forbidden = {"gswin64c.exe", "gsdll64.dll", "pdfa_def.ps"}
folders = [root / "assets", root / "src", root / "dist"] + list(root.glob("dist-candidate-*"))
violations = [
    path
    for folder in folders
    if folder.exists()
    for path in folder.rglob("*")
    if path.is_file() and path.name.casefold() in forbidden
]
if violations:
    raise SystemExit("Forbidden external-tool payloads found:\n" + "\n".join(map(str, violations)))
print("Packaging safeguard passed: Ghostscript remains external.")
required = [
    root / "vendor-stage/verapdf/verapdf.bat",
    root / "vendor-stage/verapdf/bin/cli-1.30.2.jar",
    root / "vendor-stage/jre/bin/java.exe",
    root / "licenses/VERAPDF-NOTICE.txt",
    root / "licenses/TEMURIN-SOURCE-NOTICE.txt",
]
missing = [path for path in required if not path.exists()]
if missing:
    raise SystemExit(
        "Required validator payload or notices missing:\n" + "\n".join(map(str, missing))
    )
print("Bundled validator safeguard passed: veraPDF, Temurin, and notices are present.")
