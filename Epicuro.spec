# -*- mode: python ; coding: utf-8 -*-
"""Lean Windows build for Epicuro 2.0.1.

The project intentionally depends on PySide6-Essentials instead of the full
PySide6 distribution. Only QtCore/QtGui/QtWidgets are imported by the app.
"""
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules, copy_metadata

binaries = []
datas = [("assets/epicuro.ico", "assets")]
hiddenimports = ["pkg_resources"]

# yt-dlp discovers extractors/postprocessors dynamically.
hiddenimports += collect_submodules("yt_dlp.extractor")
hiddenimports += collect_submodules("yt_dlp.postprocessor")
try:
    datas += copy_metadata("yt-dlp")
except Exception:
    pass

# imageio-ffmpeg contains the FFmpeg binary used by both yt-dlp and SpotDL.
i_datas, i_binaries, i_hidden = collect_all("imageio_ffmpeg")
datas += i_datas
binaries += i_binaries
hiddenimports += i_hidden

# SpotDL imports providers dynamically. Keep Python modules and package data,
# but do not use collect_all(), which can pull unrelated dependency payloads.
hiddenimports += collect_submodules("spotdl")
try:
    datas += collect_data_files("spotdl", include_py_files=False)
except Exception:
    pass
try:
    datas += copy_metadata("spotdl")
except Exception:
    pass

qt_excludes = [
    "PySide6.Qt3DAnimation", "PySide6.Qt3DCore", "PySide6.Qt3DExtras",
    "PySide6.Qt3DInput", "PySide6.Qt3DLogic", "PySide6.Qt3DRender",
    "PySide6.QtBluetooth", "PySide6.QtCharts", "PySide6.QtDataVisualization",
    "PySide6.QtDesigner", "PySide6.QtGraphs", "PySide6.QtHelp",
    "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets", "PySide6.QtNetworkAuth",
    "PySide6.QtNfc", "PySide6.QtPdf", "PySide6.QtPdfWidgets",
    "PySide6.QtPositioning", "PySide6.QtQml", "PySide6.QtQuick",
    "PySide6.QtQuickControls2", "PySide6.QtQuickWidgets", "PySide6.QtRemoteObjects",
    "PySide6.QtSensors", "PySide6.QtSerialBus", "PySide6.QtSerialPort",
    "PySide6.QtSpatialAudio", "PySide6.QtStateMachine", "PySide6.QtTextToSpeech",
    "PySide6.QtUiTools", "PySide6.QtWebChannel", "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineQuick", "PySide6.QtWebEngineWidgets", "PySide6.QtWebSockets",
]

excludes = qt_excludes + [
    "numpy", "pandas", "scipy", "matplotlib", "IPython", "jupyter",
    "notebook", "pytest", "sphinx",
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=1,
)

# PySide6-Essentials plus the explicit excludes above keep the Qt payload lean.

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Epicuro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/epicuro.ico",
    version="assets/version_info.txt",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Epicuro",
)
