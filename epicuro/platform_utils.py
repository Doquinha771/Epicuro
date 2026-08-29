from __future__ import annotations

import os


def enable_dark_titlebar(widget) -> None:
    """Ask Windows 10/11 DWM for an immersive dark title bar when available."""
    if os.name != "nt":
        return
    try:
        import ctypes

        hwnd = int(widget.winId())
        enabled = ctypes.c_int(1)
        dwm = ctypes.windll.dwmapi
        # 20 is current, 19 covers older Windows 10 builds.
        for attribute in (20, 19):
            result = dwm.DwmSetWindowAttribute(
                ctypes.c_void_p(hwnd),
                ctypes.c_uint(attribute),
                ctypes.byref(enabled),
                ctypes.sizeof(enabled),
            )
            if result == 0:
                break
    except Exception:
        pass
