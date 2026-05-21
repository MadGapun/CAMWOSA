# Master-Implementierungsplan

> **Stand:** 17.05.2026 · Lebendiges Dokument · Wird mit jedem Schritt aktualisiert.
>
> **Arbeitsprinzip:** Master-Plan-First. Neue Ideen werden erst hier eingeordnet (mit Status ⬜ und ggf. Issue), dann nach Plan abgearbeitet — nicht ad-hoc gebaut und spaeter nachgezogen.

Dieser Plan listet **alle Funktionen** die CAMWOSA bekommen wird, in Reihenfolge der Umsetzung. Jede Position verlinkt auf ihren Wiki-Eintrag (Stub solange nicht umgesetzt). Die Reihenfolge ist nach Abhängigkeit sortiert: was unten steht, baut auf dem auf was oben steht.

**Legende Status:**
- ⬜ geplant
- 🟨 in Arbeit
- ✅ fertig (Code + Tests + Wiki-Eintrag)

---

## Teil A — Fundament (Backend-Kern, keine UI)

| Nr | Funktion | Issue | Wiki | Status |
|----|----------|-------|------|--------|
| A1 | Repo-Skelett, Tooling, CI-Vorbereitung | — | [Architektur](Architektur.md) | ✅ |
| A2 | Datenmodell (Maschine, Werkzeug, Material, Projekt) + SQLite | — | [Datenmodell](Datenmodell.md) | ✅ |
| A3 | DXF-Parser-Modul | [#1](https://github.com/MadGapun/CAMWOSA/issues/1) | [DXF-Import](DXF-Import.md) | ✅ |
| A4 | GRBL-Postprozessor-Basisklasse + Standard-Implementierung | [#4](https://github.com/MadGapun/CAMWOSA/issues/4) | [Postprozessor-GRBL](Postprozessor-GRBL.md) | ✅ |
| A5 | Postprozessor-Plugin-Architektur (User-Postprozessoren laden) | [#10](https://github.com/MadGapun/CAMWOSA/issues/10) | [Postprozessor-Plugins](Postprozessor-Plugins.md) | ✅ |
| A6 | Postprozessor: GRBL Genmitsu | [#10](https://github.com/MadGapun/CAMWOSA/issues/10) | [Postprozessor-GRBL-Genmitsu](Postprozessor-GRBL-Genmitsu.md) | ✅ |
| A7 | Geometrie-Hilfsmodul (shapely-Wrapper, Offset, Boolean) | — | [Geometrie](Geometrie.md) | ✅ |
| A8 | CAM-Operation: Kontur (Innen/Außen/auf Linie, Tabs, Stepdown, Lead-In/Out, Climb/Conventional) | [#1](https://github.com/MadGapun/CAMWOSA/issues/1) | [Operation-Kontur](Operation-Kontur.md) | ✅ |
| A9 | CAM-Operation: Tasche (Parallel/Spiral/Adaptive/Offset, Inseln, Schlichtgang) | [#1](https://github.com/MadGapun/CAMWOSA/issues/1) | [Operation-Tasche](Operation-Tasche.md) | ✅ |
| A10 | CAM-Operation: Bohren (Standard/Peck/Tief-Peck/Helix/Reib) | [#1](https://github.com/MadGapun/CAMWOSA/issues/1) | [Operation-Bohren](Operation-Bohren.md) | ✅ |
| A11 | CAM-Operation: Gravur (konstante Tiefe + V-Carving) | [#1](https://github.com/MadGapun/CAMWOSA/issues/1) | [Operation-Gravur](Operation-Gravur.md) | ✅ |
| A12 | Material-Datenbank (Holz, Holzwerkstoffe, Kunststoffe, NE-Metalle) | [#3](https://github.com/MadGapun/CAMWOSA/issues/3) | [Material-Datenbank](Material-Datenbank.md) | ✅ |
| A13 | Werkzeug-Bibliothek (alle 10 Werkzeug-Typen) | — | [Werkzeug-Bibliothek](Werkzeug-Bibliothek.md) | ✅ |
| A14 | Feeds & Speeds Rechner | [#3](https://github.com/MadGapun/CAMWOSA/issues/3) | [Feeds-Speeds](Feeds-Speeds.md) | ✅ |
| A14b | Per-Feature-Override (pro Operation einzelne Parameter ueberschreiben + zuruecksetzen) | — | [Per-Feature-Override](Per-Feature-Override.md) | ✅ |
| A14c | CAD-Format-System: DXF/SVG/STL/STEP + Plugin-Architektur fuer Maker-CAD (FreeCAD/Fusion/OpenSCAD…) | — | [CAD-Import](CAD-Import.md) | ✅ |
| A14d | Spindel-System (Multi-Spindel pro Maschine, Safety + Feeds&Speeds Spindel-aware) | — | [Spindel](Spindel.md) | ✅ |
| A14e | Maschinen-Profil-Sharing (Bundle-Export/Import inkl. Spindeln) | — | [Maschinenprofil-Format](Maschinenprofil-Format.md) | ✅ |
| A15 | Sicherheits-Checks (alle 6 + Erweiterungen) | [#11](https://github.com/MadGapun/CAMWOSA/issues/11) | [Sicherheits-Checks](Sicherheits-Checks.md) | ✅ |
| A16 | Maschinen-Profil-Modul + 5 Default-Profile | — | [Maschinenprofil-Format](Maschinenprofil-Format.md) | ✅ |
| A17 | Rohmaterial-Definition (Quader/Zylinder/Platte/frei) | — | [Rohmaterial](Rohmaterial.md) | ✅ |
| A18 | Projekt-Format `.cwp` (ZIP, Schema-Version, Auto-Save, Crash-Recovery) | [#9](https://github.com/MadGapun/CAMWOSA/issues/9) | [Projekt-Format](Projekt-Format.md) | ✅ |
| A19 | Varianten-System innerhalb eines Projekts — Backend (`Variante` in schema.py) ✅ + Frontend-VarianteSwitcher in Topbar mit Snapshot-Logik + Verwaltungs-Modal ✅ | [#9](https://github.com/MadGapun/CAMWOSA/issues/9) | [Varianten](Varianten.md) | ✅ |
| A20 | Multi-Setup Workflow-Modul (Setups, Pausen, Werkzeugwechsel-Bestätigung) | [#13](https://github.com/MadGapun/CAMWOSA/issues/13) | [Workflow-Modul](Workflow-Modul.md) [ArbeitsSchritt](ArbeitsSchritt.md) [Multi-Werkzeug-Setup](Multi-Werkzeug-Setup.md) | ✅ |
| A21 | Arbeitsplan-Generator (PDF + In-UI-Checkliste) | [#13](https://github.com/MadGapun/CAMWOSA/issues/13) | [Arbeitsplan](Arbeitsplan.md) | ✅ |
| A22 | Nesting-Engine (rectpack + nest2D, Faserrichtung, Sperrzonen) | [#14](https://github.com/MadGapun/CAMWOSA/issues/14) | [Nesting](Nesting.md) | ✅ |
| A23 | STL-Parser + Heightmap-Berechnung | [#5](https://github.com/MadGapun/CAMWOSA/issues/5) | [STL-Import](STL-Import.md) | ✅ |
| A24 | CAM-Operation: 2.5D-Relief (Raster, Konturparallel, 3D-Offset) | [#5](https://github.com/MadGapun/CAMWOSA/issues/5) | [Operation-Relief](Operation-Relief.md) | ✅ |
| A25 | Maschinen-Modi-Konzept (Standard XYZ vs Rotary) | [#12](https://github.com/MadGapun/CAMWOSA/issues/12) | [Maschinenmodi](Maschinenmodi.md) | ✅ |
| A26 | Postprozessor: GRBL Rotary Y | [#12](https://github.com/MadGapun/CAMWOSA/issues/12) | [Postprozessor-GRBL-Rotary](Postprozessor-GRBL-Rotary.md) | ✅ |
| A27 | Rotary-Wrapping (2D-Geometrie auf Zylinder) | [#12](https://github.com/MadGapun/CAMWOSA/issues/12) | [Rotary-Wrapping](Rotary-Wrapping.md) | ✅ |
| A28 | Rotary-Vorschub-Korrektur (linear → Grad/min am Radius) | [#12](https://github.com/MadGapun/CAMWOSA/issues/12) | [Rotary-Vorschub](Rotary-Vorschub.md) | ✅ |
| A29 | 3,5-Achs-Indexing (Y wird durch Drehung ersetzt) | [#12](https://github.com/MadGapun/CAMWOSA/issues/12) | [Rotary-Indexing](Rotary-Indexing.md) | ✅ |
| A30 | Drechsel-Operationen (Plandrehen, Längsdrehen, Spirale, Helix) — Continuous-Lathe + 4 Strategien + Postprozessor + Frontend-Profil-Editor | — | [Drechseln](Drechseln.md) [Wrap-Mode](Wrap-Mode.md) | ✅ |
| A31 | Backplot-Annotation im G-Code (Operations-Kommentare) | [#8](https://github.com/MadGapun/CAMWOSA/issues/8) | [Backplot-Annotation](Backplot-Annotation.md) | ✅ |
| A32 | Wrap-Mode-Generator (cam/wrap.py) — 2D-Pfad → Y→A-Umrechnung + Pattern-Skalierung auf Werkstueck | — | [Wrap-Mode](Wrap-Mode.md) | ✅ |
| A33 | Bild-zu-Heightmap — Phase A: Grayscale-Bild → Heightmap (stl/bild_heightmap.py), API + MCP, kompatibel zu cam/relief.py | — | [Bild-zu-Relief](Bild-zu-Relief.md) | ✅ |
| A34 | Bild-zu-Relief — Phase C: Wrap-Kombination, Heightmap auf Zylinder (`erzeuge_wrap_relief_toolpath` in cam/wrap.py + 2 API-Endpoints + 12 Tests) | [#16](https://github.com/MadGapun/CAMWOSA/issues/16) | [Bild-zu-Relief](Bild-zu-Relief.md#wrap-kombination-✅-fertig-phase-c) | ✅ |
| A35 | Bild-zu-Relief — Phase D Backend: 6 Heightmap-Filter (Gamma, Histogramm-Stretch, Zero-Plane, Edge-Boost, Selective-Smoothing, Detail-Slider) + 6 API-Endpoints + 22 Tests | [#17](https://github.com/MadGapun/CAMWOSA/issues/17) | [Bild-zu-Relief](Bild-zu-Relief.md#stufe-2-heightmap-bild--vorverarbeitung-✅-backend-fertig-phase-d) | ✅ |
| A36 | Bild-zu-Relief — Phase E (`[ai]`-Extra): AI-Tiefenschaetzung Scaffolding (Depth-Anything-V2 + MiDaS via HuggingFace transformers, Lazy-Import, 3 Modelle, API `/aus-bild-ai` + `/ai/modelle`, 422+Hinweis ohne Extra, 9 Tests + 1 Integration-Smoke) | [#18](https://github.com/MadGapun/CAMWOSA/issues/18) | [Bild-zu-Relief](Bild-zu-Relief.md#stufe-3-ai-basierte-tiefenbild-generierung-anspruchsvoll) | ✅ |
| A37 | Text-zu-Pfad-Konverter (fontTools-basiert, System-Font-Fallback, Loch-Erkennung via Contains-Hierarchie, integriert in `auto_cam_erstellen.beschriftung_wrap`, 2 API-Endpoints + 18 Tests) | [#19](https://github.com/MadGapun/CAMWOSA/issues/19) | [Text-zu-Pfad](Text-zu-Pfad.md) · [Wrap-Mode](Wrap-Mode.md) | ✅ |
| A38 | DXF-Import in Wrap-Editor: Backend-Skalierungs-Helper `skaliere_pattern_fuer_werkstueck` (3 Modi: feste/auf_werkstueck/wiederholen) + Batch-Toolpath fuer Polygon-Listen + 2 API-Endpoints + 18 Tests. Frontend-Integration ist D24/Wrap-View | [#20](https://github.com/MadGapun/CAMWOSA/issues/20) | [Wrap-Mode](Wrap-Mode.md#pattern-skalierung-master-plan-a38) | ✅ |
| A39 | Werkzeug-Typen-Erweiterung: V-Bit-Spitzenwinkel-Range 1-179° (statt 10-180), neuer Typ `BALLNOSE_V_BIT` mit Pflicht-Feldern `spitzenwinkel` + `spitzendurchmesser`. Plus `DRAG_GRAVIERER`-Typ (E6). Validator + 11 Tests. **Default-Werkzeuge** und Operations-Anpassung folgen separat. | [#24](https://github.com/MadGapun/CAMWOSA/issues/24) | [Werkzeug-Typen](Werkzeug-Typen.md) | ✅ |
| A40 | Drehen: 3D-Modell als Quelle (STL/OBJ/STEP) statt nur 2D-Halbschnitt. Sub-Stufen: (a) Import + Ausrichtung, (b) Nullpunkt + Fixpunkte/Spannfutter, (c) Profil-Extraktion fuer rotationssymmetrische Modelle, (d) 3D-Strategien (Konturschale + Schlichten), (e) Multi-Index fuer asymmetrische Modelle. Grosser Brocken, analog zu Bild-zu-Relief-Pipeline. | [#31](https://github.com/MadGapun/CAMWOSA/issues/31) | [Drechseln](Drechseln.md) | ⬜ |
| A41 | Werkzeug-Typen-Wiki neu — 12 Typen (inkl. BALLNOSE_V_BIT + DRAG_GRAVIERER) mit ASCII-Skizze + Anwendung + Pflichtfelder + Empfehlungen. Audit-Tabelle (TORUSFRAESER/BOHRER/GRAVIERSTICHEL brauchen noch Validator-Refinement). Markus' Fischschwanz-Frage explizit beantwortet. SVG-Skizzen folgen in D34. | [#32](https://github.com/MadGapun/CAMWOSA/issues/32) | [Werkzeug-Typen](Werkzeug-Typen.md) | ✅ |
| A42 | Vector-Operations vervollstaendigen — Profiling 3 Strategien (Outside/Inside/OnCurve) + Cutting-Direction (Climb/Conventional/Shortest/Original/Reversed), Pocketing-Detail (Offset/Parallel Outside-in/Inside-out/Alternating + Stepover% + Angle + Finishing-Profile-Path), V-Carving-Cleanup (Depth-Limit + Flat-Bottom-Stepover + Auto-Cleanup-Operation), Allowance/Skin pro Vector-Op. | [#35](https://github.com/MadGapun/CAMWOSA/issues/35) | [Operation-Kontur](Operation-Kontur.md) · [Operation-Tasche](Operation-Tasche.md) · [Operation-Gravur](Operation-Gravur.md) | ⬜ |
| A43 | 3D-Strategien — **Waterline** ✅ (alpha.3), **Circular Pocketing** ✅ (alpha.5 `cam/circular_radial.py`, 6 Tests), **Radial Pocketing** ✅ (alpha.5, 6 Tests). Offset/Pencil-Trace folgen in spaeteren Stufen. | [#36](https://github.com/MadGapun/CAMWOSA/issues/36) | [Operation-Relief](Operation-Relief.md) | 🟨 |
| A44 | Workflow-Patterns — Two-Sided (manual flip) mit Wizard + Border/Tab/Reference-Planes/Report-File · Indexed (N-Sided rotary) Wizard mit 2-99 Parts · Combined-Project (Vector+Geometry+Bitmap in einem Projekt mit Cross-Referenz) · Vector-/Bitmap-auf-3D-projizieren (Logo auf Vase, Foto auf Schluesselanhaenger). Stufen C1-C6. | [#37](https://github.com/MadGapun/CAMWOSA/issues/37) | [Workflow-Modul](Workflow-Modul.md) | ⬜ |
| A45 | Spezial-Operationen — **E3 Dogbone-Slots** ✅ (alpha.3), **E8 Lithophane** ✅ (alpha.3), **Chamfering** ✅ (alpha.3 `cam/chamfer.py`), **Auto-Inlay** ✅ (alpha.5 `cam/auto_inlay.py`, 12 Tests), **Thread-Milling** ✅ (alpha.5 `cam/thread_milling.py`, 9 Tests), **Drag-Engraving** ✅ (alpha.5 `cam/drag_engraving.py`, 12 Tests). V-Carve-Inlay + Rest-Machining folgen in spaeteren Stufen. | [#39](https://github.com/MadGapun/CAMWOSA/issues/39) | [Spezial-Operationen](Spezial-Operationen.md) | 🟨 |
| A46 | Cutter-Modellierung erweitert — `free_length_mm` (Collet-Distanz, Default = gesamtlaenge), `auto_set_speeds: bool` + `auto_feedrate` + `auto_spindel_rpm` fuer Werkzeug-Wahl, neuer Typ `DRAG_GRAVIERER` (E6 — Diamant ohne Spindel-Drehung). Multi-Diameter via `segmente` ist schon vorhanden. **Tests: 11 neue.** Special-Cutters (Disk/Saege/Hot-Wire) sind separate Erweiterung. | [#40](https://github.com/MadGapun/CAMWOSA/issues/40) | [Werkzeug-Bibliothek](Werkzeug-Bibliothek.md) | ✅ |
| A47 | Sicherheit/Workholding — **Spannmittel-Modell** ✅ (alpha.3), Collet-Check via `free_length_mm` (alpha.3), **Z-Grid-Diagnose-Tool** ✅ (alpha.5 `diagnostics/z_grid.py`, eigener Plane-Fit ohne numpy, 4 Befund-Stufen, 10 Tests). Reference-Planes + Collet-3D-Visualisierung in spaeteren Stufen. | [#42](https://github.com/MadGapun/CAMWOSA/issues/42) | [Sicherheits-Checks](Sicherheits-Checks.md) | 🟨 |
| A48 | Projekt-Modell Dirty-Tracking — `OperationStatus` Enum (NEU/OK/DIRTY/BROKEN), `input_hash` + `letzte_berechnung` + `fehler_text` pro Operation. `workflow/run_lock.py` mit `darf_gcode_generieren()` + `pruefe_projekt()` + `markiere_abhaengige_dirty()` + `operation_input_hash()`. API-Endpoint `POST /api/workflow/run-lock`. **Markus' Regel: „Im Zweifel laeuft das Programm nicht."** 22 neue Tests. Schema-Version v2. Frontend-Visualisierung folgt in D35. | [#43](https://github.com/MadGapun/CAMWOSA/issues/43) | [Projekt-Format](Projekt-Format.md) · [Workflow-Modul](Workflow-Modul.md) | ✅ |
| A49 | Multi-Setup mit **Werkstueck-Transformation** (Rotation/Spiegelung zwischen Setups, nicht nur Nullpunkt-Verschiebung) + **Maschinen-Umbau als eigener Pause-Typ** (Standard XYZ <-> Rotary) + strukturiertes Spannmittel pro Setup + Stabilitaets-Heuristik (letzter Setup = Boden-Setup) + optional Rest-Material-Tracking via Voxel zwischen Setups. Aus Markus' realen Workflows: 5-Sided Teelicht-Halter + Schale-mit-Rotary. Wizard „N-Sided Manual Flip". | [#44](https://github.com/MadGapun/CAMWOSA/issues/44) | [Workflow-Modul](Workflow-Modul.md) · [Multi-Werkzeug-Setup](Multi-Werkzeug-Setup.md) | ⬜ |

### Cluster I — Echte 3D-Frässtrategien (aus Fusion-CAM-Analyse)

Quelle: `docs/FUSION-CAM-VERGLEICH.md` (live gegen Fusion-CAM-API verifiziert). Basis ist die STL-Heightmap (`stl/heightmap.py`) — fuer 3-Achs fachlich korrekt (keine Hinterschnitte moeglich). Modul `cam/strategie_3d.py`.

| Nr | Funktion | Issue | Wiki | Status |
|----|----------|-------|------|--------|
| I1 | **Planfräsen (`face`)** als eigene Op — Spoilboard/Stock-Top ebnen. stepover, passAngle, maximumStepdown, stockOffset, bothSides. Synergie mit Z-Grid-Diagnose („Werkstueck planen"-Empfehlung). `cam/planfraesen.py` + 11 Tests + API. | [#45](https://github.com/MadGapun/CAMWOSA/issues/45) | [Planfraesen](Planfraesen.md) | ✅ |
| I2 | **3D-Parallel-Schlichten** auf STL-Heightmap — Werkzeug-Form-Dilation (Kugel/Schaft/Torus), beliebiger Bahn-Winkel, Scallop- + Distanz-Stepover, StockToLeave, tolerance-Bahn-Vereinfachung, Zickzack. `cam/strategie_3d.py` + 14 Tests + API. | [#45](https://github.com/MadGapun/CAMWOSA/issues/45) | [3D-Strategien](3D-Strategien.md) | ✅ |
| I3 | **Steilheits-Trennung** — slope angle from/to + machineSteepAreas. Flach = Parallel, steil = Waterline/Contour. | [#45](https://github.com/MadGapun/CAMWOSA/issues/45) | [3D-Strategien](3D-Strategien.md) | ⬜ |
| I4 | **3D-Scallop-Schlichten** — konstante Riefenhoehe entlang Surface-Offset (nicht nur projiziert). Mathematisch aufwaendig. | [#45](https://github.com/MadGapun/CAMWOSA/issues/45) | [3D-Strategien](3D-Strategien.md) | ⬜ |
| I5 | **3D-Adaptive-Schruppen** — 3D mit konstantem Werkzeug-Eingriff (trochoidal, Z-Level). Erweitert 2D-Adaptive. | [#45](https://github.com/MadGapun/CAMWOSA/issues/45) | [3D-Strategien](3D-Strategien.md) | ⬜ |
| I6 | **Rest-Material-Tracking** zwischen Operationen (Stock = Voxel-Ergebnis vorheriger Pass). Verschraenkt mit A49. | [#45](https://github.com/MadGapun/CAMWOSA/issues/45) | [3D-Strategien](3D-Strategien.md) | ⬜ |

## Teil B — REST-API + MCP

| Nr | Funktion | Issue | Wiki | Status |
|----|----------|-------|------|--------|
| B1 | Flask-App-Setup (localhost only, CORS, Logging) | — | [API](API.md) | ✅ |
| B2 | API-Endpoints für alle Backend-Module | — | [API-Endpoints](API-Endpoints.md) | ✅ |
| B3 | OpenAPI-3.1-Spec automatisch aus Flask-Routen + Docstrings (`api/openapi.py`) + `GET /api/openapi.json` + `/api/openapi.yaml` + Swagger-UI unter `/api/docs` + 9 Tests | — | [API](API.md#interaktive-doku-openapi--swagger) | ✅ |
| B4 | MCP-Server-Setup (FastMCP) | — | [MCP-Server](MCP-Server.md) | ✅ |
| B5 | MCP-Tools für alle Backend-Funktionen (vollständige Parität mit UI) | — | [MCP-Tools](MCP-Tools.md) | ✅ |
| B6 | MCP-Tool: `auto_cam_erstellen` (Claude erstellt komplette Bearbeitung) — 3 Aufgaben-Typen: tasche, anschlagbohrungen, beschriftung_wrap. Regelbasierte Heuristik für Werkzeug-Auswahl + Schrupp+Schlicht | — | [MCP-AutoCAM](MCP-AutoCAM.md) | ✅ |

## Teil C — Desktop-App (Electron)

| Nr | Funktion | Issue | Wiki | Status |
|----|----------|-------|------|--------|
| C1 | Electron-Skelett mit Vite/React/TypeScript | [#6](https://github.com/MadGapun/CAMWOSA/issues/6) | [Electron-App](Electron-App.md) | ✅ |
| C2 | Backend-Subprozess-Management (Start/Stop/Health-Check) | [#6](https://github.com/MadGapun/CAMWOSA/issues/6) | [Electron-App](Electron-App.md) | ✅ |
| C3 | Datei-Assoziation `.cwp` + OS-Tray | [#6](https://github.com/MadGapun/CAMWOSA/issues/6) | [Electron-App](Electron-App.md) | ✅ |
| C4 | Auto-Updater Frontend — `electron-updater` Lazy-Import in main.ts mit update-available / update-downloaded Dialogs + Quit-and-Install. Inaktiv im Dev-Modus. | — | [Auto-Updater](Auto-Updater.md) | ✅ |
| C5 | i18n-Setup (DE/EN, Translation-Keys auf Deutsch) | — | [Frontend](Frontend.md) | ✅ |
| C6 | State-Management (zustand) | — | [Frontend](Frontend.md) | ✅ |
| C7 | Tailwind + Komponenten-Bibliothek | — | [Frontend](Frontend.md) | ✅ |
| C8 | Routing + Layout (Sidebar, Hauptansicht, Properties-Panel) | — | [Frontend](Frontend.md) | ✅ |

## Teil D — UI-Module

| Nr | Funktion | Issue | Wiki | Status |
|----|----------|-------|------|--------|
| D1 | Maschinen-Verwaltung (Liste, Editor, Profil-Import/Export) | — | [UI-Maschinen](UI-Maschinen.md) | ✅ |
| D2 | Werkzeug-Verwaltung (Liste, Editor, Material-Presets pro Werkzeug) | — | [UI-Werkzeuge](UI-Werkzeuge.md) | ✅ |
| D3 | Material-Verwaltung (Liste, Editor, Janka-Sortierung) | — | [UI-Material](UI-Material.md) | ✅ |
| D4 | Projekt-Verwaltung (Neu/Öffnen/Speichern/Speichern als + Variante-Sync via varianteStore + Autor + Dirty-Indikator + Recent-List + 5 API-Tests) | [#9](https://github.com/MadGapun/CAMWOSA/issues/9) | [UI-Projekt](UI-Projekt.md) | ✅ |
| D5 | Rohmaterial-Editor (Form + Position + Nullpunkt) | — | [UI-Rohmaterial](UI-Rohmaterial.md) | ✅ |
| D6 | DXF/STL-Import-Dialog mit Vorschau | [#1](https://github.com/MadGapun/CAMWOSA/issues/1) [#5](https://github.com/MadGapun/CAMWOSA/issues/5) | [UI-Import](UI-Import.md) | ✅ |
| D7 | Integriertes Zeichnen (LightBurn-inspiriert, Konva) | [#7](https://github.com/MadGapun/CAMWOSA/issues/7) | [Zeichnen](Zeichnen.md) | ✅ |
| D8 | Operations-Editor (alle Operations-Typen) | — | [UI-Operationen](UI-Operationen.md) | ✅ |
| D9 | 2D-Toolpath-Preview (Konva, Tiefen-Vorschau Seitenansicht) | [#2](https://github.com/MadGapun/CAMWOSA/issues/2) | [Preview-2D](Preview-2D.md) | ✅ |
| D10 | 3D-Materialabtrag-Simulation (Three.js, Voxel) — InstancedMesh + Surface-Extraktion | — | [Simulation-3D](Simulation-3D.md) [Material-Abtrag-Simulation](Material-Abtrag-Simulation.md) | ✅ |
| D11 | Sicherheits-Panel (Status, Klick-zur-Stelle, Blocker-Logik) | [#11](https://github.com/MadGapun/CAMWOSA/issues/11) | [UI-Sicherheits-Panel](UI-Sicherheits-Panel.md) | ✅ |
| D12 | Workflow-/Setup-Editor (Setups anlegen, Pausen einfügen) | [#13](https://github.com/MadGapun/CAMWOSA/issues/13) | [UI-Workflow](UI-Workflow.md) | ✅ |
| D13 | Arbeitsplan-Ansicht (PDF-Export + In-UI-Checkliste) | [#13](https://github.com/MadGapun/CAMWOSA/issues/13) | [Arbeitsplan](Arbeitsplan.md) | ✅ |
| D14 | Nesting-Editor (Teile-Liste, Platten, Drag&Drop, Statistik) | [#14](https://github.com/MadGapun/CAMWOSA/issues/14) | [UI-Nesting](UI-Nesting.md) | ✅ |
| D15 | Feeds & Speeds Panel (live-berechnet beim Operation-Editing) | [#3](https://github.com/MadGapun/CAMWOSA/issues/3) | [UI-Feeds-Speeds](UI-Feeds-Speeds.md) | ✅ |
| D16 | G-Code-Editor (Monaco, Befehlsbibliothek, Live-Sync, Outline, Mass-Edit) | [#8](https://github.com/MadGapun/CAMWOSA/issues/8) | [GCode-Editor](GCode-Editor.md) | ✅ |
| D17 | Settings (Theme, Sprache, Pfade, Update-Verhalten, KI-Features) | — | [UI-Settings](UI-Settings.md) | ✅ |
| D18 | Foto-Slot pro Setup | [#13](https://github.com/MadGapun/CAMWOSA/issues/13) | [UI-Workflow](UI-Workflow.md) | ✅ |
| D19 | Design-System (CSS-Tokens, Theme Dark/Light, 3 Density-Stufen 10"-34", Vorschau-Modi) | — | [Design-System](Design-System.md) | ✅ |
| D20 | First-Run-Wizard (4-Schritt-Onboarding: Maschine → Spindel → Werkzeug → Material) | — | [First-Run-Wizard](First-Run-Wizard.md) | ✅ |
| D21 | Tooltip-System (3-stufig: Wert / Fachbegriff / Coach-Mark) | — | [Tooltip-System](Tooltip-System.md) | ✅ |
| D22 | Bild-Relief-View (Frontend Phase B: Drag&Drop-Upload + Live-Vorschau + Parameter-Panel + Heightmap-Generierung) | — | [Bild-zu-Relief](Bild-zu-Relief.md) | ✅ |
| D23 | Wrap-Preview3D (Three.js-Komponente: 2D-Pfad auf Zylinder gewickelt anzeigen mit Pattern-Skalierung) | — | [Wrap-Mode](Wrap-Mode.md) | ✅ |
| D24 | Operation-Preview3D (Three.js-Komponente: Toolpath einer einzelnen Operation in 3D) | — | [Simulation-3D](Simulation-3D.md) | ✅ |
| D25 | Bild-Relief-Filterpanel — Frontend zu Phase D: `HeightmapFilterStack`-Komponente mit Filter-Liste (6 Filter), Reorder ↑↓, Toggle, Reset, Live-Anwendung gegen Backend-Endpoints + AI-Toggle in `BildReliefView` (Phase E). Three.js-3D-Preview folgt als spaetere Iteration. | [#17](https://github.com/MadGapun/CAMWOSA/issues/17) | [Bild-zu-Relief](Bild-zu-Relief.md) | ✅ |
| D26 | First-Run-Wizard: Maschine + Spindel im Wizard direkt anlegen statt nur aus Default-Liste waehlen. Quick-Add-Inline-Form mit Pflichtfeldern, reuse Backend-CRUD-Validierung. Aus Markus' Alpha-0-Feedback. | [#22](https://github.com/MadGapun/CAMWOSA/issues/22) | [First-Run-Wizard](First-Run-Wizard.md) | ✅ |
| D27 | First-Run-Wizard: Werkzeug im Wizard direkt anlegen + optional Werkzeug-Set-Import (JSON-Bundle). Quick-Add mit dynamischen Feldern je Typ (V-Bit braucht Spitzenwinkel, Ballnose-V-Bit braucht zusaetzlich Spitzendurchmesser). | [#23](https://github.com/MadGapun/CAMWOSA/issues/23) | [First-Run-Wizard](First-Run-Wizard.md) | ✅ |
| D28 | Zeichnen: Eigenschaften-Panel mit numerischer Eingabe (X/Y/Breite/Hoehe/Rotation pro Objekt) + Transform-Handles (Resize + Drag) + Vertex-Drag fuer Polygone + Pfeil-Hotkeys + Undo/Redo. Aus Markus' Workflow „ich muss Masse eingeben + nachtraeglich aendern koennen". | [#25](https://github.com/MadGapun/CAMWOSA/issues/25) | [Zeichnen](Zeichnen.md) | ⬜ |
| D29 | Zeichnen: Geometrien zueinander ausrichten — Smart-Snap (Mitte/Kante/Vertex eines anderen Objekts, Hilfslinien live) + 8 Align-Buttons fuer Multi-Select (Links/Rechts/Mitte/Verteilen). Snap an/aus via Hotkey S. | [#26](https://github.com/MadGapun/CAMWOSA/issues/26) | [Zeichnen](Zeichnen.md) | ⬜ |
| D30 | Zeichnen: Text-Werkzeug fuer Schriftzug — neues Werkzeug „T" in Toolbar, Editor-Popup (Text/Font/Hoehe/Stil), nutzt A37 Text-zu-Pfad-Backend (existiert). Properties-Panel erlaubt Text-Inhalt-Editierung mit Pfad-Neugenerierung. | [#27](https://github.com/MadGapun/CAMWOSA/issues/27) | [Zeichnen](Zeichnen.md) · [Text-zu-Pfad](Text-zu-Pfad.md) | ⬜ |
| D31 | Workflow: Geometrie → Operation Verknuepfung — Properties-Panel zeigt „Verwendet von Operationen X,Y" + Buttons „+ Kontur/Tasche/Bohren/Gravur/Relief" fuer Quick-Create. Im OperationenView: Pflicht-Dropdown „Geometrie waehlen". Backend: `geometrie_id` Pflicht statt null-Fallback. Markierung im Zeichnen-View welche Geometrien Operations haben. | [#28](https://github.com/MadGapun/CAMWOSA/issues/28) | [Zeichnen](Zeichnen.md) · [UI-Operationen](UI-Operationen.md) | ✅ |
| D32 | Rename UI „Drechseln" → „Drehen" (DE) im Locale + DrechselnView-Header. Backend-Identifier bleiben. | [#29](https://github.com/MadGapun/CAMWOSA/issues/29) | [Drechseln](Drechseln.md) | ✅ |
| D33 | Drehen-Profil-Editor: numerische Eingabe pro Punkt (Inline-Popup X/Radius), Rohmaterial-Ø+L editierbar im Header, 0-Punkt-Markierung in Canvas + Drehachsen-Beschriftung, Punkt-Tabelle rechts mit Edit/Del. Hotkeys Pfeil 1 mm / Shift 10 mm. | [#30](https://github.com/MadGapun/CAMWOSA/issues/30) | [Drechseln](Drechseln.md) | ⬜ |
| D34 | Werkzeug-UI mit Skizzen: 11 SVG-Files (eine pro Typ) in WerkzeugeView + Wizard-Auswahl-Liste + OperationenView-Dropdown. Im WerkzeugEditor grosse annotierte Skizze mit Mass-Pfeilen die beim Feld-Fokus highlighten (zeigt welches Mass gemeint ist). Dynamische Skizze beim Typ-Wechsel. | [#33](https://github.com/MadGapun/CAMWOSA/issues/33) | [Werkzeug-Bibliothek](Werkzeug-Bibliothek.md) | ⬜ |
| D35 | UI-Konzepte aus etablierten CAM-Tools — Project-Tree mit Sichtbarkeits-Lampen pro Operation + Doppelklick-Edit + Rechtsklick-Kontextmenue + Drag&Drop · NC-Files-Window · Multi-View-Layout (1/2/3/4 Splits Top/Front/Right/Default) · Animation (Cutter-Symbol auf Toolpath mit Speed-Slider) · Wizard-Framework + 3 Basis-Wizards (Vector/Geometry/Bitmap) · Toolpath-Display-Optionen (Points/Arrows/Rapid) · Default-Project/Part/Operation pro User. | [#38](https://github.com/MadGapun/CAMWOSA/issues/38) | [Frontend](Frontend.md) | ⬜ |
| D36 | Hilfe-System — **Glossar mit 60+ CNC-Begriffen** ✅ (Werkzeug-Doku + Operations + Strategien). Hover-Help-Audit auf 200+ Eingaben, Inline-Grafiken pro Strategie, FachTooltip-Pattern-Erweiterung folgen in Frontend-Iteration. | [#41](https://github.com/MadGapun/CAMWOSA/issues/41) | [Tooltip-System](Tooltip-System.md) · [First-Run-Wizard](First-Run-Wizard.md) · [Glossar](Glossar.md) | 🟨 |

## Teil E — Polish und Pro-Features

| Nr | Funktion | Issue | Wiki | Status |
|----|----------|-------|------|--------|
| E1 | EN-Übersetzung | — | [i18n](i18n.md) | ✅ |
| E2 | Werkzeug-Standzeit-Tracking | — | [Standzeit-Tracking](Standzeit-Tracking.md) | ✅ |
| E3 | Kollisionsanalyse Werkzeughalter (3D) | — | [Kollisionsanalyse](Kollisionsanalyse.md) | ✅ |
| E4 | Adaptive Clearing — kleines Stepover (12%) + trochoidale Sinus-Modulation senkrecht zur Bahn (`_adaptive_bahnen` + `_modulieren`) + 2 Parameter-Felder (`adaptive_amplitude_faktor`, `adaptive_wellen_pro_mm`) + 5 Tests | — | [Adaptive-Clearing](Adaptive-Clearing.md) | ✅ |
| E5 | Community-Sharing für Werkzeuge/Materialien (JSON-Austausch + optionaler Cloud-Sync) | — | [Community-Sharing](Community-Sharing.md) | ✅ |
| E6 | Bohrbild aus DXF-Kreisen automatisch erkennen | — | [Bohrbild-Erkennung](Bohrbild-Erkennung.md) | ✅ |
| E7 | Spezial-Operationen: T-Nuten, Schwalbenschwanz, Fasen | — | [Spezial-Operationen](Spezial-Operationen.md) | ✅ |
| E8 | PCB-Isolationsfräsen | — | [PCB-Fraesen](PCB-Fraesen.md) | ✅ |
| E9 | Plugin-API für Operations (eigene Operations-Typen nachladbar) | — | [Operations-Plugins](Operations-Plugins.md) | ✅ |

## Teil F — Distribution

| Nr | Funktion | Issue | Wiki | Status |
|----|----------|-------|------|--------|
| F1 | Cross-Platform-Installer (Windows MSI, macOS DMG, Linux AppImage/deb) | — | [Installer](Installer.md) | ✅ |
| F2 | Python-Backend gebündelt (PyInstaller / py2app) | — | [Installer](Installer.md) | ✅ |
| F3 | Code-Signing (Windows + macOS) | — | [Installer](Installer.md) | ⬜ |
| F4 | GitHub Actions: Build + Release-Pipeline | — | [CI-CD](CI-CD.md) | ✅ |
| F5 | Auto-Updater-Backend — `publish.github` Config + `app-update.yml` im Bundle + `electron-updater.checkForUpdates()` laeuft beim Start. **Auto-Update funktioniert nur mit NSIS-Installer**: portable ZIP kann sich nicht selbst aktualisieren (electron-updater hat keinen ZIP-Provider). NSIS-Build scheitert aktuell am winCodeSign-Symlink-Bug auf Windows ohne Developer-Mode (siehe [Issue #21](https://github.com/MadGapun/CAMWOSA/issues/21)). User bekommt update-available-Dialog, kann das ZIP manuell laden. | [#21](https://github.com/MadGapun/CAMWOSA/issues/21) | [Auto-Updater](Auto-Updater.md) | 🟨 |

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
