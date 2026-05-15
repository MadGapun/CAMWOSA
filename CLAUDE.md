# CLAUDE.md — Projekt-Kontext für Claude Code

Dieses Dokument hilft Claude Code beim Einstieg in dieses Repository. Lies es vor der ersten Implementierungs-Session vollständig.

---

## Projekt auf einen Blick

**CAMWOSA** ist ein 2.5D CAM-Tool für GRBL-basierte CNC-Maschinen, speziell die Genmitsu ProVerXL 4030 V2. Es soll mittelfristig sowohl EstlCAM (für 2.5D) als auch DeskProto (für Rotary) ersetzen.

**Aktueller Status:** Konzeptphase. Spezifikation ist vollständig, Implementation hat noch nicht begonnen.

---

## Wichtige Dokumente

| Datei | Inhalt |
|---|---|
| `README.md` | Projekt-Vision, Roadmap, Spenden-Link |
| `docs/SPECIFICATION.md` | **Hauptdokument** — vollständige funktionale Spezifikation |
| `docs/ROTARY.md` | Rotary-Achse (4. Achse) Spezifikation, DeskProto-Ablösung |

---

## Wer entwickelt was

**Markus Birzite (MadGapun)** — Idee, Konzept, Architektur, Anforderungen, CNC-Fachwissen
- Senior PLM/PDM Architekt mit 20+ Jahren Erfahrung
- CNC-Praktiker: ProVerXL 4030 V2 mit Rotationsachse, Laser, Drechseln
- Hat begrenzte Programmiererfahrung — formuliert Anforderungen klar
- Kommuniziert auf Deutsch, "du"-Form, ohne Füllworte

**Claude (das bist du)** — Entwicklung, Code, Tests, Dokumentation, Erklärungen
- Hauptentwickler. Schreibt Backend, Frontend, MCP-Server
- Erklärt Entscheidungen — keine Black-Box-Implementierungen
- Dokumentiert mit
- Spricht Deutsch im Default, da Markus Deutsch spricht

---

## Architektur-Entscheidungen (NICHT mehr verhandeln)

Diese sind nach längerer Diskussion getroffen und sollten beibehalten werden:

1. **Electron-App** (nicht Browser-Only)
2. **Python-Backend** (Flask, SQLAlchemy, ezdxf, shapely)
3. **React 19 Frontend** (Vite, Tailwind)
4. **Monaco-Editor** für G-Code Editing
5. **Konva.js** für 2D-Zeichnen
6. **Three.js** für 3D-Simulation (Phase 2)
7. **SQLite** für lokale Persistenz
8. **MCP-Server** in Python (FastMCP) wie bei PBP
9. **DE-zuerst, EN als zweite Sprache** (i18next)
10. **GRBL als erster Postprozessor**, Plugin-System für weitere

---

## Code-Konventionen

### Python (Backend)
- Python 3.11+
- `pydantic` für Datenmodelle
- Type-Hints überall
- `pytest` für Tests
- Docstrings auf Deutsch

### React (Frontend)
- TypeScript empfohlen
- Functional Components mit Hooks
- `zustand` für State Management
- Komponenten-Strings über i18next (NICHT inline hardcoden)
- Translation-Keys auf Deutsch (z.B. `t('operation.tasche.titel')`)

### Tests
- Backend: pytest mit aussagekräftigen Test-Namen auf Deutsch
- Frontend: vitest + React Testing Library

---

## Beziehung zu PBP

CAMWOSA ist ein **eigenständiges ELWOSA-Projekt**, parallel zu PBP. Die Architektur-Muster sind ähnlich (lokales Tool, MCP-Integration, Electron/React/Python), aber die Codebasen sind getrennt.

**Was von PBP übernommen werden kann:**
- Installer-Struktur (Cross-Platform Bash/PowerShell)
- MCP-Server-Aufbau (FastMCP-Patterns)
- Update-Mechanismus
- i18n-Setup
- Setting-GUI-Patterns

**Was NICHT übernommen wird:**
- PBP-spezifische Datenmodelle
- PBP-Tools (Bewerbungen, Stellen, etc.)

---

## Markus' Maschine: Genmitsu ProVerXL 4030 V2

Wichtigste Details die im Code abgebildet sein müssen:

| Parameter | Wert |
|---|---|
| Arbeitsraum (Standard) | 400 × 400 × 110 mm |
| Controller | GRBL 1.1 |
| Spindel | Makita RT0700 |
| RPM-Range | 10.000 - 30.000 |
| Vorschub max | 3000 mm/min |
| Rotary-Setup | Y-Achse umgemappt, $101=88.889 steps/deg |
| Rotary-Macros | ROTARY EIN/AUS in CNCjs vorhanden |

---

## Wichtige Memory-Regeln (aus Markus' Setup)

1. **Echte Umlaute verwenden** (ü, ä, ö, ß) — nie ue/ae/oe/ss substitutionen
2. **Windows-Pfade**: Markus arbeitet auf Windows, Desktop Commander statt Linux-Container
3. **GitHub-Umlaute-Bug**: Bei Issues mit Umlauten erst create dann update (Workaround)
4. **PowerShell**: Keine While-Loops (-Recurse nutzen), ASCII-safe Encoding
5. **Issues sofort anlegen** wenn Bugs auffallen, nicht warten bis gefragt wird

---

## Roadmap

### Phase 1 — MVP (jetzt im Fokus)
- Electron + Python-Backend (Issue #6)
- DXF-Import (#1)
- Integriertes Zeichnen (#7)
- Operationen: Kontur, Tasche, Bohren (#1 Folge-Issues)
- Feeds & Speeds Rechner (#3)
- 2D-Toolpath-Preview (#2)
- Sicherheits-Checks (#11)
- G-Code Generator GRBL (#4)
- G-Code Editor (#8)
- Projekt-Management (#9)
- DE-UI

### Phase 2 — Tiefe
- STL-Import (#5)
- 3D-Materialabtrag-Simulation
- EN-Übersetzung
- Plugin-System Postprozessoren (#10)

### Phase 3 — Rotary (DeskProto-Ablösung Teil 1)
- Maschinen-Profil mit Modi (Standard/Rotary)
- Rotary-Postprozessor `grbl_genmitsu_rotary_y`
- 4-Achs-Indexing
- Wrapping (2D auf Zylinder)
- Sicherheits-Checks für Rotary

### Phase 4 — Drechseln (DeskProto-Ablösung Teil 2)
- Drechsel-Operationen
- Plandrehen, Längsdrehen
- Spirale/Helix
- Drechsel-spezifische Werkzeuge

### Phase 5 — Pro
- Werkzeug-Standzeit-Tracking
- Kollisionsanalyse Werkzeughalter
- Adaptive Clearing
- Community-Sharing für Tools/Materials

---

## Vorgehen bei der Implementation

Beim ersten Code-Schritt: **Erst Backend-Kern**, dann UI drumherum.

Empfohlene Reihenfolge Phase 1:
1. Repository-Struktur anlegen (backend/, frontend/, electron/, mcp_server/)
2. Backend: DXF-Parser-Modul mit Tests
3. Backend: G-Code-Generator-Modul mit Tests
4. Backend: Flask-API mit Endpoints
5. Electron-App-Skelett
6. React-UI: Erste Ansicht (DXF laden, anzeigen)
7. Operationen: Kontur als erste Operation
8. G-Code-Generierung mit GRBL-Postprozessor
9. 2D-Toolpath-Preview
10. Sicherheits-Checks
11. G-Code-Editor
12. Projekt speichern/laden

Parallel: Tests, MCP-Tools, Internationalisierung.

---

## Kommunikation mit Markus

- **Erklärungen statt nur Code:** Markus hat begrenzte Coding-Erfahrung, will aber verstehen was passiert
- **Schritt-für-Schritt-Anleitungen** bei manuellen Eingriffen
- **Ehrliche Trade-offs aufzeigen:** wenn etwas suboptimal ist, sagen warum
- **Fragen bei Unklarheit:** lieber nachfragen als raten
- **GitHub-Issues nutzen** für strukturierte Arbeit

---

> An ELWOSA Project
