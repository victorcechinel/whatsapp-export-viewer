from pathlib import Path

import whatsapp_export_viewer.gui as gui


class ImmediateRoot:
    def after(self, _delay, callback):
        callback()


def test_generation_worker_keeps_exception_for_scheduled_callback(monkeypatch):
    app = gui.ViewerApp.__new__(gui.ViewerApp)
    app.root = ImmediateRoot()
    app.zip_path = type("Value", (), {"get": lambda self: "chat.zip"})()
    app.output_path = type("Value", (), {"get": lambda self: "site"})()
    app.owner = type("Value", (), {"get": lambda self: "Ana"})()
    app.language = type("Value", (), {"get": lambda self: "en"})()
    app.date_from = type("Value", (), {"get": lambda self: ""})()
    app.date_to = type("Value", (), {"get": lambda self: ""})()
    captured = []

    def fail_build(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(gui, "build_export", fail_build)
    app._generation_failed = lambda exc: captured.append(str(exc))

    app._generate_worker()

    assert captured == ["boom"]


def test_participants_worker_keeps_exception_for_scheduled_callback(monkeypatch):
    app = gui.ViewerApp.__new__(gui.ViewerApp)
    app.root = ImmediateRoot()
    captured = []

    def fail_inspect(_zip_path):
        raise RuntimeError("bad zip")

    monkeypatch.setattr(gui, "inspect_export", fail_inspect)
    app._participants_failed = lambda exc: captured.append(str(exc))

    app._load_participants_worker(Path("chat.zip"))

    assert captured == ["bad zip"]
