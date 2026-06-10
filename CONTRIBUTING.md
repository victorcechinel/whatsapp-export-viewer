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

For most external contributions:

1. Fork the repository on GitHub.
2. Clone your fork locally.
3. Open an issue in this repository describing the bug, feature, parser format, or documentation change.
4. Create a branch in your fork.
5. Commit using Conventional Commits.
6. Push to your fork.
7. Open a pull request from your fork to `victorcechinel/whatsapp-export-viewer:main`.
8. Link the issue in the pull request description.

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
node scripts/validate-docs-site.mjs
python -m build
```

Test the CLI with a tiny fictional ZIP export:

```bash
python - <<'PY'
import zipfile
from pathlib import Path
path = Path("/tmp/whatsapp-viewer-sample.zip")
with zipfile.ZipFile(path, "w") as archive:
    archive.writestr("_chat.txt", "10/06/2026 14:35 - Ana: Olá\n")
print(path)
PY
whatsapp-export-viewer /tmp/whatsapp-viewer-sample.zip --output /tmp/whatsapp-viewer-test
```

If you are working on the GUI, run:

```bash
whatsapp-export-viewer-gui
```

Check:

- language selection
- ZIP picker
- output folder picker
- owner field
- audio conversion checkbox
- self-contained option
- generated output folder

If you changed release packaging, also test:

```bash
pyinstaller --onefile --name whatsapp-export-viewer --collect-data whatsapp_export_viewer scripts/whatsapp-export-viewer.py
pyinstaller --onefile --name whatsapp-export-viewer-gui --collect-data whatsapp_export_viewer --hidden-import tkinter --hidden-import tkinter.filedialog --hidden-import tkinter.messagebox --hidden-import tkinter.ttk scripts/whatsapp-export-viewer-gui.py
```

Then run the generated binaries:

```bash
./dist/whatsapp-export-viewer --version
./dist/whatsapp-export-viewer-gui
```

If you changed the GitHub Pages site, run:

```bash
node scripts/validate-docs-site.mjs
python -m http.server 4173 --directory docs
```

Then open `http://127.0.0.1:4173/` and test the custom language selector in English, Portuguese, and Spanish.

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

Viewer template text should use `{{viewer_*}}` placeholders in `whatsapp_export_viewer/templates/index.html` and `t("viewer_*")` in `whatsapp_export_viewer/templates/app.js`. Do not hard-code user-facing generated-viewer text in a single language.

When changing the project website, update the localized pages and shared scripts in:

```text
docs/en/index.html
docs/pt-BR/index.html
docs/es/index.html
docs/site.js
```
