# CAMWOSA — CAM für Maker, nicht für Konzerne

<sup>An <b>ELWOSA</b> Project</sup>

> CAMWOSA ist eine 2.5D CAM-Desktop-App, die direkt mit Claude zusammenarbeitet. Du importierst dein DXF, definierst was gefräst werden soll — und bekommst fertigen G-Code für deine Maschine. Läuft lokal als Electron-App, kostet nichts, deine Daten bleiben bei dir.

[![Status](https://img.shields.io/badge/Status-Konzeptphase-orange.svg)](#roadmap)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Lizenz](https://img.shields.io/badge/Lizenz-MIT-green.svg)](LICENSE)
[![Plattformen](https://img.shields.io/badge/Plattformen-Windows_%7C_macOS_%7C_Linux-blue.svg)](#)
[![Maschinen](https://img.shields.io/badge/Maschinen-GRBL%2FGenmitsu%2FProVerXL-lightgrey.svg)](#maschinenprofile)

---

## Die Idee

Professionelle CAM-Software ist entweder zu teuer, zu komplex oder beides. Hobbyisten und kleine Werkstätten brauchen etwas anderes: ein Tool, das den Workflow kennt, die Werte rechnet und G-Code erzeugt — ohne Lernkurve von Wochen.

**CAMWOSA ist dieser fehlende Baustein.**

| Du hast | Du bekommst |
|---------|-------------|
| DXF aus Solid Edge / Inkscape / LibreCAD | Fertiger G-Code für deine Maschine |
| STL für 2.5D-Relief | Toolpath mit Tiefensteuerung |
| Material + Fräser | Berechnete Feeds & Speeds |
| Fragen | Claude als Sparringspartner |

---

## Warum nicht einfach EstlCAM / DeskProto nutzen?

EstlCAM und DeskProto sind gute Tools — sie bleiben für spezifische Use Cases (z.B. Rotationsachse) weiter im Einsatz. CAMWOSA ergänzt sie, ersetzt sie nicht.

Der Unterschied: **CAMWOSA ist Claude-nativ.** Claude kann nicht nur helfen — Claude kann die CAM-Arbeit direkt erledigen. Parameter setzen, Toolpaths erzeugen, G-Code prüfen — alles in einem Gespräch, ohne Klickorgien durch verschachtelte Dialoge.

---

## Geplante Features

### Phase 1 — 2.5D Kern
- **DXF-Import** (Solid Edge, Inkscape, LibreCAD, …)
- **Integriertes Zeichnen** (LightBurn-inspiriert) — schnelle Formen ohne CAD-Wechsel
- **Visueller Toolpath-Preview** (2D-Ansicht im Desktop-Fenster)
- **Nullpunkt setzen** — Ecke, Mitte, beliebiger Punkt per Klick
- **Rotation & Ausrichtung** — Modell drehen bis es stimmt
- **Operationen:** Kontur (innen/außen), Tasche, Bohren, Gravur (V-Carving)
- **Tabs** — für Konturfräsungen ohne Ausbrechen
- **G-Code Export** — GRBL-kompatibel, direkt für ProVerXL und ähnliche Maschinen
- **G-Code-Editor** (Monaco) mit Befehlsbibliothek und Live-Sync
- **Feeds & Speeds Rechner** — Material + Fräser → optimale Werte
- **Sicherheits-Checks** — Crash-Erkennung vor Export
- **Multi-Setup-Workflow** — mehrere Aufspannungen + druckbarer Arbeitsplan
- **Verschnittoptimierung (Nesting)** — mehrere Teile auf einer Platte

### Phase 2 — STL, 3D-Simulation, Plugins
- **STL-Import** für 2.5D-Reliefs mit Heatmap-Vorschau
- **3D-Materialabtrag-Simulation** (Three.js)
- **Plugin-System für Postprozessoren** — eigene Controller nachrüsten
- **Englische Übersetzung**

### Phase 3 — Rotary
- **Maschinen-Modi-Konzept** (Standard XYZ vs. Rotary)
- **Rotary-Postprozessor** — Y-Achse als Rotationsachse
- **Wrapping** (2D-Geometrie auf Zylinder)
- **4-Achs-Indexing**

### Phase 4 — Drechseln
- **Drechsel-Operationen** (Plandrehen, Längsdrehen, Spirale, Helix)
- DeskProto-Ablösung Teil 2

### Phase 5 — Pro
- **Werkzeug-Standzeit-Tracking**
- **Kollisionsanalyse Werkzeughalter**
- **Adaptive Clearing**
- **Community-Sharing** für Werkzeuge und Materialien

Vollständiger Plan: siehe [Master-Plan im Wiki](docs/wiki/Master-Plan.md).

---

## Architektur

CAMWOSA ist eine **Electron-Desktop-App** mit Python-Backend als Subprozess. **Pure CAM** — keine Maschinen-Steuerung (das übernimmt CNCjs o.ä.).

```
CAMWOSA
├── backend/          # Python (Flask) — Geometrie, CAM-Logik, G-Code
│   └── camwosa/
│       ├── dxf/          # DXF-Parser (ezdxf)
│       ├── stl/          # STL-Parser für Relief
│       ├── cam/          # Toolpath-Berechnung (shapely)
│       ├── gcode/        # G-Code Builder
│       ├── postprocessor/# GRBL, Genmitsu, Rotary, Plugins
│       ├── feeds/        # Feeds & Speeds Rechner
│       ├── safety/       # Sicherheits-Checks
│       ├── nesting/      # Verschnittoptimierung
│       ├── workflow/     # Multi-Setup-Modul
│       ├── project/      # .cwp-Format
│       ├── db/           # SQLAlchemy + Alembic
│       └── api/          # Flask-Endpoints (localhost only)
├── frontend/         # Electron-Renderer (React 19 + Vite + TS)
├── electron/         # Electron-Main-Process
├── mcp_server/       # FastMCP-Server für Claude-Integration
├── installer/        # Cross-Platform-Installer
├── data/             # Default-Profile (Maschinen, Werkzeuge, Material)
└── docs/
    ├── SPECIFICATION.md
    ├── ROTARY.md
    └── wiki/         # Wiki (gespiegelt nach GitHub-Wiki)
```

**Technologie-Stack:**
- Desktop: Electron 30+
- Frontend: React 19, Vite, TypeScript, Tailwind, Konva (2D), Three.js (3D), Monaco (Editor), zustand, i18next
- Backend: Python 3.11+, Flask, ezdxf, shapely, pyclipper, trimesh, pydantic 2, SQLAlchemy 2 + SQLite + Alembic
- Nesting: rectpack (MIT) + optional nest2D (LGPL)
- MCP: FastMCP
- Lokal: kein Server, kein Account, keine Cloud

---

## Maschinenprofile

CAMWOSA wird von Anfang an auf realen Maschinen entwickelt und getestet:

| Maschine | Controller | Status |
|----------|-----------|--------|
| Genmitsu ProVerXL 4030 V2 | GRBL | Primäres Testgerät |
| ProVerXL 4030 V2 + Rotary | GRBL (Y-Achse) | Rotary via DeskProto |

---

## Schnellstart

> **CAMWOSA befindet sich in der Konzeptphase.** Es gibt noch keinen stabilen Release.
> Wenn du die Entwicklung mitverfolgen möchtest: ⭐ Star vergeben und Notifications aktivieren.

---

## Roadmap

| Phase | Inhalt | Status |
|-------|--------|--------|
| **Konzept** | Vision, Architektur, Repository, Wiki | ✅ |
| **Phase 1 — MVP** | Backend-Kern, Electron+UI, DXF, Operations, Editor, Feeds&Speeds, Safety, Workflow, Nesting, GRBL-Output | 🟨 in Arbeit |
| **Phase 2 — Tiefe** | STL-Relief, 3D-Simulation, Plugin-System Postprozessoren, EN | ⏳ |
| **Phase 3 — Rotary** | Rotary-Modus, Wrapping, 4-Achs-Indexing | ⏳ |
| **Phase 4 — Drechseln** | Drechsel-Operationen | ⏳ |
| **Phase 5 — Pro** | Standzeit, Kollisionsanalyse, Adaptive Clearing, Community-Sharing | ⏳ |

Detaillierter Status pro Funktion: [Master-Plan im Wiki](docs/wiki/Master-Plan.md).

---

## Lizenz

[MIT License](LICENSE) — Markus Birzite

---

## Credits

**Markus Birzite** — Idee, Konzept, Architektur & Projektleitung
> Langjähriger CNC-Praktiker (Genmitsu ProVerXL 4030 V2, Rotationsachse, Laserschneiden, Drechseln). Hat die Lücke im Hobbyisten-CAM-Markt identifiziert und CAMWOSA erdacht.

**Claude** (Anthropic) — Entwicklung, Code, Dokumentation
> Entwicklungspartner. Schreibt Backend, Frontend, CAM-Logik und G-Code-Generator — und erklärt was er dabei tut.

---

<p align="center">
<a href="https://paypal.me/birzite"><img src="https://img.shields.io/badge/☕_Kaffee_spendieren-PayPal-blue?style=for-the-badge" alt="Kaffee spendieren"></a>
<br><sub>An <b>ELWOSA</b> Project</sub>
</p>
