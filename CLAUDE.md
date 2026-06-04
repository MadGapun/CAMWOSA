# CLAUDE.md — Projekt-Kontext für Claude Code

Dieses Dokument hilft Claude Code beim Einstieg in dieses Repository. Lies es vor der ersten Implementierungs-Session vollständig.

---

## Projekt auf einen Blick

**CAMWOSA** ist ein 2.5D CAM-Tool für GRBL-basierte CNC-Maschinen, speziell die Genmitsu ProVerXL 4030 V2. Es soll mittelfristig sowohl EstlCAM (für 2.5D) als auch DeskProto (für Rotary) ersetzen.

**Aktueller Status:** Phase 1 (MVP) weitgehend umgesetzt, Phase 5 partiell vorgezogen. Backend hat 325 grüne Tests, Frontend ist gebaut aber noch nicht von Markus ausgeführt-getestet. Aktuelle Schwerpunkte siehe `STATUS.md` im Repo.

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
| Spindel | 1,5 kW luftgekühlt mit VFD (ER11) — davor SainSmart 710 W Router (ersetzte Original-Spindel) |
| RPM-Range | 6.000 - 24.000 (einstellbar; alle Spindel-Werte UI-editierbar) |
| Spindel-Hochlauf | manueller Warmlauf ~10 s; G4-Dwell vor Erstschnitt ~3 s (VFD-Accel) |
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

Detaillierter Status siehe `STATUS.md`. Hier nur die Phasen-Übersicht:

### Phase 1 — MVP ✅ weitgehend fertig
- Backend (Flask + pydantic + ezdxf + shapely + trimesh)
- DXF-Import + CAD-Plugin-System (auch SVG/STL/STEP)
- Integriertes Zeichnen (Konva, mit Snap-Grid)
- Operationen: Kontur, Tasche, Bohren, Gravur, Relief, Spezial, PCB
- Per-Feature-Override-System (jedes Feld einzeln überschreibbar mit Quellen-Tracking)
- Feeds & Speeds Rechner
- 2D-Toolpath-Preview mit tiefem Zoom (1 % – 100 000 %)
- Sicherheits-Checks (G0-im-Material, Arbeitsraum, RPM, Plunge-Vorschub, Halter-Kollision)
- G-Code Generator GRBL inkl. Multi-Werkzeug-Strategie
- G-Code Editor (Monaco)
- Projekt-Management (.cwp ZIP-Container)
- DE-UI mit i18next, Density/Theme-Switcher, Fokus-Modus
- MCP-Server mit 40+ Tools (volle Parität zur UI)

### Phase 2 — Tiefe ✅ **fertig**
- STL-Import ✅ (CAD-Plugin)
- 3D-Materialabtrag-Simulation ✅ Voxel-basiert (numpy + Three.js InstancedMesh) — eigene View „Material-Abtrag". Marching-Cubes als optionale Verbesserung mid-term.
- EN-Übersetzung ✅ (Locale-Dateien existieren)
- Plugin-System Postprozessoren ✅

### Phase 3 — Rotary ✅
- 3,5-Achs Rotary-Profil (Y wird umgemappt)
- Rotary-Postprozessor `grbl_genmitsu_rotary_y`
- 4-Achs-Indexing + Wrapping
- Rotary-Sicherheits-Checks
- Rotary-Profil-System (mit/ohne Reitstock, durchschiebbar)

### Phase 4 — Drechseln ✅ **fertig**

Technisch: 4-Achs-Fraesen mit Werkstueck-Rotation (kein klassisches Drechseln).
Fraeser haengt vertikal von oben, Werkstueck dreht langsam darunter durch.

- 4 Strategien: Schruppen, Schlichten, Schrupp+Schlicht, Helix
- Rotary-Postprozessor erkennt Drechsel-Toolpaths automatisch (Setup-Header mit Drehzahl, Helix-Sync-Vorschub)
- Frontend-Profil-Editor mit Konva-Halbschnitt + Three.js Revolution-Preview
- A-Drehung wird NICHT automatisch geschaltet (Markus' Anforderung: kein direkter Sender-Push) — User startet ROTARY-Macro manuell
- **Innen-Drechseln hardware-bedingt unmoeglich** (Spindel haengt vertikal) — nicht auf der Roadmap
- Offen: Werkzeug-Eingriffsbreite-Modellierung

### Phase 5 — Pro (teilweise vorgezogen)
- Werkzeug-Standzeit-Tracking ✅
- Kollisionsanalyse Werkzeughalter ✅ (Segment-basiert für Gravurstichel)
- Adaptive Clearing ✅
- Community-Sharing für Tools/Materials/Spindeln/Rotary-Profile/Presets ✅ (Bundle-Pattern)
- Werkzeug-Editor + Material-Editor + CuttingPreset-Editor ✅
- Annotation-System (Anschlagbohrungen nachträglich, Auto-Operation-Generierung) ✅

### Konzeptuell neu (nicht in der ursprünglichen Roadmap)
- ArbeitsSchritt-Konzept (flexible Multi-Schritt-Workflows pro Setup) ✅
- QuickCAM-Templates (in <60 s zum lauffähigen Projekt) ✅
- WerkzeugWechselStrategie (separate Datei / inline M6 / inline Makro) ✅
- Design-System mit 3 Densities (10" Tablet bis 34" Curved) ✅
- Fokus-Modus + collapsible Sidebar/Topbar/StatusBar ✅

---

## Vorgehen bei der Implementation

Backend-Kern + Tests sind etabliert. Der typische Flow für neue Features:

1. **Datenmodell** in `backend/camwosa/db/models.py` oder `project/schema.py` (pydantic, deutsche Felder, rückwärts-kompatibel via Defaults)
2. **Algorithmus/Generator** in einem eigenen Modul (`workflow/`, `cam/`, `quickcam/`, etc.) mit pytest
3. **API-Endpoint** in `backend/camwosa/api/endpoints/` + Blueprint-Registrierung in `app.py`
4. **API-Test** in `backend/tests/api/`
5. **Frontend-Client** in `frontend/src/api/client.ts`
6. **Editor-Komponente** in `frontend/src/editor/` falls eigener Editor nötig
7. **View-Integration** in `frontend/src/views/`
8. **MCP-Tool** in `mcp_server/camwosa_mcp/server.py` (Parität zur UI Pflicht)
9. **Wiki-Seite** in `docs/wiki/` + Eintrag in `Home.md`
10. **Volle pytest-Suite** muss grün bleiben (aktuell 325 Tests)
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
