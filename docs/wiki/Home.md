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

### Funktionen (werden befüllt sobald implementiert)

#### Kern (Backend)
- [Datenmodell](Datenmodell.md) — Maschinen, Werkzeuge, Material, Projekt
- [CAD-Import](CAD-Import.md) — DXF, SVG, STL, STEP + Plugin-System fuer Maker-CAD
- [DXF-Import](DXF-Import.md) — DXF-Parsing mit ezdxf
- [STL-Import](STL-Import.md) — STL für 2.5D-Relief
- [GRBL-Postprozessor](Postprozessor-GRBL.md) — G-Code für GRBL-Maschinen
- [GRBL-Postprozessor (Genmitsu)](Postprozessor-GRBL-Genmitsu.md) — Genmitsu-Spezialitäten
- [GRBL-Postprozessor (Rotary)](Postprozessor-GRBL-Rotary.md) — Y-Achse als Rotationsachse
- [Postprozessor-Plugin-System](Postprozessor-Plugins.md) — Erweiterbarkeit für eigene Postprozessoren
- [CAM-Operation: Kontur](Operation-Kontur.md) — Innen-/Außenkontur, Tabs, Lead-In/Out
- [CAM-Operation: Tasche](Operation-Tasche.md) — Pocketing-Strategien
- [CAM-Operation: Bohren](Operation-Bohren.md) — Drilling-Zyklen
- [CAM-Operation: Gravur](Operation-Gravur.md) — Einfache Gravur und V-Carving
- [CAM-Operation: Relief](Operation-Relief.md) — 2.5D-Relief aus STL
- [Feeds & Speeds Rechner](Feeds-Speeds.md) — Berechnung optimaler Schnittparameter
- [Per-Feature-Override](Per-Feature-Override.md) — pro Operation einzelne Parameter ueberschreiben/zuruecksetzen
- [Sicherheits-Checks](Sicherheits-Checks.md) — Crash-Vermeidung
- [Multi-Setup Workflow](Workflow-Modul.md) — Mehrere Aufspannungen + Arbeitsplan
- [Nesting / Verschnittoptimierung](Nesting.md) — Mehrere Teile auf einer Platte
- [Projekt-Format (.cwp)](Projekt-Format.md) — Speichern, Laden, Varianten
- [Flask-API](API.md) — REST-Endpoints (lokal)

#### Frontend
- [Electron-App](Electron-App.md) — Desktop-Wrapper
- [React-Frontend](Frontend.md) — Aufbau, State, i18n
- [2D-Toolpath-Preview](Preview-2D.md) — Konva-basierte Vorschau
- [3D-Simulation](Simulation-3D.md) — Three.js-basierte Simulation
- [Integriertes Zeichnen](Zeichnen.md) — LightBurn-inspiriertes 2D-CAD
- [G-Code-Editor](GCode-Editor.md) — Monaco-basierter Editor

#### Integration
- [MCP-Server](MCP-Server.md) — Claude-Integration als zweite Bedienoberfläche
- [Installer](Installer.md) — Cross-Platform-Installation

### Maschinen-Profile
- [Genmitsu ProVerXL 4030 V2](Maschine-ProVerXL-4030-V2.md) — Markus' Test-Maschine
- [Maschinen-Profil-Format](Maschinenprofil-Format.md) — Aufbau und Felder

### Material-Datenbank
- [Holz](Material-Holz.md)
- [Holzwerkstoffe](Material-Holzwerkstoffe.md)
- [Kunststoffe](Material-Kunststoffe.md)
- [NE-Metalle](Material-NE-Metalle.md)
- [Sonstiges](Material-Sonstiges.md)

### Werkzeug-Bibliothek
- [Werkzeug-Typen](Werkzeug-Typen.md)
- [Werkzeug-Format](Werkzeug-Format.md)

---

## Status der Implementierung

Den aktuellen Stand pro Funktion findest du im [Master-Plan](Master-Plan.md). Jede dort aufgelistete Funktion hat im Status-Feld einen Hinweis ob sie geplant, in Arbeit oder fertig ist. Sobald eine Funktion fertig ist, ersetzt der zugehörige Wiki-Eintrag den Stub.

---

## Konventionen

- **Sprache:** Deutsch (Code-Identifier auch englisch erlaubt, Doku in DE).
- **Echte Umlaute** verwenden (ü, ä, ö, ß).
- **Windows-Default**, aber alle Skripte cross-platform (PowerShell + Bash).
- **Tests sind Pflicht** — Backend-Module ohne Tests gelten als nicht fertig.
- **Wiki-Eintrag ist Pflicht** — Funktionen ohne Wiki-Eintrag gelten als nicht fertig.
