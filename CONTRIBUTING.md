# 🤝 Contributing to WhatsApp Export Viewer

Thanks for helping improve this project.

## 🧭 Project Goals

- Keep the generated viewer fully offline.
- Never upload chat data anywhere.
- Support WhatsApp exports from Windows, macOS, Linux, Android, and iPhone workflows.
- Prefer simple, dependency-light Python.
- Keep parser behavior covered by tests.

## 🛠️ Local Setup

```bash
git clone https://github.com/victorcechinel/whatsapp-export-viewer.git
cd whatsapp-export-viewer
python -m pip install -e ".[dev]"
pytest
```

## 🌿 Branches

Use small, focused branches:

```bash
git switch -c fix/iphone-date-format
git switch -c feat/dark-theme
```

## ✍️ Commit Messages

This repository uses semantic releases from Conventional Commits. Commit messages decide whether a release is created and which version is published.

Use:

```text
feat: add desktop language selector
fix: parse attached iPhone audio exports
docs: add Linux install guide
ci: deploy GitHub Pages automatically
test: add fixture for invisible date markers
```

Breaking changes must include `BREAKING CHANGE:` in the commit body.

## ✅ Before Opening a PR

Please run:

```bash
pytest
python -m build
```

If you changed release packaging, also test:

```bash
pyinstaller --onefile --name whatsapp-export-viewer --collect-data whatsapp_export_viewer scripts/whatsapp-export-viewer.py
pyinstaller --onefile --name whatsapp-export-viewer-gui --collect-data whatsapp_export_viewer --hidden-import tkinter --hidden-import tkinter.filedialog --hidden-import tkinter.messagebox --hidden-import tkinter.ttk scripts/whatsapp-export-viewer-gui.py
```

If you changed the GitHub Pages site, open `docs/index.html` locally and test the language selector.

## 🧪 Test Fixtures

Do not commit real WhatsApp conversations. Use tiny fictional fixtures only.

Good fixture data:

```text
10/06/2026 14:35 - Ana: Olá
[10/06/2026, 14:36:22] Beto: <attached: IMG-20260610-WA0001.jpg>
```

Avoid:

- real names without consent
- phone numbers
- addresses
- private messages
- real media files

## 🐛 Bug Reports

Please include:

- operating system
- Python version or binary version
- WhatsApp platform: Android or iPhone
- date format example
- a fictional/minimized sample that reproduces the bug

## 💡 Feature Ideas

Useful areas:

- new WhatsApp export formats
- better gallery navigation
- accessibility improvements
- dark mode
- internationalization
- safer media matching
- app/GUI wrapper
- GitHub Pages documentation
- installer improvements
- i18n coverage

## 🔐 Privacy Rules

This project should not add:

- analytics
- remote scripts
- CDN dependencies in generated output
- telemetry
- network upload

The generated archive must stay portable and private.

## 🌍 Translations

When changing app text, update:

```text
whatsapp_export_viewer/i18n/en.json
whatsapp_export_viewer/i18n/pt-BR.json
whatsapp_export_viewer/i18n/es.json
```

When changing the project website, update the translations in:

```text
docs/site.js
```
