import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from .services.pdfa_conversion_service import PdfAConversionCancelled, export_pdfa_1b


class PdfAWorker(QObject):
    stage = Signal(str)
    completed = Signal(object)
    failed = Signal(str)
    cancelled = Signal()
    finished = Signal()

    def __init__(
        self,
        paths: list[Path],
        output: Path,
        ghostscript_path: str,
        verapdf_path: str,
        page_limit: int | None = None,
    ) -> None:
        super().__init__()
        self.paths = paths
        self.output = output
        self.ghostscript_path = ghostscript_path
        self.verapdf_path = verapdf_path
        self.page_limit = page_limit
        self._cancel = threading.Event()

    @Slot()
    def run(self) -> None:
        try:
            result = export_pdfa_1b(
                self.paths,
                self.output,
                page_limit=self.page_limit,
                saved_ghostscript=self.ghostscript_path or None,
                saved_verapdf=self.verapdf_path or None,
                progress=self.stage.emit,
                cancelled=self._cancel.is_set,
            )
            self.completed.emit(result)
        except PdfAConversionCancelled:
            self.cancelled.emit()
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()

    @Slot()
    def request_cancel(self) -> None:
        self._cancel.set()
