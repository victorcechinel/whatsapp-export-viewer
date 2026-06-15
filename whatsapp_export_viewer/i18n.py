from __future__ import annotations

import json
import locale
from importlib import resources
from typing import Any

SUPPORTED_LANGUAGES = ("en", "pt-BR", "es")
DEFAULT_LANGUAGE = "en"


def normalize_language(language: str | None) -> str:
    if not language:
        return DEFAULT_LANGUAGE
    value = language.replace("_", "-").lower()
    if value.startswith("pt"):
        return "pt-BR"
    if value.startswith("es"):
        return "es"
    return "en"


def system_language() -> str:
    language, _encoding = locale.getlocale()
    return normalize_language(language)


def load_translations(language: str | None = None) -> dict[str, Any]:
    normalized = normalize_language(language)
    with resources.files("whatsapp_export_viewer").joinpath("i18n", f"{normalized}.json").open(encoding="utf-8") as handle:
        return json.load(handle)
