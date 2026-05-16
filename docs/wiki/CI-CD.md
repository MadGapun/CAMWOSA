# CI / CD

> **Status:** ✅ ci.yml + release.yml implementiert.
> **Code:** [.github/workflows/ci.yml](../../.github/workflows/ci.yml) · [.github/workflows/release.yml](../../.github/workflows/release.yml)

## CI (`ci.yml`)

Bei jedem Push und PR auf `main`:

- **backend-tests** (Ubuntu)
  - Python 3.11, `pip install -e ".[dev]"`
  - `pytest -v`
  - Ruff-Lint (non-blocking)
- **frontend-build** (Ubuntu)
  - Node 20, `npm install`
  - `tsc --noEmit` (non-blocking)
  - `npm run build` (non-blocking)

Status-Badge im README ergaenzen sobald erste Pipeline laeuft.

## Release (`release.yml`)

Bei Git-Tag `v*`:
- Matrix-Build auf Windows, macOS, Linux
- PyInstaller-Bundle + Vite-Build + electron-builder
- Artifacts hochgeladen, manuell als GitHub-Release veroeffentlichen

## Release-Workflow

```bash
# Version in package.json bumpen
git tag v0.2.0
git push --tags
# -> Actions baut auf 3 OS
# -> Artifacts downloaden, signieren, GitHub-Release erstellen
```

## Verwandt

- [Installer](Installer)
- [Auto-Updater](Auto-Updater)
