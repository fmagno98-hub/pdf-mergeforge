import ast
import re
from pathlib import Path

DISALLOWED_MODULES = {
    "aiohttp",
    "ftplib",
    "http",
    "requests",
    "socket",
    "urllib",
    "webbrowser",
    "websocket",
}


def test_runtime_has_no_network_imports() -> None:
    source_root = Path(__file__).resolve().parents[1] / "src" / "pdf_merger_desktop"
    violations: list[str] = []
    for source in source_root.rglob("*.py"):
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if name.split(".", maxsplit=1)[0] in DISALLOWED_MODULES:
                    violations.append(f"{source.name}: {name}")
    assert not violations, f"Network-capable runtime imports found: {violations}"


def test_runtime_contains_no_remote_endpoints() -> None:
    source_root = Path(__file__).resolve().parents[1] / "src" / "pdf_merger_desktop"
    combined = "\n".join(path.read_text(encoding="utf-8") for path in source_root.rglob("*.py"))
    endpoints = re.findall(r"https?://[^\"')\s]+", combined)
    assert endpoints == ["https://ghostscript.com/releases/gsdnld.html"]
