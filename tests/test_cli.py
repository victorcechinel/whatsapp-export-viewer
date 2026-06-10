from whatsapp_export_viewer.cli import build_parser


def test_cli_accepts_expected_options():
    args = build_parser().parse_args([
        "chat.zip",
        "--output",
        "site",
        "--owner",
        "Ana",
        "--language",
        "es",
    ])

    assert str(args.zip_path) == "chat.zip"
    assert str(args.output) == "site"
    assert args.owner == "Ana"
    assert args.language == "es"
