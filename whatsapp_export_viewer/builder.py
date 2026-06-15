from __future__ import annotations

import json
import tempfile
import zipfile
from collections import Counter
from datetime import datetime
from html import escape
from importlib import resources
from pathlib import Path
from typing import Any

from .i18n import load_translations, normalize_language
from .media import copy_media, media_kind
from .parser import match_message_line, parse_chat_text, read_text_flex, safe_name

MediaMap = dict[str, list[dict[str, Any]]]


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


def prepare_output_directory(output: Path) -> Path:
    output = output.expanduser().resolve()
    if output.exists() and not output.is_dir():
        raise NotADirectoryError(f"Output path exists and is not a directory: {output}")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    return output


def discover_participants(zip_path: Path) -> list[str]:
    zip_path = zip_path.expanduser()
    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP not found: {zip_path}")
    with tempfile.TemporaryDirectory() as tmp:
        extracted = Path(tmp) / "extract"
        extracted.mkdir()
        safe_extract_zip(zip_path, extracted)
        chat_file = find_chat_file(extracted)
        messages = parse_chat_text(read_text_flex(chat_file))
    participants = Counter(message["sender"] for message in messages if message.get("sender"))
    return [name for name, _count in participants.most_common()]


def date_input_format(language: str | None) -> str:
    return "%m/%d/%Y" if normalize_language(language) == "en" else "%d/%m/%Y"


def date_format_label(language: str | None) -> str:
    return "MM/DD/YYYY" if normalize_language(language) == "en" else "DD/MM/YYYY"


def parse_filter_date(value: str | None, language: str | None = None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    for fmt in (date_input_format(language), "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Invalid date '{value}'. Use {date_format_label(language)}.")


def filter_messages_by_date(messages: list[dict[str, Any]], date_from: str | None, date_to: str | None, language: str | None = None) -> list[dict[str, Any]]:
    start = parse_filter_date(date_from, language)
    end = parse_filter_date(date_to, language)
    if start and end and start > end:
        raise ValueError("Start date must be before or equal to end date.")
    if not start and not end:
        return messages
    filtered: list[dict[str, Any]] = []
    for message in messages:
        if not message.get("datetime"):
            continue
        current = datetime.fromisoformat(message["datetime"])
        current_day = datetime(current.year, current.month, current.day)
        if start and current_day < start:
            continue
        if end and current_day > end:
            continue
        filtered.append(message)
    return filtered


def original_text_from_messages(messages: list[dict[str, Any]]) -> str:
    lines = []
    for message in messages:
        prefix = f"{message.get('date', '')} {message.get('time', '')}"
        sender = f" - {message['sender']}:" if message.get("sender") else " -"
        text = message.get("text", "")
        refs = " ".join(f"<attached: {ref}>" for ref in message.get("attachment_refs", []))
        body = " ".join(part for part in (text, refs) if part).strip()
        lines.append(f"{prefix}{sender} {body}".rstrip())
    return "\n".join(lines) + ("\n" if lines else "")


def inspect_export(zip_path: Path) -> dict[str, Any]:
    zip_path = zip_path.expanduser()
    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP not found: {zip_path}")
    with tempfile.TemporaryDirectory() as tmp:
        extracted = Path(tmp) / "extract"
        extracted.mkdir()
        safe_extract_zip(zip_path, extracted)
        chat_file = find_chat_file(extracted)
        messages = parse_chat_text(read_text_flex(chat_file))
        media = Counter()
        for item in extracted.rglob("*"):
            if item.is_file() and item != chat_file:
                kind = media_kind(item)
                if kind:
                    media[kind] += 1
    participants = Counter(message["sender"] for message in messages if message.get("sender"))
    dates = [message["date"] for message in messages if message.get("date")]
    events = Counter(message["type"] for message in messages if message.get("type") not in {"message", "system"})
    return {
        "total_messages": len(messages),
        "first_date": dates[0] if dates else "",
        "last_date": dates[-1] if dates else "",
        "participants": [name for name, _count in participants.most_common()],
        "media": {
            "images": media.get("images", 0),
            "videos": media.get("videos", 0),
            "audios": media.get("audios", 0),
            "documents": media.get("documents", 0),
        },
        "events": dict(events),
    }


def attach_media(messages: list[dict[str, Any]], media_map: MediaMap, owner: str | None) -> None:
    for message in messages:
        message["side"] = "out" if owner and message.get("sender") == owner else "in"
        if message["type"] == "system":
            message["side"] = "system"
        seen: set[str] = set()
        for ref in message.get("attachment_refs", []):
            found = False
            for attachment in media_map.get(safe_name(ref), []):
                if attachment["path"] in seen:
                    continue
                message["attachments"].append(attachment)
                seen.add(attachment["path"])
                found = True
            if not found:
                message.setdefault("missing_attachments", []).append(safe_name(ref))


def summarize(messages: list[dict[str, Any]], media_map: MediaMap | None = None) -> dict[str, Any]:
    participants = Counter(m["sender"] for m in messages if m.get("sender"))
    seen_media: set[str] = set()
    media = Counter()
    for message in messages:
        for attachment in message.get("attachments", []):
            path = attachment["path"]
            if path in seen_media:
                continue
            seen_media.add(path)
            media[attachment["kind"]] += 1
    dates = Counter(m["date"] for m in messages if m.get("date"))
    events = Counter(m["type"] for m in messages if m.get("type") not in {"message", "system"})
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
        "events": dict(events),
        "dates": dict(sorted_dates),
    }


def viewer_translations(language: str | None) -> dict[str, str]:
    translations = load_translations(language)
    return {key: str(value) for key, value in translations.items() if key.startswith("viewer_")}


def render_html_template(template: str, translations: dict[str, str]) -> str:
    html = template
    for key, value in translations.items():
        html = html.replace("{{" + key + "}}", escape(value, quote=True))
    return html


def js_data_literal(messages: list[dict[str, Any]], summary: dict[str, Any], translations: dict[str, str]) -> str:
    payload = {"messages": messages, "summary": summary, "translations": translations}
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    return "window.WHATSAPP_EXPORT_DATA = " + data + ";\n"


def template_text(name: str) -> str:
    return resources.files("whatsapp_export_viewer.templates").joinpath(name).read_text(encoding="utf-8")


def write_static_files(output: Path, messages: list[dict[str, Any]], summary: dict[str, Any], translations: dict[str, str]) -> None:
    index = render_html_template(template_text("index.html"), translations)
    css = template_text("style.css")
    app = template_text("app.js")
    (output / "assets").mkdir(parents=True, exist_ok=True)
    (output / "index.html").write_text(index, encoding="utf-8")
    (output / "assets" / "style.css").write_text(css, encoding="utf-8")
    (output / "assets" / "app.js").write_text(app, encoding="utf-8")


def build_export(
    zip_path: Path,
    output: Path,
    owner: str | None = None,
    language: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    progress_callback: Any | None = None,
) -> None:
    zip_path = zip_path.expanduser()
    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP not found: {zip_path}")
    output = prepare_output_directory(output)
    language = normalize_language(language)
    translations = viewer_translations(language)
    progress = progress_callback or (lambda _step, _message: None)

    with tempfile.TemporaryDirectory() as tmp:
        progress(1, "progress_extracting")
        extracted = Path(tmp) / "extract"
        extracted.mkdir()
        safe_extract_zip(zip_path, extracted)
        progress(2, "progress_reading")
        chat_file = find_chat_file(extracted)
        original_dir = output / "original"
        original_dir.mkdir(parents=True)
        original_chat = original_dir / "chat.txt"
        raw_chat_text = read_text_flex(chat_file)
        messages = parse_chat_text(raw_chat_text)
        messages = filter_messages_by_date(messages, date_from, date_to, language)
        original_chat.write_text(original_text_from_messages(messages) if (date_from or date_to) else raw_chat_text, encoding="utf-8")
        progress(3, "progress_copying_media")
        allowed_names = {safe_name(ref) for message in messages for ref in message.get("attachment_refs", [])} if (date_from or date_to) else None
        media_map = copy_media(extracted, output, chat_file, allowed_names=allowed_names)
        attach_media(messages, media_map, owner)
        summary = summarize(messages, media_map)
        summary["date_range"] = {
            "from": date_from or "",
            "to": date_to or "",
        }

    progress(4, "progress_writing_viewer")
    (output / "data").mkdir(parents=True, exist_ok=True)
    (output / "data" / "messages.json").write_text(json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "data" / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "data" / "translations.json").write_text(json.dumps(translations, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "data" / "bootstrap.js").write_text(js_data_literal(messages, summary, translations), encoding="utf-8")
    write_static_files(output, messages, summary, translations)
    progress(5, "progress_done")
