# CAMWOSA — CAM für Maker, nicht für Konzerne

<sup>An <b>ELWOSA</b> Project</sup>

> CAMWOSA ist ein browserbasiertes 2.5D CAM-Tool, das direkt mit Claude zusammenarbeitet. Du importierst dein DXF, definierst was gefräst werden soll — und bekommst fertigen G-Code für deine Maschine. Läuft lokal, kostet nichts, deine Daten bleiben bei dir.

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
- **Visueller Toolpath-Preview** im Browser (2D-Ansicht)
- **Nullpunkt setzen** — Ecke, Mitte, beliebiger Punkt per Klick
- **Rotation & Ausrichtung** — Modell drehen bis es stimmt
- **Operationen:** Kontur (innen/außen), Tasche, Bohren, Gravur
- **Tabs** — für Konturfräsungen ohne Ausbrechen
- **G-Code Export** — GRBL-kompatibel, direkt für ProVerXL und ähnliche Maschinen
- **Feeds & Speeds Rechner** — Material + Fräser → optimale Werte

### Phase 2 — STL & Relief
- **STL-Import** für 2.5D-Reliefs
- **Tiefenkarte** aus STL-Geometrie
- **Relief-Strategien:** Raster, Kontur, kombiniert
- **Vorschau** der Relieftiefe als Heatmap

### Phase 3 — Erweiterungen
- **Werkzeugbibliothek** — deine Fräser gespeichert, wiederverwendbar
- **Maschinenprofile** — Voreinstellungen für ProVerXL 4030 V2 und andere GRBL-Maschinen
- **Post-Prozessor-System** — unterschiedliche GRBL-Varianten
- **Simulation** — einfache 2D-Simulation des Toolpaths vor dem Export

---

## Architektur

```
CAMWOSA
├── backend/          # Python (Flask) — Geometrie, CAM-Logik, G-Code
│   ├── dxf/          # DXF-Parser (ezdxf)
│   ├── stl/          # STL-Parser für Relief
│   ├── cam/          # Toolpath-Berechnung (shapely)
│   ├── gcode/        # G-Code Generator (GRBL)
│   └── api/          # REST-API für das Frontend
├── frontend/         # Browser-UI (React + Vite)
│   ├── viewer/       # 2D-Toolpath-Vorschau
│   ├── operations/   # Operationen definieren
│   └── export/       # G-Code Export
└── docs/             # Dokumentation
```

**Technologie-Stack:**
- Backend: Python 3.11+, Flask, ezdxf, shapely, numpy
- Frontend: React 19, Vite, Tailwind CSS
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
| **Konzept** | Vision, Architektur, Repository | ✅ |
| **Phase 1** | DXF → Kontur/Tasche/Bohren → Preview → G-Code | 🔜 |
| **Phase 2** | STL → Relief → G-Code | ⏳ |
| **Phase 3** | Werkzeugbibliothek, Maschinenprofile, Simulation | ⏳ |

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
