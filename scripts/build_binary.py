from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys


TARGETS = {
    "cli": {
        "name": "whatsapp-export-viewer",
        "script": "scripts/whatsapp-export-viewer.py",
        "hidden_imports": [],
    },
    "gui": {
        "name": "whatsapp-export-viewer-gui",
        "script": "scripts/whatsapp-export-viewer-gui.py",
        "hidden_imports": [
            "tkinter",
            "tkinter.filedialog",
            "tkinter.messagebox",
            "tkinter.ttk",
        ],
    },
}


def build_command(target: str, require_ffmpeg: bool) -> list[str]:
    config = TARGETS[target]
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        config["name"],
        "--collect-data",
        "whatsapp_export_viewer",
    ]
    for tool in ("ffmpeg", "ffprobe"):
        executable = shutil.which(tool)
        if executable:
            command.extend(["--add-binary", f"{executable}{os.pathsep}."])
        elif require_ffmpeg:
            raise SystemExit(f"Required executable not found on PATH: {tool}")
    for hidden_import in config["hidden_imports"]:
        command.extend(["--hidden-import", hidden_import])
    command.append(config["script"])
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description="Build PyInstaller binaries with bundled FFmpeg tools.")
    parser.add_argument("target", choices=TARGETS)
    parser.add_argument("--require-ffmpeg", action="store_true", help="Fail if ffmpeg or ffprobe is not available.")
    args = parser.parse_args()
    subprocess.run(build_command(args.target, args.require_ffmpeg), check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
