# Architektur

> Bezugnahme: [Master-Plan](Master-Plan.md), [Spezifikation](../SPECIFICATION.md)

CAMWOSA besteht aus vier Hauptkomponenten:

```
┌─────────────────────────────────────────────────────────────┐
│                  CAMWOSA Desktop-App                        │
│                                                             │
│   ┌─────────────────┐     ┌──────────────────────────────┐  │
│   │  Electron Main  │     │  Electron Renderer           │  │
│   │  (Node.js)      │     │  (React 19 + Vite)           │  │
│   │                 │     │                              │  │
│   │  - Datei-Dialoge│◄───►│  - 2D-/3D-Viewer             │  │
│   │  - Tray         │ IPC │  - G-Code-Editor (Monaco)    │  │
│   │  - Auto-Updater │     │  - Zeichnen-Modul (Konva)    │  │
│   │  - Backend-Mgmt │     │  - Operations-Editor         │  │
│   └────────┬────────┘     └─────────────────┬────────────┘  │
│            │                                │ HTTP          │
│            ▼                                ▼               │
│   ┌─────────────────────────────────────────────────────┐   │
│   │            Python Backend (Flask)                   │   │
│   │            localhost only                           │   │
│   │                                                     │   │
│   │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────┐  │   │
│   │   │  DXF/   │  │  CAM-   │  │  G-Code │  │  DB  │  │   │
│   │   │  STL    │  │  Engine │  │  +Post  │  │      │  │   │
│   │   └─────────┘  └─────────┘  └─────────┘  └──────┘  │   │
│   │                                                     │   │
│   │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────┐  │   │
│   │   │  Feeds  │  │ Safety  │  │ Nesting │  │ Work │  │   │
│   │   │  Speeds │  │ Checks  │  │         │  │ flow │  │   │
│   │   └─────────┘  └─────────┘  └─────────┘  └──────┘  │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                                ▲
                                │ HTTP (gleiche API)
                                │
                       ┌────────┴─────────┐
                       │  MCP-Server      │
                       │  (FastMCP)       │
                       │                  │
                       │  Claude Desktop, │
                       │  Claude Code     │
                       └──────────────────┘
```

## Pure CAM, keine Maschinen-Steuerung

CAMWOSA erzeugt G-Code, prüft ihn, speichert ihn. **Die Ausführung auf der Maschine ist Sache der Maschinen-Steuerung** (CNCjs, Candle, GRBLgru, …). Konkret heißt das:

- Kein Jog-Panel
- Kein Job-Send
- Kein Probing-Aufruf
- Keine Echtzeit-Überwachung der Spindel

Diese Grenze ist bewusst gezogen. Wer eine Steuerung braucht, hat CNCjs — wer ein CAM braucht, bekommt CAMWOSA.

## MCP-First-Prinzip

Die UI ist vollständig stand-alone bedienbar. **Das MCP ist eine zweite Bedienoberfläche** zur gleichen Backend-API. Konsequenzen:

- Jede UI-Aktion ist auch als MCP-Tool verfügbar
- Wenn Claude eine komplette CAM-Bearbeitung erstellt, sind die Schritte ganz normale Operations in der Liste — editierbar wie selbst angelegt
- Backend-API ist die "Single Source of Truth" — Frontend und MCP sind beide nur Konsumenten

## Komponenten-Verantwortlichkeiten

### Electron Main Process
- Lifecycle: Backend starten beim App-Start, beenden beim App-Quit
- OS-Integration: Datei-Assoziationen (`.cwp`), Tray, Auto-Updater
- Native-Dialoge (Save-As, Datei-Öffnen)
- IPC zur Renderer-UI

### Electron Renderer (React-UI)
- Alle Bedien-Oberflächen
- Kommunikation: HTTP an `http://localhost:<port>/api/...`
- Optionaler Live-Sync via Server-Sent-Events (Toolpath-Progress)

### Python-Backend
- Geometrie-Verarbeitung (DXF, STL, shapely)
- CAM-Algorithmen (Operations, Nesting, Workflow)
- G-Code-Erzeugung mit Postprozessor-System
- Sicherheits-Checks
- Persistenz (SQLite + Projekt-Dateien)
- Flask-API (REST, JSON)

### MCP-Server
- FastMCP-basiert
- Bridge zur Backend-API
- Tools 1:1 zu API-Endpoints
- Kein eigenes State-Management

## Datenfluss "DXF → G-Code"

```
1. UI/MCP: dxf_importieren(pfad)
2. Backend: ezdxf-Parse → GeometrieObjekt-Liste
3. UI/MCP: rohmaterial_definieren(...)
4. UI/MCP: nullpunkt_setzen(x, y, z)
5. UI/MCP: operation_kontur(geo_id, werkzeug_id, parameter)
6. Backend: Toolpath-Berechnung (shapely) → Toolpath-Segmente
7. Backend: Sicherheits-Checks → Status-Liste
8. Backend: Postprozessor → G-Code-String
9. UI/MCP: gcode_exportieren(pfad) → .nc/.gcode-Datei
```

Jeder Schritt ist sowohl per UI als auch per MCP aufrufbar und liefert dasselbe Ergebnis.

## Tech-Stack

| Schicht | Technologie | Begründung |
|---------|-------------|------------|
| Desktop-Wrapper | Electron 30+ | Native Datei-Integration, Cross-Platform |
| Frontend | React 19, Vite, TypeScript | Modern, breite Tooling-Basis |
| Frontend-2D | Konva.js | Hohe Performance bei Canvas-Drawing |
| Frontend-3D | Three.js | Standard für WebGL-Simulation |
| Frontend-Editor | Monaco | Gleiche Engine wie VS Code, G-Code-Mode möglich |
| State | zustand | Klein, ohne Boilerplate |
| i18n | i18next | DE/EN, erweiterbar |
| Styling | Tailwind CSS | Konsistente Design-Tokens |
| Backend | Python 3.11+, Flask | Mature CAM-Bibliotheken in Python |
| Geometrie | shapely 2.x, pyclipper | 2D-Boolean, Offset, schnell |
| DXF | ezdxf | Robuster DXF-Parser |
| STL | trimesh, numpy-stl | STL-Lese, Heightmap |
| Datenmodelle | pydantic 2 | Validierung, Serialisierung |
| Persistenz | SQLAlchemy 2 + SQLite + Alembic | Schema-Migrationen |
| Nesting | rectpack (MIT) + optional nest2D (LGPL) | Bin-Packing + No-Fit-Polygon |
| Tests Backend | pytest, hypothesis | Property-Based + Snapshot-Tests |
| Tests Frontend | vitest, React Testing Library, Playwright | Unit + E2E |
| MCP | FastMCP | Standard MCP-Server-Framework |
| PDF (Arbeitsplan) | reportlab | Server-side PDF-Generation |

## Verzeichnis-Struktur

Siehe Repo-Root nach Anlegen:

```
CAMWOSA/
├── backend/
│   ├── camwosa/
│   │   ├── api/             # Flask-Endpoints
│   │   ├── cam/             # Operations + Geometrie
│   │   ├── db/              # SQLAlchemy-Modelle, Alembic
│   │   ├── dxf/             # DXF-Parser
│   │   ├── feeds/           # Feeds & Speeds
│   │   ├── gcode/           # G-Code-Builder (Postprozessor-agnostisch)
│   │   ├── nesting/         # Nesting-Algorithmen
│   │   ├── postprocessor/   # GRBL, Genmitsu, Rotary, Plugins
│   │   ├── project/         # .cwp-Format
│   │   ├── safety/          # Sicherheits-Checks
│   │   ├── stl/             # STL-Parser + Heightmap
│   │   └── workflow/        # Multi-Setup
│   ├── tests/
│   ├── pyproject.toml
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── viewer2d/
│   │   ├── viewer3d/
│   │   ├── editor/          # Monaco G-Code
│   │   ├── drawing/         # Konva-Zeichnen
│   │   ├── operations/
│   │   ├── workflow/
│   │   ├── nesting/
│   │   ├── settings/
│   │   └── locales/         # i18n DE/EN
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
├── electron/
│   ├── main.ts              # Main-Process
│   ├── preload.ts
│   └── backend_runner.ts    # Backend-Subprozess-Lifecycle
├── mcp_server/
│   ├── server.py            # FastMCP
│   ├── pyproject.toml
│   └── README.md
├── installer/
│   ├── windows/
│   ├── macos/
│   └── linux/
├── data/                    # Default-Profile (mitgeliefert)
│   ├── machines/
│   ├── tools/
│   ├── materials/
│   └── postprocessors/
├── docs/
│   ├── SPECIFICATION.md
│   ├── ROTARY.md
│   └── wiki/                # Dieses Wiki (gespiegelt nach GitHub-Wiki)
└── README.md
```

## Internationalisierung

- **DE-zuerst** — alle Strings werden zuerst in Deutsch erstellt.
- **i18n-Keys auf Deutsch** — z.B. `t('operation.tasche.titel')`.
- **EN folgt nach Stabilisierung** der DE-Begriffe (Phase E1).
- Glossar ([Glossar](Glossar.md)) enthält das DE-EN-Mapping als verbindliche Übersetzungs-Referenz.

## Sicherheit & Datenschutz

- **Lokal-First**: kein Account, keine Cloud-Pflicht.
- **Backend nur auf localhost**: Flask bindet nur auf `127.0.0.1`, niemals `0.0.0.0`.
- **Keine Telemetrie ohne Opt-In**.
- **Optionales Cloud-Sync** (Phase E5) ausschließlich für Tool/Material-Sharing, nie für Projekte.

## Verlinkungen

- [Datenmodell](Datenmodell.md)
- [API](API.md)
- [MCP-Server](MCP-Server.md)
- [Glossar](Glossar.md)
- [Contribution-Guide](Contribution.md)
