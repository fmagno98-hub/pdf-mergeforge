import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from .pdf_to_word_service import PdfToWordCancelled, convert_pdfs_to_docx


class WordWorker(QObject):
    progress = Signal(int, int, str)
    completed = Signal(str, int, int)
    failed = Signal(str)
    cancelled = Signal()
    finished = Signal()

    def __init__(
        self,
        paths: list[Path],
        output: Path,
        preserve_layout: bool = True,
        ghostscript_path: str | None = None,
    ) -> None:
        super().__init__()
        self.paths = paths
        self.output = output
        self.preserve_layout = preserve_layout
        self.ghostscript_path = ghostscript_path
        self._cancel = threading.Event()

    @Slot()
    def run(self) -> None:
        try:
            result, pages, images = convert_pdfs_to_docx(
                self.paths,
                self.output,
                lambda current, total, name: self.progress.emit(current, total, name),
                self._cancel.is_set,
                preserve_layout=self.preserve_layout,
                ghostscript_path=self.ghostscript_path,
            )
            self.completed.emit(str(result), pages, images)
        except PdfToWordCancelled:
            self.cancelled.emit()
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()

    @Slot()
    def request_cancel(self) -> None:
        self._cancel.set()
