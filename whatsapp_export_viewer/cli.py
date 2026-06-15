from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .builder import build_export
from .i18n import SUPPORTED_LANGUAGES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="whatsapp-export-viewer",
        description="Convert WhatsApp ZIP chat exports into beautiful, searchable, fully offline HTML viewers.",
    )
    parser.add_argument("zip_path", type=Path, help="Path to the WhatsApp exported ZIP file.")
    parser.add_argument("--output", "-o", type=Path, default=Path("whatsapp-html-export"), help="Output folder for the static website.")
    parser.add_argument("--owner", help="Participant name rendered as 'me' and aligned to the right.")
    parser.add_argument("--language", "--locale", dest="language", choices=SUPPORTED_LANGUAGES, default="en", help="Language/locale for the generated offline viewer.")
    parser.add_argument("--date-from", help="Optional start date. Uses MM/DD/YYYY for English, DD/MM/YYYY for Portuguese or Spanish, or YYYY-MM-DD.")
    parser.add_argument("--date-to", help="Optional end date. Uses MM/DD/YYYY for English, DD/MM/YYYY for Portuguese or Spanish, or YYYY-MM-DD.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        build_export(
            args.zip_path,
            args.output,
            owner=args.owner,
            language=args.language,
            date_from=args.date_from,
            date_to=args.date_to,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Site generated at: {args.output.expanduser() / 'index.html'}")
    return 0
