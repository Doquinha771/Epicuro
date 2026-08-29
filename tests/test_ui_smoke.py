from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

NEEDED = ("PySide6", "yt_dlp", "imageio_ffmpeg")
pytestmark = pytest.mark.skipif(
    not all(importlib.util.find_spec(x) for x in NEEDED),
    reason="UI smoke test requires runtime dependencies",
)


def _app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def test_ui_builds_offscreen():
    app = _app()
    from epicuro.ui import AppWindow

    window = AppWindow()
    assert "Epicuro 3.4" in window.windowTitle()
    assert window.transfers.columnCount() == 9
    assert window.completed.columnCount() == 6
    assert window.act_new.isEnabled()
    assert window.search_edit.placeholderText() == "Pesquisar transferências..."
    assert window.library_search.placeholderText() == "Pesquisar biblioteca..."
    window.close()
    app.processEvents()


def test_new_download_fields_validate_and_detect_service():
    app = _app()
    from epicuro.ui import AddDownloadDialog

    dialog = AddDownloadDialog({"mode": "video", "video_quality": "1080p", "audio_quality": "320"})
    dialog.url_edit.setText("não é link")
    app.processEvents()
    assert not dialog.ok_button.isEnabled()

    dialog.url_edit.setText("https://youtu.be/example")
    app.processEvents()
    assert dialog.ok_button.isEnabled()
    assert "YouTube" in dialog.url_state.text()

    dialog.url_edit.setText("https://open.spotify.com/track/123")
    app.processEvents()
    assert dialog.ok_button.isEnabled()
    assert dialog.mode.currentData() == "spotify"

    dialog.url_edit.setText("https://youtu.be/example2")
    app.processEvents()
    assert dialog.mode.currentData() != "spotify"
    dialog.close()


def test_options_download_folder_field_is_validated(tmp_path):
    app = _app()
    from epicuro.ui import OptionsDialog

    dialog = OptionsDialog({
        "download_dir": str(tmp_path),
        "auto_open_folder": False,
        "auto_start_queue": True,
    })
    dialog.folder.setText("")
    app.processEvents()
    assert not dialog.save_button.isEnabled()

    file_target = tmp_path / "arquivo.txt"
    file_target.write_text("x", encoding="utf-8")
    dialog.folder.setText(str(file_target))
    app.processEvents()
    assert not dialog.save_button.isEnabled()

    target = tmp_path / "downloads"
    dialog.folder.setText(str(target))
    app.processEvents()
    assert dialog.save_button.isEnabled()
    dialog.close()


def test_tools_dialog_builds_and_exposes_maintenance_actions(tmp_path):
    app = _app()
    from epicuro.ui import ToolsDialog

    dialog = ToolsDialog(
        {"download_dir": str(tmp_path)},
        active_download=False,
        refresh_library=lambda: None,
    )
    app.processEvents()
    assert dialog.cleanup_button.isEnabled()
    assert "incompleto" in dialog.partial_state.text().lower()
    dialog.close()
