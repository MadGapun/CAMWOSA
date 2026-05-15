# Master-Plan — Analyse und Optimierung

> **Stand:** 15.05.2026 · Aktualisiert nach jedem Plan-Review

Diese Seite enthält die kritische Analyse des [Master-Plans](Master-Plan.md). Sie listet Risiken, Trade-offs, Optimierungsmöglichkeiten und konkrete Anpassungen, die in den Plan eingeflossen sind.

---

## Identifizierte Risiken im ursprünglichen Plan

### R1 — Postprozessor zu spät
**Risiko:** Ohne Postprozessor produzieren CAM-Operations keinen prüfbaren G-Code, dann sind die Operations praktisch nicht testbar.
**Maßnahme:** GRBL-Postprozessor-Basis (A4) wird **vor** Operations (A8-A11) gebaut. Erledigt.

### R2 — Datenmodell-Lock-In
**Risiko:** Wenn Datenmodell zu früh festgelegt und nicht erweiterbar, müssen wir später migrieren.
**Maßnahme:**
- Pydantic-Modelle mit `model_config = {"extra": "ignore"}` für Vorwärtskompatibilität.
- SQLAlchemy mit Alembic ab Tag 1 — Schema-Migrationen sind eingeplant.
- Schema-Version im `.cwp`-Format eingebettet (siehe [Projekt-Format](Projekt-Format.md)).

### R3 — shapely-Performance bei großen Geometrien
**Risiko:** Pocketing mit Adaptive Clearing auf großen Flächen kann shapely überfordern (Sekunden statt ms).
**Maßnahme:**
- Toolpath-Berechnung läuft als Background-Job mit Progress-Reporting via Server-Sent-Events.
- Für Adaptive Clearing wird `pyclipper` als Alternative evaluiert (deutlich schneller bei Polygon-Offsets).
- Caching der berechneten Toolpaths pro Operation-Hash.

### R4 — Electron-Backend-Subprozess
**Risiko:** Python-Backend als Subprozess birgt Race-Conditions beim App-Start (Backend nicht ready, UI versucht zu laden).
**Maßnahme:**
- Health-Endpoint `/health` im Backend, Electron pollt bis "ready".
- Splash-Screen während Backend-Bootstrap.
- Logs des Backend-Subprozesses werden in einen Tray-erreichbaren Log-Viewer geschrieben (Debugbarkeit).

### R5 — Nesting-Algorithmus-Lizenz
**Risiko:** `nest2D` ist eine Wrapping-Bibliothek über libnest2d (LGPL-3.0). LGPL ist mit MIT vereinbar bei dynamischer Verlinkung, sollte aber dokumentiert sein.
**Maßnahme:**
- Lizenz-Doku in [Nesting](Nesting.md) explizit auflisten.
- `rectpack` ist MIT — wird Default. `nest2D` als optionales Backend für No-Fit-Polygon.
- Pure-Python-Fallback (langsamer aber lizenzfrei) für minimalen Build.

### R6 — STL kann beliebig groß werden
**Risiko:** Eine 100-MB-STL würgt die Heightmap-Berechnung ab.
**Maßnahme:**
- STL-Größe vor Verarbeitung prüfen, ab Schwelle Mesh-Reduzierung anbieten (`open3d` oder `meshlab`-Subprozess).
- Heightmap mit konfigurierbarer Auflösung (Default 0.2 mm).
- Numpy-vektorisierte Berechnung statt Python-Loop.

### R7 — i18n-Aufwand bei deutscher Operation-Terminologie
**Risiko:** Englische Übersetzungen für CAM-Begriffe wie "Eintauchstrategie" oder "Schlichtgang" können verwirren — Werkstatt-Englisch ist anders als Lehrbuch-Englisch.
**Maßnahme:**
- Translation-Keys auf Deutsch (`t('operation.tasche.eintauchstrategie.helix')`), Werte für DE und EN.
- Glossar im Wiki ([Glossar](Glossar.md)) mit DE-EN-Mapping als Referenz für Übersetzer.
- EN-Übersetzung erfolgt nach Stabilisierung der DE-Begriffe (Phase E1).

### R8 — Sicherheits-Checks-Override
**Risiko:** Wenn Override zu einfach ist, ignorieren Nutzer Warnungen. Wenn zu schwer, frustriert es bei False-Positives.
**Maßnahme:**
- Blocker (G0 im Material, Arbeitsraum-Verletzung) erfordern explizite Eingabe ("VERSTANDEN" tippen).
- Override wird im Projekt protokolliert (wer/wann/warum).
- Telemetrie (lokal, opt-in) hilft False-Positive-Quote zu monitoren.

### R9 — Monaco-Editor-Bundle-Größe
**Risiko:** Monaco-Editor ist groß (~2 MB minified). Für Electron OK, aber Lade-Performance.
**Maßnahme:**
- Monaco wird lazy-loaded — erst wenn G-Code-Editor geöffnet wird.
- Nur nötige Sprachen registriert (eigener G-Code-Mode statt Bundle).

### R10 — Rotary ohne Maschine validieren
**Risiko:** Ich (Claude) habe keine ProVerXL. Rotary-G-Code-Korrektheit ist nur gegen DeskProto-Output prüfbar.
**Maßnahme:**
- Referenz-DXFs + erwartete G-Code-Outputs aus DeskProto-Bestand sammeln.
- Snapshot-Tests: gleicher Input → gleicher G-Code (oder dokumentierte Abweichung).
- Markus testet die ersten Rotary-Outputs auf der Maschine, bevor Wrapping als ✅ markiert wird.

---

## Optimierungen am Plan

### O1 — Geometrie-Hilfsmodul als A7 (neu)
**Vorher:** shapely-Aufrufe verteilten sich über alle Operations.
**Nachher:** Eigenes `cam.geometry`-Modul kapselt Offset, Boolean, Clipping, Bounding-Box. Vereinfacht Tests und Algorithmus-Austausch (z.B. `pyclipper` statt `shapely`).

### O2 — Backplot-Annotation als eigene Position A31
**Vorher:** Im G-Code-Editor (D16) versteckt.
**Nachher:** Als Backend-Feature des Postprozessors. So ist der G-Code unabhängig vom Editor lesbar.

### O3 — Maschinen-Modi-Konzept als A25 vor Rotary
**Vorher:** Rotary direkt als Postprozessor.
**Nachher:** Erst das **Konzept** (ein Maschinenprofil mit mehreren Modi), dann der konkrete Rotary-Postprozessor (A26). Ermöglicht spätere Modi (Laser, Drag-Knife) ohne Refactoring.

### O4 — Postprozessor-Plugin-System früh (A5)
**Vorher:** Plugin-System spät.
**Nachher:** Direkt nach erstem Postprozessor (A4 → A5). Damit ist die API von Anfang an plugin-fähig — nicht nachträglich umstrukturiert.

### O5 — Drechsel-Operationen als A30
**Vorher:** Im ursprünglichen Spec Phase 4 weit hinten.
**Nachher:** Direkt nach Rotary-Wrapping. Drechsel ist Rotary mit speziellen Strategien — sollte unmittelbar darauf folgen, sonst veraltet das Wissen.

### O6 — REST-API als eigener Teil B
**Vorher:** API verstreut in einzelnen Backend-Modulen.
**Nachher:** Klare Trennung: Backend-Module sind Bibliotheken, API ist Wrapper. So ist die Library auch ohne Flask nutzbar (z.B. Skripte, Tests).

### O7 — MCP-Tool-Parität als hartes Kriterium (B5)
**Vorher:** MCP hat eine "Auswahl" an Tools.
**Nachher:** **Vollständige Parität** mit der UI-API. Jede Backend-Funktion ist sowohl per UI als auch per MCP erreichbar. Sonst wird MCP zur Zweitklasse-Bedienung.

### O8 — Auto-Updater als eigene Position F5
**Vorher:** Im Electron-Skelett.
**Nachher:** Eigener Punkt — weil Auto-Update auch Backend-Updates braucht (Python-Bundle), nicht nur Electron.

### O9 — Schritt-für-Schritt-Test-Strategie
- Backend-Module: 100% pytest-Coverage angestrebt für `cam/`, `gcode/`, `safety/`, `feeds/`. Niedrigere Schwellen (>70%) für `api/`, `db/`.
- Snapshot-Tests für G-Code-Output (kleine Änderungen am Postprozessor brechen ggf. erwarteten Output, was bewusst auffallen muss).
- Frontend: vitest + React Testing Library. Kritische Module (Preview, Editor) zusätzlich Playwright-Smoke-Tests.

### O10 — Issue-Aufteilung im Repo
- Bestehende Issues bleiben als Phasen-Tickets.
- **Pro Position im Master-Plan ein Sub-Issue** unter dem Hauptissue als Aufgabenliste.
- Sub-Issues verlinken auf den Wiki-Stub und werden geschlossen sobald Wiki-Eintrag fertig ist.

---

## Reihenfolge-Trade-offs

| Diskutierte Reihenfolge | Bewertung |
|---|---|
| Erst kleine MVP (DXF→Kontur→GRBL), dann iterativ erweitern | Verworfen — Markus will alles, Plan zielt auf vollständiges Tool. Iteration findet innerhalb der Komponenten statt, nicht am Scope. |
| Frontend parallel zu Backend ab A2 | Verworfen — Backend-API muss stabil sein, sonst doppelter Aufwand. UI startet wenn API bereit ist. |
| MCP vor UI | Geprüft — MCP braucht Backend-API (B1-B3) genauso wie UI. Beide starten parallel **nach** Backend-API steht. |
| Rotary früher | Verworfen — Rotary baut auf Standard-CAM auf. Vorziehen bringt nichts und blockiert Standard-Pfad. |
| Nesting nach Operations | Behalten — Nesting transformiert Geometrien vor Operations, nicht danach. Reihenfolge passt. |

---

## Was wird getrackt

- **Plan-Fortschritt:** Status-Spalten im [Master-Plan](Master-Plan.md) werden mit jedem Schritt aktualisiert.
- **Wiki-Vollständigkeit:** Diese Datei listet alle Wiki-Stubs. Sobald ein Stub vollständig wird, hat die Position das ✅.
- **Issue-Verlinkung:** Jede Position verweist auf das relevante GitHub-Issue.
- **Test-Coverage:** Wird im CI gemessen (Phase F4).

---

## Annahmen die noch zu prüfen sind

- [ ] Makita RT0700 RPM-Range: Spec sagt 10.000–30.000, Issue #3 sagt 10.000–24.000. **Markus klärt.**
- [ ] Welcher Schriften-Provider für Text-Gravur? (Vorschlag: System-Fonts via `fontTools` extrahieren → Vektoren).
- [ ] Cloud-Sync-Backend für E5 — wenn ja, welcher Provider? (Vorschlag: nur GitHub-Gist als Sharing-Mechanismus, kein eigener Server).
- [ ] Update-Mechanismus: Squirrel.Windows + electron-updater, oder eigener Updater wie PBP? (Vorschlag: electron-updater, Backend-Bundle als Asset).
- [ ] Nesting-Default-Bibliothek: rectpack (MIT, schnell, nur Rechtecke) vs. nest2D (LGPL, langsamer, polygon-fähig). Vorschlag: beide unterstützen, rectpack default.

---

## Änderungs-Historie

| Datum | Änderung |
|---|---|
| 2026-05-15 | Erstanlage. Plan A-F mit Optimierungen O1-O10 und Risiken R1-R10. |
