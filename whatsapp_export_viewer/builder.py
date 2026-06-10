from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from collections import Counter
from datetime import datetime
from importlib import resources
from pathlib import Path
from typing import Any

from .media import copy_media
from .parser import match_message_line, parse_chat_text, read_text_flex, safe_name


def safe_extract_zip(zip_path: Path, destination: Path) -> None:
    destination = destination.resolve()
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if destination != target and destination not in target.parents:
                raise ValueError(f"Unsafe ZIP entry blocked: {member.filename}")
        archive.extractall(destination)


def find_chat_file(root: Path) -> Path:
    txt_files = sorted(root.rglob("*.txt"), key=lambda item: item.stat().st_size, reverse=True)
    if not txt_files:
        raise FileNotFoundError("No .txt chat file was found inside the ZIP.")
    scored = []
    for item in txt_files:
        sample = read_text_flex(item)[:20000]
        score = sum(1 for line in sample.splitlines() if match_message_line(line))
        scored.append((score, item.stat().st_size, item))
    scored.sort(reverse=True)
    if scored[0][0] == 0:
        raise ValueError("TXT files were found, but none looks like a WhatsApp chat export.")
    return scored[0][2]


def attach_media(messages: list[dict[str, Any]], media_map: dict[str, dict[str, Any]], owner: str | None) -> None:
    for message in messages:
        message["side"] = "out" if owner and message.get("sender") == owner else "in"
        if message["type"] == "system":
            message["side"] = "system"
        seen: set[str] = set()
        for ref in message.get("attachment_refs", []):
            attachment = media_map.get(safe_name(ref))
            if attachment and attachment["path"] not in seen:
                message["attachments"].append(attachment)
                seen.add(attachment["path"])
        text = message.get("text", "")
        for name, attachment in media_map.items():
            if name in text and attachment["path"] not in seen:
                message["attachments"].append(attachment)
                seen.add(attachment["path"])


def summarize(messages: list[dict[str, Any]], media_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    participants = Counter(m["sender"] for m in messages if m.get("sender"))
    media = Counter(item["kind"] for item in media_map.values())
    dates = Counter(m["date"] for m in messages if m.get("date"))
    sorted_dates = sorted(dates.items(), key=lambda item: datetime.strptime(item[0], "%d/%m/%Y"))
    return {
        "total_messages": len(messages),
        "participants": dict(sorted(participants.items())),
        "media": {
            "images": media.get("images", 0),
            "videos": media.get("videos", 0),
            "audios": media.get("audios", 0),
            "documents": media.get("documents", 0),
        },
        "dates": dict(sorted_dates),
    }


def js_data_literal(messages: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    payload = {"messages": messages, "summary": summary}
    return "window.WHATSAPP_EXPORT_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n"


def template_text(name: str) -> str:
    return resources.files("whatsapp_export_viewer.templates").joinpath(name).read_text(encoding="utf-8")


def write_static_files(output: Path, self_contained: bool, messages: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    index = template_text("index.html")
    css = template_text("style.css")
    app = template_text("app.js")
    if self_contained:
        html = index.replace('<link rel="stylesheet" href="assets/style.css">', f"<style>{css}</style>")
        html = html.replace('<script src="data/bootstrap.js"></script>', f"<script>{js_data_literal(messages, summary)}</script>")
        html = html.replace('<script src="assets/app.js"></script>', f"<script>{app}</script>")
        (output / "index.html").write_text(html, encoding="utf-8")
        return
    (output / "assets").mkdir(parents=True, exist_ok=True)
    (output / "index.html").write_text(index, encoding="utf-8")
    (output / "assets" / "style.css").write_text(css, encoding="utf-8")
    (output / "assets" / "app.js").write_text(app, encoding="utf-8")


def build_export(zip_path: Path, output: Path, owner: str | None = None, convert_audio: bool = False, self_contained: bool = False) -> None:
    zip_path = zip_path.expanduser()
    output = output.expanduser()
    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP not found: {zip_path}")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    with tempfile.TemporaryDirectory() as tmp:
        extracted = Path(tmp) / "extract"
        extracted.mkdir()
        safe_extract_zip(zip_path, extracted)
        chat_file = find_chat_file(extracted)
        original_dir = output / "original"
        original_dir.mkdir(parents=True)
        original_chat = original_dir / "chat.txt"
        original_chat.write_text(read_text_flex(chat_file), encoding="utf-8")

        messages = parse_chat_text(original_chat.read_text(encoding="utf-8"))
        media_map = copy_media(extracted, output, chat_file, convert_audio)
        attach_media(messages, media_map, owner)
        summary = summarize(messages, media_map)

    (output / "data").mkdir(parents=True, exist_ok=True)
    (output / "data" / "messages.json").write_text(json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "data" / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "data" / "bootstrap.js").write_text(js_data_literal(messages, summary), encoding="utf-8")
    write_static_files(output, self_contained, messages, summary)
