from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def load_main():
    path = Path(__file__).resolve().parents[1] / "main.py"
    name = "epicuro_main_under_test"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_spotdl_worker_forwards_arguments(monkeypatch):
    main = load_main()
    fake = types.ModuleType("spotdl")
    captured = {}

    def entry():
        captured["argv"] = list(sys.argv)
        return 0

    fake.console_entry_point = entry
    monkeypatch.setitem(sys.modules, "spotdl", fake)
    monkeypatch.setattr(sys, "argv", ["Epicuro.exe", "--spotdl-worker", "download", "https://example.test/song"])
    assert main.run_spotdl_worker() == 0
    assert captured["argv"] == ["spotdl", "download", "https://example.test/song"]


def test_windows_job_setup_is_safe_off_windows():
    main = load_main()
    # On the Linux test environment this is intentionally a no-op.
    main.install_windows_kill_job()


def test_missing_standard_streams_are_replaced(monkeypatch):
    main = load_main()
    monkeypatch.setattr(sys, "stdin", None)
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    main.ensure_standard_streams()
    assert sys.stdin is not None
    assert sys.stdout is not None
    assert sys.stderr is not None
