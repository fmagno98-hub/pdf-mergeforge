import re
from pathlib import Path
from typing import Any


def natural_key(value: str | Path) -> list[Any]:
    name = Path(value).name if isinstance(value, Path) else value
    return [int(part) if part.isdigit() else part.casefold() for part in re.split(r"(\d+)", name)]
