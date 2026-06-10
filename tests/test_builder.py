import json
import zipfile

import pytest

from whatsapp_export_viewer.builder import build_export, discover_participants, safe_extract_zip


def test_builds_offline_export_with_organized_media(tmp_path):
    zip_path = tmp_path / "WhatsApp Chat.zip"
    output = tmp_path / "site"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr(
            "_chat.txt",
            """10/06/2026 14:35 - Ana: Olá
[10/06/2026, 14:36:22] Beto: <attached: IMG-20260610-WA0001.jpg>
[10/06/2026, 14:39:01] Ana: áudio PTT-20260610-WA0002.opus
""",
        )
        archive.writestr("IMG-20260610-WA0001.jpg", b"fake-jpg")
        archive.writestr("PTT-20260610-WA0002.opus", b"fake-opus")

    build_export(zip_path, output, owner="Ana", convert_audio=False, self_contained=False, language="pt-BR")

    assert (output / "index.html").exists()
    assert (output / "assets" / "style.css").exists()
    assert (output / "assets" / "app.js").exists()
    assert (output / "data" / "bootstrap.js").exists()
    assert (output / "data" / "translations.json").exists()
    assert (output / "media" / "images" / "IMG-20260610-WA0001.jpg").exists()
    assert (output / "media" / "audios" / "PTT-20260610-WA0002.opus").exists()

    app_js = (output / "assets" / "app.js").read_text(encoding="utf-8")
    index_html = (output / "index.html").read_text(encoding="utf-8")
    assert "showMediaView" in app_js
    assert "media-card ${esc(message.side" in app_js
    assert "Voltar" in index_html
    assert 'data-kind="images"' in index_html
    assert 'id="participantDropdown"' in index_html
    assert '<select id="participant"' not in index_html
    assert 'class="gallery"' not in index_html
    assert "{{" not in index_html

    messages = json.loads((output / "data" / "messages.json").read_text(encoding="utf-8"))
    summary = json.loads((output / "data" / "summary.json").read_text(encoding="utf-8"))
    translations = json.loads((output / "data" / "translations.json").read_text(encoding="utf-8"))
    assert summary["total_messages"] == 3
    assert summary["participants"]["Ana"] == 2
    assert summary["media"]["images"] == 1
    assert summary["media"]["audios"] == 1
    assert messages[0]["side"] == "out"
    assert messages[1]["text"] == ""
    assert translations["viewer_chat"] == "Conversa"


def test_blocks_zip_path_traversal(tmp_path):
    zip_path = tmp_path / "bad.zip"
    destination = tmp_path / "extract"
    destination.mkdir()
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("../evil.txt", "nope")

    with pytest.raises(ValueError, match="Unsafe ZIP entry"):
        safe_extract_zip(zip_path, destination)

    assert not (tmp_path / "evil.txt").exists()


def test_discovers_participants_from_zip(tmp_path):
    zip_path = tmp_path / "WhatsApp Chat.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr(
            "_chat.txt",
            """10/06/2026 14:35 - Ana: Olá
10/06/2026 14:36 - Beto: Oi
10/06/2026 14:37 - Ana: Tudo bem?
""",
        )

    assert discover_participants(zip_path) == ["Ana", "Beto"]


def test_refuses_non_empty_output_directory(tmp_path):
    zip_path = tmp_path / "WhatsApp Chat.zip"
    output = tmp_path / "site"
    output.mkdir()
    (output / "keep.txt").write_text("do not delete", encoding="utf-8")
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("_chat.txt", "10/06/2026 14:35 - Ana: Olá\n")

    with pytest.raises(FileExistsError, match="Output directory is not empty"):
        build_export(zip_path, output)

    assert (output / "keep.txt").read_text(encoding="utf-8") == "do not delete"


def test_self_contained_escapes_script_end_tag(tmp_path):
    zip_path = tmp_path / "WhatsApp Chat.zip"
    output = tmp_path / "site"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("_chat.txt", "10/06/2026 14:35 - Ana: </script><script>alert(1)</script>\n")

    build_export(zip_path, output, self_contained=True, language="es")

    html = (output / "index.html").read_text(encoding="utf-8")
    assert "\\u003c/script>" in html
    assert "</script><script>alert(1)" not in html
    assert "Conversación" in html
    assert "{{" not in html


def test_duplicate_media_names_remain_reachable(tmp_path):
    zip_path = tmp_path / "WhatsApp Chat.zip"
    output = tmp_path / "site"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr(
            "_chat.txt",
            """10/06/2026 14:35 - Ana: <attached: photo.jpg>
10/06/2026 14:36 - Beto: <attached: photo.jpg>
""",
        )
        archive.writestr("first/photo.jpg", b"first")
        archive.writestr("second/photo.jpg", b"second")

    build_export(zip_path, output)

    summary = json.loads((output / "data" / "summary.json").read_text(encoding="utf-8"))
    messages = json.loads((output / "data" / "messages.json").read_text(encoding="utf-8"))
    assert summary["media"]["images"] == 2
    assert (output / "media" / "images" / "photo.jpg").exists()
    assert (output / "media" / "images" / "photo-2.jpg").exists()
    assert {attachment["stored_name"] for attachment in messages[0]["attachments"]} == {"photo.jpg", "photo-2.jpg"}
