from pathlib import Path

FORBIDDEN = {"gswin64c.exe", "gsdll64.dll", "pdfa_def.ps", "verapdf.jar", "java.exe"}


def test_repository_bundles_no_external_tool_payloads() -> None:
    root = Path(__file__).resolve().parents[1]
    checked = [root / "assets", root / "src"]
    violations = [
        str(path.relative_to(root))
        for folder in checked
        for path in folder.rglob("*")
        if path.is_file() and path.name.casefold() in FORBIDDEN
    ]
    assert not violations


def test_pyinstaller_specs_have_no_external_tool_binaries() -> None:
    root = Path(__file__).resolve().parents[1]
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.spec")).casefold()
    assert "gswin64c.exe" not in text and "gsdll64.dll" not in text
    assert "verapdf.jar" not in text and "java.exe" not in text
