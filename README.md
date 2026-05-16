# CAMWOSA — CAM für Maker, nicht für Konzerne

<sup>An <b>ELWOSA</b> Project</sup>

> CAMWOSA ist eine 2.5D CAM-Desktop-App, die direkt mit Claude zusammenarbeitet. Du importierst dein CAD-Modell (DXF, STL, STEP, SVG, …), definierst was gefräst werden soll — und bekommst fertigen G-Code für deine Maschine. Läuft lokal als Electron-App, kostet nichts, deine Daten bleiben bei dir.

[![Status](https://img.shields.io/badge/Status-Konzeptphase-orange.svg)](#roadmap)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Lizenz](https://img.shields.io/badge/Lizenz-MIT-green.svg)](LICENSE)
[![Plattformen](https://img.shields.io/badge/Plattformen-Windows_%7C_macOS_%7C_Linux-blue.svg)](#)
[![Maschinen](https://img.shields.io/badge/Maschinen-GRBL%2FGenmitsu%2FProVerXL-lightgrey.svg)](#maschinenprofile)

---

## Die Idee

Professionelle CAM-Software ist entweder zu teuer, zu komplex oder beides. Hobbyisten und kleine Werkstätten brauchen etwas anderes: ein Tool, das den Workflow kennt, die Werte rechnet und G-Code erzeugt — ohne Lernkurve von Wochen.

**CAMWOSA ist dieser fehlende Baustein.** Claude-nativ — Parameter setzen, Toolpaths erzeugen, G-Code prüfen, alles in einem Gespräch.

| Du hast | Du bekommst |
|---------|-------------|
| 2D-Zeichnung (DXF / SVG) oder direkt im Tool gezeichnet | Fertiger G-Code für deine Maschine |
| 3D-Modell (STL / STEP) | Toolpath mit Tiefensteuerung, Reliefs |
| Material + Fräser | Berechnete Feeds & Speeds |
| Mehrere Aufspannungen | Druckbarer Arbeitsplan, ein G-Code pro Setup |
| Fragen | Claude als Sparringspartner |

---

## Geplante Features

### Phase 1 — 2.5D Kern
- **CAD-Import** — DXF, SVG für 2D; STL, STEP für 3D; native Maker-CAD-Formate (FreeCAD, Fusion, …) als Plugin-System
- **Integriertes Zeichnen** — schnelle Formen ohne CAD-Wechsel
- **Visueller Toolpath-Preview** (2D-Ansicht im Desktop-Fenster)
- **Nullpunkt setzen** — Ecke, Mitte, beliebiger Punkt per Klick
- **Rotation & Ausrichtung** — Modell drehen bis es stimmt
- **Operationen:** Kontur (innen/außen), Tasche, Bohren, Gravur (V-Carving)
- **Tabs** — für Konturfräsungen ohne Ausbrechen
- **G-Code Export** — GRBL-kompatibel, direkt für ProVerXL und ähnliche Maschinen
- **G-Code-Editor** mit Befehlsbibliothek und Live-Sync zur Vorschau
- **Feeds & Speeds Rechner** — Material + Fräser → optimale Werte
- **Per-Feature-Override** — jede Operation kann projekt- oder werkstoffweite Standards individuell überschreiben und zurücksetzen
- **Sicherheits-Checks** — Crash-Erkennung vor Export
- **Multi-Setup-Workflow** — mehrere Aufspannungen + druckbarer Arbeitsplan
- **Verschnittoptimierung (Nesting)** — mehrere Teile auf einer Platte

### Phase 2 — STL, 3D-Simulation, Plugins
- **STL-Import** für 2.5D-Reliefs mit Heatmap-Vorschau
- **STEP-Import** für solide 3D-Modelle (neutrales Format)
- **3D-Materialabtrag-Simulation**
- **Plugin-System für Postprozessoren** — eigene Controller nachrüsten
- **Plugin-System für CAD-Formate** — native Maker-CAD nachrüstbar (Fusion .f3d, FreeCAD .FCStd, OpenSCAD …)
- **Englische Übersetzung**

### Phase 3 — Rotary (3,5-Achse)
Die Genmitsu-Rotary-Lösung ist eine **3,5-Achse**: die Y-Linearachse wird im Rotary-Modus durch eine Drehachse (A) ersetzt. Es laufen also weiter X, Z und A — aber Y und A sind dieselbe Hardware und können nicht gleichzeitig genutzt werden.
- **Maschinen-Modi-Konzept** (Standard XYZ vs. Rotary)
- **Rotary-Postprozessor** — Y-Achse als Rotationsachse
- **Wrapping** (2D-Geometrie auf Zylinder)
- **3,5-Achs-Indexing**

### Phase 4 — Drechseln
- **Drechsel-Operationen** (Plandrehen, Längsdrehen, Spirale, Helix)

### Phase 5 — Pro
- **Werkzeug-Standzeit-Tracking**
- **Kollisionsanalyse Werkzeughalter**
- **Adaptive Clearing**
- **Community-Sharing** für Werkzeuge und Materialien

Vollständiger Plan: siehe [Master-Plan im Wiki](docs/wiki/Master-Plan.md).

---

## CAD-Format-Unterstützung

CAMWOSA setzt auf **neutrale Formate** als Pflicht — und unterstützt **native Maker-CAD-Formate** wo möglich.

| Format | Status | Anmerkung |
|--------|--------|-----------|
| **DXF** | ✅ | LINE, POLYLINE, CIRCLE, ARC, ELLIPSE, SPLINE, POINT |
| **STL** | ✅ | ASCII + binary, Heightmap-Berechnung |
| **SVG** | 🟨 in Arbeit | Inkscape-Export, paths/rect/circle/polygon |
| **STEP** | 🟨 in Arbeit | Industriestandard für 3D-CAD-Austausch |
| **IGES** | ⏳ | Geplant |
| **G-Code** | ⏳ | Re-Import zur Bearbeitung im Editor |
| **FreeCAD .FCStd** | ⏳ Plugin | OSS-CAD, kostenlos |
| **Fusion .f3d / .f3z** | ⏳ Plugin | Hobby-Lizenz kostenlos |
| **OpenSCAD .scad** | ⏳ Plugin | Skript-CAD |
| **SolidWorks / Solid Edge / Inventor** | ⏳ Plugin | Wenn deren Hersteller-API nutzbar ist |

Details: siehe [CAD-Import im Wiki](docs/wiki/CAD-Import.md).

---

## Architektur

CAMWOSA ist eine **Electron-Desktop-App** mit Python-Backend als Subprozess. **Pure CAM** — keine Maschinen-Steuerung (das übernimmt deine vorhandene Steuerungs-Software wie CNCjs).

```
CAMWOSA
├── backend/          # Python (Flask) — Geometrie, CAM-Logik, G-Code
│   └── camwosa/
│       ├── cad/          # CAD-Importer (DXF, SVG, STEP, STL + Plugin-System)
│       ├── stl/          # STL-Heightmap für 2.5D-Relief
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
| Genmitsu ProVerXL 4030 V2 + Rotary | GRBL (3,5-Achs, Y→A) | Wrapping + Indexing |
| Genmitsu PROVer 3018 | GRBL | Profil mitgeliefert |
| Generisch GRBL 3-Achs | GRBL | Profil mitgeliefert |

Eigene Maschinenprofile lassen sich als JSON importieren — siehe [Maschinenprofil-Format](docs/wiki/Maschinenprofil-Format.md).

---

## Schnellstart

> **CAMWOSA befindet sich in der Konzeptphase.** Es gibt noch keinen stabilen Release.
> Wenn du die Entwicklung mitverfolgen möchtest: ⭐ Star vergeben und Notifications aktivieren.

---

## Roadmap

| Phase | Inhalt | Status |
|-------|--------|--------|
| **Konzept** | Vision, Architektur, Repository, Wiki | ✅ |
| **Phase 1 — MVP** | Backend-Kern, Electron+UI, CAD-Import (DXF/SVG), Operations, Editor, Feeds&Speeds, Safety, Workflow, Nesting, GRBL-Output | 🟨 in Arbeit |
| **Phase 2 — Tiefe** | STL-Relief, STEP-Import, 3D-Simulation, Plugin-System, EN | ⏳ |
| **Phase 3 — Rotary (3,5-Achs)** | Rotary-Modus, Wrapping, 3,5-Achs-Indexing | ⏳ |
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
