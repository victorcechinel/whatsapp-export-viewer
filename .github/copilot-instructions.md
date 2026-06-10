# Copilot Instructions

This project converts WhatsApp ZIP exports into private, fully offline HTML archives.

## Core Rules

- Generated viewers must work offline from `index.html`.
- Do not add CDN scripts, remote fonts, analytics, telemetry, or network uploads.
- Never commit real WhatsApp chats, phone numbers, addresses, or private media.
- Use fictional fixtures for tests.
- Preserve Windows, macOS, and Linux compatibility.
- Keep CLI, GUI, generated viewer, and GitHub Pages text aligned with the i18n strategy.
- Prefer standard-library Python unless a dependency is clearly justified.

## Implementation Guidance

- Add parser tests before changing export parsing.
- Treat ZIP extraction and path handling carefully; prevent path traversal.
- Keep media paths relative inside generated output.
- Keep generated HTML portable across browsers opened with `file://`.
- Use Conventional Commits: `feat:`, `fix:`, `docs:`, `ci:`, `test:`, `refactor:`.
- Update README, site docs, and translations when user-facing behavior changes.

## Review Guidance

- Check privacy regressions first.
- Check cross-platform path behavior.
- Check that PDFs still open safely with `target="_blank"` and `rel="noopener"`.
- Check that generated output has no remote dependencies.
- Check parser changes against multiline, invisible marker, `<attached: ...>`, iPhone, and Android examples.
- Check release workflow changes against semantic-release behavior on `main`.

