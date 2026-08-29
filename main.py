from __future__ import annotations

import importlib.util
import multiprocessing
import os
import subprocess
import sys


_WINDOWS_JOB_HANDLE = None


def ensure_standard_streams() -> None:
    """Provide harmless streams in PyInstaller windowed mode.

    PyInstaller's Windows ``--noconsole`` mode may expose stdin/stdout/stderr
    as ``None``. Some third-party CLIs (notably the internal SpotDL worker)
    still probe those objects even when their output is intentionally hidden.
    Point missing streams at ``os.devnull`` so the GUI remains terminal-free
    without making those libraries crash.
    """
    if sys.stdin is None:
        sys.stdin = open(os.devnull, "r", encoding="utf-8")
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


def install_windows_kill_job() -> None:
    """Put the app in a Windows Job Object so child tools die with the GUI.

    This covers FFmpeg/SpotDL even if the window is closed while a child process
    is busy. Failure is harmless (some launchers place apps in restrictive jobs).
    """
    global _WINDOWS_JOB_HANDLE
    if os.name != "nt" or _WINDOWS_JOB_HANDLE is not None:
        return
    try:
        import ctypes
        from ctypes import wintypes

        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
        JobObjectExtendedLimitInformation = 9

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_ulonglong),
                ("WriteOperationCount", ctypes.c_ulonglong),
                ("OtherOperationCount", ctypes.c_ulonglong),
                ("ReadTransferCount", ctypes.c_ulonglong),
                ("WriteTransferCount", ctypes.c_ulonglong),
                ("OtherTransferCount", ctypes.c_ulonglong),
            ]

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_longlong),
                ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ("IoInfo", IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        kernel32.SetInformationJobObject.restype = wintypes.BOOL
        kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE

        job = kernel32.CreateJobObjectW(None, None)
        if not job:
            return
        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel32.SetInformationJobObject(
            job, JobObjectExtendedLimitInformation, ctypes.byref(info), ctypes.sizeof(info)
        ):
            kernel32.CloseHandle(job)
            return
        if not kernel32.AssignProcessToJobObject(job, kernel32.GetCurrentProcess()):
            kernel32.CloseHandle(job)
            return
        _WINDOWS_JOB_HANDLE = job
    except Exception:
        # App startup must never fail just because the host restricts job objects.
        _WINDOWS_JOB_HANDLE = None

REQUIRED = {
    "PySide6": "PySide6>=6.7",
    "yt_dlp": "yt-dlp[default]>=2025.1.0",
    "imageio_ffmpeg": "imageio-ffmpeg>=0.5.1",
    "spotdl": "spotdl>=4.2",
    "pkg_resources": "setuptools>=70,<81",
}


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def ensure_dependencies() -> None:
    missing = [pkg for module, pkg in REQUIRED.items() if importlib.util.find_spec(module) is None]
    if not missing:
        return
    if is_frozen():
        # A build correta já contém tudo. Em modo frozen, o próprio executável
        # não deve ser reutilizado como interpretador para instalar pacotes.
        raise RuntimeError(
            "A instalação do Epicuro está incompleta. Refaça o build pelo GERAR_EXE.bat.\n\n"
            f"Componentes ausentes: {', '.join(missing)}"
        )
    print("[Epicuro] Instalando dependências necessárias:", ", ".join(missing))
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", *missing])


def run_spotdl_worker() -> int:
    """Internal worker used by the frozen GUI to run SpotDL without a console."""
    args = sys.argv[sys.argv.index("--spotdl-worker") + 1 :]
    sys.argv = ["spotdl", *args]
    try:
        from spotdl import console_entry_point

        result = console_entry_point()
        return int(result or 0)
    except SystemExit as exc:
        if isinstance(exc.code, int):
            return exc.code
        return 0 if exc.code in (None, "") else 1


def show_startup_error(message: str) -> None:
    # Prefer a native message box on Windows even when the EXE has no console.
    if os.name == "nt":
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(None, message, "Epicuro", 0x10)
            return
        except Exception:
            pass
    print(message, file=sys.stderr)


def main() -> int:
    multiprocessing.freeze_support()
    ensure_standard_streams()
    install_windows_kill_job()
    if "--spotdl-worker" in sys.argv:
        return run_spotdl_worker()

    try:
        ensure_dependencies()
    except Exception as exc:
        show_startup_error(str(exc))
        return 1

    # Keep Qt's scaling decisions deterministic before QApplication is created.
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    from PySide6.QtWidgets import QApplication, QStyleFactory
    from epicuro.ui import AppWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Epicuro")
    app.setApplicationDisplayName("Epicuro")
    app.setOrganizationName("Epicuro")
    app.setQuitOnLastWindowClosed(True)

    # Fusion keeps the custom theme consistent across supported Windows versions.
    if "Fusion" in QStyleFactory.keys():
        app.setStyle("Fusion")

    window = AppWindow()
    window.show()
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
