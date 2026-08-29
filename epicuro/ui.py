from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import uuid
import threading
import time

from PySide6.QtCore import QObject, Qt, Signal, QSize, QRectF, QMimeData, QUrl
from PySide6.QtGui import QAction, QActionGroup, QBrush, QColor, QDrag, QKeySequence, QPainter, QPen, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QMenu,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .icons import make_icon
from .platform_utils import enable_dark_titlebar

from .core import (
    APP_NAME,
    APP_VERSION,
    DATA_DIR,
    DOWNLOAD_DIR,
    CancelledByUser,
    DownloadEngine,
    HistoryStore,
    MediaInfo,
    SettingsStore,
    analyze_media,
    cleanup_partial_downloads,
    detect_service,
    find_partial_downloads,
    history_item,
    human_bytes,
    human_eta,
    human_speed,
    normalize_media_url,
    open_file,
    open_in_file_manager,
    runtime_diagnostics,
    validate_download_directory,
)


# ---------------------------------------------------------------------------
# Interface compacta inspirada em gerenciadores clássicos, com controles atuais.
# ---------------------------------------------------------------------------
APP_QSS = r"""
QMainWindow, QDialog {
    background: #0B0F14;
    color: #E6EDF5;
    font-family: "Segoe UI Variable", "Segoe UI", Arial;
    font-size: 12px;
}
QWidget {
    color: #E6EDF5;
    font-family: "Segoe UI Variable", "Segoe UI", Arial;
    font-size: 12px;
}
QMenuBar {
    background: #0E141C;
    border-bottom: 1px solid #202B39;
    padding: 2px 4px;
}
QMenuBar::item {
    background: transparent;
    padding: 5px 9px;
    border-radius: 5px;
}
QMenuBar::item:selected { background: #182231; }
QMenu {
    background: #111821;
    border: 1px solid #293646;
    padding: 5px;
}
QMenu::item { padding: 7px 30px 7px 24px; border-radius: 4px; }
QMenu::item:selected { background: #244A7A; color: #FFFFFF; }
QToolBar#MainToolbar {
    background: #0F1620;
    border: none;
    border-bottom: 1px solid #223043;
    spacing: 3px;
    padding: 7px 8px 6px 8px;
}
QToolBar#MainToolbar::separator {
    background: #263345;
    width: 1px;
    margin: 10px 6px;
}
QToolBar#MainToolbar QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 6px 10px 5px 10px;
    min-width: 68px;
    min-height: 56px;
    color: #DCE7F3;
}
QToolBar#MainToolbar QToolButton:hover {
    background: #182332;
    border: 1px solid #304258;
}
QToolBar#MainToolbar QToolButton:pressed,
QToolBar#MainToolbar QToolButton:checked {
    background: #20334C;
    border: 1px solid #4B78AC;
}
QToolBar#MainToolbar QToolButton:disabled { color: #596879; }
QToolBar#SideToolbar {
    background: #0E141C;
    border: 1px solid #202B39;
    border-radius: 8px;
    spacing: 3px;
    padding: 5px 3px;
}
QToolBar#SideToolbar::separator {
    background: #263345;
    height: 1px;
    margin: 5px 4px;
}
QToolBar#SideToolbar QToolButton {
    min-width: 34px;
    min-height: 34px;
    border: 1px solid transparent;
    border-radius: 7px;
    padding: 3px;
}
QToolBar#SideToolbar QToolButton:hover {
    background: #172231;
    border: 1px solid #304258;
}
QToolBar#SideToolbar QToolButton:checked {
    background: #20334C;
    border: 1px solid #4B78AC;
}
QFrame#Pane {
    background: #10161E;
    border: 1px solid #253244;
    border-radius: 8px;
}
QFrame#PaneHeader {
    background: #151E2A;
    border: none;
    border-bottom: 1px solid #28384B;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}
QLabel#PaneTitle {
    color: #EEF5FC;
    font-weight: 650;
    font-size: 13px;
    padding-left: 3px;
}
QLabel#PaneHint { color: #8190A3; font-size: 11px; }
QTableWidget {
    background: #0F151D;
    alternate-background-color: #121A24;
    gridline-color: #202B39;
    border: none;
    selection-background-color: #214B78;
    selection-color: #FFFFFF;
    outline: none;
}
QTableWidget::item { padding: 2px 5px; }
QTableWidget::item:hover { background: #172333; }
QHeaderView::section {
    background: #151E29;
    color: #AFC0D4;
    border: none;
    border-right: 1px solid #243143;
    border-bottom: 1px solid #2A394C;
    padding: 6px 7px;
    font-weight: 600;
}
QPushButton {
    min-height: 28px;
    padding: 3px 11px;
    border: 1px solid #314257;
    border-radius: 7px;
    background: #16202C;
    color: #DCE7F3;
}
QPushButton:hover {
    border: 1px solid #4D6684;
    background: #1C2A3A;
}
QPushButton:pressed { background: #23364B; }
QPushButton:focus { border: 1px solid #5B9CFF; }
QPushButton:disabled {
    color: #5D6A78;
    background: #111821;
    border-color: #202A36;
}
QPushButton#PrimaryButton {
    background: #2563A9;
    border: 1px solid #3C7DCA;
    color: white;
    font-weight: 600;
}
QPushButton#PrimaryButton:hover { background: #2D72BF; border-color: #65A7F4; }
QPushButton#DangerButton:hover { background: #3A1D25; border-color: #9F4659; }
QLineEdit, QComboBox {
    min-height: 29px;
    background: #0C1219;
    color: #E7EEF7;
    border: 1px solid #314052;
    border-radius: 7px;
    padding: 2px 8px;
    selection-background-color: #2E67A6;
    selection-color: white;
}
QLineEdit:hover, QComboBox:hover { border-color: #445970; }
QLineEdit:focus, QComboBox:focus { border: 1px solid #5B9CFF; }
QComboBox QAbstractItemView {
    background: #111821;
    color: #E7EEF7;
    border: 1px solid #314052;
    selection-background-color: #244A7A;
}
QGroupBox {
    border: 1px solid #283648;
    border-radius: 8px;
    margin-top: 11px;
    padding-top: 11px;
    background: #101720;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 9px;
    padding: 0 5px;
    color: #B9C8D9;
}
QCheckBox { spacing: 7px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #42546B;
    border-radius: 4px;
    background: #0C1219;
}
QCheckBox::indicator:checked {
    background: #4A8FE7;
    border-color: #69A7F2;
}
QStatusBar {
    background: #0D131B;
    border-top: 1px solid #223043;
    min-height: 24px;
}
QStatusBar QLabel {
    color: #93A4B8;
    border-right: 1px solid #253244;
    padding: 2px 9px;
}
QSplitter::handle {
    background: #0B0F14;
    height: 8px;
}
QScrollBar:vertical {
    background: #0C1118; width: 11px; margin: 0;
}
QScrollBar::handle:vertical {
    background: #2D3D51; min-height: 26px; border-radius: 5px;
}
QScrollBar::handle:vertical:hover { background: #3C516A; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal {
    background: #0C1118; height: 11px; margin: 0;
}
QScrollBar::handle:horizontal {
    background: #2D3D51; min-width: 26px; border-radius: 5px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
QToolTip {
    background: #111A25;
    color: #F2F6FB;
    border: 1px solid #33475F;
    border-radius: 6px;
    padding: 5px 7px;
}
QPushButton#QuietButton {
    background: transparent;
    border: 1px solid transparent;
    color: #AAB8C8;
}
QPushButton#QuietButton:hover {
    background: #172230;
    border-color: #2A3A4D;
    color: #F0F5FB;
}
QPushButton#LibraryActionButton {
    min-height: 30px;
    padding: 4px 10px;
    background: #141F2B;
    border-color: #2A3B50;
}
QPushButton#LibraryActionButton:hover {
    background: #1B2A3A;
    border-color: #46617E;
}
QLabel#CountBadge {
    background: #1A2B3F;
    color: #8FC0FF;
    border: 1px solid #31547A;
    border-radius: 9px;
    padding: 1px 7px;
    font-size: 10px;
    font-weight: 650;
}
QLabel#DragHint {
    color: #7F90A5;
    font-size: 10px;
    padding: 0 3px;
}
QFrame#SummaryCard {
    background: #0E151E;
    border: 1px solid #223044;
    border-radius: 8px;
}
QLineEdit#LibrarySearch {
    min-width: 190px;
    max-width: 260px;
}
QDialogButtonBox QPushButton {
    min-width: 92px;
}
"""


class ClassicProgressBar(QWidget):
    """Barra azul segmentada, estilo gerenciador de downloads antigo."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._value = 0
        self.setMinimumHeight(17)
        self.setMaximumHeight(17)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def setValue(self, value: int | float) -> None:
        self._value = max(0, min(100, int(value)))
        self.update()

    def value(self) -> int:
        return self._value

    def paintEvent(self, _event) -> None:  # noqa: N802 - API Qt
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)
        r = self.rect().adjusted(0, 0, -1, -1)
        p.fillRect(r, QColor("#0A1017"))
        p.setPen(QPen(QColor("#33455C"), 1))
        p.drawRect(r)

        inner = r.adjusted(2, 2, -2, -2)
        if inner.width() <= 0 or inner.height() <= 0:
            return

        segment_w = 6
        gap = 1
        filled_px = inner.width() * (self._value / 100.0)
        x = inner.left()
        while x <= inner.right():
            w = min(segment_w, inner.right() - x + 1)
            if (x - inner.left()) < filled_px:
                segment_right = min(x + w, inner.left() + int(filled_px))
                if segment_right > x:
                    p.fillRect(QRectF(x, inner.top(), segment_right - x, inner.height()), QColor("#347DDF"))
                    p.fillRect(QRectF(x, inner.top(), segment_right - x, max(1, inner.height() // 4)), QColor("#6EA9F4"))
            x += segment_w + gap


class ProgressCell(QWidget):
    def __init__(self):
        super().__init__()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 1, 4, 1)
        lay.setSpacing(5)
        self.bar = ClassicProgressBar()
        self.percent = QLabel("0%")
        self.percent.setFixedWidth(34)
        self.percent.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lay.addWidget(self.bar, 1)
        lay.addWidget(self.percent)

    def set_value(self, value: float | int) -> None:
        value = max(0, min(100, int(value)))
        self.bar.setValue(value)
        self.percent.setText(f"{value}%")



FILE_LIST_ROLE = 0x0101
HISTORY_ID_ROLE = 0x0102


class DraggableFileTable(QTableWidget):
    """Library table that exports real files through the native OS drag protocol.

    Qt converts local-file URLs to CF_HDROP on Windows, so rows can be dragged
    straight to Explorer, Desktop and any application that accepts file drops.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setDefaultDropAction(Qt.CopyAction)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def selected_file_paths(self) -> list[str]:
        rows = sorted({index.row() for index in self.selectionModel().selectedRows(0)})
        if not rows and self.currentRow() >= 0:
            rows = [self.currentRow()]
        paths: list[str] = []
        seen: set[str] = set()
        for row in rows:
            item = self.item(row, 0)
            if not item:
                continue
            stored = item.data(FILE_LIST_ROLE)
            candidates = stored if isinstance(stored, (list, tuple)) else [item.data(Qt.UserRole)]
            for raw in candidates:
                if not raw:
                    continue
                path = str(Path(str(raw)).expanduser().resolve())
                if path in seen or not Path(path).is_file():
                    continue
                seen.add(path)
                paths.append(path)
        return paths

    def startDrag(self, _supported_actions) -> None:  # noqa: N802 - Qt API
        files = self.selected_file_paths()
        if not files:
            return
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(path) for path in files])
        mime.setText("\n".join(files))
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setPixmap(make_icon("file", 34).pixmap(34, 34))
        drag.exec(Qt.CopyAction)


class AnalyzeWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self) -> None:
        try:
            self.finished.emit(analyze_media(self.url))
        except Exception as exc:
            self.failed.emit(str(exc))


class DownloadWorker(QObject):
    progress = Signal(str, object)
    finished = Signal(str, object)
    failed = Signal(str, str)
    cancelled = Signal(str)

    def __init__(self, job_id: str, info: MediaInfo, mode: str, quality: str, playlist_mode: str, output_dir: str):
        super().__init__()
        self.job_id = job_id
        self.info = info
        self.mode = mode
        self.quality = quality
        self.playlist_mode = playlist_mode
        self.engine = DownloadEngine(output_dir)
        self._last_progress_emit = 0.0
        self._last_stage = ""

    def _emit_progress(self, data: dict) -> None:
        # yt-dlp can fire progress hooks many times per second. Limiting visual
        # updates keeps the Qt event queue responsive without slowing downloads.
        now = time.monotonic()
        stage = str(data.get("stage") or "")
        important = stage != self._last_stage or float(data.get("percent") or 0) >= 100
        if important or now - self._last_progress_emit >= 0.08:
            self._last_progress_emit = now
            self._last_stage = stage
            self.progress.emit(self.job_id, data)

    def run(self) -> None:
        try:
            files = self.engine.download(
                self.info.url,
                self.mode,
                self.quality,
                self.playlist_mode,
                progress=self._emit_progress,
            )
            self.finished.emit(self.job_id, files)
        except CancelledByUser:
            self.cancelled.emit(self.job_id)
        except Exception as exc:
            # yt-dlp may wrap exceptions raised by a progress hook. If the user
            # requested stop/pause, keep cancellation as the final state.
            if self.engine.cancel_event.is_set():
                self.cancelled.emit(self.job_id)
            else:
                self.failed.emit(self.job_id, str(exc))

    def cancel(self) -> None:
        self.engine.cancel()


class AddDownloadDialog(QDialog):
    def __init__(self, settings: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.settings = settings
        self.setObjectName("AddDownloadDialog")
        self.setWindowTitle("Novo download")
        self.setModal(True)
        self.resize(620, 330)
        self.setMinimumWidth(560)
        enable_dark_titlebar(self)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(12)

        hero = QFrame()
        hero.setObjectName("SummaryCard")
        hero_lay = QHBoxLayout(hero)
        hero_lay.setContentsMargins(12, 10, 12, 10)
        hero_lay.setSpacing(11)
        icon = QLabel()
        icon.setPixmap(make_icon("new", 34).pixmap(34, 34))
        hero_lay.addWidget(icon, 0, Qt.AlignTop)
        texts = QVBoxLayout()
        texts.setSpacing(1)
        title = QLabel("Adicionar à fila")
        title.setObjectName("PaneTitle")
        subtitle = QLabel("Cole um link e escolha como salvar.")
        subtitle.setObjectName("PaneHint")
        texts.addWidget(title)
        texts.addWidget(subtitle)
        hero_lay.addLayout(texts, 1)
        root.addWidget(hero)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        url_box = QVBoxLayout()
        url_row = QHBoxLayout()
        url_row.setSpacing(7)
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://youtube.com/... ou https://open.spotify.com/...")
        self.url_edit.setClearButtonEnabled(True)
        paste = QPushButton(make_icon("link", 19), "Colar")
        paste.setIconSize(QSize(17, 17))
        paste.setToolTip("Colar link da área de transferência")
        paste.clicked.connect(self._paste)
        url_row.addWidget(self.url_edit, 1)
        url_row.addWidget(paste)
        url_box.addLayout(url_row)
        self.url_state = QLabel("Cole um link válido para continuar")
        self.url_state.setObjectName("PaneHint")
        url_box.addWidget(self.url_state)
        form.addRow("Link:", url_box)

        self.mode = QComboBox()
        self.mode.addItem(make_icon("video", 18), "Vídeo · MP4", "video")
        self.mode.addItem(make_icon("audio", 18), "Áudio · MP3", "audio")
        self.mode.addItem(make_icon("audio", 18), "Spotify", "spotify")
        preferred = settings.get("mode", "video")
        idx = max(0, self.mode.findData(preferred))
        self.mode.setCurrentIndex(idx)
        self.mode.currentIndexChanged.connect(self._update_quality)
        form.addRow("Formato:", self.mode)

        self.quality = QComboBox()
        form.addRow("Qualidade:", self.quality)

        destination = QLabel(str(Path(settings.get("download_dir", str(DOWNLOAD_DIR)))))
        destination.setObjectName("PaneHint")
        destination.setTextInteractionFlags(Qt.TextSelectableByMouse)
        destination.setToolTip(destination.text())
        form.addRow("Destino:", destination)
        root.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")
        self.ok_button = buttons.button(QDialogButtonBox.Ok)
        self.ok_button.setText("Analisar e adicionar")
        self.ok_button.setIcon(make_icon("analyze", 18))
        self.ok_button.setObjectName("PrimaryButton")
        buttons.accepted.connect(self._accept_checked)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.url_edit.textChanged.connect(self._auto_detect)
        QShortcut(QKeySequence("Ctrl+V"), self, activated=self._paste)
        self._update_quality()

        clip = QApplication.clipboard().text().strip()
        if clip.lower().startswith(("http://", "https://")):
            self.url_edit.setText(clip)
        self._validate()
        self.url_edit.setFocus()
        self.url_edit.selectAll()

    def _paste(self) -> None:
        text = QApplication.clipboard().text().strip()
        if text:
            self.url_edit.setText(text)

    def _auto_detect(self, text: str) -> None:
        service = detect_service(text.strip())
        if service == "spotify":
            idx = self.mode.findData("spotify")
            if idx >= 0:
                self.mode.setCurrentIndex(idx)
        elif self.mode.currentData() == "spotify":
            preferred = self.settings.get("mode", "video")
            if preferred == "spotify":
                preferred = "video"
            idx = self.mode.findData(preferred)
            if idx >= 0:
                self.mode.setCurrentIndex(idx)
        self._validate()

    def _validate(self) -> bool:
        text = self.url_edit.text()
        try:
            normalized = normalize_media_url(text)
        except ValueError as exc:
            self.ok_button.setEnabled(False)
            self.url_state.setText(str(exc))
            self.url_state.setStyleSheet("color:#7F90A5;" if not text.strip() else "color:#FF7A8C;")
            return False

        service = detect_service(normalized)
        label = {"youtube": "YouTube detectado", "spotify": "Spotify detectado"}.get(service, "Link válido")
        self.ok_button.setEnabled(True)
        self.url_state.setText(label)
        self.url_state.setStyleSheet("color:#65D894;")
        return True

    def _update_quality(self) -> None:
        current = self.mode.currentData()
        self.quality.clear()
        if current == "video":
            options = [
                ("Máxima disponível", "best"),
                ("4K · 2160p", "2160p"),
                ("2K · 1440p", "1440p"),
                ("Full HD · 1080p", "1080p"),
                ("HD · 720p", "720p"),
                ("SD · 480p", "480p"),
            ]
            wanted = self.settings.get("video_quality", "1080p")
        elif current == "audio":
            options = [("320 kbps · máxima", "320"), ("256 kbps", "256"), ("192 kbps", "192"), ("128 kbps", "128")]
            wanted = self.settings.get("audio_quality", "320")
        else:
            options = [("Automática · melhor disponível", "best")]
            wanted = "best"
        for text, data in options:
            self.quality.addItem(text, data)
        idx = self.quality.findData(wanted)
        self.quality.setCurrentIndex(idx if idx >= 0 else 0)

    def _accept_checked(self) -> None:
        if not self._validate():
            self.url_edit.setFocus()
            return
        self.accept()

    def values(self) -> tuple[str, str, str]:
        return normalize_media_url(self.url_edit.text()), str(self.mode.currentData()), str(self.quality.currentData())


class OptionsDialog(QDialog):
    def __init__(self, settings: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.settings = dict(settings)
        self.setWindowTitle("Opções")
        self.resize(590, 300)
        self.setMinimumWidth(540)
        enable_dark_titlebar(self)

        root = QVBoxLayout(self)
        root.setContentsMargins(15, 14, 15, 14)
        root.setSpacing(11)

        header = QFrame()
        header.setObjectName("SummaryCard")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(12, 9, 12, 9)
        icon = QLabel(); icon.setPixmap(make_icon("settings", 32).pixmap(32, 32))
        hl.addWidget(icon)
        text_lay = QVBoxLayout(); text_lay.setSpacing(1)
        title = QLabel("Preferências do Epicuro"); title.setObjectName("PaneTitle")
        desc = QLabel("Destino e comportamento dos downloads."); desc.setObjectName("PaneHint")
        text_lay.addWidget(title); text_lay.addWidget(desc)
        hl.addLayout(text_lay, 1)
        root.addWidget(header)

        group = QGroupBox("Downloads")
        form = QFormLayout(group)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(9)

        folder_row = QHBoxLayout()
        self.folder = QLineEdit(self.settings.get("download_dir", str(DOWNLOAD_DIR)))
        self.folder.setClearButtonEnabled(True)
        browse = QPushButton(make_icon("folder", 18), "Escolher...")
        browse.setIconSize(QSize(16, 16))
        browse.clicked.connect(self._browse)
        reset = QPushButton("Padrão")
        reset.setObjectName("QuietButton")
        reset.clicked.connect(lambda: self.folder.setText(str(DOWNLOAD_DIR)))
        folder_row.addWidget(self.folder, 1)
        folder_row.addWidget(browse)
        folder_row.addWidget(reset)
        folder_box = QVBoxLayout()
        folder_box.setSpacing(4)
        folder_box.addLayout(folder_row)
        self.folder_state = QLabel()
        self.folder_state.setObjectName("PaneHint")
        folder_box.addWidget(self.folder_state)
        form.addRow("Pasta padrão:", folder_box)

        self.auto_start = QCheckBox("Iniciar a fila automaticamente")
        self.auto_start.setChecked(bool(self.settings.get("auto_start_queue", True)))
        self.auto_start.setToolTip("Quando desativado, novos itens ficam aguardando até você clicar em Iniciar.")
        form.addRow("", self.auto_start)

        self.auto_open = QCheckBox("Abrir a pasta ao concluir um download")
        self.auto_open.setChecked(bool(self.settings.get("auto_open_folder", False)))
        form.addRow("", self.auto_open)
        root.addWidget(group)

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Save)
        buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")
        self.save_button = buttons.button(QDialogButtonBox.Save)
        self.save_button.setText("Salvar alterações")
        self.save_button.setIcon(make_icon("done", 18))
        self.save_button.setObjectName("PrimaryButton")
        buttons.accepted.connect(self._save_checked)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.folder.textChanged.connect(self._validate_folder)
        self._validate_folder()

    def _browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Pasta de downloads", self.folder.text())
        if folder:
            self.folder.setText(folder)

    def _validate_folder(self) -> bool:
        try:
            path = validate_download_directory(self.folder.text(), create=False)
        except ValueError as exc:
            self.folder_state.setText(str(exc))
            self.folder_state.setStyleSheet("color:#FF7A8C;")
            if hasattr(self, "save_button"):
                self.save_button.setEnabled(False)
            return False
        self.folder_state.setText(f"Destino: {path}")
        self.folder_state.setStyleSheet("color:#7F90A5;")
        if hasattr(self, "save_button"):
            self.save_button.setEnabled(True)
        return True

    def _save_checked(self) -> None:
        if not self._validate_folder():
            self.folder.setFocus()
            return
        try:
            validate_download_directory(self.folder.text(), create=True)
        except ValueError as exc:
            QMessageBox.warning(self, "Pasta inválida", str(exc))
            return
        self.accept()

    def values(self) -> dict:
        self.settings["download_dir"] = str(validate_download_directory(self.folder.text(), create=False))
        self.settings["auto_start_queue"] = self.auto_start.isChecked()
        self.settings["auto_open_folder"] = self.auto_open.isChecked()
        return self.settings


class ToolsDialog(QDialog):
    def __init__(
        self,
        settings: dict,
        active_download: bool,
        refresh_library,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.settings = settings
        self.active_download = active_download
        self.refresh_library_callback = refresh_library
        self.download_dir = Path(settings.get("download_dir", str(DOWNLOAD_DIR)))
        self.setWindowTitle("Ferramentas")
        self.resize(610, 430)
        self.setMinimumWidth(560)
        enable_dark_titlebar(self)

        root = QVBoxLayout(self)
        root.setContentsMargins(15, 14, 15, 14)
        root.setSpacing(11)

        header = QFrame()
        header.setObjectName("SummaryCard")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(12, 9, 12, 9)
        icon = QLabel()
        icon.setPixmap(make_icon("tools", 32).pixmap(32, 32))
        hl.addWidget(icon)
        text_lay = QVBoxLayout()
        text_lay.setSpacing(1)
        title = QLabel("Manutenção e diagnóstico")
        title.setObjectName("PaneTitle")
        desc = QLabel("Verifique componentes e limpe resíduos de downloads interrompidos.")
        desc.setObjectName("PaneHint")
        text_lay.addWidget(title)
        text_lay.addWidget(desc)
        hl.addLayout(text_lay, 1)
        root.addWidget(header)

        diag_group = QGroupBox("Componentes")
        diag_form = QFormLayout(diag_group)
        diag_form.setHorizontalSpacing(14)
        diag_form.setVerticalSpacing(7)
        self.diag_labels: dict[str, QLabel] = {}
        for key in ("Epicuro", "Python", "yt-dlp", "SpotDL", "FFmpeg"):
            label = QLabel("—")
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.diag_labels[key] = label
            diag_form.addRow(f"{key}:", label)
        root.addWidget(diag_group)

        maintenance = QGroupBox("Manutenção")
        ml = QVBoxLayout(maintenance)
        ml.setSpacing(8)
        self.partial_state = QLabel()
        self.partial_state.setObjectName("PaneHint")
        ml.addWidget(self.partial_state)
        row = QHBoxLayout()
        self.cleanup_button = QPushButton(make_icon("cleanup", 18), "Limpar downloads incompletos")
        self.cleanup_button.setIconSize(QSize(17, 17))
        self.cleanup_button.setEnabled(not active_download)
        self.cleanup_button.clicked.connect(self._cleanup_partials)
        refresh_button = QPushButton(make_icon("refresh", 18), "Recarregar biblioteca")
        refresh_button.setIconSize(QSize(17, 17))
        refresh_button.clicked.connect(self._refresh_library)
        row.addWidget(self.cleanup_button)
        row.addWidget(refresh_button)
        row.addStretch(1)
        ml.addLayout(row)
        if active_download:
            busy = QLabel("A limpeza fica bloqueada enquanto há download ativo ou pausado.")
            busy.setObjectName("PaneHint")
            ml.addWidget(busy)
        root.addWidget(maintenance)

        utilities = QHBoxLayout()
        verify = QPushButton(make_icon("diagnostic", 18), "Verificar componentes")
        verify.clicked.connect(self._refresh_diagnostics)
        copy = QPushButton(make_icon("copy", 18), "Copiar diagnóstico")
        copy.clicked.connect(self._copy_diagnostics)
        data = QPushButton(make_icon("folder", 18), "Abrir dados do app")
        data.clicked.connect(lambda: open_in_file_manager(DATA_DIR))
        utilities.addWidget(verify)
        utilities.addWidget(copy)
        utilities.addWidget(data)
        root.addLayout(utilities)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.button(QDialogButtonBox.Close).setText("Fechar")
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self._refresh_diagnostics()
        self._refresh_partial_state()

    def _refresh_diagnostics(self) -> None:
        info = runtime_diagnostics()
        for key, label in self.diag_labels.items():
            value = info.get(key, "—")
            if key == "FFmpeg":
                display = "Disponível" if value != "não encontrado" else value
            else:
                display = value
            label.setText(display)
            label.setStyleSheet("color:#FF7A8C;" if "não " in display else "")

    def _diagnostic_text(self) -> str:
        info = runtime_diagnostics()
        lines = [f"{key}: {value}" for key, value in info.items()]
        lines.append(f"Downloads: {self.download_dir}")
        return "\n".join(lines)

    def _copy_diagnostics(self) -> None:
        QApplication.clipboard().setText(self._diagnostic_text())
        self.partial_state.setText("Diagnóstico copiado para a área de transferência.")

    def _refresh_partial_state(self) -> None:
        files = find_partial_downloads(self.download_dir)
        total = 0
        for path in files:
            try:
                total += path.stat().st_size
            except OSError:
                pass
        if files:
            self.partial_state.setText(f"{len(files)} arquivo(s) incompleto(s) · {human_bytes(total)}")
        else:
            self.partial_state.setText("Nenhum download incompleto encontrado.")

    def _cleanup_partials(self) -> None:
        if self.active_download:
            return
        files = find_partial_downloads(self.download_dir)
        if not files:
            self._refresh_partial_state()
            return
        answer = QMessageBox.question(
            self,
            "Limpar downloads incompletos",
            f"Remover {len(files)} arquivo(s) parcial(is)? Downloads concluídos não serão apagados.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        removed, freed = cleanup_partial_downloads(self.download_dir)
        remaining = len(find_partial_downloads(self.download_dir))
        text = f"{removed} arquivo(s) removido(s) · {human_bytes(freed)} liberados"
        if remaining:
            text += f" · {remaining} não puderam ser removidos"
        self.partial_state.setText(text)

    def _refresh_library(self) -> None:
        self.refresh_library_callback()
        self.partial_state.setText("Biblioteca recarregada.")



@dataclass
class Job:
    id: str
    info: MediaInfo
    mode: str
    quality: str
    playlist_mode: str = "single"
    status: str = "Aguardando"
    row: int = -1
    progress: float = 0.0
    downloaded: int = 0
    total: int = 0
    speed: float = 0.0
    eta: Optional[int] = None
    files: list[str] = field(default_factory=list)

    @property
    def source_text(self) -> str:
        service = detect_service(self.info.url)
        if service == "youtube":
            return "YouTube"
        if service == "spotify":
            return "Spotify"
        return self.info.extractor or "Web"

    @property
    def format_text(self) -> str:
        if self.mode == "audio":
            return f"MP3 {self.quality}k"
        if self.mode == "spotify":
            return "Spotify"
        return "MP4 MAX" if self.quality == "best" else f"MP4 {self.quality}"


class AppWindow(QMainWindow):
    COL_NAME = 0
    COL_SIZE = 1
    COL_DONE = 2
    COL_SPEED = 3
    COL_PROGRESS = 4
    COL_SOURCE = 5
    COL_FORMAT = 6
    COL_STATUS = 7
    COL_REMAIN = 8

    def __init__(self):
        super().__init__()
        self.settings_store = SettingsStore()
        self.settings = self.settings_store.load()
        self.history_store = HistoryStore()

        self.jobs: dict[str, Job] = {}
        self.queue: list[str] = []
        self.active_job_id: Optional[str] = None
        self.download_thread: Optional[threading.Thread] = None
        self.download_worker: Optional[DownloadWorker] = None
        self.analyze_thread: Optional[threading.Thread] = None
        self.analyze_worker: Optional[AnalyzeWorker] = None
        self.pending_request: Optional[tuple[str, str, str]] = None
        self.pause_requested = False
        self.cancel_requested = False
        self.current_speed = 0.0
        self.filter_mode = "all"
        self._rows_filtered = False
        self._start_next_pending = False
        self._closing = False

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.setWindowIcon(make_icon("download", 32))
        enable_dark_titlebar(self)
        self.resize(1180, 760)
        self.setMinimumSize(920, 610)
        self.setStyleSheet(APP_QSS)

        self._build_actions()
        self._build_menu()
        self._build_main_toolbar()
        self._build_central()
        self._build_status_bar()
        self.refresh_history()
        self._update_status_bar()
        self._update_action_states()

        QShortcut(QKeySequence("Ctrl+L"), self, activated=self.add_download_dialog)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self.focus_search)

    # ------------------------------------------------------------------ UI
    def _action(self, text: str, icon_name: str, slot, shortcut: str = "", tip: str = "") -> QAction:
        act = QAction(make_icon(icon_name, 28), text, self)
        act.triggered.connect(slot)
        if shortcut:
            act.setShortcut(QKeySequence(shortcut))
        if tip:
            act.setToolTip(tip)
            act.setStatusTip(tip)
        return act

    def _build_actions(self) -> None:
        self.act_new = self._action("Novo link", "new", self.add_download_dialog, "Ctrl+N", "Adicionar um link à fila")
        self.act_analyze = self._action("Colar link", "clipboard", self.analyze_clipboard, "Ctrl+Shift+V", "Analisar o link da área de transferência")
        self.act_folder = self._action("Abrir pasta", "folder", self.open_download_folder, tip="Abrir a pasta de downloads")
        self.act_options = self._action("Opções", "settings", self.open_options, tip="Configurações do Epicuro")
        self.act_tools = self._action("Ferramentas", "tools", self.show_tools, tip="Diagnóstico e manutenção")
        self.act_help = self._action("Ajuda", "help", self.show_help, "F1")
        self.act_exit = self._action("Sair", "exit", self.close, "Alt+F4")

        self.act_start = self._action("Iniciar", "play", self.start_selected, "Ctrl+Enter", "Iniciar ou retomar o item selecionado")
        self.act_pause = self._action("Pausar", "pause", self.pause_current, "Ctrl+P", "Pausar o download ativo")
        self.act_stop = self._action("Cancelar", "stop", self.stop_current, "Ctrl+Shift+X", "Cancelar o download ativo")
        self.act_remove = self._action("Remover", "trash", self.remove_selected, "Delete", "Remover o item selecionado da lista")
        self.act_up = self._action("Priorizar", "up", self.move_selected_top, tip="Mover o item para o topo da fila")
        self.act_down = self._action("Adiar", "down", self.move_selected_down, tip="Mover o item uma posição para baixo")

    def _build_menu(self) -> None:
        menu_file = self.menuBar().addMenu("&Arquivo")
        menu_file.addAction(self.act_new)
        menu_file.addAction(self.act_folder)
        menu_file.addSeparator()
        menu_file.addAction(self.act_exit)

        menu_transfers = self.menuBar().addMenu("&Transferências")
        for act in (self.act_start, self.act_pause, self.act_stop, self.act_remove):
            menu_transfers.addAction(act)
        menu_transfers.addSeparator()
        menu_transfers.addAction(self.act_up)
        menu_transfers.addAction(self.act_down)

        menu_tools = self.menuBar().addMenu("&Ferramentas")
        menu_tools.addAction(self.act_options)
        menu_tools.addAction(self.act_tools)

        menu_help = self.menuBar().addMenu("A&juda")
        menu_help.addAction(self.act_help)

    def _build_main_toolbar(self) -> None:
        tb = QToolBar("Principal")
        tb.setObjectName("MainToolbar")
        tb.setMovable(False)
        tb.setFloatable(False)
        tb.setIconSize(QSize(24, 24))
        tb.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(Qt.TopToolBarArea, tb)

        tb.addAction(self.act_new)
        tb.addAction(self.act_analyze)
        tb.addAction(self.act_folder)
        tb.addSeparator()
        tb.addAction(self.act_options)
        tb.addAction(self.act_tools)
        tb.addSeparator()
        tb.addAction(self.act_help)
        self.main_toolbar = tb

    def _build_central(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(8)

        side = QToolBar("Filtros")
        side.setObjectName("SideToolbar")
        side.setOrientation(Qt.Vertical)
        side.setMovable(False)
        side.setIconSize(QSize(20, 20))
        side.setToolButtonStyle(Qt.ToolButtonIconOnly)
        outer.addWidget(side)

        all_act = QAction(make_icon("all", 21), "Todos", self)
        active_act = QAction(make_icon("download", 21), "Ativos", self)
        queue_act = QAction(make_icon("play", 21), "Fila", self)
        error_act = QAction(make_icon("error", 21), "Erros", self)
        self.filter_group = QActionGroup(self)
        self.filter_group.setExclusive(True)
        for act, mode in ((all_act, "all"), (active_act, "active"), (queue_act, "queue"), (error_act, "error")):
            act.setCheckable(True)
            self.filter_group.addAction(act)
            act.triggered.connect(lambda _=False, m=mode: self.set_filter(m))
        all_act.setChecked(True)
        for act in (all_act, active_act, queue_act, error_act):
            side.addAction(act)

        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        outer.addWidget(splitter, 1)

        transfers_pane = self._make_pane()
        transfers_layout = transfers_pane.layout()
        transfer_header = self._pane_header("Transferências")
        self.transfer_count = QLabel("0 itens")
        self.transfer_count.setObjectName("CountBadge")
        transfer_header.layout().addWidget(self.transfer_count)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Pesquisar transferências...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setMaximumWidth(260)
        self.search_edit.textChanged.connect(self.apply_filter)
        transfer_header.layout().addWidget(self.search_edit)
        transfers_layout.addWidget(transfer_header)

        self.transfers = QTableWidget(0, 9)
        self.transfers.setHorizontalHeaderLabels([
            "Nome do arquivo",
            "Tamanho",
            "Concluído",
            "Velocidade",
            "Progresso",
            "Origem",
            "Formato",
            "Status",
            "Restante",
        ])
        self.transfers.setAlternatingRowColors(True)
        self.transfers.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.transfers.setSelectionMode(QAbstractItemView.SingleSelection)
        self.transfers.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.transfers.setShowGrid(True)
        self.transfers.setIconSize(QSize(18, 18))
        self.transfers.verticalHeader().setVisible(False)
        self.transfers.verticalHeader().setDefaultSectionSize(29)
        header = self.transfers.horizontalHeader()
        header.setSectionResizeMode(self.COL_NAME, QHeaderView.Stretch)
        for col, width in {
            self.COL_SIZE: 90,
            self.COL_DONE: 90,
            self.COL_SPEED: 95,
            self.COL_PROGRESS: 180,
            self.COL_SOURCE: 90,
            self.COL_FORMAT: 100,
            self.COL_STATUS: 95,
            self.COL_REMAIN: 80,
        }.items():
            header.setSectionResizeMode(col, QHeaderView.Fixed)
            self.transfers.setColumnWidth(col, width)
        transfers_layout.addWidget(self.transfers, 1)
        self.transfers.itemSelectionChanged.connect(self._update_action_states)
        self.transfers.itemDoubleClicked.connect(lambda *_: self.start_selected())
        self.transfers.setContextMenuPolicy(Qt.CustomContextMenu)
        self.transfers.customContextMenuRequested.connect(self._show_transfer_menu)

        control_row = QHBoxLayout()
        control_row.setContentsMargins(6, 5, 6, 6)
        control_row.setSpacing(6)
        self.control_buttons = {}
        for action in (self.act_start, self.act_pause, self.act_stop, self.act_remove, self.act_up, self.act_down):
            btn = QPushButton(action.icon(), action.text())
            btn.setIconSize(QSize(17, 17))
            btn.setToolTip(action.toolTip())
            btn.clicked.connect(action.trigger)
            self.control_buttons[action] = btn
            control_row.addWidget(btn)
        self.control_buttons[self.act_start].setObjectName("PrimaryButton")
        self.control_buttons[self.act_start].setMinimumWidth(112)
        self.control_buttons[self.act_pause].setMinimumWidth(88)
        self.control_buttons[self.act_stop].setObjectName("DangerButton")
        self.control_buttons[self.act_stop].setMinimumWidth(92)
        self.control_buttons[self.act_remove].setObjectName("DangerButton")
        self.control_buttons[self.act_up].setObjectName("QuietButton")
        self.control_buttons[self.act_down].setObjectName("QuietButton")
        control_row.addStretch(1)
        transfers_layout.addLayout(control_row)
        splitter.addWidget(transfers_pane)

        completed_pane = self._make_pane()
        completed_layout = completed_pane.layout()

        library_header = self._pane_header("Biblioteca")
        self.library_count = QLabel("0 arquivos")
        self.library_count.setObjectName("CountBadge")
        library_header.layout().addWidget(self.library_count)
        self.library_search = QLineEdit()
        self.library_search.setObjectName("LibrarySearch")
        self.library_search.setPlaceholderText("Pesquisar biblioteca...")
        self.library_search.setClearButtonEnabled(True)
        self.library_search.textChanged.connect(self.apply_library_filter)
        library_header.layout().addWidget(self.library_search)
        completed_layout.addWidget(library_header)

        self.completed = DraggableFileTable(0, 6)
        self.completed.setHorizontalHeaderLabels([
            "Nome do arquivo",
            "Tamanho",
            "Concluído em",
            "Tipo",
            "Qualidade",
            "Origem",
        ])
        self.completed.setAlternatingRowColors(True)
        self.completed.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.completed.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.completed.setIconSize(QSize(20, 20))
        self.completed.setContextMenuPolicy(Qt.CustomContextMenu)
        self.completed.customContextMenuRequested.connect(self._show_library_menu)
        self.completed.itemSelectionChanged.connect(self._update_library_actions)
        self.completed.verticalHeader().setVisible(False)
        self.completed.verticalHeader().setDefaultSectionSize(30)
        ch = self.completed.horizontalHeader()
        ch.setSectionResizeMode(0, QHeaderView.Stretch)
        for col, width in {1: 92, 2: 145, 3: 75, 4: 105, 5: 105}.items():
            ch.setSectionResizeMode(col, QHeaderView.Fixed)
            self.completed.setColumnWidth(col, width)
        self.completed.cellDoubleClicked.connect(self.open_completed_file)
        completed_layout.addWidget(self.completed, 1)

        library_bottom = QWidget()
        bottom_controls = QHBoxLayout(library_bottom)
        bottom_controls.setContentsMargins(7, 5, 7, 7)
        bottom_controls.setSpacing(6)

        self.library_open_btn = QPushButton(make_icon("file", 19), "Abrir")
        self.library_reveal_btn = QPushButton(make_icon("folder", 19), "Mostrar na pasta")
        self.library_copy_btn = QPushButton(make_icon("copy", 19), "Copiar caminho")
        for btn in (self.library_open_btn, self.library_reveal_btn, self.library_copy_btn):
            btn.setIconSize(QSize(17, 17))
            btn.setObjectName("LibraryActionButton")
        self.library_open_btn.clicked.connect(lambda: self.open_completed_file())
        self.library_reveal_btn.clicked.connect(self.open_selected_completed)
        self.library_copy_btn.clicked.connect(self.copy_completed_paths)

        clear_btn = QPushButton(make_icon("trash", 19), "Limpar histórico")
        clear_btn.setIconSize(QSize(17, 17))
        clear_btn.setObjectName("DangerButton")
        clear_btn.clicked.connect(self.clear_history)

        bottom_controls.addWidget(self.library_open_btn)
        bottom_controls.addWidget(self.library_reveal_btn)
        bottom_controls.addWidget(self.library_copy_btn)
        bottom_controls.addStretch(1)
        drag_hint = QLabel("Arraste os arquivos para fora do Epicuro")
        drag_hint.setObjectName("DragHint")
        bottom_controls.addWidget(drag_hint)
        bottom_controls.addStretch(1)
        bottom_controls.addWidget(clear_btn)
        completed_layout.addWidget(library_bottom)
        splitter.addWidget(completed_pane)
        splitter.setSizes([465, 235])


    def _make_pane(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("Pane")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        return frame

    def _pane_header(self, title: str, hint: str = "") -> QFrame:
        frame = QFrame()
        frame.setObjectName("PaneHeader")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(9, 6, 9, 6)
        lay.setSpacing(8)
        title_label = QLabel(title)
        title_label.setObjectName("PaneTitle")
        lay.addWidget(title_label)
        if hint:
            hint_label = QLabel(hint)
            hint_label.setObjectName("PaneHint")
            lay.addWidget(hint_label)
        lay.addStretch(1)
        return frame

    def _build_status_bar(self) -> None:
        bar = QStatusBar()
        self.setStatusBar(bar)
        self.status_connection = QLabel("● Pronto")
        self.status_connection.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.status_queue = QLabel("Fila: 0")
        self.status_speed = QLabel("↓ —")
        for w in (self.status_connection, self.status_queue, self.status_speed):
            bar.addWidget(w)

    # --------------------------------------------------------------- actions
    def add_download_dialog(self) -> None:
        if self.analyze_thread is not None:
            QMessageBox.information(self, "Análise em andamento", "O Epicuro já está analisando um link.")
            return
        dlg = AddDownloadDialog(self.settings, self)
        if dlg.exec() != QDialog.Accepted:
            return
        url, mode, quality = dlg.values()
        if detect_service(url) == "spotify":
            mode, quality = "spotify", "best"
        self.pending_request = (url, mode, quality)
        self._start_analysis(url)

    def analyze_clipboard(self) -> None:
        if self.analyze_thread is not None:
            return
        raw = QApplication.clipboard().text()
        try:
            url = normalize_media_url(raw)
        except ValueError:
            self.add_download_dialog()
            return
        service = detect_service(url)
        if service == "spotify":
            mode, quality = "spotify", "best"
        else:
            mode = str(self.settings.get("mode", "video"))
            if mode == "spotify":
                mode = "video"
            quality = str(self.settings.get("audio_quality" if mode == "audio" else "video_quality", "320" if mode == "audio" else "1080p"))
        self.pending_request = (url, mode, quality)
        self._start_analysis(url)

    def _start_analysis(self, url: str) -> None:
        if self._closing:
            return
        self.status_connection.setText("◌ Analisando link...")
        self.act_new.setEnabled(False)
        self.act_analyze.setEnabled(False)

        worker = AnalyzeWorker(url)
        worker.finished.connect(self._analysis_finished)
        worker.failed.connect(self._analysis_failed)
        thread = threading.Thread(target=worker.run, name="EpicuroAnalyze", daemon=True)
        self.analyze_thread = thread
        self.analyze_worker = worker
        thread.start()

    def _analysis_thread_done(self) -> None:
        self.analyze_thread = None
        self.analyze_worker = None
        if not self._closing:
            self.act_new.setEnabled(True)
            self.act_analyze.setEnabled(True)
            self._update_action_states()

    def _analysis_finished(self, info: MediaInfo) -> None:
        self._analysis_thread_done()
        if self._closing or not self.pending_request:
            return
        _url, mode, quality = self.pending_request
        self.pending_request = None
        playlist_mode = "single"
        if info.is_playlist:
            box = QMessageBox(self)
            box.setWindowTitle("Playlist reconhecida")
            count = f" ({info.playlist_count} itens)" if info.playlist_count else ""
            box.setText(f"{info.title}{count}")
            box.setInformativeText("O que deve entrar na fila?")
            all_btn = box.addButton("Baixar tudo", QMessageBox.AcceptRole)
            one_btn = box.addButton("Somente este item", QMessageBox.ActionRole)
            box.addButton(QMessageBox.Cancel)
            box.exec()
            if box.clickedButton() is all_btn:
                playlist_mode = "all"
            elif box.clickedButton() is one_btn:
                playlist_mode = "single"
            else:
                self.status_connection.setText("● Pronto")
                return

        self._remember_preferences(mode, quality)
        job = Job(
            id=uuid.uuid4().hex,
            info=info,
            mode=mode,
            quality=quality,
            playlist_mode=playlist_mode,
        )
        self.jobs[job.id] = job
        self.queue.append(job.id)
        self._insert_job_row(job)
        self.status_connection.setText("● Adicionado à fila")
        self._update_status_bar()
        if self.settings.get("auto_start_queue", True):
            self._start_next_if_idle()

    def _analysis_failed(self, message: str) -> None:
        self._analysis_thread_done()
        if self._closing:
            return
        self.pending_request = None
        self.status_connection.setText("● Pronto")
        QMessageBox.warning(self, "Não foi possível analisar", message)

    def _remember_preferences(self, mode: str, quality: str) -> None:
        self.settings["mode"] = mode
        if mode == "video":
            self.settings["video_quality"] = quality
        elif mode == "audio":
            self.settings["audio_quality"] = quality
        self.settings_store.save(self.settings)

    # --------------------------------------------------------------- queue
    def _insert_job_row(self, job: Job) -> None:
        row = self.transfers.rowCount()
        self.transfers.insertRow(row)
        job.row = row
        self._set_item(row, self.COL_NAME, self._display_job_name(job))
        self._set_item(row, self.COL_SIZE, "—")
        self._set_item(row, self.COL_DONE, "0 B")
        self._set_item(row, self.COL_SPEED, "—")
        progress = ProgressCell()
        self.transfers.setCellWidget(row, self.COL_PROGRESS, progress)
        self._set_item(row, self.COL_SOURCE, job.source_text)
        self._set_item(row, self.COL_FORMAT, job.format_text)
        self._set_item(row, self.COL_STATUS, job.status)
        self._set_item(row, self.COL_REMAIN, "—")
        name_item = self.transfers.item(row, self.COL_NAME)
        name_item.setData(Qt.UserRole, job.id)
        name_item.setToolTip(job.info.url)
        name_item.setIcon(make_icon("audio" if job.mode in {"audio", "spotify"} else "video", 18))
        self.transfers.selectRow(row)
        self.apply_filter()

    def _display_job_name(self, job: Job) -> str:
        prefix = "[Playlist] " if job.info.is_playlist and job.playlist_mode == "all" else ""
        return prefix + (job.info.title or "Download")

    def _set_item(self, row: int, col: int, text: str) -> None:
        item = self.transfers.item(row, col)
        if item is None:
            item = QTableWidgetItem()
            self.transfers.setItem(row, col, item)
        item.setText(str(text))

    def _start_next_if_idle(self) -> None:
        if self.active_job_id is not None:
            return
        while self.queue:
            job_id = self.queue[0]
            job = self.jobs.get(job_id)
            if job is None:
                self.queue.pop(0)
                continue
            if job.status not in {"Aguardando", "Pausado"}:
                self.queue.pop(0)
                continue
            self._start_job(job)
            return
        self._update_status_bar()

    def _start_job(self, job: Job) -> None:
        if self._closing:
            return
        self.active_job_id = job.id
        job.status = "Iniciando"
        self.pause_requested = False
        self.cancel_requested = False
        self._update_job_row(job)

        worker = DownloadWorker(
            job.id,
            job.info,
            job.mode,
            job.quality,
            job.playlist_mode,
            self.settings.get("download_dir", str(DOWNLOAD_DIR)),
        )
        worker.progress.connect(self._job_progress)
        worker.finished.connect(self._job_finished)
        worker.failed.connect(self._job_failed)
        worker.cancelled.connect(self._job_cancelled)

        thread = threading.Thread(target=worker.run, name=f"EpicuroDownload-{job.id[:8]}", daemon=True)
        self.download_thread = thread
        self.download_worker = worker
        thread.start()
        self.status_connection.setText("● Baixando")
        self._update_status_bar()
        self._update_action_states()

    def _job_progress(self, job_id: str, data: dict) -> None:
        if self._closing:
            return
        job = self.jobs.get(job_id)
        if not job:
            return
        stage = data.get("stage", "downloading")
        stage_map = {
            "downloading": "Baixando",
            "processing": "Processando",
            "converting": "Convertendo",
            "completed": "Concluído",
        }
        job.status = stage_map.get(stage, str(stage).title())
        job.progress = float(data.get("percent") or job.progress or 0)
        job.speed = float(data.get("speed") or 0)
        job.eta = data.get("eta")
        job.downloaded = int(data.get("downloaded") or job.downloaded or 0)
        job.total = int(data.get("total") or job.total or 0)
        self.current_speed = job.speed
        self._update_job_row(job)
        self._update_status_bar()

    def _update_job_row(self, job: Job) -> None:
        row = self._row_for_job(job.id)
        if row < 0:
            return
        job.row = row
        self._set_item(row, self.COL_SIZE, human_bytes(job.total) if job.total else "—")
        self._set_item(row, self.COL_DONE, human_bytes(job.downloaded))
        self._set_item(row, self.COL_SPEED, human_speed(job.speed))
        widget = self.transfers.cellWidget(row, self.COL_PROGRESS)
        if isinstance(widget, ProgressCell):
            widget.set_value(job.progress)
        self._set_item(row, self.COL_STATUS, job.status)
        status_item = self.transfers.item(row, self.COL_STATUS)
        if status_item is not None:
            status_colors = {
                "Concluído": "#49D17D",
                "Erro": "#FF667A",
                "Cancelado": "#FF667A",
                "Pausado": "#F7C65C",
                "Pausando...": "#F7C65C",
                "Cancelando...": "#F7C65C",
                "Baixando": "#6EA9F4",
                "Convertendo": "#B896FF",
                "Processando": "#B896FF",
            }
            status_item.setForeground(QBrush(QColor(status_colors.get(job.status, "#AFC0D4"))))
        self._set_item(row, self.COL_REMAIN, human_eta(job.eta))
        self.apply_filter()

    def _job_finished(self, job_id: str, files: list[str]) -> None:
        if self._closing:
            return
        job = self.jobs.get(job_id)
        if not job:
            return
        job.status = "Concluído"
        job.progress = 100
        job.speed = 0
        job.eta = 0
        job.files = list(files)
        if files:
            try:
                job.total = sum(Path(p).stat().st_size for p in files if Path(p).exists())
                job.downloaded = job.total
            except OSError:
                pass
        self._update_job_row(job)
        item = history_item(job.info, job.mode, job.quality, files)
        self.history_store.add(item)
        self.refresh_history()
        self._remove_from_queue(job_id)
        self.active_job_id = None
        self.current_speed = 0
        self.status_connection.setText("● Download concluído")
        if self.settings.get("auto_open_folder"):
            open_in_file_manager(self.settings.get("download_dir", str(DOWNLOAD_DIR)))
        self._update_status_bar()
        self._start_next_pending = True
        self._download_thread_done()

    def _job_failed(self, job_id: str, message: str) -> None:
        if self._closing:
            return
        job = self.jobs.get(job_id)
        if job:
            job.status = "Erro"
            job.speed = 0
            job.eta = None
            self._update_job_row(job)
        self._remove_from_queue(job_id)
        self.active_job_id = None
        self.current_speed = 0
        self.status_connection.setText("● Erro no download")
        self._update_status_bar()
        QMessageBox.warning(self, "Download não concluído", message)
        self._start_next_pending = True
        self._download_thread_done()

    def _job_cancelled(self, job_id: str) -> None:
        if self._closing:
            return
        job = self.jobs.get(job_id)
        if job:
            if self.pause_requested:
                job.status = "Pausado"
                if job_id in self.queue:
                    self.queue.remove(job_id)
            else:
                job.status = "Cancelado"
                self._remove_from_queue(job_id)
            job.speed = 0
            job.eta = None
            self._update_job_row(job)
        self.active_job_id = None
        self.current_speed = 0
        self.pause_requested = False
        self.cancel_requested = False
        self.status_connection.setText("● Pronto")
        self._update_status_bar()
        self._start_next_pending = True
        self._download_thread_done()

    def _download_thread_done(self) -> None:
        self.download_thread = None
        self.download_worker = None
        if self._closing:
            return
        self._update_action_states()
        if self._start_next_pending:
            self._start_next_pending = False
            if self.settings.get("auto_start_queue", True):
                self._start_next_if_idle()

    def _remove_from_queue(self, job_id: str) -> None:
        while job_id in self.queue:
            self.queue.remove(job_id)

    def start_selected(self) -> None:
        job = self._selected_job()
        if job is None:
            self._start_next_if_idle()
            return
        if job.id == self.active_job_id:
            return
        if job.status not in {"Aguardando", "Pausado", "Erro", "Cancelado"}:
            return
        job.status = "Aguardando"
        self._remove_from_queue(job.id)
        self.queue.insert(0, job.id)
        self._update_job_row(job)
        self._start_next_if_idle()

    def pause_current(self) -> None:
        if not self.active_job_id or not self.download_worker:
            return
        self.pause_requested = True
        self.cancel_requested = False
        job = self.jobs.get(self.active_job_id)
        if job:
            job.status = "Pausando..."
            self._update_job_row(job)
        self.download_worker.cancel()

    def stop_current(self) -> None:
        if not self.active_job_id or not self.download_worker:
            return
        self.pause_requested = False
        self.cancel_requested = True
        job = self.jobs.get(self.active_job_id)
        if job:
            job.status = "Cancelando..."
            self._update_job_row(job)
        self.download_worker.cancel()

    def remove_selected(self) -> None:
        job = self._selected_job()
        if not job:
            return
        if job.id == self.active_job_id:
            QMessageBox.information(self, "Download ativo", "Pare ou pause o download antes de removê-lo da lista.")
            return
        self._remove_from_queue(job.id)
        row = self._row_for_job(job.id)
        if row >= 0:
            self.transfers.removeRow(row)
        self.jobs.pop(job.id, None)
        self._reindex_rows()
        self._update_status_bar()

    def move_selected_top(self) -> None:
        job = self._selected_job()
        if not job or job.id == self.active_job_id:
            return
        if job.id not in self.queue:
            return
        self.queue.remove(job.id)
        insert_at = 1 if self.active_job_id and self.queue and self.queue[0] == self.active_job_id else 0
        self.queue.insert(insert_at, job.id)
        self._reorder_table_from_queue()

    def move_selected_down(self) -> None:
        job = self._selected_job()
        if not job or job.id not in self.queue or job.id == self.active_job_id:
            return
        idx = self.queue.index(job.id)
        if idx >= len(self.queue) - 1:
            return
        self.queue[idx], self.queue[idx + 1] = self.queue[idx + 1], self.queue[idx]
        self._reorder_table_from_queue()

    def _reorder_table_from_queue(self) -> None:
        # Reconstrói a tabela preservando dados dos jobs; simples e robusto para filas pequenas.
        selected = self._selected_job()
        ordered_ids = []
        for jid in self.queue:
            if jid in self.jobs and jid not in ordered_ids:
                ordered_ids.append(jid)
        for row in range(self.transfers.rowCount()):
            item = self.transfers.item(row, self.COL_NAME)
            if item:
                jid = item.data(Qt.UserRole)
                if jid in self.jobs and jid not in ordered_ids:
                    ordered_ids.append(jid)

        self.transfers.setRowCount(0)
        for jid in ordered_ids:
            job = self.jobs[jid]
            self._insert_job_row(job)
            self._update_job_row(job)
        if selected:
            row = self._row_for_job(selected.id)
            if row >= 0:
                self.transfers.selectRow(row)
        self.apply_filter()

    def _selected_job(self) -> Optional[Job]:
        row = self.transfers.currentRow()
        if row < 0:
            return None
        item = self.transfers.item(row, self.COL_NAME)
        if not item:
            return None
        return self.jobs.get(str(item.data(Qt.UserRole)))

    def _row_for_job(self, job_id: str) -> int:
        for row in range(self.transfers.rowCount()):
            item = self.transfers.item(row, self.COL_NAME)
            if item and item.data(Qt.UserRole) == job_id:
                return row
        return -1

    def _reindex_rows(self) -> None:
        for row in range(self.transfers.rowCount()):
            item = self.transfers.item(row, self.COL_NAME)
            if item:
                job = self.jobs.get(str(item.data(Qt.UserRole)))
                if job:
                    job.row = row

    def _update_action_states(self) -> None:
        if not hasattr(self, "transfers"):
            return
        job = self._selected_job()
        active = self.active_job_id is not None and self.download_worker is not None
        active_job = self.jobs.get(self.active_job_id) if self.active_job_id else None
        active_controllable = active and (active_job is None or active_job.status not in {"Pausando...", "Cancelando..."})

        start_ok = False
        remove_ok = False
        up_ok = False
        down_ok = False
        if job is not None:
            start_ok = (not active) and job.status in {"Aguardando", "Pausado", "Erro", "Cancelado"}
            remove_ok = job.id != self.active_job_id
            if job.id in self.queue and job.id != self.active_job_id:
                idx = self.queue.index(job.id)
                first_movable = 1 if self.active_job_id and self.queue and self.queue[0] == self.active_job_id else 0
                up_ok = idx > first_movable
                down_ok = idx < len(self.queue) - 1
        elif not active:
            start_ok = any(j.status in {"Aguardando", "Pausado"} for j in self.jobs.values())

        if job is not None and job.status in {"Pausado", "Erro", "Cancelado"}:
            start_text = "Retomar"
        elif job is not None and job.status == "Aguardando":
            start_text = "Iniciar agora"
        elif job is None and not active:
            start_text = "Iniciar fila"
        else:
            start_text = "Iniciar"
        self.act_start.setText(start_text)

        self.act_start.setEnabled(start_ok)
        self.act_pause.setEnabled(active_controllable)
        self.act_stop.setEnabled(active_controllable)
        self.act_remove.setEnabled(remove_ok)
        self.act_up.setEnabled(up_ok)
        self.act_down.setEnabled(down_ok)
        self.act_new.setEnabled(not self._closing and self.analyze_thread is None)
        self.act_analyze.setEnabled(not self._closing and self.analyze_thread is None)

        for action, button in getattr(self, "control_buttons", {}).items():
            button.setEnabled(action.isEnabled())
            if action is self.act_start:
                button.setText(start_text)

    def _show_transfer_menu(self, pos) -> None:
        row = self.transfers.rowAt(pos.y())
        if row >= 0 and self.transfers.currentRow() != row:
            self.transfers.selectRow(row)
        self._update_action_states()
        menu = QMenu(self.transfers)
        menu.addAction(self.act_start)
        menu.addAction(self.act_pause)
        menu.addAction(self.act_stop)
        menu.addSeparator()
        menu.addAction(self.act_up)
        menu.addAction(self.act_down)
        menu.addSeparator()
        menu.addAction(self.act_remove)
        menu.exec(self.transfers.viewport().mapToGlobal(pos))

    # -------------------------------------------------------------- filters
    def set_filter(self, mode: str) -> None:
        self.filter_mode = mode
        self.apply_filter()

    def focus_search(self) -> None:
        self.search_edit.setFocus()
        self.search_edit.selectAll()

    def apply_filter(self) -> None:
        query = self.search_edit.text().strip().lower() if hasattr(self, "search_edit") else ""
        # Most of the time there is no active filter. Avoid rescanning every row
        # for every download progress tick in that common case.
        if self.filter_mode == "all" and not query:
            if self._rows_filtered:
                for row in range(self.transfers.rowCount()):
                    if self.transfers.isRowHidden(row):
                        self.transfers.setRowHidden(row, False)
                self._rows_filtered = False
            return
        self._rows_filtered = True
        for row in range(self.transfers.rowCount()):
            item = self.transfers.item(row, self.COL_NAME)
            if not item:
                continue
            job = self.jobs.get(str(item.data(Qt.UserRole)))
            if not job:
                self.transfers.setRowHidden(row, False)
                continue
            visible = True
            if self.filter_mode == "active":
                visible = job.id == self.active_job_id or job.status in {"Baixando", "Processando", "Convertendo", "Iniciando", "Pausando..."}
            elif self.filter_mode == "queue":
                visible = job.status in {"Aguardando", "Pausado"}
            elif self.filter_mode == "error":
                visible = job.status in {"Erro", "Cancelado"}
            if query:
                visible = visible and query in self._display_job_name(job).lower()
            self.transfers.setRowHidden(row, not visible)

    # -------------------------------------------------------------- history
    def refresh_history(self) -> None:
        entries = self.history_store.load()
        self.completed.setRowCount(0)
        for entry in entries:
            row = self.completed.rowCount()
            self.completed.insertRow(row)
            files = [str(f) for f in (entry.get("files") or []) if f]
            first = files[0] if files else ""
            source = detect_service(entry.get("url", ""))
            source = "YouTube" if source == "youtube" else "Spotify" if source == "spotify" else "Web"
            mode = entry.get("mode", "")
            type_text = "MP3" if mode in {"audio", "spotify"} else "MP4"
            quality = entry.get("quality", "")
            if mode == "spotify":
                quality = "Automática"
            elif mode == "video" and quality == "best":
                quality = "Máxima"
            elif mode == "audio" and str(quality).isdigit():
                quality = f"{quality} kbps"
            values = [
                entry.get("title", "Download"),
                human_bytes(entry.get("size", 0)),
                entry.get("created_at", ""),
                type_text,
                quality,
                source,
            ]
            exists = any(Path(f).is_file() for f in files)
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col == 0:
                    item.setData(Qt.UserRole, first)
                    item.setData(FILE_LIST_ROLE, files)
                    item.setData(HISTORY_ID_ROLE, str(entry.get("id", "")))
                    item.setToolTip(
                        f"{entry.get('url', '')}\n\n"
                        + ("Arraste esta linha para usar o arquivo em outro lugar." if exists else "O arquivo não está mais no caminho registrado.")
                    )
                    item.setIcon(make_icon("audio" if mode in {"audio", "spotify"} else "video", 20))
                    if not exists:
                        item.setForeground(QBrush(QColor("#748397")))
                self.completed.setItem(row, col, item)

        self.apply_library_filter()
        self._update_library_actions()

    def _selected_library_rows(self) -> list[int]:
        return sorted({index.row() for index in self.completed.selectionModel().selectedRows(0)})

    def _first_selected_library_path(self) -> str:
        files = self.completed.selected_file_paths()
        return files[0] if files else ""

    def open_completed_file(self, row: Optional[int] = None, _col: Optional[int] = None) -> None:
        if row is None:
            row = self.completed.currentRow()
        if row is None or row < 0:
            return
        item = self.completed.item(int(row), 0)
        if not item:
            return
        files = item.data(FILE_LIST_ROLE)
        candidates = files if isinstance(files, (list, tuple)) else [item.data(Qt.UserRole)]
        path = next((str(p) for p in candidates if p and Path(str(p)).is_file()), "")
        if not path:
            QMessageBox.warning(self, "Arquivo não encontrado", "Esse arquivo foi movido, renomeado ou apagado fora do Epicuro.")
            return
        try:
            open_file(path)
        except Exception as exc:
            QMessageBox.warning(self, "Não foi possível abrir", str(exc))

    def open_selected_completed(self) -> None:
        path = self._first_selected_library_path()
        if path:
            open_in_file_manager(path)
        elif self.completed.currentRow() >= 0:
            QMessageBox.warning(self, "Arquivo não encontrado", "O caminho salvo não existe mais.")
        else:
            self.open_download_folder()

    def copy_completed_paths(self) -> None:
        files = self.completed.selected_file_paths()
        if not files:
            return
        QApplication.clipboard().setText("\n".join(files))
        self.status_connection.setText(f"● {len(files)} caminho(s) copiado(s)")

    def _show_library_menu(self, pos) -> None:
        row = self.completed.rowAt(pos.y())
        selected_rows = self._selected_library_rows()
        if row >= 0 and row not in selected_rows:
            self.completed.clearSelection()
            self.completed.selectRow(row)
        menu = QMenu(self.completed)
        open_action = menu.addAction(make_icon("file", 18), "Abrir arquivo")
        reveal_action = menu.addAction(make_icon("folder", 18), "Mostrar na pasta")
        copy_action = menu.addAction(make_icon("copy", 18), "Copiar caminho")
        menu.addSeparator()
        remove_action = menu.addAction(make_icon("trash", 18), "Remover da biblioteca")
        has_files = bool(self.completed.selected_file_paths())
        has_rows = bool(self._selected_library_rows())
        open_action.setEnabled(has_files)
        reveal_action.setEnabled(has_files)
        copy_action.setEnabled(has_files)
        remove_action.setEnabled(has_rows)
        chosen = menu.exec(self.completed.viewport().mapToGlobal(pos))
        if chosen is open_action:
            self.open_completed_file()
        elif chosen is reveal_action:
            self.open_selected_completed()
        elif chosen is copy_action:
            self.copy_completed_paths()
        elif chosen is remove_action:
            self.remove_selected_history()

    def remove_selected_history(self) -> None:
        ids: set[str] = set()
        for row in self._selected_library_rows():
            item = self.completed.item(row, 0)
            if item:
                value = item.data(HISTORY_ID_ROLE)
                if value:
                    ids.add(str(value))
        if not ids:
            return
        removed = self.history_store.remove_ids(ids)
        if removed:
            self.refresh_history()
            self.status_connection.setText(f"● {removed} item(ns) removido(s) da biblioteca")

    def apply_library_filter(self) -> None:
        if not hasattr(self, "completed"):
            return
        query = self.library_search.text().strip().lower() if hasattr(self, "library_search") else ""
        visible = 0
        for row in range(self.completed.rowCount()):
            text = " ".join(
                self.completed.item(row, col).text() if self.completed.item(row, col) else ""
                for col in range(self.completed.columnCount())
            ).lower()
            show = not query or query in text
            self.completed.setRowHidden(row, not show)
            if show:
                visible += 1
        total = self.completed.rowCount()
        if hasattr(self, "library_count"):
            self.library_count.setText(f"{visible}/{total}" if query else f"{total} arquivo{'s' if total != 1 else ''}")

    def _update_library_actions(self) -> None:
        if not hasattr(self, "completed"):
            return
        has_files = bool(self.completed.selected_file_paths())
        for btn in (getattr(self, "library_open_btn", None), getattr(self, "library_reveal_btn", None), getattr(self, "library_copy_btn", None)):
            if btn is not None:
                btn.setEnabled(has_files)

    def clear_history(self) -> None:
        if not self.history_store.load():
            return
        answer = QMessageBox.question(
            self,
            "Limpar biblioteca",
            "Remover o histórico visual? Os arquivos baixados não serão apagados.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            self.history_store.clear()
            self.refresh_history()

    # -------------------------------------------------------------- settings
    def open_download_folder(self) -> None:
        open_in_file_manager(self.settings.get("download_dir", str(DOWNLOAD_DIR)))

    def open_options(self) -> None:
        previous_auto_start = bool(self.settings.get("auto_start_queue", True))
        dlg = OptionsDialog(self.settings, self)
        if dlg.exec() == QDialog.Accepted:
            self.settings = dlg.values()
            self.settings_store.save(self.settings)
            validate_download_directory(self.settings["download_dir"], create=True)
            self._update_status_bar()
            if self.settings.get("auto_start_queue", True) and not previous_auto_start and not self.active_job_id:
                self._start_next_if_idle()

    def show_tools(self) -> None:
        cleanup_blocked = self.active_job_id is not None or any(j.status == "Pausado" for j in self.jobs.values())
        dlg = ToolsDialog(
            self.settings,
            active_download=cleanup_blocked,
            refresh_library=self.refresh_history,
            parent=self,
        )
        dlg.exec()

    def show_help(self) -> None:
        QMessageBox.information(
            self,
            "Epicuro · Ajuda",
            "Novo link: adiciona mídia à fila.\n"
            "Ctrl+Shift+V: usa o link copiado.\n"
            "Ctrl+Enter: inicia ou retoma.\n"
            "Delete: remove o item selecionado.\n\n"
            "Na Biblioteca, arraste arquivos diretamente para o Explorer, Área de Trabalho ou outro aplicativo.\n\n"
            "Use apenas conteúdo que você tenha permissão para baixar.",
        )

    # --------------------------------------------------------------- status
    def _update_status_bar(self) -> None:
        waiting = sum(1 for j in self.jobs.values() if j.status == "Aguardando")
        paused = sum(1 for j in self.jobs.values() if j.status == "Pausado")
        active = 1 if self.active_job_id else 0
        parts = [f"Fila: {waiting}", f"Ativo: {active}"]
        if paused:
            parts.append(f"Pausado: {paused}")
        self.status_queue.setText("  ·  ".join(parts))
        self.status_speed.setText(f"↓ {human_speed(self.current_speed)}")
        if hasattr(self, "transfer_count"):
            total = len(self.jobs)
            self.transfer_count.setText(f"{total} item" if total == 1 else f"{total} itens")
        self._update_action_states()

    def closeEvent(self, event) -> None:  # noqa: N802 - API Qt
        # Closing the main window stops queued work and exits the application.
        self._closing = True
        self.pending_request = None
        self.queue.clear()
        self._start_next_pending = False
        if self.download_worker is not None:
            try:
                self.download_worker.cancel()
            except Exception:
                pass
        event.accept()
        app = QApplication.instance()
        if app is not None:
            app.quit()
