## Summary

What changed and why?

## Related issue

Closes #

## Contribution flow

- [ ] I opened or linked an issue before this PR.
- [ ] This PR comes from a feature branch or fork, not directly from `main`.
- [ ] I used Conventional Commits in my commits.

## Type of change

- [ ] Bug fix
- [ ] Feature
- [ ] Documentation
- [ ] Parser/export compatibility
- [ ] GUI
- [ ] GitHub Pages website
- [ ] CI/release
- [ ] Refactor

## Privacy and safety

- [ ] I used fictional test data only.
- [ ] I did not add remote scripts, remote fonts, analytics, telemetry, or CDN dependencies to generated output.
- [ ] I did not commit real WhatsApp chats, phone numbers, addresses, or private media.
- [ ] ZIP extraction, paths, and generated links remain safe across Windows, macOS, and Linux.

## Local verification

Paste the commands you ran and the results:

```text
python -m pip install -e ".[dev]"
pytest
python -m build
```

## GUI verification

- [ ] I tested the GUI locally, or this change does not affect the GUI.
- [ ] I tested language switching, or this change does not affect i18n.
- [ ] I tested ZIP selection and output folder selection, or this change does not affect generation.

## Local packaging verification

- [ ] I tested local CLI packaging, or this change does not affect packaging.
- [ ] I tested local GUI packaging, or this change does not affect packaging.

Commands:

```text
pyinstaller --onefile --name whatsapp-export-viewer --collect-data whatsapp_export_viewer scripts/whatsapp-export-viewer.py
pyinstaller --onefile --name whatsapp-export-viewer-gui --collect-data whatsapp_export_viewer --hidden-import tkinter --hidden-import tkinter.filedialog --hidden-import tkinter.messagebox --hidden-import tkinter.ttk scripts/whatsapp-export-viewer-gui.py
```

## Documentation and translations

- [ ] README, CONTRIBUTING, or GitHub Pages docs were updated when needed.
- [ ] English, Portuguese, and Spanish text were updated when user-facing text changed.
- [ ] Screenshots or examples were added when UI changed, if applicable.

## Screenshots

Add screenshots for generated HTML, GUI, or GitHub Pages changes.
