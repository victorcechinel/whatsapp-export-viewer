# 💬 WhatsApp Export Viewer

Convert WhatsApp ZIP chat exports into a private, searchable, fully offline HTML archive with messages, images, videos, voice notes, and documents.

**Português:** transforme uma conversa exportada do WhatsApp em uma página HTML bonita, navegável e offline.<br>
**English:** convert a WhatsApp chat export into a browser-ready archive that stays on your computer.<br>
**Español:** convierte un chat exportado de WhatsApp en un archivo HTML privado y fácil de navegar.

> 🔒 Your conversations stay local. The generated viewer has no backend, no CDN, no analytics, and no upload step.

[![CI](https://github.com/victorcechinel/whatsapp-export-viewer/actions/workflows/ci.yml/badge.svg)](https://github.com/victorcechinel/whatsapp-export-viewer/actions/workflows/ci.yml)
[![Pages](https://github.com/victorcechinel/whatsapp-export-viewer/actions/workflows/pages.yml/badge.svg)](https://github.com/victorcechinel/whatsapp-export-viewer/actions/workflows/pages.yml)
[![Release](https://github.com/victorcechinel/whatsapp-export-viewer/actions/workflows/release.yml/badge.svg)](https://github.com/victorcechinel/whatsapp-export-viewer/actions/workflows/release.yml)

## 🌐 Project Website

Visit the multilingual website:

**[victorcechinel.github.io/whatsapp-export-viewer](https://victorcechinel.github.io/whatsapp-export-viewer/)**

The site supports English, Portuguese, and Spanish. It detects the browser language and also lets visitors switch manually.

## ⬇️ Downloads

Download the latest release for your platform:

| Platform | Download |
| --- | --- |
| Windows | [Windows x64 package](https://github.com/victorcechinel/whatsapp-export-viewer/releases/latest) |
| macOS Apple Silicon | [macOS arm64 package](https://github.com/victorcechinel/whatsapp-export-viewer/releases/latest) |
| macOS Intel | [macOS x64 package](https://github.com/victorcechinel/whatsapp-export-viewer/releases/latest) |
| Linux | [Linux x64 package](https://github.com/victorcechinel/whatsapp-export-viewer/releases/latest) |
| Python | [Source and wheel](https://github.com/victorcechinel/whatsapp-export-viewer/releases/latest) |

Each desktop package includes:

- `whatsapp-export-viewer-gui` for people who prefer a graphical app
- `whatsapp-export-viewer` for command-line use and automation

## ✨ Features

- 📦 Reads WhatsApp exported ZIP files
- 🧠 Automatically detects the conversation `.txt`
- 💬 Renders a WhatsApp Web-inspired chat view
- 🔎 Searches messages, senders, and attachment names
- 🧑 Filters by participant
- 📅 Navigates by date
- 🖼️ Shows media galleries for images, videos, audio, and documents
- 🎨 Keeps participant colors consistent between chat bubbles and gallery cards
- 🎧 Plays `.opus` audio when the browser supports it
- 🔁 Converts `.opus` to `.mp3` when `ffmpeg` is available
- 📄 Opens PDFs in a new browser tab
- 📴 Generates a static folder that opens from `index.html`
- 🖥️ Works on Windows, macOS, and Linux

## 🖱️ Use the Desktop App

1. Download the package for your operating system.
2. Extract the archive.
3. Open `whatsapp-export-viewer-gui`.
4. Choose your WhatsApp ZIP export.
5. Choose an output folder.
6. Pick the language and optional audio conversion.
7. Generate the viewer and open `index.html`.

The graphical app currently supports English, Portuguese, and Spanish. The language can be changed inside the app.

## 🧰 Use the Command Line

Install with Python:

```bash
python -m pip install whatsapp-export-viewer
```

Convert a chat:

```bash
whatsapp-export-viewer "WhatsApp Chat.zip" \
  --output conversa-html \
  --owner "Your Name" \
  --language pt-BR \
  --convert-audio
```

Useful options:

| Option | Description |
| --- | --- |
| `--output`, `-o` | Output folder for the static website |
| `--owner "Name"` | Participant rendered as “me”, aligned right |
| `--language en|pt-BR|es` | Language used by the generated offline viewer |
| `--convert-audio` | Convert `.opus` to `.mp3` when `ffmpeg` is available |
| `--no-convert-audio` | Keep original audio files only |
| `--self-contained` | Inline CSS, JavaScript, and data into one `index.html` |
| `--version` | Print the installed version |

## 📁 Generated Folder

```text
conversa-html/
  index.html
  assets/
    style.css
    app.js
  data/
    bootstrap.js
    messages.json
    summary.json
  media/
    images/
    videos/
    audios/
    documents/
  original/
    chat.txt
```

You can zip this generated folder and open it later on Windows, macOS, or Linux. Keep the folder structure intact so relative media links continue to work.

## 🪟 Windows

Use the Windows package from the latest release. Extract it and run the graphical app. If Windows SmartScreen warns about an unsigned executable, choose the option to run it only if you trust this open-source project and the release came from this repository.

## 🍎 macOS

Download the Apple Silicon or Intel package. Extract it and run the GUI or CLI. macOS may ask for confirmation because the binary is not yet notarized.

## 🐧 Linux

Download the Linux x64 archive, extract it, and run:

```bash
chmod +x whatsapp-export-viewer whatsapp-export-viewer-gui
./whatsapp-export-viewer-gui
```

For server or batch usage:

```bash
./whatsapp-export-viewer "WhatsApp Chat.zip" --output conversa-html
```

## 🌍 Languages

The project is being prepared for full internationalization:

- English
- Portuguese Brazil
- Spanish

The app, generated offline viewer, and GitHub Pages site support English, Brazilian Portuguese, and Spanish. The generated viewer stores its local UI translations in `data/translations.json`, so it keeps working offline.

## 🔐 Privacy and Safety

WhatsApp Export Viewer is designed for private archives:

- no cloud upload
- no external scripts in generated output
- no tracking
- no backend server
- no CDN dependency
- local ZIP processing

Do not publish or share a generated archive unless all participants consent.

## 🔄 Releases and Versioning

Releases are automated from the `main` branch with Python Semantic Release and Conventional Commits.

Examples:

```text
feat: add iPhone export date parser
fix: avoid merging attached audio messages
docs: improve Linux installation guide
```

When commits merged into `main` require a new version, the release workflow:

1. updates the Python package version,
2. updates the changelog,
3. creates a Git tag,
4. publishes a GitHub Release,
5. builds Windows, macOS, and Linux packages,
6. attaches the desktop and CLI binaries to the release.

## 🤝 Contributing

Contributions are welcome. Good first areas:

- support more WhatsApp export formats
- improve the desktop GUI
- add translations
- improve accessibility
- add parser fixtures
- refine media galleries
- test Windows, macOS, and Linux packages

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## 🧪 Development

```bash
python -m pip install -e ".[dev]"
pytest
python -m build
```

Run the GUI from a local checkout:

```bash
python -m whatsapp_export_viewer.gui
```

If you use a virtual environment in the repository:

```bash
.venv/bin/python -m whatsapp_export_viewer.gui
.venv/bin/whatsapp-export-viewer-gui
```

Build local executables:

```bash
pyinstaller --onefile --name whatsapp-export-viewer --collect-data whatsapp_export_viewer scripts/whatsapp-export-viewer.py
pyinstaller --onefile --name whatsapp-export-viewer-gui --collect-data whatsapp_export_viewer --hidden-import tkinter --hidden-import tkinter.filedialog --hidden-import tkinter.messagebox --hidden-import tkinter.ttk scripts/whatsapp-export-viewer-gui.py
```

## 📜 License

MIT License. See [LICENSE](LICENSE).
