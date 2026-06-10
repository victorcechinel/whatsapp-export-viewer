from whatsapp_export_viewer.parser import parse_chat_text


SAMPLE_CHAT = """10/06/2026 14:35 - Ana: Olá 😄
continuação da mensagem
[10/06/2026, 14:36:22] Jossan Pedreiro: Foto legal IMG-20260610-WA0001.jpg
10/06/2026 14:37 - As mensagens e as ligações são protegidas com a criptografia de ponta a ponta.
10/06/2026 14:38 - Ana: <Arquivo de mídia oculto>
[10/06/2026, 14:39:01] Jossan Pedreiro: áudio PTT-20260610-WA0002.opus
"""


def test_parses_portuguese_exports_with_multiline_system_and_media():
    messages = parse_chat_text(SAMPLE_CHAT)

    assert len(messages) == 5
    assert messages[0]["sender"] == "Ana"
    assert messages[0]["text"] == "Olá 😄\ncontinuação da mensagem"
    assert messages[1]["sender"] == "Jossan Pedreiro"
    assert messages[1]["time"] == "14:36:22"
    assert messages[2]["type"] == "system"
    assert "IMG-20260610-WA0001.jpg" in messages[1]["attachment_refs"]
    assert "PTT-20260610-WA0002.opus" in messages[4]["attachment_refs"]


def test_invisible_markers_do_not_merge_attached_messages():
    messages = parse_chat_text(
        """[23/07/25, 12:19:18] Jossan Pedreiro: Ok
\u200e[23/07/25, 13:35:12] Jossan Pedreiro: \u200e<attached: 00000178-AUDIO-2025-07-23-13-35-12.opus>
\u200e[23/07/25, 13:41:54] Jossan Pedreiro: \u200e<attached: 00000181-PHOTO-2025-07-23-13-41-54.jpg>
"""
    )

    assert len(messages) == 3
    assert messages[0]["text"] == "Ok"
    assert messages[1]["text"] == ""
    assert messages[1]["attachment_refs"] == ["00000178-AUDIO-2025-07-23-13-35-12.opus"]
    assert messages[2]["attachment_refs"] == ["00000181-PHOTO-2025-07-23-13-41-54.jpg"]

