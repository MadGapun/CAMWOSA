# Changelog

Alle nennenswerten Aenderungen an CAMWOSA. Format orientiert sich an
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/), Versionsschema
[SemVer](https://semver.org/lang/de/).

## [0.0.1-alpha.1] — 2026-05-17

**Fix-Release fuer Alpha 0.** Alpha 0 hatte einen Show-Stopper: schwarzer
Bildschirm beim Start, nur Menue-Leiste sichtbar.

### Gefixt

- **Vite-Asset-Pfade jetzt relativ** (`base: './'` in vite.config.ts).
  Vorher: `<script src="/assets/...">` schlug unter `file://`-Protokoll
  fehl, Frontend lud nicht.
- **API-baseURL via IPC**: `api.defaults.baseURL` wird zur Laufzeit vom
  Main-Process via `window.camwosa.backendUrl()` gesetzt. Vorher gingen
  API-Calls an `file:///api/...` ins Leere.
- **electron-updater transitive Dependencies komplett**: `pack-portable.ps1`
  macht jetzt einen sauberen `npm install --omit=dev` statt selektiver
  Copy-Liste — `sax`, `fs-extra` etc. sind jetzt drin.
- **`app-update.yml`** wird vom Pack mitgeneriert (sonst ENOENT beim
  Update-Check).
- **DevTools im Bundle** auf Abruf: `CAMWOSA_DEBUG=1` oeffnet sie auch
  in Production-Builds.
- **StatusBar-Version** wird aus Backend-`/health` gelesen statt
  hartcodiert.

### Neues Process-Protokoll

Vor jedem Release: ZIP **entpacken in frischen Pfad** + doppelklicken +
`/api/tools/` pruefen. „Backend antwortet" reicht nicht. Siehe
[Memory feedback_bundle_real_testen.md].

### Verifiziert in dieser Version

- Backend Port 8766 antwortet `/health`
- `/api/tools/` liefert 12 Werkzeuge → Frontend hat den Backend wirklich erreicht
- Kein ENOENT, kein MODULE_NOT_FOUND in stderr
- Backend pytest: 542 / 542 gruen

---

## [0.0.1-alpha.0] — 2026-05-17

**Erste Alpha-Veroeffentlichung.** Lauffaehiges Windows-Bundle (portable
ZIP), nicht signiert. Backend hat 542 gruene Tests. Frontend ist aufgebaut
aber noch nicht intensiv getestet.

### Backend (Master-Plan Teil A komplett)

- **A1-A18** ✅ Repo, Datenmodell, DXF, GRBL-Postprozessor, Operations
  (Kontur/Tasche/Bohren/Gravur/Relief), Material- + Werkzeug-Bibliothek,
  Feeds & Speeds, Sicherheits-Checks, Maschinen-Profile,
  Rohmaterial-Definition, .cwp-Projekt-Format.
- **A19** ✅ Varianten-System (Backend + Frontend-Switcher mit
  Snapshot-Logik).
- **A20-A23** ✅ Multi-Setup-Workflow, Arbeitsplan-Generator (PDF),
  Nesting-Engine, STL-Parser + Heightmap.
- **A24-A31** ✅ Relief-Operation, Maschinen-Modi, Rotary-Wrapping,
  Rotary-Indexing, Drechseln (Continuous-Lathe), Backplot-Annotation.
- **A32-A38** ✅ Wrap-Mode + Bild-zu-Relief Pipeline
  (Grayscale + Filter-Stack + AI-Tiefenschaetzung als optionales Extra) +
  Text-zu-Pfad + Wrap-Pattern-Skalierung.

### REST-API + MCP (Teil B)

- **B1-B6** ✅ Flask-API, alle Backend-Module ueber Endpoints,
  OpenAPI-3.1-Spec automatisch generiert (`/api/openapi.json` +
  Swagger-UI auf `/api/docs`), MCP-Server mit 40+ Tools inkl.
  `auto_cam_erstellen`.

### Desktop-App + Frontend (Teil C/D)

- **C1-C8** ✅ Electron-Skelett, Backend-Subprozess-Management,
  .cwp-Dateiverknuepfung, i18n (DE+EN), zustand-State-Management,
  Tailwind, Routing.
- **D1-D24** ✅ Maschinen-/Werkzeug-/Material-/Projekt-Verwaltung,
  Rohmaterial-Editor, DXF/STL-Import, Zeichnen (Konva), Operations-Editor,
  2D-Toolpath-Preview, 3D-Material-Abtrag-Simulation, Sicherheits-Panel,
  Workflow-/Setup-Editor, Arbeitsplan-Ansicht, Nesting-Editor, Feeds &
  Speeds Panel, G-Code-Editor (Monaco), Settings, Foto-Slot, Design-System
  (3 Densities, Dark/Light), First-Run-Wizard, Tooltip-System (3-stufig),
  Bild-Relief-View, Wrap-Preview3D, OperationPreview3D.
- **D25** ✅ Bild-Relief-Filterpanel (6 Filter mit Reorder + Toggle +
  AI-Toggle).

### Polish (Teil E)

- **E1-E9** ✅ EN-Uebersetzung, Werkzeug-Standzeit-Tracking,
  Kollisionsanalyse Werkzeughalter, Adaptive Clearing (trochoidal),
  Community-Sharing (Bundle-Pattern), Bohrbild-Erkennung,
  Spezial-Operationen, PCB-Fraesen, Operations-Plugin-API.

### Distribution (Teil F)

- **F1, F2** ✅ Cross-Platform-Installer-Skripte vorbereitet (Linux
  AppImage, macOS DMG, Windows portable ZIP), Backend mit PyInstaller
  gebuendelt.
- **F4** ✅ GitHub Actions CI-Pipeline.

### Bekannt offen / blockiert

- **A36** AI-Tiefenschaetzung: Scaffolding fertig, Modell-Download +
  Inferenz nur mit `pip install camwosa[ai]`.
- **C4 / F5** Auto-Updater: blockiert auf ersten GitHub-Release.
- **F3** Code-Signing: blockiert auf User-Zertifikate + Plattform-Setup.
- **NSIS-Installer**: `electron-builder` haengt am winCodeSign-Symlink-Bug
  auf Windows ohne Developer-Mode. Alpha 0 verwendet stattdessen einen
  **portablen ZIP-Bundle** via `scripts/pack-portable.ps1` — entpacken +
  `CAMWOSA.exe` doppelt-klicken. NSIS-Installer kommt mit Alpha 0.0.2.
- **Tests** Frontend (vitest) sind angelegt aber noch nicht im CI.

### Tests

- Backend pytest: **542 / 542 gruen** (+ 1 skipped Integration-Smoke fuer
  `[ai]`-Extra)
- Frontend vitest: 14 Tests fuer `varianteStore` angelegt, nicht im CI

### Bundle

- Portable Windows-Bundle: `CAMWOSA-0.0.1-alpha.0-portable.zip` (~204 MB)
- Inhalt: Electron-Runtime + Frontend-Build + PyInstaller-Backend-Bundle
  + data/ (Default-Stammdaten)
