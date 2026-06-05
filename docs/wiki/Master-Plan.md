# Master-Implementierungsplan

> **Stand:** 17.05.2026 · Lebendiges Dokument · Wird mit jedem Schritt aktualisiert.
>
> **Arbeitsprinzip:** Master-Plan-First. Neue Ideen werden erst hier eingeordnet (mit Status ⬜ und ggf. Issue), dann nach Plan abgearbeitet — nicht ad-hoc gebaut und spaeter nachgezogen.
>
> **Ziel-Prinzip: Dual-Audience.** CAMWOSA bedient **beide** Zielgruppen mit
> **demselben Werkzeug** (das DeskProto-Muster — Wizard für Anfänger ↔ Full-
> Control für Profis, gleiches Datenmodell):
> - **Einsteiger ohne Vorkenntnisse** — geführt, jargon-überbrückt, vertrauens-
>   bildend (Cluster K + L). Der Wizard *schreibt ins selbe Projekt-Modell*, das
>   der Profi editiert — keine getrennte „Anfänger-Version".
> - **Erfahrene Power-User** (wie Markus) — volle Kontrolle + erweiterte
>   Workflows: **V-Carve aus Modellen/Tiefenbildern**, **Multi-Setup mit
>   Umspannungen**, **Rotary/Drechseln** (Cluster M + A49 + Phase 3).
>
> Die Anfänger-Schicht darf die Power-User-Tiefe **nie** verdecken oder
> beschneiden — sie liegt als optionale Führung *darüber*, nicht *statt*.

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
| I3 | **Steilheits-Trennung** — Slope-Fenster `slope_min_grad`/`slope_max_grad` in `Strategie3DParameter`. Bahn-Punkte ausserhalb des Steigungs-Fensters werden uebersprungen (Segment-Unterbrechung). `berechne_steigungswinkel()` aus numpy-Gradient. 6 Tests. | [#45](https://github.com/MadGapun/CAMWOSA/issues/45) | [3D-Strategien](3D-Strategien.md) | ✅ |
| I4 | **3D-Scallop-Schlichten** — `StepoverModus.SCALLOP_3D`: konstante Riefenhoehe auf der 3D-Oberflaeche, XY-Bahnabstand skaliert mit cos(lokale Steigung). Adaptive Bahn-Schleife. 4 Tests. | [#45](https://github.com/MadGapun/CAMWOSA/issues/45) | [3D-Strategien](3D-Strategien.md) | ✅ |
| I5 | **3D-Adaptive-Schruppen** — 3D mit konstantem Werkzeug-Eingriff (trochoidal, Z-Level). Erweitert 2D-Adaptive. | [#45](https://github.com/MadGapun/CAMWOSA/issues/45) | [3D-Strategien](3D-Strategien.md) | ⬜ |
| I6 | **Rest-Material-Tracking** zwischen Operationen (Stock = Voxel-Ergebnis vorheriger Pass). Verschraenkt mit A49. | [#45](https://github.com/MadGapun/CAMWOSA/issues/45) | [3D-Strategien](3D-Strategien.md) | ⬜ |

### Cluster J — CAM-Qualität & Toolpath-Infrastruktur (GAP-Analyse 2026-05-21)

Lücken bei Toolpath-Qualität/Infrastruktur (nicht bei Strategien). Quelle: GAP-Analyse + `docs/FUSION-CAM-VERGLEICH.md`.

| Nr | Funktion | Issue | Wiki | Status |
|----|----------|-------|------|--------|
| J1 | **Arc-Fitting (G2/G3)** — `gcode/arc_fitting.py`: greedy Bogen-Erkennung (Umkreis durch 3 Punkte, Toleranz + Drehrichtung), nur konstantes Z+Feed, endpunkt-treu. Optional im postprocess-Endpoint (`arc_fitting:true`) + MCP. 10 Tests. | [#46](https://github.com/MadGapun/CAMWOSA/issues/46) | [Arc-Fitting](Arc-Fitting.md) | ✅ |
| J2 | **Bohr-Zyklen erweitern** — ANBOHREN (Zentrier-Spot), SENKEN (zylindrisch/konisch aus Winkel), GEWINDEBOHREN (synchron-Vorschub aus Steigung × RPM). Erweitert `BohrStrategie` + `BohrParameter` + `cam/bohren.py`. 8 Tests. | [#46](https://github.com/MadGapun/CAMWOSA/issues/46) | [Operation-Bohren](Operation-Bohren.md) | ✅ |
| J3 | **Spanausduennung (Chip Thinning)** — `chip_thinning_faktor()` + `korrigiere_vorschub_spanausduennung()` in `feeds/rechner.py`, `f_korr = f / sqrt(1-(1-2·ae/d)²)`, geklemmt ≤4. API `/api/feeds/chip-thinning` + MCP `spanausduennung_faktor`. 12 Tests. | [#46](https://github.com/MadGapun/CAMWOSA/issues/46) | [Feeds-Speeds](Feeds-Speeds.md) | ✅ |
| J4 | **Linking / Stay-Down-Optimierung** — Werkzeug unten lassen wo der direkte Weg frei + kurz ist (stayDownDistance). Weniger Luftbewegungen. | [#46](https://github.com/MadGapun/CAMWOSA/issues/46) | — | ⬜ |
| J5 | **Rampen-Eintauchen + Lead-in/out** — **Rampen-Eintauchen ✅** (`gcode/eintauchen.py:rampe_eintauchen`): senkrechte Plunges werden durch Zickzack-Rampen entlang des Folgeschnitts ersetzt (einstellbarer Winkel, `material_oberkante`-Konvention, endpunkt-treu, Fallback bei zu kurzem Segment). Opt-in `rampe_eintauchen:true` am Endpoint + MCP + UI. 10 Tests. **Lead-in/out-Bogen (tangentialer Ein-/Auslauf an Konturen) noch offen.** | [#46](https://github.com/MadGapun/CAMWOSA/issues/46) | [Fahrweg-Optimierung](Fahrweg-Optimierung.md) | 🔶 |
| J6 | **Flat-Area-Detection** — flache 3D-Bereiche (slope≈0) erkennen + separat plan-schlichten. Nutzt `berechne_steigungswinkel()`. | [#46](https://github.com/MadGapun/CAMWOSA/issues/46) | [3D-Strategien](3D-Strategien.md) | ⬜ |
| J7 | **Pencil / Kehlnaht-Cleanup** — Tal-Linien mit kleinem Werkzeug nachfahren (3D-Pencil). Grosser Brocken. | [#46](https://github.com/MadGapun/CAMWOSA/issues/46) | [3D-Strategien](3D-Strategien.md) | ⬜ |
| J8 | **Trochoidales Nutenfraesen** — Slot mit kreisender Bahn fuer tiefe schmale Nuten (konstante Last). | [#46](https://github.com/MadGapun/CAMWOSA/issues/46) | — | ⬜ |
| J9 | **Intelligente Fahrwege (kurze Wege)** — Reihenfolge der Schnitt-Gruppen (Konturen/Bahnen/Bohrungen) per Nearest-Neighbor optimieren → minimaler Eilgang-Verfahrweg = kürzere Zeit. Post-Schritt `gcode/fahrweg.py`, allgemein über alle Ops. Markus' Anforderung. | [#52](https://github.com/MadGapun/CAMWOSA/issues/52) | [Fahrweg-Optimierung](Fahrweg-Optimierung.md) | ✅ |
| J10 | **Knappe Freifahrten über Geometrie** — Zwischen-Eilgänge laufen knapp (einstellbar) über der vorhandenen Geometrie statt auf voller Sicherheitshöhe über dem Rohling. `freifahrt_hoehe` pro Op + Post-Schritt `senke_freifahrten()`. Erste Anfahrt + Schluss-Rückzug bleiben auf Sicherheitshöhe. Markus' Anforderung. | [#52](https://github.com/MadGapun/CAMWOSA/issues/52) | [Fahrweg-Optimierung](Fahrweg-Optimierung.md) | ✅ |
| J11 | **Vorschub-Anpassung bei Teil-Tiefe** — der Vorschub gilt für die volle Zustellung (`stepdown`). Pässe mit geringerer axialer Tiefe (z.B. letzter Teil-Pass, prozentuale Tiefen) bekommen höheren Vorschub (∝ stepdown/ap, gedeckelt). `feeds`-Helfer + in Kontur/Tasche-Pass-Generierung. Speist auch K5-Zeitschätzung. Markus' Anforderung. | [#52](https://github.com/MadGapun/CAMWOSA/issues/52) | [Feeds-Speeds](Feeds-Speeds.md) | ✅ |

### Cluster P — Postprozessor-Härtung / GRBL-Output-Qualität (Audit 2026-06)

Lücken im **realen G-code-Output** (was auf der Maschine läuft), gefunden beim Audit von `postprocessor/base.py` → `grbl_standard.py`. Quelle: `docs/ANALYSE-2026-06.md` §1. Betrifft **jede** erzeugte Datei → höchster Maschinen-ROI. Alle rückwärtskompatibel (Defaults = altes Verhalten).

| Nr | Funktion | Issue | Wiki | Status |
|----|----------|-------|------|--------|
| P1 | **Spindel-Hochlauf-Dwell** — `spindle_on()` hängt `G4 P<t>` nach `M3 S<rpm>` an, damit die Spindel (z.B. 1,5 kW VFD ~3 s) vor dem Erstschnitt auf Drehzahl ist. Quelle `Spindel.rampen_zeit_s` (war schon im Modell, jetzt verdrahtet), per `PostKontext.spindel_hochlauf_s`. Default 0 = aus. 4 Tests. | [#54](https://github.com/MadGapun/CAMWOSA/issues/54) | [Postprozessor-GRBL](Postprozessor-GRBL.md) | ✅ |
| P2 | **Modaler Output** — `gcode/modal.py` `komprimiere_modal()`: endpunkt-treuer Post-Pass entfernt redundante Achsworte (X/Y/Z unverändert), Feed (nur bei Änderung) und Motion-Wort. Datei kleiner, kein Z-Jitter. Boegen behalten X/Y/I/J. Opt-in `modal:true`. 11 Tests (inkl. Bahn-Treue-Replay). | [#54](https://github.com/MadGapun/CAMWOSA/issues/54) | [Postprozessor-GRBL](Postprozessor-GRBL.md) | ✅ |
| P3 | **Rapid-Safety-Split** — `entschaerfe_eilgaenge()` zerlegt mehr-achsige Eilgänge in sichere Reihenfolge: Z-hoch zuerst beim Rückzug, XY zuerst beim Anfahren. Kein diagonaler Tauchgang/Schliff. `gcode/fahrweg.py`. Opt-in `rapid_safety:true`. 6 Tests. | [#54](https://github.com/MadGapun/CAMWOSA/issues/54) | [Fahrweg-Optimierung](Fahrweg-Optimierung.md) | ✅ |
| P4 | **G54 im Header** — `grbl_standard.header()` wählt das Arbeits-KS explizit. Start-Sicherheits-Z liefern die Generatoren bereits (jeder Toolpath beginnt mit Eilgang auf Sicherheitshöhe). 1 Test. | [#54](https://github.com/MadGapun/CAMWOSA/issues/54) | [Postprozessor-GRBL](Postprozessor-GRBL.md) | ✅ |

### Cluster K — Anfänger-Erlebnis / Zero-to-Cut (Tiefenanalyse 2026-05-21)

Die **geführte Schicht über dem starken Backend** — das mächtige CAM für Menschen ohne CNC-Vorwissen bedienbar machen. Quelle: `docs/HOBBY-CAM-ANALYSE.md`. Kernerkenntnis: die Lücke ist fast vollständig die anfänger-zugewandte Bedien-Schicht, nicht das Backend. Sortiert nach Anfänger-Nutzen.

| Nr | Funktion | Phase | Issue | Status |
|----|----------|-------|-------|--------|
| K1 | **Geführter End-to-End-Assistent** — roter Faden „von der Idee zur fertigen Datei" durch alle 7 Phasen; verbindet QuickCAM + Auto-CAM statt Template-Inseln. | alle | [#47](https://github.com/MadGapun/CAMWOSA/issues/47) | ⬜ |
| K2 | **Intent-basierter Operations-Picker** — „Was soll mit dieser Form passieren?" mit Bildern (durchschneiden/aushöhlen/gravieren/Relief/bohren) → Operations-Typ + Defaults. | 2 | [#47](https://github.com/MadGapun/CAMWOSA/issues/47) | ⬜ |
| K3 | **Mystery-Bit-Helfer + Starter-Sets** — Messschieber-Werte + Form-Bild → Werkzeug-Vorschlag (unbeschrifteter Bit-Beutel = häufigstes Anfänger-Problem) + Ein-Klick-Bibliothek pro Hobby-Maschine. | 0 | [#47](https://github.com/MadGapun/CAMWOSA/issues/47) | ⬜ |
| K4 | **Konfidenz-Ampel + Klartext-Sicherheit** — Feeds-Vertrauenssignal (🟢/🟡) + Safety-Checks in Menschensprache. | 3,5 | [#47](https://github.com/MadGapun/CAMWOSA/issues/47) | ⬜ |
| K5 | **Zeit-/Aufwand-Schätzung** — `gcode/zeit_schaetzung.py`: Schnitt/Eilgang getrennt, Werkzeugwechsel-Pausen, Beschleunigungs-Overhead (1.15), Klartext („23 Min 12 Sek"). API `/api/operations/zeitschaetzung` + MCP. 15 Tests. **UI:** Bearbeitungszeit jetzt in der Toolpath-Statistik (OperationenView), `api/zeit.ts` spiegelt die Formel live (reflektiert J11-Feeds). | 5 | [#47](https://github.com/MadGapun/CAMWOSA/issues/47) | ✅ |
| K6 | **Animierte Schnitt-Wiedergabe** — Cutter fährt Pfad ab + Speed-Slider (Anteil D35, hier als Anfänger-Vertrauens-Feature). | 5 | [#47](https://github.com/MadGapun/CAMWOSA/issues/47) | ⬜ |
| K7 | **„Was jetzt?"-Übergabe-Guide** — Datei → Sender → Null → Play, druckbar; + Sender-Empfehlung nach Controller (neutral, ohne Push). | 6 | [#47](https://github.com/MadGapun/CAMWOSA/issues/47) | ⬜ |
| K8 | **Troubleshooting-Assistent** — Ergebnis-Diagnose (verbrannt/ausgefranst/…) → Korrektur + Neuberechnung. Lern-Schleife. | 7 | [#47](https://github.com/MadGapun/CAMWOSA/issues/47) | ⬜ |
| K9 | **Beispielprojekte mitliefern** — 3–5 fertige .cwp (Untersetzer, Namensschild, Box) zum Öffnen + Lernen. | alle | [#47](https://github.com/MadGapun/CAMWOSA/issues/47) | ⬜ |
| K10 | **Anfänger-Modus / Jargon-Brücke** — Begriffe in Alltagssprache + jedes Feld mit Hover-Hilfe (vollendet D36). | alle | [#47](https://github.com/MadGapun/CAMWOSA/issues/47) | ⬜ |
| K11 | **Innen/Außen-Linie + Tabs-Aufklärung visuell** — Bilder statt Dropdown; proaktiver „dein Teil fliegt weg"-Hinweis. | 2,4 | [#47](https://github.com/MadGapun/CAMWOSA/issues/47) | ⬜ |
| K12 | **Nullpunkt-Erklär-Guide** — visuelle Standard-Empfehlung (vorne-links-oben) + „warum". | 4 | [#47](https://github.com/MadGapun/CAMWOSA/issues/47) | ⬜ |
| K13 | **LightBurn-vertraute „Cuts/Layers"-Bedienung** 🔴 — Form + Operation farbcodiert zusammen (wie LightBurn/MillMage), die Ebenen-Liste *ist* die Operations-Liste mit Modus/Werkzeug/Tiefe/anzeigen-Toggle. Vereint Geometrie + Operationen statt zwei getrennter Tabs. **Größter UX-Hebel** — nutzt Markus' LightBurn-Erfahrung direkt + spricht die Laser-Crossover-Zielgruppe an. (Tool-Vergleich: `docs/HOBBY-CAM-ANALYSE.md` §6b, Muster 2.) | alle | [#47](https://github.com/MadGapun/CAMWOSA/issues/47) | ⬜ |

### Cluster L — Design-Eingabe für Hobby (Tiefenanalyse 2026-05-21)

Design leicht reinbekommen (Phase 1). Verwandt zu D28–D30, aber: Cluster L ist **Design-Inhalt reinbekommen**, nicht Zeichnen-Bedienung. Quelle: `docs/HOBBY-CAM-ANALYSE.md`.

| Nr | Funktion | Issue | Status |
|----|----------|-------|--------|
| L1 | **Bitmap → Vektor-Trace** — `cad/bitmap_trace.py`: Schwellwert → Marching-Squares-Kontur (nutzt `waterline.py`) → Douglas-Peucker → GeometrieObjekt. Skalierung + Flecken-Filter. Outline-Trace (Centerline folgt). API `/api/cad/bitmap-trace` + MCP. 11 Tests. | [#48](https://github.com/MadGapun/CAMWOSA/issues/48) | ✅ |
| L2 | **Clipart / Form-Bibliothek** — parametrische Standardformen (Herz, Stern, Zahnrad, Rahmen, Pfeil, abgerundetes Rechteck, N-Eck) → GeometrieObjekt. | [#48](https://github.com/MadGapun/CAMWOSA/issues/48) | ⬜ |
| L3 | **Bemaßung + Lineale im Zeichnen** — sichtbare Maße/Maßketten + Canvas-Lineale. Verschränkt mit D28. | [#48](https://github.com/MadGapun/CAMWOSA/issues/48) | ⬜ |

### Cluster M — Power-User / Erweiterte Workflows (Dual-Audience-Profi-Schicht)

Die **Profi-Seite** des Dual-Audience-Prinzips — die Anfänger-Schicht (K/L) darf diese Tiefe nie verdecken. Markus' genannte Profi-Workflows: V-Carve aus Modellen/Tiefenbildern, Multi-Setup mit Umspannungen, Rotary. Quelle: `docs/HOBBY-CAM-ANALYSE.md`.

| Nr | Funktion | Issue | Status |
|----|----------|-------|--------|
| M1 | **V-Bit/Gravierstichel-Kegelprofil in 3D-Strategien** — echte konische Werkzeug-Form-Dilation (Spitzenwinkel + Spitzendurchmesser-Flachfläche, TIP-Referenz) statt Flachboden-Näherung; Ball-Nose-V-Bit als Kugel+Kegel-Hybrid (tangential). Macht **V-Carve aus Tiefenbild/Modell** möglich. `cam/strategie_3d.py`, 6 Tests. Greift automatisch im 3D-Parallel-Endpoint + MCP. | [#49](https://github.com/MadGapun/CAMWOSA/issues/49) | ✅ |
| M2 | **Tiefenbild→V-Carve-Pipeline** — `v_carve_parameter_vorschlag()` (feiner 3D-Scallop + V-Bit) + Wiki-Rezept (Bild/Modell → Heightmap → 3D-V-Carve). 2 Tests. | [#49](https://github.com/MadGapun/CAMWOSA/issues/49) | ✅ |
| M3 | **Expert-Mode-Schalter** — explizite Profi-Seite des Dual-Interface: blendet alle Parameter direkt ein (kein Wizard dazwischen), Gegenstück zu K1. CAMWOSA hat die Override-Forms schon — als „Expert-Layer" explizit machen + global umschaltbar. | [#49](https://github.com/MadGapun/CAMWOSA/issues/49) | ⬜ |
| M4 | **Workflow-Vorlagen für Power-User** — wiederkehrende Multi-Setup-/Umspannungs-Abläufe als Vorlage speichern + wiederverwenden. Baut auf A49 (Umspannung) + ArbeitsSchritt + QuickCAM. | [#49](https://github.com/MadGapun/CAMWOSA/issues/49) | ⬜ |
| M5 | **Multi-Setup mit Umspannung** — siehe **A49** (Werkstück-Transformation + Maschinen-Umbau + Spannmittel pro Setup + Stabilitäts-Heuristik). Power-User-Säule, hier referenziert + priorisiert. | [#44](https://github.com/MadGapun/CAMWOSA/issues/44) | ⬜ |
| M6 | **Rotary/Drechseln (Profi)** — bereits umgesetzt (Phase 3 + A30): 3,5-Achs-Indexing, Wrapping, Continuous-Lathe, 4 Drechsel-Strategien. Hier als Power-User-Säule referenziert. | [#12](https://github.com/MadGapun/CAMWOSA/issues/12) | ✅ |

### Cluster Q — Feinkörnige Einstellbarkeit + Piktogramme + Workflow-Logik (Wettbewerbs-Audit 2026-06-05)

Quelle: `docs/ANALYSE-2026-06-05-Wettbewerb-Einstellbarkeit.md` (Vergleich Easel/Carbide/Estlcam/OpenBuilds/VCarve/OPUS). Markus' Anforderung „alle Parameter editierbar + jeder Workflow logisch/dokumentiert + alle Piktogramme da".

| Nr | Funktion | Issue | Wiki | Status |
|----|----------|-------|------|--------|
| Q1 | **Override-UI-Vollständigkeit** — ~17 fehlende Modell-Felder in `OverrideOperationForm` ergänzt (freifahrt_hoehe, vorschub_anpassung_max, rampe_winkel_grad, schlichtgang(_wand/_boden), lead_in/out, adaptive_*, loch_durchmesser, helix_steigung, anbohr_tiefe, senk_*, gewinde_steigung). Jeder Operations-Parameter pro Operation editierbar. | [#56](https://github.com/MadGapun/CAMWOSA/issues/56) | [Per-Feature-Override](Per-Feature-Override.md) | ✅ |
| Q2 | **Plunge-Feed vs. Rampen-Feed trennen** — variable Eintauchgeschwindigkeit. `OperationParameter.rampe_vorschub`/`rampe_vorschub_faktor` + Property `rampe_eintauch_vorschub`; `Bewegung.rampe_feed`; `rampe_eintauchen()` nutzt Rampen-Feed nur für Rampen-Segmente (Luft-Plunge bleibt langsam). Endpoint/MCP `rampen_vorschub(_faktor)` + UI. Rückwärtskompatibel (Default = wie bisher). 12 Tests. | [#56](https://github.com/MadGapun/CAMWOSA/issues/56) | [Feeds-Speeds](Feeds-Speeds.md) | ✅ |
| Q3 | **Per-Geometrie-Override** — Feed/Tiefe/Plunge pro Kontur **innerhalb** einer Operation (Estlcam Element-als-Entität-Modell). Größtes funktionales Delta. Recherche dokumentiert (`docs/ANALYSE-2026-06-05`). | [#56](https://github.com/MadGapun/CAMWOSA/issues/56) | [Per-Feature-Override](Per-Feature-Override.md) | ⬜ |
| Q4 | **Operations- + Strategie-Piktogramme** — `OperationGrafik.tsx` (Kontur/Tasche/Bohren/Gravur/Relief) + `StrategieGrafik.tsx` (Tasche-/Eintauch-Strategien), parametrisch wie `WerkzeugGrafik`. In Operations-Liste + Override-Form verdrahtet. Render-Tests. | [#56](https://github.com/MadGapun/CAMWOSA/issues/56) | [Design-System](Design-System.md) | ✅ |
| Q5 | **Innen/Außen/Tabs visuell** — `KonturSeiteGrafik.tsx` (innen/außen/auf_linie + Haltestege mit „Teil fliegt weg"-Hinweis), in der Kontur-Override-Form. | [#56](https://github.com/MadGapun/CAMWOSA/issues/56) | — | ✅ |
| Q6 | **Workflow-Ablauf-Diagramme + K1 geführter Faden** (Idee→Design→Werkzeug→Operation→Sicherheit→G-Code→Maschine). | [#56](https://github.com/MadGapun/CAMWOSA/issues/56) | [Workflow-Modul](Workflow-Modul.md) | ⬜ |
| Q7 | **QuickStart-Dead-End gefixt** (#50) — `quickcamProjektInStores()` in projektIO flacht `varianten[0].setups[].operationen` aus + hebt `op.parameter.__geometrie`; `QuickStartView.erzeugen()` nutzt jetzt die Rückgabe + navigiert zu /operationen. | [#50](https://github.com/MadGapun/CAMWOSA/issues/50) | [QuickCAM](QuickCAM.md) | ✅ |

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
| D34 | **Werkzeug-UI mit Skizzen + Piktogrammen + Auto-Name** (Markus-Anforderung): SVG-Skizze pro Typ — gross + annotiert (Mass-Pfeile, die beim Feld-Fokus highlighten) im WerkzeugEditor, dynamisch beim Typ-Wechsel; als **verkleinertes Piktogramm** in Werkzeug-Liste + Wizard + OperationenView-Dropdown (man sieht sofort den Typ). **Name automatisch aus den Daten** (Typ + Ø + Schneiden + Material + ggf. Winkel), am Ende **optionaler eigener Zusatz** (`name_zusatz`). Backend-Helfer `werkzeug_anzeigename()` + `name_zusatz`-Feld (D34a). **Umgesetzt:** `components/WerkzeugGrafik.tsx` (Silhouette je Typ, gross+bemasst mit Feld-Fokus-Highlight, klein als Piktogramm), Auto-Name-Vorschau + Zusatz-Feld im WerkzeugEditor, Piktogramme in Werkzeug-Liste + OperationenView-Dropdown, `api/werkzeugName.ts`. | [#33](https://github.com/MadGapun/CAMWOSA/issues/33) | [Werkzeug-Typen](Werkzeug-Typen.md) · [Werkzeug-Bibliothek](Werkzeug-Bibliothek.md) | ✅ |
| D34a | **Werkzeug-Auto-Name (Backend)** — `werkzeug_anzeigename(werkzeug)` generiert den Anzeigenamen aus den Daten; optionales `name_zusatz`-Feld wird angehängt. Vorstufe zu D34-Frontend. | [#33](https://github.com/MadGapun/CAMWOSA/issues/33) | [Werkzeug-Bibliothek](Werkzeug-Bibliothek.md) | ✅ |
| D37 | **Mehr erklärende Grafiken & Piktogramme allgemein** (Markus-Anforderung) — Strategie-Icons, Operations-Piktogramme (durchschneiden/aushöhlen/gravieren), Inline-Skizzen in Tooltips, visuelle Innen/Außen-Darstellung. Verschränkt mit D34/D36/K2/K11. Konsistentes Icon-/Skizzen-System im Design-System. **Teilweise:** Werkzeug-Grafiken (D34) sind der erste Baustein; Strategie-Icons + Operations-Piktogramme noch offen. | [#33](https://github.com/MadGapun/CAMWOSA/issues/33) | [Design-System](Design-System.md) | 🔶 |
| D35 | UI-Konzepte aus etablierten CAM-Tools — Project-Tree mit Sichtbarkeits-Lampen pro Operation + Doppelklick-Edit + Rechtsklick-Kontextmenue + Drag&Drop · NC-Files-Window · Multi-View-Layout (1/2/3/4 Splits Top/Front/Right/Default) · Animation (Cutter-Symbol auf Toolpath mit Speed-Slider) · Wizard-Framework + 3 Basis-Wizards (Vector/Geometry/Bitmap) · Toolpath-Display-Optionen (Points/Arrows/Rapid) · Default-Project/Part/Operation pro User. | [#38](https://github.com/MadGapun/CAMWOSA/issues/38) | [Frontend](Frontend.md) | ⬜ |
| D36 | Hilfe-System — **Glossar mit 60+ CNC-Begriffen** ✅ (Werkzeug-Doku + Operations + Strategien). Hover-Help-Audit auf 200+ Eingaben, Inline-Grafiken pro Strategie, FachTooltip-Pattern-Erweiterung folgen in Frontend-Iteration. | [#41](https://github.com/MadGapun/CAMWOSA/issues/41) | [Tooltip-System](Tooltip-System.md) · [First-Run-Wizard](First-Run-Wizard.md) · [Glossar](Glossar.md) | 🟨 |

| D38 | **Spindel-Editor (UI)** — `editor/SpindelEditor.tsx` + Spindel-Bibliothek in `MaschinenView` (anlegen/bearbeiten/löschen, alle Felder: Typ, RPM min/max, Leistung, Drehmoment, Spannzangen-Ø, Kühlung, **VFD-Hochlauf-Dwell**, PWM-Kennlinie, Notizen). „Als aktiv setzen" pro Maschine (Projekt-Override). Backend-CRUD war vorhanden (`api/endpoints/spindles.py`), nur die UI fehlte. Markus' Anforderung „alles einstellbar". | — | [Spindel](Spindel.md) | ✅ |
| D39 | **Maschinen-Editor (UI)** — `editor/MaschinenEditor.tsx`: Arbeitsraum, Vorschub/Eilgang, Controller, Sicherheitshöhe, Werkzeugwechsel-Position, Postprozessor, **Spindel-Zuordnung + aktiv**, **Modi + aktiv**, Inline-RPM-Fallback, Notizen. Anlegen/Bearbeiten/Löschen in `MaschinenView`. Data-loss-sicher (unmodellierte Felder wie `rotary_profile_ids` reisen mit). Backend-CRUD war vorhanden. Markus' Anforderung „man rüstet seine CNC auf — alles editierbar". | — | [Maschinenprofil-Format](Maschinenprofil-Format.md) | ✅ |
| D40 | **Rotary-Profil-Editor (UI) + Backend-CRUD** — `editor/RotaryProfilEditor.tsx` + Rotary-Bibliothek in `MaschinenView` (17 Felder: Spannfutter, Reitstock, durchschiebbar, `$101` Y-Steps/°, CNCjs-Macros …). Backend-CRUD ergänzt (`POST/PUT/DELETE /api/rotary/profile`, 4 Tests) — vorher nur GET. Letzte Daten-Entität ohne UI-Editor. | — | [Rotary-Indexing](Rotary-Indexing.md) | ✅ |

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

## Teil G — Maschinensteuerung / Sender (separate App)

> **Neu 2026-06.** Eigenständige, **lose gekoppelte** App (nicht Teil von CAMWOSA-Core). CAMWOSA bleibt Pure-CAM (streamt nichts selbst); der Sender spricht GRBL über USB-Serial. Voll-Design: `docs/SENDER-ARCHITEKTUR.md`. Reconcile mit „Pure CAM"-Grundsatz: siehe Abschnitt „Was nicht im Plan steht" unten.

| Nr | Funktion | Issue | Wiki | Status |
|----|----------|-------|------|--------|
| G1 | **Serial + Verbindung** — Port-Scan, Connect/Disconnect, Baud (Default 115200), Welcome-Parse (`Grbl 1.1`), `$$`/`$I` lesen. | [#55](https://github.com/MadGapun/CAMWOSA/issues/55) | [Sender-Architektur](../SENDER-ARCHITEKTUR.md) | ⬜ |
| G2 | **Status-DRO** — 5-Hz-`?`-Polling, Status-Parser (`<State|MPos|FS|Ov|Pn>`), WCO-Cache, WPos-Berechnung. | [#55](https://github.com/MadGapun/CAMWOSA/issues/55) | [Sender-Architektur](../SENDER-ARCHITEKTUR.md) | ⬜ |
| G3 | **Jog + Nullen + Homing** — Jog-Pad (`$J=`), Jog-Cancel (`0x85`), `$H`, `$X`, Achsen nullen (`G10 L20`). | [#55](https://github.com/MadGapun/CAMWOSA/issues/55) | [Sender-Architektur](../SENDER-ARCHITEKTUR.md) | ⬜ |
| G4 | **Streaming-Engine** — Character-Counting (128-Byte-RX), Pause/Resume/Stop, Fortschritt + ETA, Konsole. | [#55](https://github.com/MadGapun/CAMWOSA/issues/55) | [Sender-Architektur](../SENDER-ARCHITEKTUR.md) | ⬜ |
| G5 | **Real-Time-Overrides** — Feed/Rapid/Spindle (`0x90`-`0x9E`), Feed-Hold (`!`), Resume (`~`), **E-Stop** (`0x18`). | [#55](https://github.com/MadGapun/CAMWOSA/issues/55) | [Sender-Architektur](../SENDER-ARCHITEKTUR.md) | ⬜ |
| G6 | **Probing-Wizard** — `G38.2` + Plattendicke, Z-Null setzen mit Bestätigung. | [#55](https://github.com/MadGapun/CAMWOSA/issues/55) | [Sender-Architektur](../SENDER-ARCHITEKTUR.md) | ⬜ |
| G7 | **Sicherheits-Layer** — Alarm/Error-Klartext (Code-Tabellen), Limit-Warnung, Connection-Loss-Handling, **kein Auto-Resume**. | [#55](https://github.com/MadGapun/CAMWOSA/issues/55) | [Sender-Architektur](../SENDER-ARCHITEKTUR.md) | ⬜ |
| G8 | **CAMWOSA-Kopplung** — read-only Job-Export (HTTP) + „In Sender öffnen"; LAN-Discovery optional. | [#55](https://github.com/MadGapun/CAMWOSA/issues/55) | [Sender-Architektur](../SENDER-ARCHITEKTUR.md) | ⬜ |
| G9 | **MCP + i18n + Packaging** — FastMCP-Tools (Parität), DE/EN, Installer/Portable, optional reine Web-UI (Pi/Tablet). | [#55](https://github.com/MadGapun/CAMWOSA/issues/55) | [Sender-Architektur](../SENDER-ARCHITEKTUR.md) | ⬜ |
| G10 | **Controller-Plugins** — Protokoll-Adapter für grblHAL / FluidNC / Marlin-CNC (Zukunft). | [#55](https://github.com/MadGapun/CAMWOSA/issues/55) | [Sender-Architektur](../SENDER-ARCHITEKTUR.md) | ⬜ |

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

Diese Punkte gehören **nicht** zu CAMWOSA-Core — siehe [Architektur > Pure CAM](Architektur.md#pure-cam-keine-maschinen-steuerung):

- **Direkte Maschinen-Steuerung im CAMWOSA-Core** (Jog, Job-Send, Probe-Aufruf) — bleibt draußen. **Aber:** seit 2026-06 als **separate, lose gekoppelte App** geplant → **Teil G (CAMWOSA-Sender)** + `docs/SENDER-ARCHITEKTUR.md`. CAMWOSA-Core streamt weiterhin nichts selbst; der Sender ist ein eigenes Programm (eigener Prozess/Repo), das `.nc`-Dateien fährt. Der „Pure-CAM"-Grundsatz für CAMWOSA selbst bleibt damit intakt.
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
