# 💬 WhatsApp Export Viewer

**Convert WhatsApp chat exports into beautiful, searchable, fully offline HTML archives.**

**PT-BR:** Transforme exports `.zip` do WhatsApp em uma página HTML visual, navegável e privada.<br>
**EN:** Convert WhatsApp `.zip` chat exports into an offline, searchable, browser-ready website.<br>
**ES:** Convierte exportaciones `.zip` de WhatsApp en un sitio HTML offline, visual y navegable.

> 🔒 Privacy first: everything runs locally. No server, no CDN, no tracking, no cloud upload.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Offline](https://img.shields.io/badge/Offline-100%25-success)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- 📦 Reads WhatsApp exported `.zip` files
- 🧠 Automatically detects the chat `.txt`
- 🇧🇷 Supports Brazilian Portuguese date formats
- 💬 WhatsApp Web-inspired conversation view
- 🔎 Text search, participant filter, date navigation
- 🖼️ Media galleries for images, videos, audios, and documents
- 🎨 Gallery cards keep the same sender colors as chat bubbles
- 🎧 Supports `.opus` audio and optional `.mp3` conversion via `ffmpeg`
- 📄 PDFs open in a new browser tab
- 📴 Fully offline static output: open `index.html`
- 🔐 Keeps all chat data inside the generated folder

## 🚀 Quick Start

### With Python

```bash
python -m pip install whatsapp-export-viewer
whatsapp-export-viewer "WhatsApp Chat.zip" --output conversa-html
```

Open:

```text
conversa-html/index.html
```

### From Source

```bash
git clone https://github.com/victorcechinel/whatsapp-export-viewer.git
cd whatsapp-export-viewer
python -m pip install -e ".[dev]"
whatsapp-export-viewer "WhatsApp Chat.zip" --output conversa-html
```

## 🧰 CLI Usage

```bash
whatsapp-export-viewer "WhatsApp Chat.zip" \
  --output conversa-html \
  --owner "Your Name" \
  --convert-audio
```

Options:

| Option | Description |
| --- | --- |
| `--output`, `-o` | Output folder for the static HTML website |
| `--owner "Name"` | Participant rendered as “me”, aligned right |
| `--convert-audio` | Convert `.opus` to `.mp3` when `ffmpeg` is available |
| `--no-convert-audio` | Keep only original audio files |
| `--self-contained` | Inline CSS, JS, and data into a single `index.html` |
| `--version` | Print the installed version |

## 📁 Generated Output

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

Zip the whole generated folder to share it. The viewer uses relative paths, so it works on **Windows, macOS, and Linux** after extracting the ZIP and opening `index.html`.

## 🇧🇷 SEO PT-BR

Este projeto é um **visualizador de exportação do WhatsApp**, **conversor de conversa WhatsApp para HTML**, **arquivo offline do WhatsApp**, **leitor de backup do WhatsApp exportado**, e **gerador de página HTML para conversas do WhatsApp**. Ele funciona localmente, preserva anexos, mostra áudios, imagens, vídeos, documentos e cria uma experiência parecida com o WhatsApp Web.

## 🇺🇸 SEO EN

This is a **WhatsApp export viewer**, **WhatsApp chat to HTML converter**, **offline WhatsApp archive generator**, and **private WhatsApp backup viewer**. It converts exported WhatsApp ZIP files into searchable static HTML websites with media galleries and no backend.

## 🇪🇸 SEO ES

Este proyecto es un **visor de exportaciones de WhatsApp**, **conversor de chat de WhatsApp a HTML**, **generador de archivo offline de WhatsApp** y **lector privado de copias exportadas de WhatsApp**. Convierte archivos ZIP exportados en sitios HTML estáticos con galerías de medios.

## 🎧 Audio Notes

WhatsApp often exports voice notes as `.opus`. The viewer keeps the original file and tries to use the browser audio player directly. With:

```bash
whatsapp-export-viewer chat.zip --convert-audio
```

the tool converts `.opus` files to `.mp3` when `ffmpeg` is installed.

## 🧪 Development

```bash
python -m pip install -e ".[dev]"
pytest
python -m build
```

Build a local executable:

```bash
pyinstaller --onefile --name whatsapp-export-viewer --collect-data whatsapp_export_viewer scripts/whatsapp-export-viewer.py
```

## 📦 Releases

GitHub Actions builds:

- Python source distribution and wheel
- Windows executable
- macOS executable
- Linux executable

Create a release by pushing a tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

## 🤝 Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📜 License

MIT License. See [LICENSE](LICENSE).
