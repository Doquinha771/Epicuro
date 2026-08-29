from __future__ import annotations

import json
import importlib.util
import os
import subprocess
import threading
import time
import sys
from importlib import metadata
from urllib.parse import urlparse
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import imageio_ffmpeg
import yt_dlp

APP_NAME = "Epicuro"
APP_VERSION = "3.4.0"
BASE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DATA_DIR = BASE_DIR / "data"
HISTORY_FILE = DATA_DIR / "history.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()


@dataclass
class MediaInfo:
    url: str
    title: str = "Conteúdo reconhecido"
    uploader: str = ""
    duration: int = 0
    thumbnail: str = ""
    is_playlist: bool = False
    playlist_count: int = 0
    extractor: str = ""
    webpage_url: str = ""

    @property
    def duration_text(self) -> str:
        if not self.duration:
            return ""
        m, s = divmod(int(self.duration), 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


class CancelledByUser(Exception):
    pass


class HistoryStore:
    def __init__(self, path: Path = HISTORY_FILE):
        self.path = path
        self._lock = threading.Lock()

    def load(self) -> list[dict]:
        with self._lock:
            if not self.path.exists():
                return []
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                return data if isinstance(data, list) else []
            except Exception:
                return []

    def add(self, item: dict, limit: int = 100) -> None:
        with self._lock:
            current = []
            if self.path.exists():
                try:
                    current = json.loads(self.path.read_text(encoding="utf-8"))
                except Exception:
                    current = []
            current.insert(0, item)
            current = current[:limit]
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(self.path.suffix + ".tmp")
            tmp.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self.path)

    def clear(self) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(self.path.suffix + ".tmp")
            tmp.write_text("[]", encoding="utf-8")
            tmp.replace(self.path)

    def remove_ids(self, ids: set[str]) -> int:
        """Remove selected visual history entries without deleting media files."""
        if not ids:
            return 0
        with self._lock:
            current: list[dict] = []
            if self.path.exists():
                try:
                    loaded = json.loads(self.path.read_text(encoding="utf-8"))
                    current = loaded if isinstance(loaded, list) else []
                except Exception:
                    current = []
            kept = [item for item in current if str(item.get("id", "")) not in ids]
            removed = len(current) - len(kept)
            if removed:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                tmp = self.path.with_suffix(self.path.suffix + ".tmp")
                tmp.write_text(json.dumps(kept, ensure_ascii=False, indent=2), encoding="utf-8")
                tmp.replace(self.path)
            return removed


class SettingsStore:
    DEFAULTS = {
        "mode": "video",
        "video_quality": "1080p",
        "audio_quality": "320",
        "download_dir": str(DOWNLOAD_DIR),
        "auto_open_folder": False,
        "auto_start_queue": True,
    }

    def __init__(self, path: Path = SETTINGS_FILE):
        self.path = path

    def load(self) -> dict:
        data = dict(self.DEFAULTS)
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    data.update(loaded)
            except Exception:
                pass

        if data.get("mode") not in {"video", "audio", "spotify"}:
            data["mode"] = self.DEFAULTS["mode"]
        if data.get("video_quality") not in {"best", "2160p", "1440p", "1080p", "720p", "480p"}:
            data["video_quality"] = self.DEFAULTS["video_quality"]
        if str(data.get("audio_quality")) not in {"320", "256", "192", "128"}:
            data["audio_quality"] = self.DEFAULTS["audio_quality"]
        else:
            data["audio_quality"] = str(data["audio_quality"])
        if not isinstance(data.get("download_dir"), str) or not data["download_dir"].strip():
            data["download_dir"] = self.DEFAULTS["download_dir"]
        data["auto_open_folder"] = bool(data.get("auto_open_folder", False))
        data["auto_start_queue"] = bool(data.get("auto_start_queue", True))
        return data

    def save(self, data: dict) -> None:
        merged = dict(self.DEFAULTS)
        merged.update(data)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)


def human_bytes(value: float | int | None) -> str:
    if not value:
        return "0 B"
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} TB"


def human_speed(value: float | int | None) -> str:
    return f"{human_bytes(value)}/s" if value else "—"


def human_eta(seconds: float | int | None) -> str:
    if seconds is None:
        return "—"
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m:02d}m"
    if m:
        return f"{m}m {s:02d}s"
    return f"{s}s"


def normalize_media_url(value: str) -> str:
    """Validate and normalize a user-provided media URL."""
    url = (value or "").strip()
    if not url:
        raise ValueError("Cole um link para continuar.")
    parsed = urlparse(url)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError("Use um link começando com http:// ou https://.")
    if not parsed.netloc or "." not in parsed.netloc:
        raise ValueError("Esse endereço não parece ser um link válido.")
    if any(ch.isspace() for ch in url):
        raise ValueError("O link contém espaços. Confira e tente novamente.")
    return url


def validate_download_directory(value: str | Path, create: bool = False) -> Path:
    """Return a usable download directory or raise a friendly ValueError."""
    raw = str(value or "").strip().strip('"')
    if not raw:
        raise ValueError("Escolha uma pasta para os downloads.")
    path = Path(raw).expanduser()
    if path.exists() and not path.is_dir():
        raise ValueError("O destino escolhido é um arquivo, não uma pasta.")
    if create:
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ValueError(f"Não foi possível criar a pasta: {exc}") from exc
    return path.resolve() if path.exists() else path.absolute()


def detect_service(url: str) -> str:
    low = url.lower()
    if "spotify.com" in low:
        return "spotify"
    if any(x in low for x in ("youtube.com", "youtu.be", "music.youtube.com")):
        return "youtube"
    return "generic"


def runtime_diagnostics() -> dict[str, str]:
    """Small runtime report used by the Tools window and bug reports."""
    def pkg(dist_name: str, module_name: str) -> str:
        try:
            return metadata.version(dist_name)
        except metadata.PackageNotFoundError:
            return "disponível" if importlib.util.find_spec(module_name) else "não instalado"
        except Exception:
            return "indisponível"

    ffmpeg = Path(FFMPEG_PATH)
    return {
        "Epicuro": APP_VERSION,
        "Python": sys.version.split()[0],
        "yt-dlp": pkg("yt-dlp", "yt_dlp"),
        "SpotDL": pkg("spotdl", "spotdl"),
        "FFmpeg": str(ffmpeg) if ffmpeg.exists() else "não encontrado",
    }


def find_partial_downloads(directory: str | Path) -> list[Path]:
    root = Path(directory).expanduser()
    if not root.exists() or not root.is_dir():
        return []
    found: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        low = path.name.lower()
        if low.endswith(".part") or low.endswith(".ytdl"):
            found.append(path)
    return sorted(found)


def cleanup_partial_downloads(directory: str | Path) -> tuple[int, int]:
    files = find_partial_downloads(directory)
    removed = 0
    freed = 0
    for path in files:
        try:
            size = path.stat().st_size
            path.unlink()
            removed += 1
            freed += size
        except OSError:
            continue
    return removed, freed


def analyze_media(url: str) -> MediaInfo:
    url = normalize_media_url(url)

    service = detect_service(url)
    if service == "spotify":
        kind = "Playlist ou álbum do Spotify" if ("playlist/" in url or "album/" in url) else "Faixa do Spotify"
        return MediaInfo(
            url=url,
            title=kind,
            uploader="Spotify",
            is_playlist="playlist/" in url or "album/" in url,
            extractor="spotify",
            webpage_url=url,
        )

    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": "in_playlist",
        "playlistend": 30,
        "noplaylist": False,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    entries = info.get("entries") if isinstance(info, dict) else None
    is_playlist = bool(entries)
    if is_playlist:
        entries_list = [e for e in (entries or []) if e]
        first = entries_list[0] if entries_list else {}
        return MediaInfo(
            url=url,
            title=info.get("title") or "Playlist reconhecida",
            uploader=info.get("uploader") or info.get("channel") or first.get("uploader") or "",
            duration=int(first.get("duration") or 0),
            thumbnail=info.get("thumbnail") or first.get("thumbnail") or "",
            is_playlist=True,
            playlist_count=int(info.get("playlist_count") or len(entries_list)),
            extractor=info.get("extractor_key") or info.get("extractor") or "",
            webpage_url=info.get("webpage_url") or url,
        )

    return MediaInfo(
        url=url,
        title=info.get("title") or "Conteúdo reconhecido",
        uploader=info.get("uploader") or info.get("channel") or "",
        duration=int(info.get("duration") or 0),
        thumbnail=info.get("thumbnail") or "",
        is_playlist=False,
        playlist_count=0,
        extractor=info.get("extractor_key") or info.get("extractor") or "",
        webpage_url=info.get("webpage_url") or url,
    )


class DownloadEngine:
    def __init__(self, output_dir: str | Path | None = None):
        self.output_dir = validate_download_directory(output_dir or DOWNLOAD_DIR, create=True)
        self.cancel_event = threading.Event()
        self._spotify_process: Optional[subprocess.Popen] = None

    def cancel(self) -> None:
        self.cancel_event.set()
        process = self._spotify_process
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=0.8)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass

    def _check_cancel(self) -> None:
        if self.cancel_event.is_set():
            raise CancelledByUser("Download cancelado.")

    def download(
        self,
        url: str,
        mode: str,
        quality: str,
        playlist_mode: str = "single",
        progress: Optional[Callable[[dict], None]] = None,
    ) -> list[str]:
        self.cancel_event.clear()
        progress = progress or (lambda _data: None)
        started = time.time()
        service = detect_service(url)
        before = {p.resolve() for p in self.output_dir.rglob("*") if p.is_file()}

        if mode == "spotify" or service == "spotify":
            self._download_spotify(url, progress)
        else:
            self._download_ytdlp(url, mode, quality, playlist_mode, progress)

        self._check_cancel()
        after = {p.resolve() for p in self.output_dir.rglob("*") if p.is_file()}
        created = [str(p) for p in sorted(after - before, key=lambda x: x.stat().st_mtime)]
        if not created:
            recent = [p for p in after if p.stat().st_mtime >= started - 2]
            created = [str(p) for p in sorted(recent, key=lambda x: x.stat().st_mtime)]
        progress({"stage": "completed", "percent": 100, "speed": 0, "eta": 0, "filename": created[-1] if created else ""})
        return created

    def _download_ytdlp(self, url: str, mode: str, quality: str, playlist_mode: str, progress: Callable[[dict], None]) -> None:
        outtmpl = str(self.output_dir / "%(title)s.%(ext)s")
        if playlist_mode == "all":
            outtmpl = str(self.output_dir / "%(playlist_title,Unknown Playlist)s" / "%(title)s.%(ext)s")

        def hook(data: dict):
            self._check_cancel()
            status = data.get("status")
            if status == "downloading":
                total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                downloaded = data.get("downloaded_bytes") or 0
                percent = (downloaded / total * 100) if total else 0
                progress({
                    "stage": "downloading",
                    "percent": min(95, percent),
                    "speed": data.get("speed") or 0,
                    "eta": data.get("eta"),
                    "downloaded": downloaded,
                    "total": total,
                    "filename": data.get("filename") or "",
                })
            elif status == "finished":
                progress({"stage": "processing", "percent": 96, "speed": 0, "eta": None, "filename": data.get("filename") or ""})

        def post_hook(data: dict):
            self._check_cancel()
            status = data.get("status")
            pp = data.get("postprocessor") or "FFmpeg"
            if status in ("started", "processing"):
                progress({"stage": "converting", "percent": 98, "speed": 0, "eta": None, "detail": str(pp)})

        opts = {
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "ffmpeg_location": FFMPEG_PATH,
            "noplaylist": playlist_mode != "all",
            "progress_hooks": [hook],
            "postprocessor_hooks": [post_hook],
            "windowsfilenames": os.name == "nt",
            "overwrites": False,
            "continuedl": True,
            "retries": 4,
            "fragment_retries": 4,
            "concurrent_fragment_downloads": 4,
            "socket_timeout": 25,
        }

        if mode == "audio":
            bitrate = quality if quality in {"128", "192", "256", "320"} else "320"
            opts.update({
                "format": "bestaudio/best",
                "postprocessors": [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": bitrate},
                    {"key": "FFmpegMetadata"},
                    {"key": "EmbedThumbnail"},
                ],
                "writethumbnail": True,
            })
        else:
            if quality == "best":
                fmt = "bestvideo+bestaudio/best"
            else:
                height = int(quality.rstrip("p")) if quality.rstrip("p").isdigit() else 1080
                fmt = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
            opts.update({"format": fmt, "merge_output_format": "mp4"})

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    def _download_spotify(self, url: str, progress: Callable[[dict], None]) -> None:
        spotdl_args = [
            "download",
            url,
            "--output",
            str(self.output_dir / "{artists} - {title}.{output-ext}"),
        ]
        if getattr(sys, "frozen", False):
            # The packaged GUI reuses itself as a silent SpotDL worker. Calling
            # `sys.executable -m spotdl` from a frozen app would just reopen the GUI.
            cmd = [sys.executable, "--spotdl-worker", *spotdl_args]
        else:
            cmd = [sys.executable, "-m", "spotdl", *spotdl_args]
        progress({"stage": "downloading", "percent": 8, "speed": 0, "eta": None, "detail": "Preparando Spotify"})
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
        self._spotify_process = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
            startupinfo=startupinfo,
            cwd=str(self.output_dir),
        )

        # SpotDL runs without console pipes in the windowed build. Progress stays
        # below 100% until the worker process exits successfully.
        pct = 10
        while self._spotify_process.poll() is None:
            self._check_cancel()
            pct = min(92, pct + 1)
            progress({
                "stage": "downloading",
                "percent": pct,
                "speed": 0,
                "eta": None,
                "detail": "Baixando com SpotDL",
            })
            time.sleep(0.75)
        code = int(self._spotify_process.returncode or 0)
        if self.cancel_event.is_set():
            raise CancelledByUser("Download cancelado.")
        if code != 0:
            raise RuntimeError("O Spotify não pôde ser concluído. Verifique o link e sua conexão.")
        progress({"stage": "processing", "percent": 97, "speed": 0, "eta": None, "detail": "Organizando resultado"})


def open_file(path: str | Path) -> None:
    target = Path(path).expanduser()
    if not target.is_file():
        raise FileNotFoundError(str(target))
    if os.name == "nt":
        os.startfile(str(target))  # type: ignore[attr-defined]
    elif os.sys.platform == "darwin":
        subprocess.Popen(["open", str(target)])
    else:
        subprocess.Popen(["xdg-open", str(target)])


def open_in_file_manager(path: str | Path) -> None:
    """Reveal a file when possible, otherwise open its containing directory."""
    target = Path(path).expanduser()
    if target.is_file():
        if os.name == "nt":
            # Explorer understands /select,<path> and highlights the actual file.
            subprocess.Popen(["explorer.exe", f"/select,{target}"])
            return
        if os.sys.platform == "darwin":
            subprocess.Popen(["open", "-R", str(target)])
            return
        target = target.parent
    elif not target.exists() and bool(target.suffix):
        target = target.parent
    target.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        os.startfile(str(target))  # type: ignore[attr-defined]
    elif os.sys.platform == "darwin":
        subprocess.Popen(["open", str(target)])
    else:
        subprocess.Popen(["xdg-open", str(target)])


def history_item(info: MediaInfo, mode: str, quality: str, files: list[str]) -> dict:
    total_size = 0
    for f in files:
        try:
            total_size += Path(f).stat().st_size
        except OSError:
            pass
    return {
        "id": str(int(time.time() * 1000)),
        "title": info.title,
        "uploader": info.uploader,
        "url": info.url,
        "mode": mode,
        "quality": quality,
        "files": files,
        "size": total_size,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "thumbnail": info.thumbnail,
    }
