import os

import pytest

from scripts.build_binary import build_command


def test_build_command_bundles_ffmpeg_and_ffprobe(monkeypatch):
    tools = {
        "ffmpeg": "/tools/ffmpeg",
        "ffprobe": "/tools/ffprobe",
    }
    monkeypatch.setattr("scripts.build_binary.shutil.which", tools.get)

    command = build_command("cli", require_ffmpeg=True)

    assert "--add-binary" in command
    assert f"/tools/ffmpeg{os.pathsep}." in command
    assert f"/tools/ffprobe{os.pathsep}." in command
    assert command[-1] == "scripts/whatsapp-export-viewer.py"


def test_build_command_adds_gui_tkinter_hidden_imports(monkeypatch):
    monkeypatch.setattr("scripts.build_binary.shutil.which", lambda _: None)

    command = build_command("gui", require_ffmpeg=False)

    assert "--hidden-import" in command
    assert "tkinter" in command
    assert "tkinter.ttk" in command
    assert command[-1] == "scripts/whatsapp-export-viewer-gui.py"


def test_build_command_requires_ffmpeg_when_requested(monkeypatch):
    monkeypatch.setattr("scripts.build_binary.shutil.which", lambda _: None)

    with pytest.raises(SystemExit, match="Required executable not found on PATH: ffmpeg"):
        build_command("cli", require_ffmpeg=True)
