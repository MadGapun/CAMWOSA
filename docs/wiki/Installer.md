# Installer + Build-Pipeline

> **Status:** ✅ Build-Skripte + PyInstaller-Spec + electron-builder + CI/Release-Workflows.
> **Code:** [scripts/build.sh](../../scripts/build.sh) · [backend/camwosa-backend.spec](../../backend/camwosa-backend.spec) · [.github/workflows/](../../.github/workflows/)

## Lokaler Build

```bash
bash scripts/build.sh
```

Schritte:
1. **Backend** mit PyInstaller buendeln → `backend/dist/camwosa-backend(.exe)`
2. **Frontend** mit Vite buildaren → `frontend/dist/`
3. **Electron** mit electron-builder packagen → `electron/release/`

Output je nach OS:
- Windows: NSIS-Installer `CAMWOSA Setup vX.Y.Z.exe`
- macOS: `CAMWOSA-X.Y.Z.dmg`
- Linux: `CAMWOSA-X.Y.Z.AppImage`

## CI (GitHub Actions)

`.github/workflows/ci.yml` laeuft bei jedem Push/PR:
- Backend-Tests (pytest)
- Backend-Lint (ruff, non-blocking)
- Frontend-Build (vite + tsc, non-blocking)

## Release (GitHub Actions)

`.github/workflows/release.yml` laeuft bei Git-Tag `v*`:
- Build auf Windows, macOS, Linux parallel
- PyInstaller + Vite + electron-builder
- Artifacts werden hochgeladen (manuell als GitHub-Release veroeffentlichen)

```bash
git tag v0.1.0
git push --tags
```

## PyInstaller-Bundle

`backend/camwosa-backend.spec` definiert:
- Entry: `camwosa/api/app.py`
- Datas: `data/` (Default-Profile mitbundeln)
- Hidden Imports: alle Plugins die per Side-Effect laden (Postprozessoren, CAD-Importer)
- Console-Modus aktiv (Flask-Logs sichtbar)

## electron-builder

`electron/package.json` → `build`-Sektion:
- `appId`: `de.elwosa.camwosa`
- `extraResources`: backend-Binary + `data/`
- `fileAssociations`: `.cwp` registriert
- Win: NSIS · Mac: DMG · Linux: AppImage

## Auto-Updater

`electron-updater` ist als Dep da. Konfig erfolgt via `electron-builder` mit `publish: github`. Aktivierung folgt sobald CI-Release-Workflow gruene Builds liefert.

## Code-Signing (geplant)

- Windows: Cert kaufen + via electron-builder `win.certificateFile`
- macOS: Apple-Developer-Account + Notarisierung

Kommt sobald der erste oeffentliche Release ansteht.

## Verwandt

- [Electron-App](Electron-App)
- [CI-CD](CI-CD)
- [Auto-Updater](Auto-Updater)
