import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from .pdf_service import MergeCancelled, merge_pdfs


class MergeWorker(QObject):
    progress = Signal(int, int, str)
    completed = Signal(str, int)
    failed = Signal(str)
    cancelled = Signal()
    finished = Signal()

    def __init__(
        self, paths: list[Path], output: Path, page_limit: int | None = None
    ) -> None:
        super().__init__()
        self.paths = paths
        self.output = output
        self.page_limit = page_limit
        self._cancel = threading.Event()

    @Slot()
    def run(self) -> None:
        try:
            result, pages = merge_pdfs(
                self.paths,
                self.output,
                lambda current, total, name: self.progress.emit(current, total, name),
                self._cancel.is_set,
                self.page_limit,
            )
            self.completed.emit(str(result), pages)
        except MergeCancelled:
            self.cancelled.emit()
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()

    @Slot()
    def request_cancel(self) -> None:
        self._cancel.set()
