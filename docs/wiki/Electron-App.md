# Electron-App

> **Status:** ✅ Skelett implementiert (Main, Preload, Backend-Subprozess-Manager, Menue, Datei-Assoziation .cwp).
> **Issue:** [#6](https://github.com/MadGapun/coffee/issues/6)
> **Code:** [electron/src/](../../electron/src/)

CAMWOSA ist eine Electron-Desktop-App. Der Main-Process startet das Python-Backend als Subprozess und wartet auf Health-Check, dann oeffnet er das Renderer-Fenster mit der React-UI.

## Aufbau

```
electron/
├── package.json         # Electron + electron-builder
├── tsconfig.json
└── src/
    ├── main.ts          # Main-Process, Fenster, Menue
    ├── preload.ts       # ContextBridge-API fuer Renderer
    └── backend_runner.ts # Backend-Subprozess-Lifecycle
```

## Backend-Subprozess

Das Python-Backend wird beim App-Start automatisch hochgefahren:

1. Freier Port suchen (8765+)
2. Subprozess starten (`camwosa-backend` oder Dev-venv)
3. `/health` pollen bis ready (max. 30s)
4. Bei `will-quit`: SIGTERM, danach SIGKILL nach 5s

URL wird Renderer ueber `window.camwosa.backendUrl()` bereitgestellt.

## Datei-Assoziation

`.cwp` ist registriert. Doppelklick im OS oeffnet CAMWOSA (Phase 1+: Datei-Pfad-Argument auswerten).

## Auto-Updater

`electron-updater` ist als Dependency vorhanden — Konfiguration in `electron-builder` zeigt auf Releases-Page. Aktivierung kommt mit Phase F4 (CI-Pipeline).

## Dev-Modus

```bash
# 1. Backend starten
cd backend && .venv/Scripts/python.exe -m camwosa.api.app

# 2. Frontend Dev-Server starten
cd ../frontend && npm run dev

# 3. Electron im Dev-Modus starten
cd ../electron
CAMWOSA_DEV=1 npm run dev
```

Im Dev-Modus laedt Electron das Frontend von `http://localhost:5173` (Vite HMR) und nutzt den lokalen Python-venv direkt — ohne PyInstaller-Bundle.

## Prod-Build

```bash
cd electron && npm run build:installer
```

`electron-builder` baut:
- Windows: NSIS-Installer mit `.cwp`-Assoziation
- macOS: DMG
- Linux: AppImage

Das Backend wird als PyInstaller-Bundle eingebettet (siehe [Installer](Installer.md)).

## Sicherheit

- **Sandbox** + **contextIsolation: true** + **nodeIntegration: false**
- Renderer hat **keinen** direkten Zugriff auf Node — nur die explizit in `preload.ts` exponierten Methoden via `window.camwosa`.

## Verwandt

- [Architektur](Architektur.md)
- [Frontend](Frontend.md)
- [Installer](Installer.md)
