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
    parser.add_argument("--convert-audio", dest="convert_audio", action="store_true", help="Convert .opus audio to .mp3 with ffmpeg when available.")
    parser.add_argument("--no-convert-audio", dest="convert_audio", action="store_false", help="Keep original audio files only.")
    parser.set_defaults(convert_audio=False)
    parser.add_argument("--self-contained", action="store_true", help="Inline CSS, JS, and chat data into index.html.")
    parser.add_argument("--language", choices=SUPPORTED_LANGUAGES, default="en", help="Language for the generated offline viewer.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        build_export(
            args.zip_path,
            args.output,
            owner=args.owner,
            convert_audio=args.convert_audio,
            self_contained=args.self_contained,
            language=args.language,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Site generated at: {args.output.expanduser() / 'index.html'}")
    return 0
