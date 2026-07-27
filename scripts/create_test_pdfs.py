import sys
from pathlib import Path

from pypdf import PdfWriter

target = Path(sys.argv[1] if len(sys.argv) > 1 else "test-output/generated")
target.mkdir(parents=True, exist_ok=True)
for index in range(1, 3):
    writer = PdfWriter()
    writer.add_blank_page(width=595 + index, height=842)
    with (target / f"generated-{index}.pdf").open("wb") as stream:
        writer.write(stream)
