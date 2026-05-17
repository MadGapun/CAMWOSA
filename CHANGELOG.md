# Changelog

Alle nennenswerten Aenderungen an CAMWOSA. Format orientiert sich an
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/), Versionsschema
[SemVer](https://semver.org/lang/de/).

## [0.0.1-alpha.5] — 2026-05-17

**Backend-Erweiterungs-Release.** 5 neue CAM-Backend-Module + Diagnose-Tool
+ 65 neue Tests (10 Z-Grid, 12 Drag-Engraving, 12 Auto-Inlay, 9 Thread-Milling,
12 Circular/Radial, 10 API-Tests). UI-Frontend bekommt API-Client-Bindings,
echte UI-Komponenten kommen in spaeteren Sessions wenn Markus testet.

### A47-Rest — Z-Grid-Diagnose

✅ `diagnostics/z_grid.py` — analysiert Z-Probing-Daten (n×m XY-Grid mit
Z-Messungen) und meldet:
- **EBEN_OK** (< 0.1 mm) — Job kann starten
- **LEICHTE_NEIGUNG** (< 0.5 mm) — Schruppen OK, Schlichten kompensieren
- **STARKE_NEIGUNG** (< 2 mm) — neu aufspannen empfohlen
- **UNEBENE_OBERFLAECHE** (> 2 mm) — Werkstueck planen vor dem Job

Least-squares-Plane-Fit ohne numpy-Abhaengigkeit (eigene 3×3 Gauss-Jordan).
Schwellwerte passen sich an Werkzeug-Typ an (Kugelfraeser strenger).
Output liefert Klartext + Empfehlung pro Befund, plus Numerik fuer Heatmap.

### A45-Rest — 4 neue Spezial-Operationen

✅ `cam/drag_engraving.py` — Diamantgravierer/Schleppgravierer als eigene Op:
- Werkzeug-Pflicht-Check (DRAG_GRAVIERER oder DIAMANTGRAVIERER)
- Spindel zwingend AUS (M5)
- Eintauch-Vorschub 1/10 vom Vorschub (Diamantspitze schonen)
- Dwell an scharfen Knick-Ecken (Werkzeug neu ausrichten)
- Tangentialer Lead-In gegen "Tropfen" am Start

✅ `cam/auto_inlay.py` — Auto-Inlay (Tasche + passender Plug aus EINER Kontur):
- Konfigurierbares Spiel (Holz 0.05-0.15, Kunststoff 0.0-0.05)
- Werkzeug-Radius-Check (passt das Werkzeug ins Polygon?)
- Plug-Hoehe = Tasche-Tiefe + Uebermass (zum Plan-Schleifen)
- Output: zwei Polylinien (WKT + als GeometrieObjekt) zum direkten Anlegen
  von Operationen
- shapely-basiert (robuste Negativ-Buffer + MultiPolygon-Handling)

✅ `cam/thread_milling.py` — Gewindefraesen mit Helix:
- Innen- und Aussengewinde
- Rechts- und Linksgewinde (Drehrichtung an Innen/Aussen angepasst)
- Werkzeug-Pruefung (muss kleiner als Nenndurchmesser bei Innengewinde)
- "Zurueck zur Mitte" vor Lift (vermeidet Gewindeschaden)
- Metadaten markieren Thread-Milling fuer Postprozessor-Erkennung

✅ `cam/circular_radial.py` — 2 neue Pocketing-Strategien:
- **CIRCULAR**: konzentrische Kreis-Spiralen aussen↔innen
- **RADIAL**: Sonnenstrahlen vom Mittelpunkt mit konfigurierbarem Speichen-Zahl

### API-Endpoints + Frontend-Bindings

✅ `POST /api/diagnostics/z-grid`
✅ `POST /api/spezial-ops/drag-engraving`
✅ `POST /api/spezial-ops/auto-inlay`
✅ `POST /api/spezial-ops/thread-milling`
✅ `POST /api/spezial-ops/circular-pocket-pfade`
✅ `POST /api/spezial-ops/radial-pocket-pfade`

Frontend-Client-Bindings in `frontend/src/api/client.ts`: `zGridAnalysieren`,
`dragEngraving`, `autoInlay`, `threadMilling`, `circularPocketPfade`,
`radialPocketPfade`. UI-Komponenten folgen in alpha.6 wenn Markus die
Backend-Funktionen getestet hat.

### Test-Status

- Backend: **678 Tests gruen** (+65 fuer alpha.5)
- Frontend: vite build 1.66 MB / 957 Module
- conftest-Refactor: API-Test-Fixtures aus `test_crud_stammdaten.py` in
  `tests/api/conftest.py` ausgelagert — alle API-Tests koennen sie jetzt nutzen

### Master-Plan-Fortschritt

| Punkt | Was | Status |
|---|---|---|
| A47-Rest | Z-Grid-Diagnose-Tool | ✅ |
| A45-Rest | Drag-Engraving als eigene Op | ✅ |
| A45-Rest | Auto-Inlay | ✅ |
| A45-Rest | Thread-Milling | ✅ |
| A43-Rest | Circular Pocketing | ✅ |
| A43-Rest | Radial Pocketing | ✅ |

---

## [0.0.1-alpha.4] — 2026-05-17

**Frontend-Workflow + Onboarding-Release.** Master-Plan **D31** (Geometrie→
Operation Verknuepfung) und **Issues #22 + #23** (First-Run-Wizard kann
anlegen statt nur waehlen) umgesetzt. Markus' typischster Workflow
„mehrere Konturen zeichnen → nur eine soll eine Tasche werden" ist jetzt
erstmals sauber moeglich. Und beim ersten Start kann man Maschine /
Spindel / Werkzeug / Material direkt inline anlegen.

### Issues #22 + #23 — First-Run-Wizard kann anlegen

✅ **Backend** — `POST/PUT/DELETE /api/machines/` (analog zu Spindeln,
Werkzeugen, Materialien). 3 neue Tests in `test_crud_stammdaten.py`.

✅ **Frontend** — `camwosaApi.maschineAnlegen/Updaten/Loeschen` +
`spindelAnlegen/Updaten/Loeschen`. Store-Setter `setMaschinen` + `setSpindeln`.

✅ **Wizard** — pro Schritt Toggle „Vorhandene waehlen (N)" vs „+ Neu
anlegen". Inline-Formulare mit Pflichtfeldern + Defaults:
- **Maschine**: Name, Hersteller/Modell, Controller, Arbeitsraum X/Y/Z,
  max. Vorschub. Default-Werte ProVerXL-typisch (400×400×110, 3000 mm/min).
- **Spindel**: Name, Typ (manuell/PWM/analog), Hersteller/Modell, RPM-Bereich.
  Wenn Maschine im vorigen Schritt angelegt wurde, wird die neue Spindel
  automatisch verknuepft + aktiv gesetzt.
- **Werkzeug**: Name, Typ (10 Typen zur Wahl), Ø/Schaft-Ø/Schneidlaenge/
  Schneiden.
- **Material**: Name, Kategorie (6 Optionen), optional Unter-Kategorie.

✅ **Backend-Verhalten** — neue Eintraege landen als Einzeldateien in
`data/<typ>/`, die Sammel-Defaults bleiben unangetastet. User-Eintraege
koennen geloescht werden, Default-Einzeldateien auch (Maschinen-Eigenheit,
da alle Maschinen Einzeldateien sind).

---

**Frontend-Workflow-Release.** Master-Plan **D31** (Geometrie→Operation
Verknuepfung) komplett umgesetzt. Markus' typischster Workflow „mehrere
Konturen zeichnen → nur eine soll eine Tasche werden" ist jetzt erstmals
sauber moeglich.

### Master-Plan D31 — Geometrie-Verknuepfung

✅ **Datenmodell** — `OperationEintrag.geometrie_ids: string[]` (Multi-
Selektion) zusaetzlich zum Legacy-Feld `geometrie_id`. Geometrien
bekommen beim Eintritt in den Store eine stabile ID (`geo_<base36>`).

✅ **OperationenView — Pflicht-Dropdown „Geometrie-Verknuepfung"**
- Checkbox-Liste filtert auf passende Typen (Tasche → nur geschlossene
  Konturen; Bohren → nur Kreise/Punkte; Kontur/Gravur/Relief → ohne Punkte)
- „Alle" / „Keine"-Buttons fuer Schnellauswahl
- Pflichtfeld-Markierung (`*`) + gelbe Warnung wenn Geometrie fehlt
- Toolpath-Button blockiert bis Pflicht erfuellt — Tooltip erklaert warum
- Bohren ist Spezialfall (Auto-Wahl aller Kreise/Punkte), bleibt optional

✅ **ZeichnenView — Quick-Create + Op-Verknuepfungen**
- Selektierte Geometrie zeigt verknuepfte Operationen mit Toolpath-Status
- Buttons „+ Kontur / + Tasche / + Bohren / + Gravur / + Relief" legen
  Op an die selektierte Geometrie an (filtert was technisch passt)
- Auto-Uebernahme: Quick-Create sorgt selbst dafuer dass alle gezeichneten
  Objekte im Geometrie-Store landen — kein „Als Geometrie uebernehmen"
  mehr noetig fuer den Schnellweg
- IDs werden beim Uebernehmen erhalten — Zeichenobjekt und Geometrie
  sind dadurch identifizierbar dieselbe Sache

✅ **Farbliche Markierung verknuepfter Geometrien**
- Verknuepfte Objekte gruen statt hellblau auf dem Canvas
- Objekt-Liste zeigt Op-Badge „↪ N" mit Tooltip der Op-Namen

### Folgewirkung

Der Run-Lock aus alpha.3 (A48) bekommt jetzt echte Inputs: Operationen
die keine Geometrie haben werden als BROKEN gekennzeichnet, sobald der
Run-Lock-Check im UI verdrahtet ist (naechste Session).

### Tests / Smoke

- Backend: 610 grun (unveraendert)
- Frontend: vite build 1.65 MB, 957 Module
- Smoke-Test bei Pack-Prozess

---

## [0.0.1-alpha.3] — 2026-05-17

**Backend-Erweiterungs-Release.** Markus' Auftrag „vollende den Master-Plan"
wurde in mehreren Phasen abgearbeitet. UI-schwere Punkte folgen in
spaeteren Sessions.

### Master-Plan-Fortschritt (10 Positionen bearbeitet)

✅ **A39** Werkzeug-Erweiterung — BALLNOSE_V_BIT + DRAG_GRAVIERER Typen,
   V-Bit-Range 1-179° (statt 10-180°)
✅ **A41** Werkzeug-Typen-Wiki — 12 Typen mit ASCII-Skizze + Anwendung +
   Pflichtfeldern + Markus' Fischschwanz-Frage erklaert
✅ **A46** Cutter-Modellierung — `free_length_mm` + `auto_set_speeds` /
   `auto_feedrate` / `auto_spindel_rpm`
✅ **A48** Run-Lock + Dependency-Graph — OperationStatus (NEU/OK/DIRTY/
   BROKEN), `workflow/run_lock.py` mit Change-Propagation, API-Endpoint
   `POST /api/workflow/run-lock`. Markus' Regel: „Im Zweifel laeuft das
   Programm nicht."
✅ **D32** Rename UI Drechseln → Drehen
🟨 **A43** 3D-Strategien — Waterline (`cam/waterline.py` mit eigener
   Marching-Squares-Implementation)
🟨 **A45** Spezial-Operationen — Dogbone (`cam/dogbone.py` mit DOGBONE +
   T_BONE Stilen), Lithophane (`stl/lithophane.py`), Chamfer
   (`cam/chamfer.py`)
🟨 **A47** Sicherheit/Workholding — Spannmittel-Modell (`db/spannmittel.py`
   mit 8 Typen + Sicherheitszonen + Z-Hoehe-Check)
🟨 **D36** Hilfe-System — Glossar (60+ CNC-Begriffe)

### Was offen bleibt (Folge-Sessions)

UI-schwere Punkte die Frontend-Iteration brauchen:
- D26/D27 Wizard Quick-Add (Maschine/Spindel/Werkzeug)
- D28 Eigenschaften-Panel im Zeichnen
- D29 Smart-Snap + Align-Buttons
- D30 Text-Werkzeug im Zeichnen
- D31 Geometrie→Operation-Verknuepfung (Frontend)
- D33 Drehen-Profil-Editor numerisch
- D34 Werkzeug-UI mit SVG-Skizzen
- D35 ProjectTree + Animation + Multi-View
- D36 Hover-Help-Audit (200+ Eingaben)
- A40 3D-Drehen (5-stufige Pipeline)
- A42 Vector-Ops Details
- A44 Two-Sided + Indexed Wizards
- A49 Multi-Setup mit Werkstueck-Transformation
- A47 Rest (Collet-Visualisierung, Z-Grid-Tool)
- A45 Rest (Auto-Inlay, V-Carve Inlay, Thread, Rest-Machining, Drag-Engraving-Op)
- A43 Rest (Circular/Radial/Offset/Pencil)

### Tests

- Backend pytest: **610 / 610 grün** (+68 seit alpha.2)
- 7 neue Test-Module: `test_run_lock` (29), `test_dogbone` (11),
  `test_waterline` (8), `test_lithophane` (5), `test_spannmittel` (8),
  `test_chamfer` (7)
- Schema-Version 1 -> 2

---

## [0.0.1-alpha.2] — 2026-05-17

**Zweiter Show-Stopper-Fix.** Alpha 0.0.1-alpha.1 startete immer noch
schwarz: zwar Backend + Renderer-Asset-Loading OK, aber React rendert
gar nichts und Klicks in der Sidebar gehen ins Leere.

### Zwei echte Bugs gefunden

1. **React 19 vs. Ecosystem-Inkompatibilitaet.** `@react-three/drei` und
   andere Libs erwarten React 18, peer-deps wurden mit
   `--legacy-peer-deps` gewaltsam installiert. Im Production-Build
   crashed der erste Modul-Eval mit
   `Cannot read properties of undefined (reading 'ReactCurrentBatchConfig')`.
   In Dev-Mode (Vite-HMR) hatten wir das nicht gesehen, weil Vite
   andere Module-Pfade nutzt. **Fix:** Downgrade auf React 18.3.1 + 18.3
   types. `--legacy-peer-deps` ist nicht mehr noetig.

2. **`BrowserRouter` unter `file://` kaputt.** React-Router 6 mit
   `BrowserRouter` braucht die HTML5-History-API mit echten URLs. Unter
   `file://D:/.../index.html` matched keine Route, Routes ist leer.
   **Fix:** `HashRouter` in Production (Detection via
   `window.location.protocol`), `BrowserRouter` bleibt im Dev.

### Smoke-Test deutlich verstaerkt

Mein bisheriger Test pruefte nur „Backend antwortet". Das hat beide
obigen Bugs nicht erkannt, weil das Backend lief — nur der Renderer war
tot. Neu in `main.ts`:

- `console-message`-Hook leitet ALLE Renderer-Errors/Logs nach stdout
- `did-finish-load` und `render-process-gone` Handler
- `startRendererSmoke()` evaluiert nach 8s im Renderer
  `document.body.innerHTML.length` + `#root.children.length` + Anzahl
  `<aside>`/`<nav>` und loggt sie

`pack-portable.ps1` macht jetzt nach jedem Pack automatisch einen
Smoke-Test: entpackt das ZIP in `%TEMP%\camwosa-pack-smoke`, startet
`CAMWOSA.exe`, wartet 20s, parsed den `[smoke] dom` Log. Wenn
`rootChildren < 1` oder `body < 500B` -> Build wird mit Error
abgebrochen. **So kann nie wieder ein schwarzer Bildschirm released
werden.**

### Verifiziert in dieser Version

- `[smoke] dom url=...#/quickstart body=13698B rootChildren=1 aside=1`
- HashRouter sichtbar im URL (`#/quickstart`)
- Backend Port 8766 antwortet `/health` mit `0.0.1-alpha.2`
- `/api/tools/` liefert 12 Werkzeuge

---

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
