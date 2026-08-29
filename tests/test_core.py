from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def load_core():
    yt_dlp = types.ModuleType("yt_dlp")

    class DummyYDL:
        def __init__(self, *_a, **_kw):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *_a):
            return False
        def extract_info(self, *_a, **_kw):
            return {"title": "Teste", "webpage_url": "https://example.com"}
        def download(self, *_a, **_kw):
            return 0

    yt_dlp.YoutubeDL = DummyYDL
    imageio_ffmpeg = types.ModuleType("imageio_ffmpeg")
    imageio_ffmpeg.get_ffmpeg_exe = lambda: "ffmpeg-test"

    old_yt = sys.modules.get("yt_dlp")
    old_ff = sys.modules.get("imageio_ffmpeg")
    sys.modules["yt_dlp"] = yt_dlp
    sys.modules["imageio_ffmpeg"] = imageio_ffmpeg
    try:
        path = Path(__file__).resolve().parents[1] / "epicuro" / "core.py"
        name = "epicuro_core_under_test"
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        assert spec and spec.loader
        spec.loader.exec_module(module)
        return module
    finally:
        if old_yt is None:
            sys.modules.pop("yt_dlp", None)
        else:
            sys.modules["yt_dlp"] = old_yt
        if old_ff is None:
            sys.modules.pop("imageio_ffmpeg", None)
        else:
            sys.modules["imageio_ffmpeg"] = old_ff


def test_formatters_and_service_detection():
    core = load_core()
    assert core.human_bytes(0) == "0 B"
    assert "MB" in core.human_bytes(5 * 1024 * 1024)
    assert core.human_eta(65) == "1m 05s"
    assert core.detect_service("https://youtu.be/test") == "youtube"
    assert core.detect_service("https://open.spotify.com/track/123") == "spotify"
    assert core.detect_service("https://example.com/file") == "generic"


def test_history_and_settings_are_persistent(tmp_path):
    core = load_core()
    history_path = tmp_path / "history.json"
    history = core.HistoryStore(history_path)
    history.add({"title": "A"})
    history.add({"title": "B"})
    assert [x["title"] for x in history.load()] == ["B", "A"]
    assert not history_path.with_suffix(".json.tmp").exists()
    history.clear()
    assert history.load() == []

    settings_path = tmp_path / "settings.json"
    settings = core.SettingsStore(settings_path)
    data = settings.load()
    data["video_quality"] = "720p"
    settings.save(data)
    assert settings.load()["video_quality"] == "720p"
    assert not settings_path.with_suffix(".json.tmp").exists()


def test_download_engine_collects_created_files(tmp_path):
    core = load_core()
    engine = core.DownloadEngine(tmp_path)
    events = []

    def fake_download(_url, _mode, _quality, _playlist_mode, progress):
        progress({"stage": "downloading", "percent": 42, "downloaded": 42, "total": 100})
        (tmp_path / "arquivo.mp4").write_bytes(b"epicuro")

    engine._download_ytdlp = fake_download
    created = engine.download(
        "https://example.com/video",
        "video",
        "720p",
        progress=events.append,
    )
    assert len(created) == 1
    assert Path(created[0]).name == "arquivo.mp4"
    assert events[-1]["stage"] == "completed"
    assert events[-1]["percent"] == 100


def test_cancel_terminates_external_worker(tmp_path):
    core = load_core()
    engine = core.DownloadEngine(tmp_path)

    class Proc:
        terminated = False
        killed = False
        def poll(self): return None
        def terminate(self): self.terminated = True
        def wait(self, timeout=None): return 0
        def kill(self): self.killed = True

    proc = Proc()
    engine._spotify_process = proc
    engine.cancel()
    assert engine.cancel_event.is_set()
    assert proc.terminated is True
    assert proc.killed is False


def test_history_can_remove_selected_entries_without_touching_files(tmp_path):
    core = load_core()
    history = core.HistoryStore(tmp_path / "history.json")
    media_a = tmp_path / "a.mp4"
    media_b = tmp_path / "b.mp3"
    media_a.write_bytes(b"a")
    media_b.write_bytes(b"b")
    history.add({"id": "a", "title": "A", "files": [str(media_a)]})
    history.add({"id": "b", "title": "B", "files": [str(media_b)]})
    assert history.remove_ids({"a"}) == 1
    assert [item["id"] for item in history.load()] == ["b"]
    assert media_a.exists() and media_b.exists()


def test_media_url_validation_is_strict_and_friendly():
    core = load_core()
    assert core.normalize_media_url("  https://youtu.be/test  ") == "https://youtu.be/test"
    for bad in ("", "youtube.com/watch?v=1", "ftp://example.com/a", "https://not a url.com"):
        try:
            core.normalize_media_url(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid URL accepted: {bad!r}")


def test_download_directory_validation_and_creation(tmp_path):
    core = load_core()
    target = tmp_path / "nova" / "pasta"
    validated = core.validate_download_directory(target, create=True)
    assert validated.is_dir()
    file_target = tmp_path / "arquivo.txt"
    file_target.write_text("x", encoding="utf-8")
    try:
        core.validate_download_directory(file_target)
    except ValueError:
        pass
    else:
        raise AssertionError("file path accepted as download directory")


def test_partial_download_cleanup_only_removes_known_partial_files(tmp_path):
    core = load_core()
    keep = tmp_path / "video.mp4"
    part = tmp_path / "video.mp4.part"
    state = tmp_path / "video.mp4.ytdl"
    keep.write_bytes(b"keep")
    part.write_bytes(b"1234")
    state.write_bytes(b"12")
    found = core.find_partial_downloads(tmp_path)
    assert set(found) == {part, state}
    removed, freed = core.cleanup_partial_downloads(tmp_path)
    assert removed == 2
    assert freed == 6
    assert keep.exists()
    assert not part.exists() and not state.exists()


def test_invalid_saved_settings_fall_back_to_safe_defaults(tmp_path):
    core = load_core()
    path = tmp_path / "settings.json"
    path.write_text(
        '{"mode":"wat","video_quality":"12p","audio_quality":"999","download_dir":"","auto_start_queue":0}',
        encoding="utf-8",
    )
    data = core.SettingsStore(path).load()
    assert data["mode"] == "video"
    assert data["video_quality"] == "1080p"
    assert data["audio_quality"] == "320"
    assert data["download_dir"]
    assert data["auto_start_queue"] is False
