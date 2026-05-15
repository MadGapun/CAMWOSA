# CAMWOSA Backend

Python-Backend für CAMWOSA. Stellt CAM-Logik, Geometrie-Verarbeitung, G-Code-Generierung und Sicherheits-Checks als Bibliothek **und** als Flask-API bereit.

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -e ".[dev]"
pytest
```

## Module

| Modul | Verantwortung |
|-------|---------------|
| `camwosa.api` | Flask-REST-API, Endpoints |
| `camwosa.cam` | CAM-Operationen (Kontur, Tasche, Bohren, Gravur, Relief) + Geometrie-Hilfen |
| `camwosa.db` | SQLAlchemy-Modelle, Alembic-Migrationen |
| `camwosa.dxf` | DXF-Parser (ezdxf) |
| `camwosa.feeds` | Feeds & Speeds Rechner |
| `camwosa.gcode` | G-Code-Builder (postprozessor-agnostisch) |
| `camwosa.nesting` | Verschnittoptimierung |
| `camwosa.postprocessor` | GRBL, Genmitsu, Rotary, Plugin-System |
| `camwosa.project` | `.cwp`-Format (Speichern/Laden) |
| `camwosa.safety` | Sicherheits-Checks |
| `camwosa.stl` | STL-Parser + Heightmap |
| `camwosa.workflow` | Multi-Setup-Modul |

Siehe Wiki: [Architektur](../docs/wiki/Architektur.md), [Master-Plan](../docs/wiki/Master-Plan.md).

## Backend starten (Standalone für Tests)

```bash
camwosa-backend
# bindet auf http://127.0.0.1:8765 (Default)
```

## Tests

```bash
pytest
pytest --cov=camwosa --cov-report=html
```

## Lint

```bash
ruff check .
ruff format .
mypy camwosa
```
