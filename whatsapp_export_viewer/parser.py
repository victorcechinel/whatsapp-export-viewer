from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

MEDIA_PATTERN = r"jpe?g|png|webp|gif|mp4|mov|webm|opus|mp3|m4a|aac|ogg|wav|pdf|docx?|xlsx?|zip"
LEADING_MARKERS = "\ufeff\u200e\u200f"
ATTACHED_RE = re.compile(r"<?attached:\s*([^>\n\r]+)>?", re.I)
EDITED_RE = re.compile(r"\s+\((editada|edited|editado|editado/a|editada/o)\)\s*$", re.I)
MESSAGE_PATTERNS = [
    re.compile(r"^(?P<date>\d{1,2}/\d{1,2}/\d{2,4}) (?P<time>\d{1,2}:\d{2}(?::\d{2})?) - (?P<body>.*)$"),
    re.compile(r"^\[(?P<date>\d{1,2}/\d{1,2}/\d{2,4}), (?P<time>\d{1,2}:\d{2}(?::\d{2})?)\] (?P<body>.*)$"),
]
DELETED_MARKERS = (
    "esta mensagem foi apagada",
    "essa mensagem foi apagada",
    "this message was deleted",
    "you deleted this message",
    "se eliminó este mensaje",
    "mensaje eliminado",
)
VIEW_ONCE_MARKERS = (
    "visualização única",
    "visualizacao unica",
    "view once",
    "ver una sola vez",
    "visualización única",
)
CALL_MARKERS = (
    "chamada de voz",
    "voice call",
    "llamada de voz",
    "chamada de vídeo",
    "chamada de video",
    "video call",
    "llamada de video",
    "ligação de voz",
    "ligacao de voz",
)
MISSED_CALL_MARKERS = ("perdida", "missed", "perdida")


def safe_name(name: str) -> str:
    cleaned = name.replace("\\", "/").split("/")[-1].strip()
    return cleaned or "attachment"


def read_text_flex(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "utf-16", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not read chat text file: {path}")


def parse_date(date_text: str, time_text: str) -> tuple[str, str, str]:
    day, month, year = date_text.split("/")
    if len(year) == 2:
        year = "20" + year
    if len(time_text.split(":")) == 2:
        time_text += ":00"
    dt = datetime(int(year), int(month), int(day), *[int(part) for part in time_text.split(":")])
    return dt.isoformat(), dt.strftime("%d/%m/%Y"), dt.strftime("%H:%M:%S")


def split_sender(body: str) -> tuple[str | None, str]:
    if ": " not in body:
        return None, body
    sender, text = body.split(": ", 1)
    if not sender.strip() or len(sender) > 120:
        return None, body
    return sender.strip(), text


def extract_attachment_refs(text: str) -> list[str]:
    refs: list[str] = []
    for match in ATTACHED_RE.finditer(text):
        refs.append(safe_name(match.group(1)))
    for match in re.finditer(rf"([^\s\n\r<>:\"|?*]+?\.({MEDIA_PATTERN}))", text, re.I):
        refs.append(safe_name(match.group(1)))
    return list(dict.fromkeys(refs))


def clean_message_text(text: str) -> str:
    text = ATTACHED_RE.sub("", text)
    text = text.replace("\u200e", "").replace("\u200f", "").replace("\ufeff", "")
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()


def normalize_for_detection(text: str) -> str:
    return clean_message_text(text).casefold()


def classify_message(message: dict[str, Any]) -> None:
    text = clean_message_text(message["text"])
    normalized = normalize_for_detection(message["text"])
    edited = bool(EDITED_RE.search(text))
    if edited:
        text = EDITED_RE.sub("", text).strip()
    message["edited"] = edited
    message["text"] = text
    if any(marker in normalized for marker in DELETED_MARKERS):
        message["type"] = "deleted"
    elif any(marker in normalized for marker in VIEW_ONCE_MARKERS):
        message["type"] = "view_once"
    elif any(marker in normalized for marker in CALL_MARKERS):
        message["type"] = "call"
        message["call_kind"] = "video" if any(marker in normalized for marker in ("vídeo", "video")) else "voice"
        message["call_status"] = "missed" if any(marker in normalized for marker in MISSED_CALL_MARKERS) else "completed"


def match_message_line(line: str) -> re.Match[str] | None:
    normalized = line.lstrip(LEADING_MARKERS)
    for pattern in MESSAGE_PATTERNS:
        matched = pattern.match(normalized)
        if matched:
            return matched
    return None


def finalize_message(message: dict[str, Any], messages: list[dict[str, Any]]) -> None:
    raw_text = message["text"]
    message["attachment_refs"] = extract_attachment_refs(raw_text)
    classify_message(message)
    message["id"] = len(messages) + 1
    messages.append(message)


def parse_chat_text(text: str) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n")
        matched = match_message_line(line)
        if matched:
            if current:
                finalize_message(current, messages)
            iso, date_label, time_label = parse_date(matched.group("date"), matched.group("time"))
            sender, body_text = split_sender(matched.group("body"))
            current = {
                "id": 0,
                "datetime": iso,
                "date": date_label,
                "time": time_label,
                "sender": sender,
                "type": "message" if sender else "system",
                "text": body_text,
                "edited": False,
                "attachment_refs": [],
                "attachments": [],
                "missing_attachments": [],
            }
        elif current:
            current["text"] += "\n" + line
        elif line.strip():
            current = {
                "id": 0,
                "datetime": "",
                "date": "",
                "time": "",
                "sender": None,
                "type": "system",
                "text": line,
                "edited": False,
                "attachment_refs": [],
                "attachments": [],
                "missing_attachments": [],
            }

    if current:
        finalize_message(current, messages)
    return messages
