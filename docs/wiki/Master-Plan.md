# Master-Implementierungsplan

> **Stand:** 15.05.2026 · Lebendiges Dokument · Wird mit jedem Schritt aktualisiert.

Dieser Plan listet **alle Funktionen** die CAMWOSA bekommen wird, in Reihenfolge der Umsetzung. Jede Position verlinkt auf ihren Wiki-Eintrag (Stub solange nicht umgesetzt). Die Reihenfolge ist nach Abhängigkeit sortiert: was unten steht, baut auf dem auf was oben steht.

**Legende Status:**
- ⬜ geplant
- 🟨 in Arbeit
- ✅ fertig (Code + Tests + Wiki-Eintrag)

---

## Teil A — Fundament (Backend-Kern, keine UI)

| Nr | Funktion | Issue | Wiki | Status |
|----|----------|-------|------|--------|
| A1 | Repo-Skelett, Tooling, CI-Vorbereitung | — | [Architektur](Architektur.md) | ⬜ |
| A2 | Datenmodell (Maschine, Werkzeug, Material, Projekt) + SQLite | — | [Datenmodell](Datenmodell.md) | ⬜ |
| A3 | DXF-Parser-Modul | [#1](https://github.com/MadGapun/CAMWOSA/issues/1) | [DXF-Import](DXF-Import.md) | ⬜ |
| A4 | GRBL-Postprozessor-Basisklasse + Standard-Implementierung | [#4](https://github.com/MadGapun/CAMWOSA/issues/4) | [Postprozessor-GRBL](Postprozessor-GRBL.md) | ⬜ |
| A5 | Postprozessor-Plugin-Architektur (User-Postprozessoren laden) | [#10](https://github.com/MadGapun/CAMWOSA/issues/10) | [Postprozessor-Plugins](Postprozessor-Plugins.md) | ⬜ |
| A6 | Postprozessor: GRBL Genmitsu | [#10](https://github.com/MadGapun/CAMWOSA/issues/10) | [Postprozessor-GRBL-Genmitsu](Postprozessor-GRBL-Genmitsu.md) | ⬜ |
| A7 | Geometrie-Hilfsmodul (shapely-Wrapper, Offset, Boolean) | — | [Geometrie](Geometrie.md) | ⬜ |
| A8 | CAM-Operation: Kontur (Innen/Außen/auf Linie, Tabs, Stepdown, Lead-In/Out, Climb/Conventional) | [#1](https://github.com/MadGapun/CAMWOSA/issues/1) | [Operation-Kontur](Operation-Kontur.md) | ⬜ |
| A9 | CAM-Operation: Tasche (Parallel/Spiral/Adaptive/Offset, Inseln, Schlichtgang) | [#1](https://github.com/MadGapun/CAMWOSA/issues/1) | [Operation-Tasche](Operation-Tasche.md) | ⬜ |
| A10 | CAM-Operation: Bohren (Standard/Peck/Tief-Peck/Helix/Reib) | [#1](https://github.com/MadGapun/CAMWOSA/issues/1) | [Operation-Bohren](Operation-Bohren.md) | ⬜ |
| A11 | CAM-Operation: Gravur (konstante Tiefe + V-Carving) | [#1](https://github.com/MadGapun/CAMWOSA/issues/1) | [Operation-Gravur](Operation-Gravur.md) | ⬜ |
| A12 | Material-Datenbank (Holz, Holzwerkstoffe, Kunststoffe, NE-Metalle) | [#3](https://github.com/MadGapun/CAMWOSA/issues/3) | [Material-Datenbank](Material-Datenbank.md) | ⬜ |
| A13 | Werkzeug-Bibliothek (alle 10 Werkzeug-Typen) | — | [Werkzeug-Bibliothek](Werkzeug-Bibliothek.md) | ⬜ |
| A14 | Feeds & Speeds Rechner | [#3](https://github.com/MadGapun/CAMWOSA/issues/3) | [Feeds-Speeds](Feeds-Speeds.md) | ⬜ |
| A15 | Sicherheits-Checks (alle 6 + Erweiterungen) | [#11](https://github.com/MadGapun/CAMWOSA/issues/11) | [Sicherheits-Checks](Sicherheits-Checks.md) | ⬜ |
| A16 | Maschinen-Profil-Modul + 5 Default-Profile | — | [Maschinenprofil-Format](Maschinenprofil-Format.md) | ⬜ |
| A17 | Rohmaterial-Definition (Quader/Zylinder/Platte/frei) | — | [Rohmaterial](Rohmaterial.md) | ⬜ |
| A18 | Projekt-Format `.cwp` (ZIP, Schema-Version, Auto-Save, Crash-Recovery) | [#9](https://github.com/MadGapun/CAMWOSA/issues/9) | [Projekt-Format](Projekt-Format.md) | ⬜ |
| A19 | Varianten-System innerhalb eines Projekts | [#9](https://github.com/MadGapun/CAMWOSA/issues/9) | [Varianten](Varianten.md) | ⬜ |
| A20 | Multi-Setup Workflow-Modul (Setups, Pausen, Werkzeugwechsel-Bestätigung) | [#13](https://github.com/MadGapun/CAMWOSA/issues/13) | [Workflow-Modul](Workflow-Modul.md) | ⬜ |
| A21 | Arbeitsplan-Generator (PDF + In-UI-Checkliste) | [#13](https://github.com/MadGapun/CAMWOSA/issues/13) | [Arbeitsplan](Arbeitsplan.md) | ⬜ |
| A22 | Nesting-Engine (rectpack + nest2D, Faserrichtung, Sperrzonen) | [#14](https://github.com/MadGapun/CAMWOSA/issues/14) | [Nesting](Nesting.md) | ⬜ |
| A23 | STL-Parser + Heightmap-Berechnung | [#5](https://github.com/MadGapun/CAMWOSA/issues/5) | [STL-Import](STL-Import.md) | ⬜ |
| A24 | CAM-Operation: 2.5D-Relief (Raster, Konturparallel, 3D-Offset) | [#5](https://github.com/MadGapun/CAMWOSA/issues/5) | [Operation-Relief](Operation-Relief.md) | ⬜ |
| A25 | Maschinen-Modi-Konzept (Standard XYZ vs Rotary) | [#12](https://github.com/MadGapun/CAMWOSA/issues/12) | [Maschinenmodi](Maschinenmodi.md) | ⬜ |
| A26 | Postprozessor: GRBL Rotary Y | [#12](https://github.com/MadGapun/CAMWOSA/issues/12) | [Postprozessor-GRBL-Rotary](Postprozessor-GRBL-Rotary.md) | ⬜ |
| A27 | Rotary-Wrapping (2D-Geometrie auf Zylinder) | [#12](https://github.com/MadGapun/CAMWOSA/issues/12) | [Rotary-Wrapping](Rotary-Wrapping.md) | ⬜ |
| A28 | Rotary-Vorschub-Korrektur (linear → Grad/min am Radius) | [#12](https://github.com/MadGapun/CAMWOSA/issues/12) | [Rotary-Vorschub](Rotary-Vorschub.md) | ⬜ |
| A29 | 4-Achs-Indexing | [#12](https://github.com/MadGapun/CAMWOSA/issues/12) | [Rotary-Indexing](Rotary-Indexing.md) | ⬜ |
| A30 | Drechsel-Operationen (Plandrehen, Längsdrehen, Spirale, Helix) | — | [Drechseln](Drechseln.md) | ⬜ |
| A31 | Backplot-Annotation im G-Code (Operations-Kommentare) | [#8](https://github.com/MadGapun/CAMWOSA/issues/8) | [Backplot-Annotation](Backplot-Annotation.md) | ⬜ |

## Teil B — REST-API + MCP

| Nr | Funktion | Issue | Wiki | Status |
|----|----------|-------|------|--------|
| B1 | Flask-App-Setup (localhost only, CORS, Logging) | — | [API](API.md) | ⬜ |
| B2 | API-Endpoints für alle Backend-Module | — | [API-Endpoints](API-Endpoints.md) | ⬜ |
| B3 | OpenAPI-Spec generieren | — | [API-Endpoints](API-Endpoints.md) | ⬜ |
| B4 | MCP-Server-Setup (FastMCP) | — | [MCP-Server](MCP-Server.md) | ⬜ |
| B5 | MCP-Tools für alle Backend-Funktionen (vollständige Parität mit UI) | — | [MCP-Tools](MCP-Tools.md) | ⬜ |
| B6 | MCP-Tool: `auto_cam_erstellen` (Claude erstellt komplette Bearbeitung) | — | [MCP-AutoCAM](MCP-AutoCAM.md) | ⬜ |

## Teil C — Desktop-App (Electron)

| Nr | Funktion | Issue | Wiki | Status |
|----|----------|-------|------|--------|
| C1 | Electron-Skelett mit Vite/React/TypeScript | [#6](https://github.com/MadGapun/CAMWOSA/issues/6) | [Electron-App](Electron-App.md) | ⬜ |
| C2 | Backend-Subprozess-Management (Start/Stop/Health-Check) | [#6](https://github.com/MadGapun/CAMWOSA/issues/6) | [Electron-App](Electron-App.md) | ⬜ |
| C3 | Datei-Assoziation `.cwp` + OS-Tray | [#6](https://github.com/MadGapun/CAMWOSA/issues/6) | [Electron-App](Electron-App.md) | ⬜ |
| C4 | Auto-Updater | — | [Auto-Updater](Auto-Updater.md) | ⬜ |
| C5 | i18n-Setup (DE/EN, Translation-Keys auf Deutsch) | — | [Frontend](Frontend.md) | ⬜ |
| C6 | State-Management (zustand) | — | [Frontend](Frontend.md) | ⬜ |
| C7 | Tailwind + Komponenten-Bibliothek | — | [Frontend](Frontend.md) | ⬜ |
| C8 | Routing + Layout (Sidebar, Hauptansicht, Properties-Panel) | — | [Frontend](Frontend.md) | ⬜ |

## Teil D — UI-Module

| Nr | Funktion | Issue | Wiki | Status |
|----|----------|-------|------|--------|
| D1 | Maschinen-Verwaltung (Liste, Editor, Profil-Import/Export) | — | [UI-Maschinen](UI-Maschinen.md) | ⬜ |
| D2 | Werkzeug-Verwaltung (Liste, Editor, Material-Presets pro Werkzeug) | — | [UI-Werkzeuge](UI-Werkzeuge.md) | ⬜ |
| D3 | Material-Verwaltung (Liste, Editor, Janka-Sortierung) | — | [UI-Material](UI-Material.md) | ⬜ |
| D4 | Projekt-Verwaltung (Neu/Öffnen/Speichern/Speichern als/Varianten) | [#9](https://github.com/MadGapun/CAMWOSA/issues/9) | [UI-Projekt](UI-Projekt.md) | ⬜ |
| D5 | Rohmaterial-Editor (Form + Position + Nullpunkt) | — | [UI-Rohmaterial](UI-Rohmaterial.md) | ⬜ |
| D6 | DXF/STL-Import-Dialog mit Vorschau | [#1](https://github.com/MadGapun/CAMWOSA/issues/1) [#5](https://github.com/MadGapun/CAMWOSA/issues/5) | [UI-Import](UI-Import.md) | ⬜ |
| D7 | Integriertes Zeichnen (LightBurn-inspiriert, Konva) | [#7](https://github.com/MadGapun/CAMWOSA/issues/7) | [Zeichnen](Zeichnen.md) | ⬜ |
| D8 | Operations-Editor (alle Operations-Typen) | — | [UI-Operationen](UI-Operationen.md) | ⬜ |
| D9 | 2D-Toolpath-Preview (Konva, Tiefen-Vorschau Seitenansicht) | [#2](https://github.com/MadGapun/CAMWOSA/issues/2) | [Preview-2D](Preview-2D.md) | ⬜ |
| D10 | 3D-Materialabtrag-Simulation (Three.js, Voxel) | — | [Simulation-3D](Simulation-3D.md) | ⬜ |
| D11 | Sicherheits-Panel (Status, Klick-zur-Stelle, Blocker-Logik) | [#11](https://github.com/MadGapun/CAMWOSA/issues/11) | [UI-Sicherheits-Panel](UI-Sicherheits-Panel.md) | ⬜ |
| D12 | Workflow-/Setup-Editor (Setups anlegen, Pausen einfügen) | [#13](https://github.com/MadGapun/CAMWOSA/issues/13) | [UI-Workflow](UI-Workflow.md) | ⬜ |
| D13 | Arbeitsplan-Ansicht (PDF-Export + In-UI-Checkliste) | [#13](https://github.com/MadGapun/CAMWOSA/issues/13) | [Arbeitsplan](Arbeitsplan.md) | ⬜ |
| D14 | Nesting-Editor (Teile-Liste, Platten, Drag&Drop, Statistik) | [#14](https://github.com/MadGapun/CAMWOSA/issues/14) | [UI-Nesting](UI-Nesting.md) | ⬜ |
| D15 | Feeds & Speeds Panel (live-berechnet beim Operation-Editing) | [#3](https://github.com/MadGapun/CAMWOSA/issues/3) | [UI-Feeds-Speeds](UI-Feeds-Speeds.md) | ⬜ |
| D16 | G-Code-Editor (Monaco, Befehlsbibliothek, Live-Sync, Outline, Mass-Edit) | [#8](https://github.com/MadGapun/CAMWOSA/issues/8) | [GCode-Editor](GCode-Editor.md) | ⬜ |
| D17 | Settings (Theme, Sprache, Pfade, Update-Verhalten, KI-Features) | — | [UI-Settings](UI-Settings.md) | ⬜ |
| D18 | Foto-Slot pro Setup | [#13](https://github.com/MadGapun/CAMWOSA/issues/13) | [UI-Workflow](UI-Workflow.md) | ⬜ |

## Teil E — Polish und Pro-Features

| Nr | Funktion | Issue | Wiki | Status |
|----|----------|-------|------|--------|
| E1 | EN-Übersetzung | — | [i18n](i18n.md) | ⬜ |
| E2 | Werkzeug-Standzeit-Tracking | — | [Standzeit-Tracking](Standzeit-Tracking.md) | ⬜ |
| E3 | Kollisionsanalyse Werkzeughalter (3D) | — | [Kollisionsanalyse](Kollisionsanalyse.md) | ⬜ |
| E4 | Adaptive Clearing (trochoidal) | — | [Adaptive-Clearing](Adaptive-Clearing.md) | ⬜ |
| E5 | Community-Sharing für Werkzeuge/Materialien (JSON-Austausch + optionaler Cloud-Sync) | — | [Community-Sharing](Community-Sharing.md) | ⬜ |
| E6 | Bohrbild aus DXF-Kreisen automatisch erkennen | — | [Bohrbild-Erkennung](Bohrbild-Erkennung.md) | ⬜ |
| E7 | Spezial-Operationen: T-Nuten, Schwalbenschwanz, Fasen | — | [Spezial-Operationen](Spezial-Operationen.md) | ⬜ |
| E8 | PCB-Isolationsfräsen | — | [PCB-Fraesen](PCB-Fraesen.md) | ⬜ |
| E9 | Plugin-API für Operations (eigene Operations-Typen nachladbar) | — | [Operations-Plugins](Operations-Plugins.md) | ⬜ |

## Teil F — Distribution

| Nr | Funktion | Issue | Wiki | Status |
|----|----------|-------|------|--------|
| F1 | Cross-Platform-Installer (Windows MSI, macOS DMG, Linux AppImage/deb) | — | [Installer](Installer.md) | ⬜ |
| F2 | Python-Backend gebündelt (PyInstaller / py2app) | — | [Installer](Installer.md) | ⬜ |
| F3 | Code-Signing (Windows + macOS) | — | [Installer](Installer.md) | ⬜ |
| F4 | GitHub Actions: Build + Release-Pipeline | — | [CI-CD](CI-CD.md) | ⬜ |
| F5 | Auto-Updater-Backend | — | [Auto-Updater](Auto-Updater.md) | ⬜ |

---

## Reihenfolge-Logik

**Warum erst Backend, dann UI?**
Weil die UI an die Backend-API andockt. Wenn die API steht, kann die UI parallel und unabhängig entwickelt werden — das MCP nutzt dieselbe API. Ohne Backend keine UI.

**Warum Postprozessor vor Operations?**
Weil eine Operation als Test "G-Code raus" produziert. Ohne Postprozessor kann ich Operations nicht testen.

**Warum Datenmodell zuerst?**
Maschine, Werkzeug, Material sind in praktisch allen anderen Modulen Eingaben. Wenn das nicht steht, baut man Mocks und tauscht sie später wieder.

**Warum Rotary erst Teil A Ende?**
Weil Rotary auf Standard-CAM aufbaut. Ein Wrapping nimmt 2D-Geometrie und mappt sie. Die 2D-Geometrie muss erst funktionieren.

**Warum Nesting in Teil A?**
Weil Nesting Backend-Logik ist (Algorithmen). Die UI ist später Teil D14.

---

## Was nicht im Plan steht (bewusst aus Scope)

Diese Punkte gehören **nicht** zu CAMWOSA — siehe [Architektur > Pure CAM](Architektur.md#pure-cam-keine-maschinen-steuerung):

- Direkte Maschinen-Steuerung (Jog, Job-Send, Probe-Aufruf) → CNCjs
- 5-Achs-CAM
- 3D-Modellierung (parametrisch, BREP) → Solid Edge / Blender
- DWG-Editing
- ERP/PLM-Funktionen
- Cloud-Backend für Projekt-Speicherung (lokal first; optionales Sync für Werkzeug/Material-DB ist E5)

---

## Akzeptanzkriterium pro Position

Eine Position gilt nur als ✅ wenn **alle drei** zutreffen:

1. **Code** ist im Repo, lauffähig
2. **Tests** sind grün (Backend: pytest, Frontend: vitest)
3. **Wiki-Eintrag** existiert mit:
   - Kurzbeschreibung
   - Wie nutzt man die Funktion (Code-Beispiel oder UI-Screenshot)
   - Welche Parameter gibt es
   - Bekannte Einschränkungen
   - Verweis auf Issue + Code-Pfad

Solange ein Punkt fehlt, bleibt die Position 🟨 oder ⬜.

---

## Nächste Schritte

Die nächsten Schritte sind in [Master-Plan-Optimierung](Master-Plan-Optimierung.md) priorisiert und mit Zeitschätzungen versehen.
