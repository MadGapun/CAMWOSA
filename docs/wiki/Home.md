# CAMWOSA Wiki

Willkommen im CAMWOSA-Wiki. Dieses Wiki ist die zentrale Dokumentation des Projekts. **Jede umgesetzte Funktion hat einen eigenen Wiki-Eintrag** — ohne Wiki-Eintrag wird keine Funktion als fertig betrachtet.

> **Hinweis zur Wiki-Struktur:** Dieses Wiki liegt aktuell als Markdown-Sammlung unter `docs/wiki/` im Repository. Damit ist es versionskontrolliert, in Pull Requests reviewbar und mit dem Code-Stand synchron. Sobald das GitHub-Wiki einmalig initialisiert wurde (manuell auf GitHub: Wiki-Tab → "Create the first page"), wird der Inhalt 1:1 in das GitHub-Wiki gespiegelt.

---

## Übersicht

### Projekt
- [Master-Implementierungsplan](Master-Plan.md) — Schritt-für-Schritt-Plan aller Funktionen
- [Plan-Optimierung](Master-Plan-Optimierung.md) — Analyse, Trade-offs und Optimierungen am Plan
- [Architektur](Architektur.md) — Tech-Stack und Komponenten
- [Glossar](Glossar.md) — Begriffe aus CAM, CNC und CAMWOSA-spezifisch
- [Contribution-Guide](Contribution.md) — Wie man am Projekt mitarbeitet

### Aktueller Stand
- [**STATUS.md**](../../STATUS.md) — Live-Snapshot was läuft, was offen ist (Modul-Tabelle, Test-Stand, nächste Schritte)

### Funktionen

#### Daten & Stammdaten
- [Datenmodell](Datenmodell.md) — Maschinen, Werkzeuge, Material, Projekt
- [Spindel](Spindel.md) — Multi-Spindel + Sharing
- [Maschinenprofil-Format](Maschinenprofil-Format.md) — JSON-Schema
- [CuttingPreset](CuttingPreset.md) — Schnittparameter als Top-Level-Entitaet
- [CRUD-API](CRUD-API.md) — POST/PUT/DELETE für alle Stammdaten
- [Werkzeug-Format](Werkzeug-Format.md) / [Werkzeug-Typen](Werkzeug-Typen.md)
- [Material-Holz](Material-Holz.md) · [Holzwerkstoffe](Material-Holzwerkstoffe.md) · [Kunststoffe](Material-Kunststoffe.md) · [NE-Metalle](Material-NE-Metalle.md) · [Sonstiges](Material-Sonstiges.md)

#### CAD-Import + Zeichnen
- [CAD-Import](CAD-Import.md) — Plugin-System für DXF/SVG/STL/STEP
- [DXF-Import](DXF-Import.md) · [STL-Import](STL-Import.md)
- [Integriertes Zeichnen](Zeichnen.md) — Konva, 2D-CAD
- [Geometrie-Annotationen](Geometrie-Annotationen.md) — Anschlagbohrungen, Refpunkte, Auto-Op-Generator

#### CAM-Operationen
- [Operation Kontur](Operation-Kontur.md) — Innen-/Außenkontur, Tabs, Lead
- [Operation Tasche](Operation-Tasche.md) — Pocketing-Strategien
- [Operation Bohren](Operation-Bohren.md) — Drilling-Zyklen
- [Operation Gravur](Operation-Gravur.md) — Gravur + V-Carving
- [Operation Relief](Operation-Relief.md) — 2.5D-Relief aus STL
- [Drechseln](Drechseln.md) — Continuous-Lathe-Mode, rotationssymmetrische Werkstuecke (Vasen, Schalen, Drechsel-Saeulen)
- [Wrap-Mode](Wrap-Mode.md) — 2D-Design auf Zylinder wickeln (Schriftzug/Logo/Kontur auf Rundmaterial)
- [Bild-zu-Relief](Bild-zu-Relief.md) ✅ Phase A+B+C+D+E — Bild→Heightmap, Wrap auf Zylinder, 6 Bearbeitungsfilter, optional AI-Tiefenschaetzung
- [Text-zu-Pfad](Text-zu-Pfad.md) ✅ — Font → Outline-Polygone fuer Beschriftung/Wrap/Gravur
- [Spezial-Operationen](Spezial-Operationen.md) — Uebersicht ueber T-Nut/Schwalbenschwanz/Fase + Module unten
- [Dogbone-Slots](Dogbone-Slots.md) — Innenecken aufweiten fuer Steckverbindungen
- [Lithophane](Lithophane.md) — durchscheinendes Bild im Material (Backlight-Effekt)
- [Drag-Engraving](Drag-Engraving.md) — Diamantgravierer/Schleppgravierer mit Spindel-AUS + Ecken-Dwell
- [Auto-Inlay](Auto-Inlay.md) — Tasche+Plug aus EINER Kontur (Einlegearbeit)
- [Thread-Milling](Thread-Milling.md) — Gewindefraesen mit Helix-Bewegung
- [Circular+Radial Pocketing](Circular-Radial-Pocketing.md) — Spiral- und Strahlen-Tasche
- [PCB-Fraesen](PCB-Fraesen.md) — Isolation
- [Adaptive-Clearing](Adaptive-Clearing.md) — Trochoidal
- [Bohrbild-Erkennung](Bohrbild-Erkennung.md) — Raster/Polar
- [Operations-Plugins](Operations-Plugins.md) — eigene Operations-Typen
- [Per-Feature-Override](Per-Feature-Override.md) — pro Operation überschreiben
- [Feeds & Speeds Rechner](Feeds-Speeds.md)

#### Workflow
- [Multi-Setup Workflow](Workflow-Modul.md) — mehrere Aufspannungen + Arbeitsplan
- [ArbeitsSchritt](ArbeitsSchritt.md) — flexible Workflow-Schritte
- [Multi-Werkzeug-Setup](Multi-Werkzeug-Setup.md) — Schruppen + Schlichten mit G-Code-Strategie
- [QuickCAM](QuickCAM.md) — Schnellstart-Templates
- [Standzeit-Tracking](Standzeit-Tracking.md)

#### G-Code
- [GRBL-Postprozessor](Postprozessor-GRBL.md) · [Genmitsu-Spezial](Postprozessor-GRBL-Genmitsu.md) · [Rotary](Postprozessor-GRBL-Rotary.md)
- [Postprozessor-Plugins](Postprozessor-Plugins.md)
- [G-Code-Editor](GCode-Editor.md) — Monaco
- [Sicherheits-Checks](Sicherheits-Checks.md)
- [Z-Grid-Diagnose](Z-Grid-Diagnose.md) — Werkstuecks-Ebenheit aus Z-Probing-Daten analysieren
- [Spannmittel](Spannmittel.md) — 8 Spannmittel-Typen mit strukturierten Sperrzonen
- [Run-Lock + Dependency-Graph](Run-Lock.md) — "Im Zweifel laeuft das Programm nicht"

#### Frontend
- [Electron-App](Electron-App.md) · [React-Frontend](Frontend.md)
- [Design-System](Design-System.md) — Tokens, Theme, Density 10"–34", Vorschau-Modi
- [UI-Integration](UI-Integration.md) — welcher Editor in welcher View
- [First-Run-Wizard](First-Run-Wizard.md) — 4-Schritt-Onboarding
- [Tooltip-System](Tooltip-System.md) — 3 Stufen (Wert / Fachbegriff / Coach-Mark)
- [2D-Toolpath-Preview](Preview-2D.md) · [3D-Simulation](Simulation-3D.md)
- [Material-Abtrag-Simulation](Material-Abtrag-Simulation.md) — Voxel-basiert, zeigt fertiges Werkstueck

#### Sonstiges
- [Maschine ProVerXL 4030 V2](Maschine-ProVerXL-4030-V2.md) — Markus' Setup
- [Nesting](Nesting.md) — Verschnittoptimierung
- [Projekt-Format (.cwp)](Projekt-Format.md) — ZIP-Container
- [Varianten](Varianten.md) — mehrere Strategien pro Projekt (geteilte Geometrie, eigene Operationen/Setups/Rohmaterial)
- [Flask-API](API.md)
- [MCP-Server](MCP-Server.md) — Claude-Integration (40+ Tools)
- [MCP-AutoCAM](MCP-AutoCAM.md) — `auto_cam_erstellen`: Claude erzeugt komplette Bearbeitung aus High-Level-Aufgabe
- [Installer](Installer.md)

---

## Status der Implementierung

Den aktuellen Stand pro Funktion findest du in [STATUS.md](../../STATUS.md) (Live-Snapshot) oder im [Master-Plan](Master-Plan.md) (langfristige Roadmap).

---

## Konventionen

- **Sprache:** Deutsch (Code-Identifier auch englisch erlaubt, Doku in DE).
- **Echte Umlaute** verwenden (ü, ä, ö, ß).
- **Windows-Default**, aber alle Skripte cross-platform (PowerShell + Bash).
- **Tests sind Pflicht** — Backend-Module ohne Tests gelten als nicht fertig.
- **Wiki-Eintrag ist Pflicht** — Funktionen ohne Wiki-Eintrag gelten als nicht fertig.
