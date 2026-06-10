import json
import zipfile

from whatsapp_export_viewer.builder import build_export


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

    build_export(zip_path, output, owner="Ana", convert_audio=False, self_contained=False)

    assert (output / "index.html").exists()
    assert (output / "assets" / "style.css").exists()
    assert (output / "assets" / "app.js").exists()
    assert (output / "data" / "bootstrap.js").exists()
    assert (output / "media" / "images" / "IMG-20260610-WA0001.jpg").exists()
    assert (output / "media" / "audios" / "PTT-20260610-WA0002.opus").exists()

    app_js = (output / "assets" / "app.js").read_text(encoding="utf-8")
    index_html = (output / "index.html").read_text(encoding="utf-8")
    assert "showMediaView" in app_js
    assert "media-card ${esc(message.side" in app_js
    assert "Voltar" in index_html

    messages = json.loads((output / "data" / "messages.json").read_text(encoding="utf-8"))
    summary = json.loads((output / "data" / "summary.json").read_text(encoding="utf-8"))
    assert summary["total_messages"] == 3
    assert summary["participants"]["Ana"] == 2
    assert summary["media"]["images"] == 1
    assert summary["media"]["audios"] == 1
    assert messages[0]["side"] == "out"
    assert messages[1]["text"] == ""

