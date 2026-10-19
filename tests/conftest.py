import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.fixture
def tmp_path() -> Path:
    """Avoid Windows sandbox ACL issues in tempfile-created directories."""
    path = Path("test-output") / f"pytest-{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    return path.resolve()
