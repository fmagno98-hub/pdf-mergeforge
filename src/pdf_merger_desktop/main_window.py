import logging
import os
import subprocess
from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QThread, QUrl
from PySide6.QtGui import QAction, QCloseEvent, QDesktopServices, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from .config import APP_NAME, resource_path
from .file_item import PdfFileItem
from .merge_worker import MergeWorker
from .pdf_service import validate_pdf
from .pdfa_worker import PdfAWorker
from .services.ghostscript_service import (
    GhostscriptError,
    GhostscriptNotFoundError,
    discover_ghostscript,
    validate_executable,
)
from .utilities.formatting import format_bytes
from .utilities.natural_sort import natural_key
from .utilities.paths import ensure_pdf_suffix, normalized_windows_path
from .widgets.drop_area import DropArea

DATA_ROLE = Qt.ItemDataRole.UserRole


def move_indices_up(values: list, selected: set[int]) -> tuple[list, set[int]]:
    result = list(values)
    indexes = set(selected)
    for index in sorted(indexes):
        if index > 0 and index - 1 not in indexes:
            result[index - 1], result[index] = result[index], result[index - 1]
            indexes.remove(index)
            indexes.add(index - 1)
    return result, indexes


def move_indices_down(values: list, selected: set[int]) -> tuple[list, set[int]]:
    result = list(values)
    indexes = set(selected)
    for index in sorted(indexes, reverse=True):
        if index < len(result) - 1 and index + 1 not in indexes:
            result[index + 1], result[index] = result[index], result[index + 1]
            indexes.remove(index)
            indexes.add(index + 1)
    return result, indexes


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings()
        self.items: list[PdfFileItem] = []
        self.last_output: Path | None = None
        self.thread: QThread | None = None
        self.worker: MergeWorker | PdfAWorker | None = None
        self.merging = False
        self.setWindowTitle(APP_NAME)
        self.resize(1040, 680)
        self.setMinimumSize(820, 560)
        self.setAcceptDrops(True)
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        self._build_ui()
        self._create_shortcuts()
        self._refresh()

    def _button(self, text: str, slot, primary: bool = False) -> QPushButton:
        button = QPushButton(text)
        button.setMinimumHeight(40)
        button.clicked.connect(slot)
        if primary:
            button.setObjectName("primary")
        return button

    def _build_ui(self) -> None:
        container = QWidget()
        container.setObjectName("appShell")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 24, 28, 22)
        layout.setSpacing(18)

        # Brand header
        header = QFrame()
        header.setObjectName("headerCard")
        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(18, 14, 18, 14)
        header.setLayout(brand_row)
        logo = QLabel()
        logo_path = resource_path("assets/pdf-mergeforge-icon.png")
        if logo_path.exists():
            logo.setPixmap(
                QPixmap(str(logo_path)).scaled(
                    76,
                    76,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        logo.setFixedSize(80, 80)
        brand_copy = QVBoxLayout()
        brand_copy.setSpacing(2)
        title = QLabel(APP_NAME)
        title.setObjectName("title")
        subtitle = QLabel("Merge multiple PDFs into one. Fast. Offline. Secure.")
        subtitle.setObjectName("subtitle")
        brand_copy.addWidget(title)
        brand_copy.addWidget(subtitle)
        badge_row = QHBoxLayout()
        badge_row.setSpacing(8)
        for text in ("100% OFFLINE", "PRIVATE & SECURE", "PORTABLE WINDOWS APP"):
            badge = QLabel(text)
            badge.setObjectName("trustBadge")
            badge_row.addWidget(badge)
        badge_row.addStretch()
        brand_copy.addLayout(badge_row)
        brand_row.addWidget(logo)
        brand_row.addLayout(brand_copy, 1)

        # File workspace card
        workspace = QFrame()
        workspace.setObjectName("workspaceCard")
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(20, 18, 20, 18)
        workspace_layout.setSpacing(14)

        workspace_header = QHBoxLayout()
        section_copy = QVBoxLayout()
        section_title = QLabel("FILES TO MERGE")
        section_title.setObjectName("sectionTitle")
        section_hint = QLabel("The final PDF follows the order shown below.")
        section_hint.setObjectName("sectionHint")
        section_copy.addWidget(section_title)
        section_copy.addWidget(section_hint)
        workspace_header.addLayout(section_copy)
        workspace_header.addStretch()

        self.drop = DropArea()
        self.drop.setToolTip("Drop PDF files here")
        self.drop.files_dropped.connect(self.add_paths)
        self.drop.order_changed.connect(self._sync_after_internal_move)
        self.drop.itemSelectionChanged.connect(self._refresh_buttons)

        self.add_button = self._button("Add PDF files", self.add_files)
        self.add_button.setObjectName("accent")
        self.add_button.setToolTip("Choose one or more PDF files (Ctrl+O)")
        self.remove_button = self._button("Remove selected", self.remove_selected)
        self.remove_button.setToolTip("Remove selected files (Delete)")
        self.clear_button = self._button("Clear list", self.clear_list)
        self.clear_button.setObjectName("danger")
        self.sort_az_button = self._button("Sort A-Z", lambda: self.sort_items(False))
        self.sort_za_button = self._button("Sort Z-A", lambda: self.sort_items(True))
        self.up_button = self._button("Move up", self.move_up)
        self.down_button = self._button("Move down", self.move_down)
        workspace_header.addWidget(self.add_button)
        workspace_header.addWidget(self.remove_button)
        workspace_header.addWidget(self.clear_button)
        workspace_layout.addLayout(workspace_header)

        self.content_stack = QStackedWidget()
        self.content_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        empty_panel = QFrame()
        empty_panel.setObjectName("dropZone")
        empty_layout = QVBoxLayout(empty_panel)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_mark = QLabel("+")
        empty_mark.setObjectName("emptyMark")
        empty_mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label = QLabel("DROP YOUR PDF FILES HERE")
        self.empty_label.setObjectName("emptyTitle")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_help = QLabel("or click “Add PDF files” to browse your computer")
        empty_help.setObjectName("emptyHelp")
        empty_help.setAlignment(Qt.AlignmentFlag.AlignCenter)
        privacy = QLabel("Your files never leave this device")
        privacy.setObjectName("privacyNote")
        privacy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_mark)
        empty_layout.addSpacing(6)
        empty_layout.addWidget(self.empty_label)
        empty_layout.addWidget(empty_help)
        empty_layout.addSpacing(12)
        empty_layout.addWidget(privacy)
        self.content_stack.addWidget(empty_panel)
        self.content_stack.addWidget(self.drop)
        workspace_layout.addWidget(self.content_stack, 1)

        ordering = QHBoxLayout()
        ordering.setSpacing(8)
        order_label = QLabel("ORDER")
        order_label.setObjectName("toolbarLabel")
        ordering.addWidget(order_label)
        for button in (
            self.sort_az_button,
            self.sort_za_button,
            self.up_button,
            self.down_button,
        ):
            ordering.addWidget(button)
        ordering.addStretch()
        workspace_layout.addLayout(ordering)

        # Bottom action card
        action_card = QFrame()
        action_card.setObjectName("actionCard")
        action_layout = QGridLayout(action_card)
        action_layout.setContentsMargins(20, 16, 20, 16)
        summary_title = QLabel("READY TO FORGE")
        summary_title.setObjectName("sectionTitle")
        self.summary_count = QLabel("0 files")
        self.summary_count.setObjectName("summaryValue")
        self.summary_pages = QLabel("0 total pages")
        self.summary_pages.setObjectName("summaryMeta")
        action_layout.addWidget(summary_title, 0, 0)
        action_layout.addWidget(self.summary_count, 1, 0)
        action_layout.addWidget(self.summary_pages, 2, 0)

        self.merge_button = self._button("Merge PDF files", self.choose_output, True)
        self.merge_button.setMinimumSize(250, 54)
        self.merge_button.setToolTip("Choose an output file and start merging (Ctrl+M)")
        self.pdfa_button = self._button("Export as PDF/A-1b", self.choose_pdfa_output)
        self.pdfa_button.setObjectName("pdfa")
        self.pdfa_button.setMinimumSize(250, 54)
        self.pdfa_button.setToolTip(
            "Create an archival PDF/A-1b using a separately installed Ghostscript"
        )
        self.cancel_button = self._button("Cancel", self.cancel_merge)
        self.cancel_button.setObjectName("danger")
        self.open_button = self._button("Open PDF", self.open_pdf)
        self.folder_button = self._button("Open folder", self.open_folder)
        result_buttons = QHBoxLayout()
        result_buttons.addWidget(self.cancel_button)
        result_buttons.addWidget(self.open_button)
        result_buttons.addWidget(self.folder_button)
        action_layout.addLayout(result_buttons, 0, 1, 1, 2)
        export_buttons = QHBoxLayout()
        export_buttons.addWidget(self.merge_button, 2)
        export_buttons.addWidget(self.pdfa_button, 1)
        action_layout.addLayout(export_buttons, 1, 1, 2, 2)

        layout.addWidget(header)
        layout.addWidget(workspace, 1)
        layout.addWidget(action_card)
        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.progress.hide()
        layout.addWidget(self.progress)
        self.setCentralWidget(container)
        self.setStatusBar(QStatusBar())
        self.setStyleSheet("""
            * { font-family: "Segoe UI Variable", "Segoe UI"; }
            QMainWindow, QWidget#appShell { background: #061328; color: #EAF3FF; }
            QFrame#headerCard, QFrame#workspaceCard, QFrame#actionCard {
                background: #0C1C34; border: 1px solid #1C3658; border-radius: 14px;
            }
            QLabel#title { font-size: 30px; font-weight: 700; color: #F7FBFF; }
            QLabel#subtitle { font-size: 14px; color: #9FB1C9; }
            QLabel#trustBadge { background: #102A45; color: #27D9E8; border: 1px solid #1C5670;
                border-radius: 9px; padding: 3px 8px; font-size: 10px; font-weight: 700; }
            QLabel#sectionTitle, QLabel#toolbarLabel { color: #30D9EB; font-size: 11px;
                font-weight: 700; letter-spacing: 1px; }
            QLabel#sectionHint, QLabel#summaryMeta, QLabel#emptyHelp { color: #879AB4; }
            QLabel#summaryValue { color: #FFFFFF; font-size: 20px; font-weight: 700; }
            QFrame#dropZone { background: #08172C; border: 2px dashed #1E5D7A;
                border-radius: 12px; }
            QLabel#emptyMark { color: #19CFE3; border: 2px solid #19CFE3; border-radius: 26px;
                font-size: 34px; font-weight: 300; min-width: 52px; max-width: 52px;
                min-height: 52px; max-height: 52px; }
            QLabel#emptyTitle { color: #F4F8FF; font-size: 18px; font-weight: 700; }
            QLabel#privacyNote { color: #3FE0C5; font-size: 12px; }
            QListWidget { background: #08172C; color: #EAF3FF; border: 1px solid #1C3658;
                border-radius: 10px; padding: 8px; outline: 0; }
            QListWidget::item { background: #10223B; border: 1px solid #193B5D;
                border-radius: 8px; padding: 10px; margin: 4px; }
            QListWidget::item:hover { background: #143052; border-color: #247BA0; }
            QListWidget::item:selected { background: #123F5D; border: 2px solid #24CFE0; }
            QPushButton { color: #DCE8F8; background: #142944; border: 1px solid #284767;
                border-radius: 8px; padding: 8px 14px; font-weight: 600; }
            QPushButton:hover { background: #1A385B; border-color: #2DBFD3; }
            QPushButton:pressed { background: #0F223B; }
            QPushButton:focus { border: 2px solid #4CE6F1; }
            QPushButton:disabled { color: #5D708A; background: #0D1A2D; border-color: #1A2A40; }
            QPushButton#primary { color: white; background: #F0522D; border: 1px solid #FF7551;
                font-size: 15px; font-weight: 700; }
            QPushButton#primary:hover { background: #FF633D; border-color: #FF9A78; }
            QPushButton#primary:disabled { color: #6E7E92; background: #142136;
                border-color: #24354D; }
            QPushButton#pdfa { color: #061328; background: #30D9EB; border-color: #73F1F6;
                font-size: 14px; font-weight: 700; }
            QPushButton#pdfa:hover { background: #63E7F1; border-color: #B1FAFC; }
            QPushButton#pdfa:disabled { color: #5D708A; background: #0D1A2D;
                border-color: #1A2A40; }
            QPushButton#accent { color: #061328; background: #25D5E5; border-color: #63EFF5; }
            QPushButton#accent:hover { background: #51E4EF; border-color: #9CF7FA; }
            QPushButton#danger { color: #FF9B8A; }
            QPushButton#danger:disabled { color: #5D708A; background: #0D1A2D;
                border-color: #1A2A40; }
            QProgressBar { background: #09182B; border: 1px solid #1C3658; border-radius: 7px;
                color: white; text-align: center; min-height: 16px; }
            QProgressBar::chunk { background: #19CFE3; border-radius: 6px; }
            QStatusBar { background: #061328; color: #8FA4BD; }
        """)

    def _create_shortcuts(self) -> None:
        for shortcut, slot in (
            ("Ctrl+O", self.add_files),
            ("Delete", self.remove_selected),
            ("Ctrl+Shift+C", self.clear_list),
            ("Alt+Up", self.move_up),
            ("Alt+Down", self.move_down),
            ("Ctrl+M", self.choose_output),
            ("Ctrl+Shift+M", self.choose_pdfa_output),
            ("Escape", self.cancel_merge),
            ("Ctrl+Q", self.close),
        ):
            action = QAction(self)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(slot)
            self.addAction(action)

    def dragEnterEvent(self, event) -> None:
        event.acceptProposedAction() if event.mimeData().hasUrls() else event.ignore()

    def dropEvent(self, event) -> None:
        self.add_paths([url.toLocalFile() for url in event.mimeData().urls()])
        event.acceptProposedAction()

    def add_files(self) -> None:
        start = self.settings.value("last_open_dir", str(Path.home()))
        paths, _ = QFileDialog.getOpenFileNames(self, "Add PDF files", start, "PDF files (*.pdf)")
        if paths:
            self.settings.setValue("last_open_dir", str(Path(paths[0]).parent))
            self.add_paths(paths)

    def add_paths(self, paths: list[str]) -> None:
        existing = {item.normalized_path for item in self.items}
        ignored: list[str] = []
        for raw in paths:
            path = Path(raw)
            if not path.is_file() or path.suffix.casefold() != ".pdf":
                ignored.append(path.name)
                continue
            key = normalized_windows_path(path)
            if key in existing:
                ignored.append(f"{path.name} (duplicate)")
                continue
            item = validate_pdf(path)
            self.items.append(item)
            existing.add(key)
        self._render()
        if ignored:
            self.statusBar().showMessage(
                f"Ignored {len(ignored)} invalid or duplicate item(s)", 5000
            )

    def _render(self, selected: set[int] | None = None) -> None:
        self.drop.clear()
        for index, model in enumerate(self.items, 1):
            state = f"{model.page_count} pages" if model.is_valid else f"Error: {model.error}"
            row = QListWidgetItem(
                f"{index}.  {model.name}\n     {model.path}  |  "
                f"{format_bytes(model.size_bytes)}  |  {state}"
            )
            row.setData(DATA_ROLE, model)
            if not model.is_valid:
                row.setForeground(Qt.GlobalColor.red)
            self.drop.addItem(row)
        for index in selected or set():
            if index < self.drop.count():
                self.drop.item(index).setSelected(True)
        self._refresh()

    def _sync_after_internal_move(self) -> None:
        self.items = [self.drop.item(i).data(DATA_ROLE) for i in range(self.drop.count())]
        self._render()

    def remove_selected(self) -> None:
        selected = {self.drop.row(item) for item in self.drop.selectedItems()}
        self.items = [item for i, item in enumerate(self.items) if i not in selected]
        self._render()

    def clear_list(self) -> None:
        if (
            self.items
            and QMessageBox.question(self, "Clear list", "Remove all PDF files from the list?")
            == QMessageBox.StandardButton.Yes
        ):
            self.items.clear()
            self._render()

    def sort_items(self, reverse: bool) -> None:
        self.items.sort(key=lambda item: natural_key(item.name), reverse=reverse)
        self._render()

    def _selected(self) -> set[int]:
        return {self.drop.row(item) for item in self.drop.selectedItems()}

    def move_up(self) -> None:
        self.items, selected = move_indices_up(self.items, self._selected())
        self._render(selected)

    def move_down(self) -> None:
        self.items, selected = move_indices_down(self.items, self._selected())
        self._render(selected)

    def choose_output(self) -> None:
        if self.merging or not self.items:
            return
        start = str(Path(self.settings.value("last_save_dir", str(Path.home()))) / "merged.pdf")
        raw, _ = QFileDialog.getSaveFileName(self, "Save merged PDF", start, "PDF files (*.pdf)")
        if not raw:
            return
        output = ensure_pdf_suffix(raw)
        if normalized_windows_path(output) in {item.normalized_path for item in self.items}:
            QMessageBox.warning(self, "Invalid output", "The output cannot overwrite a source PDF.")
            return
        if (
            output.exists()
            and QMessageBox.question(self, "Overwrite file", f"Replace {output.name}?")
            != QMessageBox.StandardButton.Yes
        ):
            return
        self.settings.setValue("last_save_dir", str(output.parent))
        self._start_merge(output)

    def _start_merge(self, output: Path) -> None:
        invalid = [validate_pdf(item.path) for item in self.items]
        bad = next((item for item in invalid if not item.is_valid), None)
        if bad:
            QMessageBox.warning(self, "Cannot merge", f"{bad.name}: {bad.error}")
            return
        self.merging = True
        self.last_output = None
        self.progress.setRange(0, len(self.items))
        self.progress.setValue(0)
        self.progress.show()
        self._refresh()
        self.thread = QThread(self)
        self.worker = MergeWorker([item.path for item in self.items], output)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._merge_progress)
        self.worker.completed.connect(self._merge_completed)
        self.worker.failed.connect(self._merge_failed)
        self.worker.cancelled.connect(self._merge_cancelled)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self._thread_finished)
        self.thread.start()

    def choose_pdfa_output(self) -> None:
        if self.merging or not self.items:
            return
        start = str(
            Path(self.settings.value("last_save_dir", str(Path.home())))
            / "merged_document_PDFA-1b.pdf"
        )
        raw, _ = QFileDialog.getSaveFileName(self, "Export as PDF/A-1b", start, "PDF files (*.pdf)")
        if not raw:
            return
        output = ensure_pdf_suffix(raw)
        if normalized_windows_path(output) in {item.normalized_path for item in self.items}:
            QMessageBox.warning(self, "Invalid output", "The output cannot overwrite a source PDF.")
            return
        if (
            output.exists()
            and QMessageBox.question(self, "Overwrite file", f"Replace {output.name}?")
            != QMessageBox.StandardButton.Yes
        ):
            return
        installation = self._ensure_ghostscript()
        if installation is None:
            return
        self.settings.setValue("last_save_dir", str(output.parent))
        self._start_pdfa(output)

    def _ensure_ghostscript(self):
        saved = self.settings.value("external_tools/ghostscript_path", "")
        try:
            installation = discover_ghostscript(saved or None)
            if saved and str(installation.executable_path) != str(Path(saved).resolve()):
                self.settings.remove("external_tools/ghostscript_path")
            return installation
        except GhostscriptNotFoundError:
            dialog = QMessageBox(self)
            dialog.setIcon(QMessageBox.Icon.Information)
            dialog.setWindowTitle("Ghostscript required")
            dialog.setText("PDF/A-1b export requires a separately installed copy of Ghostscript.")
            dialog.setInformativeText(
                "Ghostscript is not included with PDF MergeForge and is distributed under its "
                "own licence. Normal PDF merging remains available without Ghostscript."
            )
            download = dialog.addButton("Download Ghostscript", QMessageBox.ButtonRole.ActionRole)
            locate = dialog.addButton("Locate gswin64c.exe", QMessageBox.ButtonRole.ActionRole)
            retry = dialog.addButton("Check again", QMessageBox.ButtonRole.ActionRole)
            dialog.addButton(QMessageBox.StandardButton.Cancel)
            dialog.exec()
            clicked = dialog.clickedButton()
            if clicked is download:
                QDesktopServices.openUrl(QUrl("https://ghostscript.com/releases/gsdnld.html"))
                return None
            if clicked is locate:
                raw, _ = QFileDialog.getOpenFileName(
                    self,
                    "Locate 64-bit Ghostscript",
                    "C:\\Program Files\\gs",
                    "Ghostscript console (gswin64c.exe)",
                )
                if not raw:
                    return None
                try:
                    installation = validate_executable(Path(raw))
                except GhostscriptError as exc:
                    QMessageBox.warning(self, "Invalid Ghostscript", str(exc))
                    return None
                self.settings.setValue(
                    "external_tools/ghostscript_path", str(installation.executable_path)
                )
                return installation
            if clicked is retry:
                try:
                    return discover_ghostscript()
                except GhostscriptNotFoundError:
                    QMessageBox.information(
                        self, "Ghostscript", "Ghostscript is still not available."
                    )
            return None

    def _start_pdfa(self, output: Path) -> None:
        invalid = [validate_pdf(item.path) for item in self.items]
        bad = next((item for item in invalid if not item.is_valid), None)
        if bad:
            QMessageBox.warning(self, "Cannot export PDF/A-1b", f"{bad.name}: {bad.error}")
            return
        self.merging = True
        self.last_output = None
        self.progress.setRange(0, 0)
        self.progress.show()
        self._refresh()
        self.thread = QThread(self)
        self.worker = PdfAWorker(
            [item.path for item in self.items],
            output,
            str(self.settings.value("external_tools/ghostscript_path", "")),
            str(self.settings.value("external_tools/verapdf_path", "")),
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.stage.connect(self._pdfa_stage)
        self.worker.completed.connect(self._pdfa_completed)
        self.worker.failed.connect(self._pdfa_failed)
        self.worker.cancelled.connect(self._merge_cancelled)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self._thread_finished)
        self.thread.start()

    def _pdfa_stage(self, stage: str) -> None:
        self.statusBar().showMessage(stage)

    def _pdfa_completed(self, result) -> None:
        self.last_output = result.output_path
        verification = (
            f"Validated with veraPDF {result.external.validator_version}."
            if result.external.available
            else "Baseline checks passed; veraPDF independent validation was not available."
        )
        QMessageBox.information(
            self,
            "PDF/A-1b export completed",
            f"Created: {result.output_path.name}\n{result.output_path}\n\n"
            f"{result.pages} pages\nGhostscript {result.ghostscript.version_text}\n{verification}",
        )
        self.statusBar().showMessage("PDF/A-1b export completed")

    def _pdfa_failed(self, message: str) -> None:
        logging.error("PDF/A export failed: %s", message)
        QMessageBox.critical(self, "PDF/A-1b export failed", message)
        self.statusBar().showMessage("PDF/A-1b export failed")

    def cancel_merge(self) -> None:
        if self.worker and self.merging:
            self.worker.request_cancel()
            self.statusBar().showMessage("Cancelling operation...")

    def _merge_progress(self, current: int, total: int, name: str) -> None:
        self.progress.setValue(current)
        self.statusBar().showMessage(f"Processing {current} of {total}: {name}")

    def _merge_completed(self, output: str, pages: int) -> None:
        self.last_output = Path(output)
        size = format_bytes(self.last_output.stat().st_size)
        QMessageBox.information(
            self,
            "Merge completed",
            f"Created: {self.last_output.name}\n{self.last_output}\n\n"
            f"{len(self.items)} PDF(s), {pages} pages, {size}",
        )
        self.statusBar().showMessage("Merge completed successfully")

    def _merge_failed(self, message: str) -> None:
        logging.exception("Merge failed: %s", message)
        QMessageBox.critical(self, "Merge failed", message)
        self.statusBar().showMessage("Merge failed")

    def _merge_cancelled(self) -> None:
        self.statusBar().showMessage("Operation cancelled")

    def _thread_finished(self) -> None:
        if self.thread:
            self.thread.deleteLater()
        self.thread = None
        self.worker = None
        self.merging = False
        self.progress.hide()
        self._refresh()

    def open_pdf(self) -> None:
        if self.last_output:
            try:
                os.startfile(self.last_output)  # type: ignore[attr-defined]
            except OSError as exc:
                QMessageBox.warning(self, "Open PDF", str(exc))

    def open_folder(self) -> None:
        if self.last_output:
            try:
                subprocess.Popen(["explorer", "/select,", str(self.last_output)])
            except OSError as exc:
                QMessageBox.warning(self, "Open folder", str(exc))

    def _refresh(self) -> None:
        self.content_stack.setCurrentIndex(1 if self.items else 0)
        self._refresh_buttons()
        pages = sum(item.page_count for item in self.items if item.is_valid)
        self.summary_count.setText(f"{len(self.items)} file{'s' if len(self.items) != 1 else ''}")
        self.summary_pages.setText(f"{pages} total page{'s' if pages != 1 else ''}")
        self.statusBar().showMessage(f"{len(self.items)} files loaded - {pages} total pages")

    def _refresh_buttons(self) -> None:
        selected = bool(self.drop.selectedItems())
        valid = bool(self.items) and all(item.is_valid for item in self.items)
        for button in (
            self.add_button,
            self.remove_button,
            self.clear_button,
            self.sort_az_button,
            self.sort_za_button,
            self.up_button,
            self.down_button,
            self.merge_button,
            self.pdfa_button,
        ):
            button.setEnabled(not self.merging)
        self.remove_button.setEnabled(selected and not self.merging)
        self.clear_button.setEnabled(bool(self.items) and not self.merging)
        self.up_button.setEnabled(selected and not self.merging)
        self.down_button.setEnabled(selected and not self.merging)
        self.merge_button.setEnabled(valid and not self.merging)
        self.pdfa_button.setEnabled(valid and not self.merging)
        self.cancel_button.setEnabled(self.merging)
        self.open_button.setEnabled(self.last_output is not None and not self.merging)
        self.folder_button.setEnabled(self.last_output is not None and not self.merging)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.merging:
            QMessageBox.information(
                self, "Operation in progress", "Cancel the operation before closing."
            )
            event.ignore()
            return
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()
