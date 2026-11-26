import os
import sys
import subprocess
import threading
import inspect
import requests
from pathlib import Path

from PySide6.QtCore import Qt, QObject, Signal, QBuffer, QIODevice
from PySide6.QtGui import QIcon, QColor, QAction, QPixmap, QImage, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QFrame,
    QMenu,
    QStyle,
    QSplitter,
    QScrollArea,
    QFileDialog,
)

from internal.logger import get_logger

logger = get_logger(__name__)
from internal.settings import get_settings
from internal.download import download, build_track_stem
from internal.slm_work import SLM_work
from internal.searxng import SearXNG
from internal.metadata_struct import Metadata_MP3


DARK_STYLESHEET = """
QMainWindow, QWidget#CentralWidget, QWidget#LeftPane, QWidget#RightPane {
    background-color: #121012;
    color: #F8F5F6;
    font-family: "Segoe UI", "Inter", "Ubuntu", sans-serif;
    font-size: 13px;
}

QLabel {
    background-color: transparent;
    border: none;
    color: #F8F5F6;
}

QFrame#Card {
    background-color: #1A1719;
    border: 1px solid #2D262A;
    border-radius: 10px;
}

QFrame#StatusFooter {
    background-color: #161315;
    border-top: 1px solid #2A2327;
}

QScrollArea, QScrollArea > QWidget > QWidget, QWidget#EditorScrollContent {
    background-color: transparent;
    border: none;
}

QSplitter {
    background-color: #121012;
}

QSplitter::handle {
    background-color: #2A2327;
    width: 4px;
    margin: 6px 2px;
    border-radius: 2px;
}

QSplitter::handle:hover {
    background-color: #D23C69;
}

QLabel#AppTitle {
    font-size: 18px;
    font-weight: 700;
    color: #F8F5F6;
}

QLabel#AppSubtitle {
    font-size: 12px;
    color: #A6999E;
}

QLabel#SectionTitle {
    font-size: 12px;
    font-weight: 700;
    color: #4CC9D6;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

QLabel#FieldLabel {
    font-size: 11px;
    font-weight: 600;
    color: #DED5D8;
}

QLabel#SourceHint {
    font-size: 10px;
    color: #8E8085;
    padding-left: 2px;
}

QLabel#FooterText {
    font-size: 11px;
    color: #A6999E;
}

QLabel#FooterStatusOk {
    font-size: 11px;
    font-weight: 600;
    color: #7CE0EA;
    background-color: #112A2E;
    border: 1px solid #1F6E7A;
    border-radius: 9px;
    padding: 2px 9px;
}

QLabel#FooterStatusWarn {
    font-size: 11px;
    font-weight: 600;
    color: #FBBF24;
    background-color: #2B2112;
    border: 1px solid #6B4B16;
    border-radius: 9px;
    padding: 2px 9px;
}

QLabel#FooterStatusMuted {
    font-size: 11px;
    font-weight: 600;
    color: #A6999E;
    background-color: #241F22;
    border: 1px solid #383035;
    border-radius: 9px;
    padding: 2px 9px;
}

QLabel#ThumbnailDropZone {
    background-color: #141113;
    border: 1.5px dashed #3D3338;
    border-radius: 10px;
    color: #9A8C92;
    font-size: 11px;
}

QLabel#ThumbnailDropZone[dirty="true"] {
    border: 2px solid #F59E0B;
    background-color: #211B11;
}

QLabel#ThumbnailDropZone[dragOver="true"] {
    border: 2px dashed #1F6E7A;
    background-color: #122428;
    color: #7CE0EA;
}

QLineEdit {
    background-color: #141113;
    border: 1px solid #352C31;
    border-radius: 7px;
    padding: 7px 10px;
    color: #F8F5F6;
    selection-background-color: #D23C69;
    selection-color: #FFFFFF;
}

QLineEdit:focus {
    border: 1.5px solid #1F6E7A;
    background-color: #181417;
}

QLineEdit[dirty="true"] {
    border: 1.5px solid #F59E0B;
    background-color: #211B11;
}

QLineEdit[dirty="true"]:focus {
    border: 1.5px solid #FBBF24;
}

QLineEdit:disabled {
    background-color: #161315;
    color: #6B5F64;
    border: 1px solid #262023;
}

QPushButton {
    background-color: #241F22;
    color: #F8F5F6;
    border: 1px solid #3A3136;
    border-radius: 7px;
    padding: 7px 13px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #2D262A;
    border-color: #1F6E7A;
    color: #7CE0EA;
}

QPushButton:pressed {
    background-color: #1D181B;
}

QPushButton:disabled {
    background-color: #1C181B;
    color: #5E5358;
    border-color: #292226;
}

QPushButton#SmallButton {
    padding: 4px 10px;
    font-size: 11px;
    border-radius: 6px;
}

QPushButton#PrimaryButton {
    background-color: #D23C69;
    border: 1px solid #E0527C;
    color: #FFFFFF;
    padding: 7px 16px;
}

QPushButton#PrimaryButton:hover {
    background-color: #BC315B;
    border-color: #D23C69;
    color: #FFFFFF;
}

QPushButton#PrimaryButton:pressed {
    background-color: #A4274D;
}

QPushButton#PrimaryButton:disabled {
    background-color: #4D2130;
    border-color: #5E293B;
    color: #A87C8A;
}

QPushButton#DangerButton {
    background-color: #2D1820;
    border: 1px solid #592638;
    color: #F5A3BC;
}

QPushButton#DangerButton:hover {
    background-color: #3D1F2B;
    border-color: #D23C69;
    color: #FFFFFF;
}

QTableWidget {
    background-color: #141113;
    alternate-background-color: #191518;
    border: 1px solid #2D262A;
    border-radius: 8px;
    gridline-color: #241E21;
    selection-background-color: #17383E;
    selection-color: #F8F5F6;
    outline: none;
}

QTableWidget::item {
    padding: 7px 10px;
    border-bottom: 1px solid #221C1F;
    color: #F8F5F6;
}

QHeaderView::section {
    background-color: #1E191C;
    color: #A6999E;
    border: none;
    border-bottom: 1px solid #2F282C;
    padding: 8px 10px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
}

QScrollBar:vertical {
    background: #141113;
    width: 9px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #3A3136;
    border-radius: 4px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background: #1F6E7A;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QMenu {
    background-color: #1E191C;
    border: 1px solid #3A3136;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 16px;
    border-radius: 4px;
    color: #F8F5F6;
}

QMenu::item:selected {
    background-color: #D23C69;
    color: #FFFFFF;
}
"""


def _open_path_in_file_manager(target_path: Path) -> None:
    target = target_path.resolve()
    if sys.platform.startswith("win"):
        if target.is_file():
            subprocess.Popen(["explorer", "/select,", str(target)])
        else:
            os.startfile(str(target))
    elif sys.platform == "darwin":
        if target.is_file():
            subprocess.Popen(["open", "-R", str(target)])
        else:
            subprocess.Popen(["open", str(target)])
    else:
        folder = target.parent if target.is_file() else target
        subprocess.Popen(["xdg-open", str(folder)])


def _qimage_to_jpeg_bytes(image: QImage) -> bytes | None:
    if image.isNull():
        return None
    buf = QBuffer()
    buf.open(QIODevice.WriteOnly)
    ok = image.save(buf, "PNG")
    raw = bytes(buf.data())
    buf.close()
    if not ok or not raw:
        return None
    try:
        return Metadata_MP3.convert_image_bytes_to_jpeg(raw)
    except Exception:
        return None


class ThumbnailDropZone(QLabel):
    image_dropped = Signal(bytes)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ThumbnailDropZone")
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(164, 164)
        self.setAcceptDrops(True)
        self.setWordWrap(True)
        self.setFocusPolicy(Qt.ClickFocus)
        self.setProperty("dirty", "false")
        self.setProperty("dragOver", "false")
        self._current_bytes: bytes | None = None
        self.set_placeholder()

    def _repolish(self) -> None:
        self.style().unpolish(self)
        self.style().polish(self)

    def set_dirty(self, dirty: bool) -> None:
        self.setProperty("dirty", "true" if dirty else "false")
        self._repolish()

    def set_placeholder(self, text: str = "Drop or Paste\nCover Image") -> None:
        self._current_bytes = None
        self.setPixmap(QPixmap())
        self.setText(text)

    def set_image_bytes(self, data: bytes | None) -> bool:
        if not data:
            self.set_placeholder()
            return False
        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            self.set_placeholder()
            return False
        self._current_bytes = data
        scaled = pixmap.scaled(154, 154, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setText("")
        self.setPixmap(scaled)
        return True

    def paste_from_clipboard(self) -> bool:
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()
        if mime is None:
            return False

        if mime.hasImage():
            qimg = clipboard.image()
            jpeg = _qimage_to_jpeg_bytes(qimg)
            if jpeg:
                self.image_dropped.emit(jpeg)
                return True

        if mime.hasUrls():
            for url in mime.urls():
                if self._try_emit_url(url.toLocalFile() or url.toString()):
                    return True

        if mime.hasText():
            text = mime.text().strip()
            if text.startswith(("http://", "https://")) or Path(text).is_file():
                if self._try_emit_url(text):
                    return True

        return False

    def _try_emit_url(self, target: str) -> bool:
        target = (target or "").strip()
        if not target:
            return False
        try:
            if target.startswith(("http://", "https://")):
                resp = requests.get(target, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()
                jpeg = Metadata_MP3.convert_image_bytes_to_jpeg(resp.content)
                self.image_dropped.emit(jpeg)
                return True
            local = Path(target)
            if local.is_file():
                jpeg = Metadata_MP3.convert_image_bytes_to_jpeg(local.read_bytes())
                self.image_dropped.emit(jpeg)
                return True
        except Exception:
            return False
        return False

    def keyPressEvent(self, event) -> None:
        if event.matches(QKeySequence.Paste):
            self.paste_from_clipboard()
            return
        super().keyPressEvent(event)

    def dragEnterEvent(self, event) -> None:
        mime = event.mimeData()
        if mime.hasImage() or mime.hasUrls() or mime.hasText():
            self.setProperty("dragOver", "true")
            self._repolish()
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self.setProperty("dragOver", "false")
        self._repolish()
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:
        self.setProperty("dragOver", "false")
        self._repolish()
        mime = event.mimeData()

        if mime.hasImage():
            img = mime.imageData()
            if isinstance(img, QImage):
                jpeg = _qimage_to_jpeg_bytes(img)
                if jpeg:
                    self.image_dropped.emit(jpeg)
                    event.acceptProposedAction()
                    return

        if mime.hasUrls():
            for url in mime.urls():
                if self._try_emit_url(url.toLocalFile() or url.toString()):
                    event.acceptProposedAction()
                    return

        if mime.hasText():
            if self._try_emit_url(mime.text()):
                event.acceptProposedAction()
                return

        event.ignore()


class MetadataFieldWidget(QWidget):
    changed = Signal(str)

    def __init__(self, key: str, label_text: str, placeholder: str = "", parent=None) -> None:
        super().__init__(parent)
        self.key = key
        self._committed_value: str = ""
        self._source_text: str = ""
        self._is_dirty: bool = False
        self._suppress_signal: bool = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        self.label = QLabel(label_text)
        self.label.setObjectName("FieldLabel")
        layout.addWidget(self.label)

        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.setProperty("dirty", "false")
        self.line_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.line_edit)

        self.source_label = QLabel("From: —")
        self.source_label.setObjectName("SourceHint")
        layout.addWidget(self.source_label)

    def _repolish(self) -> None:
        self.line_edit.style().unpolish(self.line_edit)
        self.line_edit.style().polish(self.line_edit)

    def _on_text_changed(self, text: str) -> None:
        if self._suppress_signal:
            return
        self._is_dirty = text.strip() != self._committed_value.strip()
        self.line_edit.setProperty("dirty", "true" if self._is_dirty else "false")
        self._repolish()
        self.changed.emit(self.key)

    def is_dirty(self) -> bool:
        return self._is_dirty

    def current_text(self) -> str:
        return self.line_edit.text().strip()

    def set_enabled(self, enabled: bool) -> None:
        self.line_edit.setEnabled(enabled)

    def set_committed(self, value: str, source: str, preserve_if_dirty: bool = False) -> None:
        clean_val = "" if value is None else str(value).strip()
        self._committed_value = clean_val
        self._source_text = source or ""
        self.source_label.setText(f"From: {self._source_text}" if self._source_text else "From: —")

        if preserve_if_dirty and self._is_dirty:
            self._is_dirty = self.line_edit.text().strip() != self._committed_value.strip()
            self.line_edit.setProperty("dirty", "true" if self._is_dirty else "false")
            self._repolish()
            return

        self._suppress_signal = True
        self.line_edit.setText(clean_val)
        self._is_dirty = False
        self.line_edit.setProperty("dirty", "false")
        self._repolish()
        self._suppress_signal = False

    def reset_to_committed(self) -> None:
        self.set_committed(self._committed_value, self._source_text, preserve_if_dirty=False)


class DownloadSignals(QObject):
    status_changed = Signal(str, str)
    metadata_updated = Signal(str, object)
    download_finished = Signal(str, object)
    services_ready = Signal(bool, bool, str)


class DownloaderMainWindow(QMainWindow):
    FIELD_SPECS = [
        ("song_title", "Title", "Track title"),
        ("artist", "Artist", "Primary / featured artist(s)"),
        ("remix", "Remix / Remixer", "Optional remix or remixer label"),
        ("album", "Album", "Album or single name"),
        ("album_artist", "Album Artist", "Album artist"),
        ("year", "Year", "Release year (e.g. 2024)"),
        ("genre", "Genre", "Music genre"),
        ("comment", "Comment", "Notes or source URL"),
    ]

    def __init__(self, controller: "gui") -> None:
        super().__init__()
        self.controller = controller
        self.signals = DownloadSignals()
        self.signals.status_changed.connect(self._on_status_changed)
        self.signals.metadata_updated.connect(self._on_metadata_updated)
        self.signals.download_finished.connect(self._on_download_finished)
        self.signals.services_ready.connect(self._on_services_ready)

        self.selected_row_id: str | None = None
        self.field_widgets: dict[str, MetadataFieldWidget] = {}
        self._committed_artwork_bytes: bytes | None = None
        self._pending_artwork_bytes: bytes | None = None
        self._artwork_dirty: bool = False

        self._build_ui()
        self._set_editor_empty()
        self._start_service_check()

    def _build_ui(self) -> None:
        self.setWindowTitle("YTDLP MP3 Downloader")
        self.resize(1060, 700)
        self.setMinimumSize(780, 540)

        icon_png = Path.cwd() / "internal" / "source" / "icon.png"
        icon_ico = Path.cwd() / "internal" / "source" / "icon.ico"
        if icon_png.is_file():
            self.setWindowIcon(QIcon(str(icon_png)))
        elif icon_ico.is_file():
            self.setWindowIcon(QIcon(str(icon_ico)))

        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # --- Main Body Container ---
        body_widget = QWidget()
        body_widget.setObjectName("CentralWidget")
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(16, 14, 16, 12)
        body_layout.setSpacing(12)

        # --- Compact Header Bar ---
        header_card = QFrame()
        header_card.setObjectName("Card")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(14, 10, 14, 10)
        header_layout.setSpacing(12)

        logo_label = QLabel()
        if icon_png.is_file():
            pixmap = QPixmap(str(icon_png)).scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        header_layout.addWidget(logo_label)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title_lbl = QLabel("YTDLP MP3 Downloader")
        title_lbl.setObjectName("AppTitle")
        subtitle_lbl = QLabel("Reliable audio-to-MP3 with automatic cookies and smart tag lookup.")
        subtitle_lbl.setObjectName("AppSubtitle")
        title_col.addWidget(title_lbl)
        title_col.addWidget(subtitle_lbl)
        header_layout.addLayout(title_col, 1)

        open_folder_btn = QPushButton("Open Music Folder")
        open_folder_btn.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        open_folder_btn.clicked.connect(self._open_download_folder)
        header_layout.addWidget(open_folder_btn)

        body_layout.addWidget(header_card)

        # --- Adjustable Left/Right Split Pane ---
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)

        # === LEFT PANE ===
        left_pane = QWidget()
        left_pane.setObjectName("LeftPane")
        left_layout = QVBoxLayout(left_pane)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.setSpacing(12)

        # URL Input Card
        input_card = QFrame()
        input_card.setObjectName("Card")
        input_layout = QHBoxLayout(input_card)
        input_layout.setContentsMargins(12, 10, 12, 10)
        input_layout.setSpacing(8)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube or YouTube Music URL(s) and press Enter...")
        self.url_input.returnPressed.connect(self._handle_add_download)
        input_layout.addWidget(self.url_input, 1)

        paste_btn = QPushButton("Paste")
        paste_btn.setToolTip("Paste URL from clipboard")
        paste_btn.clicked.connect(self._handle_paste_url)
        input_layout.addWidget(paste_btn)

        download_btn = QPushButton("Download")
        download_btn.setObjectName("PrimaryButton")
        download_btn.clicked.connect(self._handle_add_download)
        input_layout.addWidget(download_btn)

        left_layout.addWidget(input_card)

        # Queue Card
        queue_card = QFrame()
        queue_card.setObjectName("Card")
        queue_layout = QVBoxLayout(queue_card)
        queue_layout.setContentsMargins(12, 10, 12, 12)
        queue_layout.setSpacing(10)

        queue_header = QHBoxLayout()
        queue_title = QLabel("Download Queue")
        queue_title.setObjectName("SectionTitle")
        self.queue_count_lbl = QLabel("0 items")
        self.queue_count_lbl.setObjectName("AppSubtitle")
        queue_header.addWidget(queue_title)
        queue_header.addStretch(1)
        queue_header.addWidget(self.queue_count_lbl)

        clear_btn = QPushButton("Clear Completed")
        clear_btn.setObjectName("DangerButton")
        clear_btn.clicked.connect(self._clear_completed_rows)
        queue_header.addWidget(clear_btn)
        queue_layout.addLayout(queue_header)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["URL / Track", "Status"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_table_context_menu)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        self.table.cellDoubleClicked.connect(self._on_row_double_clicked)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        queue_layout.addWidget(self.table, 1)
        left_layout.addWidget(queue_card, 1)

        # === RIGHT PANE (Metadata Editor) ===
        right_pane = QWidget()
        right_pane.setObjectName("RightPane")
        right_outer = QVBoxLayout(right_pane)
        right_outer.setContentsMargins(4, 0, 0, 0)
        right_outer.setSpacing(0)

        editor_card = QFrame()
        editor_card.setObjectName("Card")
        editor_layout = QVBoxLayout(editor_card)
        editor_layout.setContentsMargins(14, 12, 14, 12)
        editor_layout.setSpacing(10)

        editor_header = QHBoxLayout()
        editor_title = QLabel("Metadata Editor")
        editor_title.setObjectName("SectionTitle")
        self.editor_state_lbl = QLabel("No track selected")
        self.editor_state_lbl.setObjectName("AppSubtitle")
        editor_header.addWidget(editor_title)
        editor_header.addStretch(1)
        editor_header.addWidget(self.editor_state_lbl)
        editor_layout.addLayout(editor_header)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        scroll_content = QWidget()
        scroll_content.setObjectName("EditorScrollContent")
        form_layout = QVBoxLayout(scroll_content)
        form_layout.setContentsMargins(0, 2, 6, 4)
        form_layout.setSpacing(10)

        # Thumbnail Section
        thumb_section = QVBoxLayout()
        thumb_section.setSpacing(6)
        thumb_top = QHBoxLayout()
        thumb_top.setSpacing(12)

        self.thumbnail_zone = ThumbnailDropZone()
        self.thumbnail_zone.image_dropped.connect(self._on_thumbnail_changed)
        thumb_top.addWidget(self.thumbnail_zone)

        thumb_actions = QVBoxLayout()
        thumb_actions.setSpacing(6)
        thumb_title = QLabel("Cover Artwork")
        thumb_title.setObjectName("FieldLabel")
        thumb_hint = QLabel("Drag & drop an image onto the preview, or paste/browse below.")
        thumb_hint.setObjectName("AppSubtitle")
        thumb_hint.setWordWrap(True)

        self.paste_thumb_btn = QPushButton("Paste Image")
        self.paste_thumb_btn.setObjectName("SmallButton")
        self.paste_thumb_btn.clicked.connect(self._paste_thumbnail)

        self.browse_thumb_btn = QPushButton("Browse Image...")
        self.browse_thumb_btn.setObjectName("SmallButton")
        self.browse_thumb_btn.clicked.connect(self._browse_thumbnail)

        thumb_actions.addWidget(thumb_title)
        thumb_actions.addWidget(thumb_hint)
        thumb_actions.addWidget(self.paste_thumb_btn)
        thumb_actions.addWidget(self.browse_thumb_btn)
        thumb_actions.addStretch(1)
        thumb_top.addLayout(thumb_actions, 1)

        thumb_section.addLayout(thumb_top)

        self.thumb_source_lbl = QLabel("From: —")
        self.thumb_source_lbl.setObjectName("SourceHint")
        thumb_section.addWidget(self.thumb_source_lbl)
        form_layout.addLayout(thumb_section)

        # Metadata Text Fields
        for key, label_text, placeholder in self.FIELD_SPECS:
            fw = MetadataFieldWidget(key, label_text, placeholder)
            fw.changed.connect(self._on_field_dirty_changed)
            self.field_widgets[key] = fw
            form_layout.addWidget(fw)

        form_layout.addStretch(1)
        scroll_area.setWidget(scroll_content)
        editor_layout.addWidget(scroll_area, 1)

        # Editor Action Footer
        action_bar = QHBoxLayout()
        action_bar.setSpacing(8)
        self.apply_feedback_lbl = QLabel("")
        self.apply_feedback_lbl.setObjectName("AppSubtitle")
        action_bar.addWidget(self.apply_feedback_lbl, 1)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self._reset_editor_changes)
        action_bar.addWidget(self.reset_btn)

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setObjectName("PrimaryButton")
        self.apply_btn.clicked.connect(self._apply_editor_changes)
        action_bar.addWidget(self.apply_btn)
        editor_layout.addLayout(action_bar)

        right_outer.addWidget(editor_card)

        self.splitter.addWidget(left_pane)
        self.splitter.addWidget(right_pane)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setSizes([610, 410])

        body_layout.addWidget(self.splitter, 1)
        outer_layout.addWidget(body_widget, 1)

        # --- Compact Status Footer ---
        footer = QFrame()
        footer.setObjectName("StatusFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 6, 16, 6)
        footer_layout.setSpacing(10)

        self.footer_activity_lbl = QLabel("Ready")
        self.footer_activity_lbl.setObjectName("FooterText")
        footer_layout.addWidget(self.footer_activity_lbl, 1)

        self.ollama_badge = QLabel("Ollama: Checking...")
        self.ollama_badge.setObjectName("FooterStatusMuted")
        self.searx_badge = QLabel("SearXNG: Checking...")
        self.searx_badge.setObjectName("FooterStatusMuted")
        footer_layout.addWidget(self.ollama_badge)
        footer_layout.addWidget(self.searx_badge)

        outer_layout.addWidget(footer)

    def _start_service_check(self) -> None:
        def _worker():
            slm = SLM_work(settings=self.controller.settings)
            searx = SearXNG(settings=self.controller.settings)
            self.controller.slm = slm
            self.controller.searxng = searx
            self.signals.services_ready.emit(slm.is_ready, searx.is_ready, slm.model_name)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_services_ready(self, ollama_ok: bool, searx_ok: bool, model_name: str) -> None:
        if ollama_ok:
            self.ollama_badge.setText(f"Ollama: {model_name}")
            self.ollama_badge.setObjectName("FooterStatusOk")
        else:
            self.ollama_badge.setText("Ollama: Offline")
            self.ollama_badge.setObjectName("FooterStatusWarn")

        if searx_ok:
            self.searx_badge.setText("SearXNG: Ready")
            self.searx_badge.setObjectName("FooterStatusOk")
        else:
            self.searx_badge.setText("SearXNG: Offline")
            self.searx_badge.setObjectName("FooterStatusWarn")

        for widget in (self.ollama_badge, self.searx_badge):
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def _handle_paste_url(self) -> None:
        text = QApplication.clipboard().text().strip()
        if text:
            self.url_input.setText(text)
            self.url_input.setFocus()

    def _handle_add_download(self) -> None:
        raw_text = self.url_input.text().strip()
        if not raw_text:
            return

        urls = [token.strip() for token in raw_text.split() if token.strip()]
        self.url_input.clear()

        for url in urls:
            entry = self.controller.start_download(
                url,
                status_emitter=self.signals.status_changed.emit,
                metadata_emitter=self.signals.metadata_updated.emit,
                finished_emitter=self.signals.download_finished.emit,
            )
            if entry:
                row_idx = self._append_table_row(entry["id"], entry["url"], entry["status"])
                if self.selected_row_id is None:
                    self.table.selectRow(row_idx)
        self._update_footer_activity()

    def _append_table_row(self, row_id: str, url: str, status: str) -> int:
        row_idx = self.table.rowCount()
        self.table.insertRow(row_idx)

        url_item = QTableWidgetItem(url)
        url_item.setData(Qt.UserRole, row_id)
        url_item.setToolTip(url)

        status_item = QTableWidgetItem(status)
        status_item.setForeground(self._status_color(status))

        self.table.setItem(row_idx, 0, url_item)
        self.table.setItem(row_idx, 1, status_item)

        self.table.scrollToBottom()
        self._update_queue_count()
        return row_idx

    @staticmethod
    def _status_color(status_msg: str) -> QColor:
        lower = status_msg.lower()
        if any(word in lower for word in ("error", "failed", "invalid", "empty")):
            return QColor("#F87171")
        if lower == "done" or "downloaded" in lower:
            return QColor("#4CC9D6")
        if any(word in lower for word in ("itunes", "searxng", "ollama", "slm", "ai", "cover", "converting", "embedding")):
            return QColor("#FBBF24")
        return QColor("#EC648E")

    def _find_row_index(self, row_id: str) -> int:
        for idx in range(self.table.rowCount()):
            item = self.table.item(idx, 0)
            if item and item.data(Qt.UserRole) == row_id:
                return idx
        return -1

    def _on_status_changed(self, row_id: str, status_msg: str) -> None:
        row_idx = self._find_row_index(row_id)
        if row_idx < 0:
            return
        status_item = self.table.item(row_idx, 1)
        if status_item:
            status_item.setText(status_msg)
            status_item.setToolTip(status_msg)
            status_item.setForeground(self._status_color(status_msg))

        if self.selected_row_id == row_id:
            data = self.controller.select_row(row_id)
            if data.get("is_processing"):
                self.editor_state_lbl.setText(f"Live: {status_msg}")
            self._update_editor_buttons()
        self._update_footer_activity()

    def _on_metadata_updated(self, row_id: str, metadata_obj: object) -> None:
        if not isinstance(metadata_obj, Metadata_MP3):
            return
        if row_id in self.controller.table_data:
            self.controller.table_data[row_id]["metadata"] = metadata_obj
            if metadata_obj.mp3_path:
                self.controller.table_data[row_id]["mp3_path"] = str(metadata_obj.mp3_path)

        row_idx = self._find_row_index(row_id)
        if row_idx >= 0 and (metadata_obj.artist or metadata_obj.song_title):
            preview_title = build_track_stem(
                metadata_obj.artist,
                metadata_obj.song_title,
                metadata_obj.remix,
                fallback=self.controller.table_data.get(row_id, {}).get("url", ""),
            )
            url_item = self.table.item(row_idx, 0)
            if url_item:
                url_item.setText(preview_title)
                url_item.setToolTip(
                    f"{preview_title}\n{self.controller.table_data.get(row_id, {}).get('url', '')}"
                )

        if self.selected_row_id == row_id:
            self._sync_editor_from_metadata(metadata_obj, preserve_dirty=True)

    def _on_download_finished(self, row_id: str, metadata_obj: object) -> None:
        row_idx = self._find_row_index(row_id)
        if row_idx >= 0 and isinstance(metadata_obj, Metadata_MP3) and metadata_obj.mp3_path:
            stem = Path(metadata_obj.mp3_path).stem
            url_item = self.table.item(row_idx, 0)
            if url_item:
                url_item.setText(stem)
                url_item.setToolTip(f"{stem}\n{self.controller.table_data.get(row_id, {}).get('url', '')}")

        if self.selected_row_id == row_id:
            data = self.controller.select_row(row_id)
            meta = data.get("metadata")
            if isinstance(meta, Metadata_MP3):
                self._sync_editor_from_metadata(meta, preserve_dirty=True)
            self.editor_state_lbl.setText("Ready to edit" if data.get("mp3_path") else data.get("status", ""))
            self._update_editor_buttons()
        self._update_footer_activity()

    def _on_row_selected(self) -> None:
        selected = self.table.selectedItems()
        if not selected:
            self.selected_row_id = None
            self._set_editor_empty()
            return

        row_idx = selected[0].row()
        id_item = self.table.item(row_idx, 0)
        if not id_item:
            return
        row_id = id_item.data(Qt.UserRole)
        self.selected_row_id = row_id
        self._load_selected_into_editor(row_id)

    def _set_editor_empty(self) -> None:
        self.editor_state_lbl.setText("No track selected")
        self.apply_feedback_lbl.setText("")
        self._committed_artwork_bytes = None
        self._pending_artwork_bytes = None
        self._artwork_dirty = False
        self.thumbnail_zone.set_dirty(False)
        self.thumbnail_zone.set_placeholder("Select a track\nto view or edit")
        self.thumb_source_lbl.setText("From: —")
        self.paste_thumb_btn.setEnabled(False)
        self.browse_thumb_btn.setEnabled(False)

        for fw in self.field_widgets.values():
            fw.set_committed("", "", preserve_if_dirty=False)
            fw.set_enabled(False)

        self.apply_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)

    def _load_selected_into_editor(self, row_id: str) -> None:
        data = self.controller.select_row(row_id)
        meta = data.get("metadata")
        is_processing = bool(data.get("is_processing"))

        self.apply_feedback_lbl.setText("")
        self.paste_thumb_btn.setEnabled(True)
        self.browse_thumb_btn.setEnabled(True)
        for fw in self.field_widgets.values():
            fw.set_enabled(True)

        if is_processing:
            self.editor_state_lbl.setText(f"Live: {data.get('status', 'Processing...')}")
        elif data.get("mp3_path"):
            self.editor_state_lbl.setText("Ready to edit")
        else:
            self.editor_state_lbl.setText(data.get("status", "Pending"))

        if isinstance(meta, Metadata_MP3):
            self._sync_editor_from_metadata(meta, preserve_dirty=False)
        else:
            self._committed_artwork_bytes = None
            self._pending_artwork_bytes = None
            self._artwork_dirty = False
            self.thumbnail_zone.set_dirty(False)
            self.thumbnail_zone.set_placeholder("Waiting for\ncover artwork...")
            self.thumb_source_lbl.setText("From: —")
            for fw in self.field_widgets.values():
                fw.set_committed("", "", preserve_if_dirty=False)

        self._update_editor_buttons()

    def _sync_editor_from_metadata(self, meta: Metadata_MP3, preserve_dirty: bool = True) -> None:
        sources = meta.field_sources or {}
        values = {
            "song_title": meta.song_title or "",
            "artist": meta.artist or "",
            "remix": meta.remix or "",
            "album": meta.album or "",
            "album_artist": meta.album_artist or "",
            "year": str(meta.year) if meta.year else "",
            "genre": meta.genre or "",
            "comment": "; ".join(c for c in meta.comment if c) if meta.comment else "",
        }

        for key, fw in self.field_widgets.items():
            fw.set_committed(values.get(key, ""), sources.get(key, ""), preserve_if_dirty=preserve_dirty)

        art_source = sources.get("artwork_url", "")
        self.thumb_source_lbl.setText(f"From: {art_source}" if art_source else "From: —")

        if meta.artwork_bytes:
            self._committed_artwork_bytes = meta.artwork_bytes
            if not (preserve_dirty and self._artwork_dirty):
                self._pending_artwork_bytes = None
                self._artwork_dirty = False
                self.thumbnail_zone.set_dirty(False)
                self.thumbnail_zone.set_image_bytes(meta.artwork_bytes)
        elif not (preserve_dirty and self._artwork_dirty):
            self._committed_artwork_bytes = None
            self._pending_artwork_bytes = None
            self._artwork_dirty = False
            self.thumbnail_zone.set_dirty(False)
            self.thumbnail_zone.set_placeholder("Drop or Paste\nCover Image")

        self._update_editor_buttons()

    def _on_thumbnail_changed(self, jpeg_bytes: bytes) -> None:
        if not self.selected_row_id:
            return
        if self.thumbnail_zone.set_image_bytes(jpeg_bytes):
            self._pending_artwork_bytes = jpeg_bytes
            self._artwork_dirty = True
            self.thumbnail_zone.set_dirty(True)
            self.apply_feedback_lbl.setText("")
            self._update_editor_buttons()

    def _paste_thumbnail(self) -> None:
        if not self.selected_row_id:
            return
        if not self.thumbnail_zone.paste_from_clipboard():
            self.apply_feedback_lbl.setText("No image found in clipboard.")

    def _browse_thumbnail(self) -> None:
        if not self.selected_row_id:
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Cover Image",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if not file_path:
            return
        try:
            jpeg = Metadata_MP3.convert_image_bytes_to_jpeg(Path(file_path).read_bytes())
            self._on_thumbnail_changed(jpeg)
        except Exception:
            self.apply_feedback_lbl.setText("Failed to load image.")

    def _on_field_dirty_changed(self, _key: str) -> None:
        self.apply_feedback_lbl.setText("")
        self._update_editor_buttons()

    def _count_dirty_fields(self) -> int:
        count = sum(1 for fw in self.field_widgets.values() if fw.is_dirty())
        if self._artwork_dirty:
            count += 1
        return count

    def _update_editor_buttons(self) -> None:
        if not self.selected_row_id:
            self.apply_btn.setEnabled(False)
            self.reset_btn.setEnabled(False)
            return

        data = self.controller.select_row(self.selected_row_id)
        is_processing = bool(data.get("is_processing"))
        has_file = bool(data.get("mp3_path")) and Path(data["mp3_path"]).is_file()
        dirty_count = self._count_dirty_fields()

        self.reset_btn.setEnabled(dirty_count > 0)
        self.apply_btn.setEnabled(dirty_count > 0 and has_file and not is_processing)

        if dirty_count > 0:
            if is_processing:
                self.apply_feedback_lbl.setText(f"{dirty_count} pending (wait for download)")
            elif not has_file:
                self.apply_feedback_lbl.setText("No MP3 file to apply yet")
            else:
                suffix = "change" if dirty_count == 1 else "changes"
                self.apply_feedback_lbl.setText(f"{dirty_count} unapplied {suffix}")

    def _reset_editor_changes(self) -> None:
        if not self.selected_row_id:
            return
        for fw in self.field_widgets.values():
            fw.reset_to_committed()

        self._pending_artwork_bytes = None
        self._artwork_dirty = False
        self.thumbnail_zone.set_dirty(False)
        if self._committed_artwork_bytes:
            self.thumbnail_zone.set_image_bytes(self._committed_artwork_bytes)
        else:
            self.thumbnail_zone.set_placeholder("Drop or Paste\nCover Image")

        self.apply_feedback_lbl.setText("Changes reset.")
        self._update_editor_buttons()

    def _apply_editor_changes(self) -> None:
        if not self.selected_row_id:
            return
        row_id = self.selected_row_id

        updates: dict[str, object] = {}
        dirty_keys: list[str] = []
        for key, fw in self.field_widgets.items():
            if fw.is_dirty():
                val = fw.current_text()
                if key == "year" and val:
                    try:
                        val = int(val)
                    except ValueError:
                        self.apply_feedback_lbl.setText("Year must be a number.")
                        return
                updates[key] = val
                dirty_keys.append(key)

        new_artwork = self._pending_artwork_bytes if self._artwork_dirty else None
        if not dirty_keys and new_artwork is None:
            return

        ok, msg, updated_meta = self.controller.apply_manual_metadata(row_id, updates, new_artwork)
        if not ok or not isinstance(updated_meta, Metadata_MP3):
            self.apply_feedback_lbl.setText(msg)
            return

        self._artwork_dirty = False
        self._pending_artwork_bytes = None
        self._sync_editor_from_metadata(updated_meta, preserve_dirty=False)

        row_idx = self._find_row_index(row_id)
        if row_idx >= 0 and updated_meta.mp3_path:
            stem = Path(updated_meta.mp3_path).stem
            url_item = self.table.item(row_idx, 0)
            if url_item:
                url_item.setText(stem)
                url_item.setToolTip(f"{stem}\n{self.controller.table_data.get(row_id, {}).get('url', '')}")
            status_item = self.table.item(row_idx, 1)
            if status_item:
                status_item.setText("Done")
                status_item.setForeground(self._status_color("Done"))

        self.apply_feedback_lbl.setText("Applied to MP3.")
        self._update_editor_buttons()

    def _on_row_double_clicked(self, row_idx: int, _col: int) -> None:
        id_item = self.table.item(row_idx, 0)
        if not id_item:
            return
        row_id = id_item.data(Qt.UserRole)
        data = self.controller.select_row(row_id)
        mp3_path = data.get("mp3_path")
        if mp3_path and Path(mp3_path).exists():
            _open_path_in_file_manager(Path(mp3_path))

    def _show_table_context_menu(self, pos) -> None:
        row_idx = self.table.rowAt(pos.y())
        if row_idx < 0:
            return
        self.table.selectRow(row_idx)
        id_item = self.table.item(row_idx, 0)
        if not id_item:
            return
        row_id = id_item.data(Qt.UserRole)
        data = self.controller.select_row(row_id)

        menu = QMenu(self)
        copy_action = QAction("Copy URL", self)
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(data.get("url", "")))
        menu.addAction(copy_action)

        retry_action = QAction("Retry Download", self)
        retry_action.triggered.connect(lambda: self._retry_url(data.get("url", "")))
        menu.addAction(retry_action)

        mp3_path = data.get("mp3_path")
        if mp3_path and Path(mp3_path).exists():
            reveal_action = QAction("Show File in Folder", self)
            reveal_action.triggered.connect(lambda: _open_path_in_file_manager(Path(mp3_path)))
            menu.addAction(reveal_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _retry_url(self, url: str) -> None:
        if not url:
            return
        entry = self.controller.start_download(
            url,
            status_emitter=self.signals.status_changed.emit,
            metadata_emitter=self.signals.metadata_updated.emit,
            finished_emitter=self.signals.download_finished.emit,
        )
        if entry:
            self._append_table_row(entry["id"], entry["url"], entry["status"])
            self._update_footer_activity()

    def _clear_completed_rows(self) -> None:
        rows_to_delete = []
        for idx in range(self.table.rowCount()):
            status_item = self.table.item(idx, 1)
            if not status_item:
                continue
            status_text = status_item.text().lower()
            if status_text == "done" or any(k in status_text for k in ("downloaded", "error", "failed", "invalid", "empty")):
                rows_to_delete.append(idx)

        for idx in reversed(rows_to_delete):
            id_item = self.table.item(idx, 0)
            row_id = id_item.data(Qt.UserRole) if id_item else None
            if row_id == self.selected_row_id:
                self.selected_row_id = None
                self._set_editor_empty()
            self.table.removeRow(idx)

        active_ids = []
        for idx in range(self.table.rowCount()):
            id_item = self.table.item(idx, 0)
            if id_item:
                active_ids.append(id_item.data(Qt.UserRole))
        self.controller.clear_completed(active_ids)
        self._update_queue_count()
        self._update_footer_activity()

    def _update_queue_count(self) -> None:
        count = self.table.rowCount()
        self.queue_count_lbl.setText(f"{count} item" if count == 1 else f"{count} items")

    def _update_footer_activity(self) -> None:
        active = sum(1 for item in self.controller.table_data.values() if item.get("is_processing"))
        if active > 0:
            self.footer_activity_lbl.setText(f"Processing {active} track{'s' if active != 1 else ''}...")
        else:
            self.footer_activity_lbl.setText("Ready")

    def _open_download_folder(self) -> None:
        folder = Path.cwd() / self.controller.settings["app"]["download_folder"]
        os.makedirs(folder, exist_ok=True)
        _open_path_in_file_manager(folder)

    def closeEvent(self, event) -> None:
        self.controller.on_window_closing()
        super().closeEvent(event)


class gui:
    """
    Handles PySide6 desktop window lifecycle, background download orchestration,
    and session-scoped metadata editing.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.slm: SLM_work | None = None
        self.searxng: SearXNG | None = None
        self.COOKIE_FILE = self.settings["yt_downloader"]["cookie_file"]
        self.row_counter = 1

        # Runtime-only structure:
        # {row_id: {"url": str, "status": str, "mp3_path": str, "metadata": Metadata_MP3, "is_processing": bool}}
        self.table_data: dict[str, dict] = {}
        self.window: DownloaderMainWindow | None = None

        self.cleanup_cookie()

    def cleanup_cookie(self) -> None:
        PIPELINE = f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"
        if os.path.exists(self.COOKIE_FILE):
            try:
                os.remove(self.COOKIE_FILE)
            except Exception:
                logger.warning("Failed to remove cookie file.")

    def init_ui(self) -> None:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        app.setApplicationName("YTDLP MP3 Downloader")
        app.setStyle("Fusion")
        app.setStyleSheet(DARK_STYLESHEET)

        self.window = DownloaderMainWindow(self)
        self.window.show()
        app.exec()

    def on_window_closing(self) -> None:
        PIPELINE = f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"
        self.cleanup_cookie()
        logger.info("Cookie file cleaned up on exit.")

    def start_download(
        self,
        url: str,
        status_emitter=None,
        metadata_emitter=None,
        finished_emitter=None,
    ) -> dict | None:
        url = url.strip()
        if not url:
            return None

        current_id = str(self.row_counter)
        self.row_counter += 1

        self.table_data[current_id] = {
            "url": url,
            "status": "Queued",
            "mp3_path": "",
            "metadata": Metadata_MP3(),
            "is_processing": True,
        }

        threading.Thread(
            target=self.download_instance,
            args=(url, current_id, status_emitter, metadata_emitter, finished_emitter),
            daemon=True,
        ).start()

        return {
            "id": current_id,
            "url": url,
            "status": "Queued",
        }

    def download_instance(
        self,
        url: str,
        row_id: str,
        status_emitter=None,
        metadata_emitter=None,
        finished_emitter=None,
    ) -> None:
        PIPELINE = f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"

        def ui_progress_callback(status_msg: str) -> None:
            if row_id in self.table_data:
                if self.table_data[row_id]["status"] == status_msg:
                    return
                self.table_data[row_id]["status"] = status_msg
                if status_emitter:
                    status_emitter(row_id, status_msg)

        def ui_metadata_callback(meta_snapshot: Metadata_MP3) -> None:
            if row_id in self.table_data:
                self.table_data[row_id]["metadata"] = meta_snapshot
                if meta_snapshot.mp3_path:
                    self.table_data[row_id]["mp3_path"] = str(meta_snapshot.mp3_path)
                if metadata_emitter:
                    metadata_emitter(row_id, meta_snapshot)

        logger.info(f"Start downloading using GUI: {url}")
        metadata = Metadata_MP3()
        try:
            if self.slm is None:
                self.slm = SLM_work(settings=self.settings)
            if self.searxng is None:
                self.searxng = SearXNG(settings=self.settings)

            dn = download(
                settings=self.settings,
                slm=self.slm,
                searxng=self.searxng,
                progress_callback=ui_progress_callback,
                metadata_callback=ui_metadata_callback,
            )
            metadata = dn.download(url=url)
        except ValueError as e:
            if len(e.args) > 0 and e.args[0] in ("URL is empty.", "URL is invalid."):
                logger.error(f"URL is invalid: {url}")
                ui_progress_callback("Invalid URL")
            else:
                ui_progress_callback("Failed")
                logger.error(f"An error occurred during download: {e}")
        except Exception as e:
            ui_progress_callback("Failed")
            logger.error(f"An error occurred during download: {e}")
        finally:
            if row_id in self.table_data:
                self.table_data[row_id]["is_processing"] = False

        if metadata.mp3_path and row_id in self.table_data:
            self.table_data[row_id]["mp3_path"] = str(metadata.mp3_path)
            self.table_data[row_id]["metadata"] = metadata
            ui_progress_callback("Done")
            logger.info(f"Download completed for: {url}")

        if finished_emitter:
            finished_emitter(row_id, metadata)

    def apply_manual_metadata(
        self,
        row_id: str,
        updates: dict,
        new_artwork_bytes: bytes | None = None,
    ) -> tuple[bool, str, Metadata_MP3 | None]:
        PIPELINE = f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"
        if row_id not in self.table_data:
            return False, "Item not found.", None

        entry = self.table_data[row_id]
        mp3_path_str = entry.get("mp3_path", "")
        if not mp3_path_str or not Path(mp3_path_str).is_file():
            return False, "MP3 file does not exist.", None

        meta: Metadata_MP3 = entry.get("metadata") or Metadata_MP3()
        meta.mp3_path = mp3_path_str

        rename_needed = False
        for key, val in updates.items():
            if key == "comment":
                items = [part.strip() for part in str(val).replace("\n", ";").split(";") if part.strip()]
                meta.comment = items
                meta.field_sources["comment"] = "Manual"
            elif key == "year":
                meta.year = int(val) if val else None
                meta.field_sources["year"] = "Manual" if val else ""
            elif key in ("song_title", "artist", "remix", "album", "album_artist", "genre"):
                clean = str(val).strip() if val is not None else ""
                setattr(meta, key, clean or None)
                meta.field_sources[key] = "Manual" if clean else ""
                if key in ("song_title", "artist", "remix"):
                    rename_needed = True

        if new_artwork_bytes is not None:
            meta.artwork_bytes = new_artwork_bytes
            meta.artwork_url = None
            meta.field_sources["artwork_url"] = "Manual"

        try:
            meta.embed_metadata(Path(mp3_path_str), clear_empty=True)
        except Exception as e:
            logger.error(f"Failed to embed manual metadata: {e}")
            return False, f"Failed to write tags: {e}", None

        if rename_needed:
            try:
                current_path = Path(mp3_path_str)
                folder = current_path.parent
                new_stem = build_track_stem(
                    artist=meta.artist,
                    title=meta.song_title,
                    remix=meta.remix,
                    fallback=current_path.stem,
                )
                target_path = folder / f"{new_stem}.mp3"
                if current_path.resolve() != target_path.resolve():
                    if target_path.exists():
                        counter = 2
                        while (folder / f"{new_stem} ({counter}).mp3").exists():
                            counter += 1
                        target_path = folder / f"{new_stem} ({counter}).mp3"
                    os.rename(current_path, target_path)
                    meta.mp3_path = str(target_path)
                    entry["mp3_path"] = str(target_path)
                    entry["status"] = "Done"
            except Exception as e:
                logger.warning(f"Manual metadata applied, but rename failed: {e}")

        entry["metadata"] = meta
        logger.info(f"Applied manual metadata edits for row {row_id}: {meta.mp3_path}")
        return True, "Applied", meta.clone()

    def select_row(self, row_id: str) -> dict:
        if row_id in self.table_data:
            return dict(self.table_data[row_id])
        return {"url": "", "status": "", "mp3_path": "", "metadata": None, "is_processing": False}

    def clear_completed(self, active_ids: list) -> bool:
        to_remove = [k for k in list(self.table_data.keys()) if k not in active_ids]
        for k in to_remove:
            self.table_data.pop(k, None)
        return True