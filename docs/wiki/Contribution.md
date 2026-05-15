# Contribution-Guide

CAMWOSA ist Open Source unter MIT-Lizenz. Beiträge sind willkommen — egal ob Bugfix, neuer Postprozessor oder Material-Eintrag.

## Wer kann beitragen

- **Code-Beiträge:** Pull Requests über GitHub.
- **Postprozessoren:** Eigene Postprozessoren als Plugin (siehe [Postprozessor-Plugins](Postprozessor-Plugins.md)).
- **Material- und Werkzeug-Daten:** JSON-Dateien als PR oder via Community-Sharing (Phase E5).
- **Dokumentation:** Wiki-Verbesserungen, neue Tutorials, Beispiele.
- **Bug-Reports:** GitHub-Issues mit Reproduzier-Schritten.
- **Feature-Wünsche:** GitHub-Issues mit klarem Use-Case.

## Wichtigste Regel

**Jede Funktion braucht einen Wiki-Eintrag.** Pull Requests ohne Wiki-Update werden nicht gemerged.

## Setup für Entwickler

### Voraussetzungen

- Python 3.11+
- Node.js 20+
- Git
- (Optional) Eine GRBL-Maschine für Real-Tests

### Repository klonen

```bash
git clone https://github.com/MadGapun/CAMWOSA.git
cd CAMWOSA
```

### Backend einrichten

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -e ".[dev]"
pytest
```

### Frontend einrichten

```bash
cd frontend
npm install
npm run dev
```

### Electron starten (Dev-Modus)

```bash
cd electron
npm install
npm run dev
```

### MCP-Server starten

```bash
cd mcp_server
pip install -e .
python -m camwosa_mcp.server
```

## Code-Konventionen

### Python (Backend)
- **Python 3.11+**
- **Type-Hints überall** (mypy-strict)
- **pydantic 2** für Datenmodelle
- **pytest** für Tests, Test-Namen auf Deutsch (`def test_dxf_geschlossene_kontur_wird_erkannt`)
- **Docstrings auf Deutsch** (Module + öffentliche Funktionen)
- **`black`** als Formatter, **`ruff`** als Linter
- Imports in dieser Reihenfolge: stdlib → third-party → camwosa-intern

### TypeScript (Frontend / Electron)
- **TypeScript strict mode**
- **Functional Components** mit Hooks
- **zustand** für State Management — kein Redux
- **i18next**: Strings nicht hardcoden, immer `t('schluessel')`
- **Translation-Keys auf Deutsch** (`operation.tasche.titel`)
- **Tailwind** für Styles, keine CSS-Module außer in Ausnahmen
- **`prettier`** + **`eslint`**

### Tests
- **Backend:** pytest, Coverage-Ziel 80%+ für `cam/`, `gcode/`, `safety/`, `feeds/`
- **Frontend:** vitest + React Testing Library
- **E2E:** Playwright für kritische Flows (DXF-Import → G-Code-Export)
- **Snapshot-Tests** für G-Code-Output (Postprozessor-Änderungen müssen bewusst gereviewed werden)

### Commit-Messages
Konvention: [Conventional Commits](https://www.conventionalcommits.org/)

```
feat(dxf): unterstuetzte SPLINE-Entities fuer Solid-Edge-Export
fix(gcode): GRBL-Header-Zeile bei leerem Kommentar
docs(wiki): Postprozessor-Plugin-Beispiel ergaenzt
test(safety): G0-im-Material-Check fuer schraege Anfahrten
```

## Pull Request Workflow

1. Issue erstellen oder existierendes referenzieren.
2. Branch von `main`: `feature/<kurzbeschreibung>` oder `fix/<kurzbeschreibung>`.
3. Implementierung **mit Tests**.
4. Wiki-Eintrag schreiben oder aktualisieren (`docs/wiki/<Funktion>.md`).
5. PR öffnen mit:
   - Verweis auf Issue (`Closes #X`)
   - Was geändert wurde
   - Wie es getestet wurde
   - Screenshot bei UI-Änderungen
6. Review abwarten, Anmerkungen einarbeiten.
7. Merge nach Freigabe.

## Postprozessor beitragen

Eigene Postprozessoren sind besonders willkommen — CAMWOSA wird besser je mehr Maschinen unterstützt sind.

Siehe [Postprozessor-Plugins](Postprozessor-Plugins.md) für die API. Kurzform:

```python
from camwosa.postprocessor.base import PostProcessor

class MeinPostProcessor(PostProcessor):
    name = "Meine Maschine v1"
    file_extension = ".nc"

    def header(self, ctx):
        return ["G21", "G90", "G17"]

    def linear_move(self, x, y, z, feed):
        return [f"G1 X{x:.3f} Y{y:.3f} Z{z:.3f} F{feed:.0f}"]

    # ... weitere Methoden
```

Datei in `backend/camwosa/postprocessor/community/` ablegen, Test in `backend/tests/postprocessor/community/`, Wiki-Eintrag in `docs/wiki/Postprozessor-MeineMaschine.md`.

## Material- oder Werkzeug-Daten beitragen

JSON-Format siehe [Material-Datenbank](Material-Datenbank.md) und [Werkzeug-Bibliothek](Werkzeug-Bibliothek.md).

Eintrag in `data/materials/community/` bzw. `data/tools/community/` ablegen, mit Quellenangabe (Hersteller-Datenblatt, eigene Erfahrung etc.).

## Verhaltenskodex

- Respektvoller Umgang.
- Konstruktive Kritik, kein Personen-Bashing.
- Hilf neuen Beitragenden — jeder hat mal angefangen.

## Lizenz

Beiträge stehen unter MIT-Lizenz, siehe [LICENSE](https://github.com/MadGapun/CAMWOSA/blob/main/LICENSE).

Mit dem Einreichen eines PR bestätigst du, dass du dazu berechtigt bist und dem Projekt das Recht einräumst, deinen Beitrag unter MIT zu verbreiten.

## Wo Hilfe holen

- **GitHub-Issues:** Bugs und Feature-Wünsche
- **GitHub-Discussions:** Fragen, Ideen, Diskussionen (sobald aktiviert)
- **Wiki:** Diese Doku — wenn etwas fehlt, gerne PR aufmachen
