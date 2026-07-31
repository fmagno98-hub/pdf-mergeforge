from pathlib import Path

FORBIDDEN = {"gswin64c.exe", "gsdll64.dll", "pdfa_def.ps"}


def test_repository_bundles_no_ghostscript_payloads() -> None:
    root = Path(__file__).resolve().parents[1]
    checked = [root / "assets", root / "src"]
    violations = [
        str(path.relative_to(root))
        for folder in checked
        for path in folder.rglob("*")
        if path.is_file() and path.name.casefold() in FORBIDDEN
    ]
    assert not violations


def test_pyinstaller_specs_keep_ghostscript_external_and_bundle_validator() -> None:
    root = Path(__file__).resolve().parents[1]
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.spec")).casefold()
    assert "gswin64c.exe" not in text and "gsdll64.dll" not in text
    assert "vendor-stage" in text and "vendor/verapdf" in text and "vendor/jre" in text


def test_bundled_validator_has_reproducible_preparation_and_licensing() -> None:
    root = Path(__file__).resolve().parents[1]
    assert (root / "scripts/prepare_bundled_validator.ps1").is_file()
    assert (root / "licenses/VERAPDF-NOTICE.txt").is_file()
    assert (root / "licenses/MPL-2.0.txt").is_file()
    assert (root / "licenses/TEMURIN-SOURCE-NOTICE.txt").is_file()
