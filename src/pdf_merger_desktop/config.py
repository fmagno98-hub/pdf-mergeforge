import sys
from pathlib import Path

APP_NAME = "PDF MergeForge"
ORGANIZATION = "PDF MergeForge"
VERSION = "1.1.0"


def resource_path(relative: str) -> Path:
    """Resolve bundled assets in development and PyInstaller builds."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return base / relative
