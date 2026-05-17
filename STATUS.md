# CAMWOSA — Aktueller Stand

Kompakter Snapshot was läuft, was offen ist, wo der nächste Aufschlag sinnvoll ist.
Detaillierte Begründungen + Beispiele liegen im [Wiki](docs/wiki/).

## Tests

| Bereich | Stand |
|---------|-------|
| Backend pytest | **542 / 542** grün (+ 1 skipped Integration-Smoke fuer [ai]) |
| Frontend (npm) | nicht ausgeführt — kein `node_modules` lokal |
| MCP-Server | Syntax-OK, smoke nicht ausgeführt |
| Frontend vitest | `varianteStore.test.ts` mit 14 Tests angelegt — nicht ausgeführt mangels `node_modules` |

## Backend — Module-Übersicht

| Modul | Zweck | Status |
|-------|-------|--------|
| `db/models.py` | Maschine, Spindel, Werkzeug (mit Segmenten), Material, Rohmaterial | ✅ |
| `db/cutting_presets.py` | Schnittparameter als Top-Level-Entität, Legacy-Migration | ✅ |
| `db/crud.py` | Einzeldatei-CRUD mit Dedup gegen Sammel-Defaults | ✅ |
| `db/rotary.py` | Rotary-Profile (Spannfutter, Reitstock, durchschiebbar) | ✅ |
| `db/standzeit.py` | Werkzeug-Standzeit-Tracking | ✅ |
| `cad/` | Plugin-System für DXF/SVG/STL/STEP | ✅ |
| `cam/` | Kontur / Tasche / Bohren / Gravur / Relief / Spezial / PCB / Bohrbild | ✅ |
| `cam/overrides.py` | Per-Feature-Override-Auflöser (Quellen-Hierarchie) | ✅ |
| `cam/parameter.py` | Pydantic-Modelle aller Operations-Parameter | ✅ |
| `cam/rotary.py` | 2D → Zylinder-Wrapping | ✅ |
| `gcode/` | Toolpath-Modell, Postprozessor-Registry | ✅ |
| `postprocessors/` | GRBL Standard + Rotary-Y | ✅ |
| `project/schema.py` | CWPProjekt, Variante, Setup, Annotation | ✅ |
| `project/schritte.py` | ArbeitsSchritt-Union (Operation/WW/Umspann/Achswechsel/ManualNC/Pause) | ✅ |
| `project/io.py` | .cwp-ZIP-Container Lesen/Schreiben | ✅ |
| `safety/` | Sicherheits-Checks inkl. Segment-basierter Kollision | ✅ |
| `workflow/manager.py` | Pre-Check Workflow, gcode-pro-Setup | ✅ |
| `workflow/gcode_schritte.py` | G-Code-Bloecke aus Schritt-Liste, WW-Strategie | ✅ |
| `workflow/arbeitsplan.py` | Arbeitsplan-Markdown + PDF | ✅ |
| `workflow/annotationen_zu_operationen.py` | Auto-Generator (Anschlag → Bohrop) | ✅ |
| `quickcam/templates.py` | 4 Templates (Tasche, Schriftzug, Bohrlochmuster, Kontur) | ✅ |
| `cam/drechseln.py` | Drechsel-Operationen (Continuous-Lathe) — Profil, Schruppen, Schlichten, Helix | ✅ Backend + Frontend |
| `cam/wrap.py` | Wrap-Mode — 2D-Design auf Zylinder (Y → A°), Gravur/Kontur auf Rundmaterial | ✅ Backend + API + MCP + Frontend |
| `cam/simulation.py` | Voxel-Material-Abtrag-Sim mit Werkzeug-Stempel + Surface-Extraktion | ✅ |
| `stl/bild_heightmap.py` | Bild → Heightmap (Phase A der Bild-zu-Relief-Pipeline) | ✅ Backend + API + MCP + Frontend |
| `workflow/auto_cam.py` | High-Level-Aufgaben → komplettes Projekt (Master-Plan B6) | ✅ Backend + MCP-Tool |
| `api/` | Flask-Endpoints, alles über REST + alles CRUD | ✅ |

## Frontend — Views & Editoren

| Komponente | Status |
|------------|--------|
| `views/QuickStartView` | ✅ Galerie + Template-Picker |
| `views/ProjektView` | ✅ Basis (Markus' Workflow-Start) |
| `views/MaschinenView` | ✅ |
| `views/WerkzeugeView` | ✅ Liste + Editor + V-Bit-Smart-Helper |
| `views/MaterialienView` | ✅ Liste + Editor + CuttingPreset-Editor |
| `views/ZeichnenView` | ✅ Konva-Editor + Annotationen-Integration (Pick + Auto-Op-Generator) |
| `views/OperationenView` | ✅ Override-Form + Live-3D-Preview |
| `views/PreviewView` | ✅ ToolpathStage mit tiefem Zoom |
| `views/Simulation3DView` | ✅ Three.js |
| `views/GCodeEditorView` | ✅ Monaco mit CAMWOSA-Syntax-Highlighting (orange Drechsel-Banner, gelbe Warnungen, blaue CNCjs-Macros) |
| `views/WorkflowView` | ✅ Setup-Karten + SchrittListe-Editor pro Setup |
| `views/NestingView` | ✅ |
| `views/EinstellungenView` | ✅ |
| `views/DrechselnView` | ✅ Profil-Editor + 3D-Revolution-Preview + alle 4 Strategien |
| `views/WrapView` | ✅ 2D-Pfad-Editor + 3D-Zylinder-Preview + Live-Pruefung + Vorlagen |
| `views/MaterialAbtragView` | ✅ Voxel-Sim mit Three.js InstancedMesh |

| Editor | Status |
|--------|--------|
| `editor/WerkzeugEditor` | ✅ |
| `editor/MaterialEditor` | ✅ |
| `editor/CuttingPresetEditor` | ✅ |
| `editor/SchrittListeEditor` | ✅ |
| `editor/AnnotationenEditor` | ✅ |
| `editor/DrechselProfilEditor` | ✅ Konva-Halbschnitt + Three.js Revolution |
| `components/FirstRunWizard` | ✅ 4-Schritt-Onboarding (Maschine/Spindel/Werkzeug/Material) |
| `components/Tooltip` | ✅ 3 Stufen (WertTooltip / FachTooltip / CoachMark) |
| `components/fachbegriffe` | ✅ 12 zentrale CAM-Erklaerungen (Stepdown, Stepover, Spanlast, ...) |
| FachTooltips integriert in | ✅ OverrideForm, FeedsSpeedsPanel, CuttingPresetEditor, MaterialEditor, DrechselnView, WerkzeugEditor, QuickStartView |
| `WerkzeugeView`: Standzeit-Progress-Bar | ✅ farbig nach Status |

| System | Status |
|--------|--------|
| `state/uiPrefs` | ✅ Theme/Density/Vorschau-Modus + Sichtbarkeit |
| `styles/tokens.css` | ✅ Komplettes Design-System aus Design-Exploration |
| `components/OperationPreview3D` | ✅ 3 Modi (aus/vereinfacht/komplett) |
| `components/UIPrefsMenu` | ✅ Pop-Menu in Topbar |
| Floating-Toggles + Hotkeys (F/Esc/B/T) | ✅ |

## Roadmap-Position

| Phase | Stand |
|-------|-------|
| Phase 1 — MVP | **fertig** |
| Phase 2 — Tiefe | **fertig** — STL, Plugins, Voxel-Material-Abtrag-Simulation |
| Phase 3 — Rotary | **fertig** |
| Phase 4 — Drechseln | **fertig** — Backend + Postprozessor + Frontend-Profil-Editor mit 3D-Revolution-Preview + alle 4 Strategien |
| Phase 5 — Pro | großteils vorgezogen, Adaptive-Clearing fertig |

## Was als Nächstes sinnvoll ist

**Arbeitsprinzip:** Master-Plan-First. Nach Reihenfolge der offenen Positionen im [Master-Plan](docs/wiki/Master-Plan.md):

| Pos | Funktion | Issue | Aufwand |
|-----|----------|-------|---------|
| ~~A19~~ | ~~Varianten-System Frontend-Switcher~~ — **fertig** (`VarianteSwitcher` in Topbar + Verwaltungs-Modal + `varianteStore` mit Snapshot-Logik + 14 Vitests + Wiki) | [#9](https://github.com/MadGapun/CAMWOSA/issues/9) | ✅ |
| ~~A34~~ | ~~Bild-zu-Relief Phase C — Wrap-Kombination~~ — **fertig** (`erzeuge_wrap_relief_toolpath` + Pruefung + 2 API-Endpoints + 12 neue Tests) | [#16](https://github.com/MadGapun/CAMWOSA/issues/16) | ✅ |
| ~~A35~~ | ~~Bild-zu-Relief Phase D Backend — 6 Filter (Gamma/Stretch/Zero-Plane/Edge-Boost/Smoothing/Detail-Slider) + 6 API-Endpoints + 22 Tests~~ — **fertig** (Frontend-Filterpanel ist D25) | [#17](https://github.com/MadGapun/CAMWOSA/issues/17) | ✅ |
| ~~A36~~ | ~~Bild-zu-Relief Phase E [ai]-Extra — AI-Tiefenschaetzung Scaffolding (Depth-Anything-V2 + MiDaS via transformers, Lazy-Import, API + 9 Tests + 1 Integration-Smoke)~~ — **fertig** | [#18](https://github.com/MadGapun/CAMWOSA/issues/18) | ✅ |
| ~~A37~~ | ~~Text-zu-Pfad-Konverter — fontTools, System-Font-Fallback, robuste Loch-Erkennung via Contains-Hierarchie, integriert in auto_cam_erstellen.beschriftung_wrap, 2 API-Endpoints + 18 Tests~~ — **fertig** | [#19](https://github.com/MadGapun/CAMWOSA/issues/19) | ✅ |
| ~~A38~~ | ~~Wrap-Pattern-Skalierung Backend (3 Modi: feste / auf_werkstueck / wiederholen) + Batch-Toolpath fuer Polygon-Listen + 2 API-Endpoints + 18 Tests~~ — **fertig** (DXF-Frontend-Integration kommt mit WrapView-Update) | [#20](https://github.com/MadGapun/CAMWOSA/issues/20) | ✅ |
| ~~B3~~ | ~~OpenAPI-3.1-Spec automatisch generiert aus Flask-Routen + Docstrings, `GET /api/openapi.{json,yaml}` + Swagger-UI `/api/docs` + 9 Tests~~ — **fertig** | — | ✅ |
| ~~D4~~ | ~~Projekt-Verwaltung Frontend (Neu/Oeffnen/Speichern/Speichern-Als + projektStore + projektIO Bridge + 5 API-Tests + Wiki)~~ — **fertig** | [#9](https://github.com/MadGapun/CAMWOSA/issues/9) | ✅ |
| ~~E4~~ | ~~Adaptive Clearing — kleiner Stepover (12%) + trochoidale Sinus-Modulation senkrecht zur Bahn + 2 neue Parameter-Felder + 5 Tests~~ — **fertig** | — | ✅ |
| ~~D25~~ | ~~Bild-Relief-Filterpanel Frontend — `HeightmapFilterStack` mit 6 Filtern + Reorder + Toggle + Reset, AI-Modus-Umschalter mit Modell-Auswahl, integriert in BildReliefView~~ — **fertig** | [#17](https://github.com/MadGapun/CAMWOSA/issues/17) [#18](https://github.com/MadGapun/CAMWOSA/issues/18) | ✅ |
| C4 / F5 | Auto-Updater Frontend + Backend (blockiert auf ersten Release) | — | 2-3 Tage |
| F3 | Code-Signing (Windows + macOS) | — | 1-2 Tage |

**Parallel zum Master-Plan**: Markus testet die App tatsaechlich (`cd frontend && npm install && npm run dev` + Electron-Wrapper starten).

**Bewusst NICHT auf der Roadmap:**
- Direkter Sender-Push (CNCjs / UGS / Candle / seriell) — Markus laedt G-Code-Dateien manuell, will sich offenhalten welcher Sender spaeter dazukommt
- **Innen-Drechseln** (Schalen-Innen) — hardware-bedingt unmoeglich. Die ProVerXL-Spindel haengt vertikal, der Fraeser kommt nicht von der Seite in einen Hohlraum rein. Wer das will, spannt das Werkstueck danach um und bearbeitet als Standard-XYZ-Tasche.

## Bekannte offene Punkte / Tech-Debt

- **`__geometrie` / `__punkte` / `__quelle`** als Magic-Keys im Parameter-Dict — sollten in eigene Felder migrieren wenn Schema v3 ansteht
- **`_tool_nummer` per Hash** in `workflow/gcode_schritte.py` — funktioniert, aber ein deterministisches Mapping pro Werkzeug-Name wäre nutzerfreundlicher
- **Frontend-Tests** (vitest) sind angelegt aber nicht ausgeführt
- **`MaterialEditor` ohne Validation** bei numerischen Feldern — fängt nur Server-Fehler
- **Floating-Toggle-Bar overlappt** möglicherweise mit Header-Buttons in einigen Views — UI-Test ausstehend
- **`OperationPreview3D` macht eigene OrbitControls per Hand** statt drei/drei — Doppel-Implementation gegenüber `Simulation3D`

## Wiki-Index

Siehe [docs/wiki/Home.md](docs/wiki/Home.md). Wichtigste Seiten in dieser Session:

- [Design-System](docs/wiki/Design-System.md)
- [ArbeitsSchritt](docs/wiki/ArbeitsSchritt.md)
- [Multi-Werkzeug-Setup](docs/wiki/Multi-Werkzeug-Setup.md)
- [CuttingPreset](docs/wiki/CuttingPreset.md)
- [QuickCAM](docs/wiki/QuickCAM.md)
- [Geometrie-Annotationen](docs/wiki/Geometrie-Annotationen.md)
- [CRUD-API](docs/wiki/CRUD-API.md)
- [UI-Integration](docs/wiki/UI-Integration.md)
- [MCP-Server](docs/wiki/MCP-Server.md)
