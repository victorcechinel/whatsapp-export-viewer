from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from .parser import safe_name

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXTS = {".mp4", ".mov", ".webm"}
AUDIO_EXTS = {".opus", ".mp3", ".m4a", ".aac", ".ogg", ".wav"}
DOCUMENT_EXTS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip"}


def media_kind(path: Path) -> str | None:
    ext = path.suffix.lower()
    if ext in IMAGE_EXTS:
        return "images"
    if ext in VIDEO_EXTS:
        return "videos"
    if ext in AUDIO_EXTS:
        return "audios"
    if ext in DOCUMENT_EXTS:
        return "documents"
    return None


def unique_destination(directory: Path, filename: str) -> Path:
    base = safe_name(filename)
    dest = directory / base
    if not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    counter = 2
    while True:
        candidate = directory / f"{stem}-{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def convert_opus_to_mp3(source: Path, destination: Path) -> bool:
    if not shutil.which("ffmpeg"):
        return False
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(source), "-vn", "-codec:a", "libmp3lame", "-q:a", "4", str(destination)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0 and destination.exists()


def audio_duration(path: Path) -> float | None:
    if not shutil.which("ffprobe"):
        return None
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nokey=1:noprint_wrappers=1", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        return round(float(result.stdout.strip()), 2)
    except ValueError:
        return None


def copy_media(extracted: Path, output: Path, chat_file: Path, convert_audio: bool) -> dict[str, dict[str, Any]]:
    media_map: dict[str, dict[str, Any]] = {}
    for directory in ("images", "videos", "audios", "documents"):
        (output / "media" / directory).mkdir(parents=True, exist_ok=True)

    for source in extracted.rglob("*"):
        if not source.is_file() or source == chat_file:
            continue
        kind = media_kind(source)
        if not kind:
            continue
        dest = unique_destination(output / "media" / kind, source.name)
        shutil.copy2(source, dest)
        rel = dest.relative_to(output).as_posix()
        info: dict[str, Any] = {
            "name": source.name,
            "stored_name": dest.name,
            "kind": kind,
            "path": rel,
            "original_path": rel,
            "size": dest.stat().st_size,
        }
        if kind == "audios":
            info["duration"] = audio_duration(dest)
            if convert_audio and dest.suffix.lower() == ".opus":
                mp3_dest = unique_destination(output / "media" / "audios", dest.with_suffix(".mp3").name)
                if convert_opus_to_mp3(dest, mp3_dest):
                    info["mp3_path"] = mp3_dest.relative_to(output).as_posix()
        media_map.setdefault(safe_name(source.name), info)
    return media_map

