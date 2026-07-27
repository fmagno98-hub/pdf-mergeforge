import logging
import os
from pathlib import Path


def configure_logging() -> Path:
    root = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    log_dir = root / "PDF MergeForge" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "pdf-mergeforge.log"
    logging.basicConfig(
        filename=log_file, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    return log_file
