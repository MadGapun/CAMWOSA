# Postprozessor-Plugin-System

> **Status:** ✅ Implementiert.
> **Issue:** [#10](https://github.com/MadGapun/CAMWOSA/issues/10)
> **Code:** [backend/camwosa/postprocessor/base.py](../../backend/camwosa/postprocessor/base.py) · **Tests:** [backend/tests/postprocessor/test_grbl.py](../../backend/tests/postprocessor/test_grbl.py)

CAMWOSA unterstuetzt **eigene Postprozessoren** als User-Plugins. Jeder Postprozessor ist eine Python-Klasse, die von `PostProcessor` erbt.

## Mitgelieferte Postprozessoren

| ID | Klasse | Beschreibung |
|----|--------|--------------|
| `grbl_standard` | `GRBLStandard` | GRBL 1.1 Standard |
| `grbl_genmitsu` | `GRBLGenmitsu` | Genmitsu (ProVerXL, PROVer) — Standard + Modus-Hinweis |
| `grbl_genmitsu_rotary_y` | `GRBLGenmitsuRotaryY` | Genmitsu mit Y-Achse als Rotary |

## Postprozessor-API

```python
from camwosa.postprocessor.base import PostKontext, PostProcessor
from camwosa.gcode.toolpath import Bewegung, BewegungsTyp


POSTPROCESSOR_ID = "meine_maschine_v1"


class MeinPostProcessor(PostProcessor):
    name = "Meine Maschine v1"
    file_extension = ".nc"
    beschreibung = "Mein eigener Postprozessor fuer Maschine XY"

    def header(self, ctx: PostKontext) -> list[str]:
        return [
            self._kommentar(f"Maschine: {ctx.maschine.name}"),
            "G21", "G90", "G17", "G94",
        ]

    def footer(self, ctx: PostKontext) -> list[str]:
        return ["M5", "M30"]

    def tool_change(self, ctx: PostKontext, tool) -> list[str]:
        return ["M5", "G0 Z25", "M0"]

    def rapid_move(self, ctx: PostKontext, b: Bewegung) -> list[str]:
        return [f"G0 X{b.x:.3f} Y{b.y:.3f} Z{b.z:.3f}"]

    def linear_move(self, ctx: PostKontext, b: Bewegung) -> list[str]:
        feed = b.feed or ctx.maschine.sicherer_vorschub
        return [f"G1 X{b.x:.3f} Y{b.y:.3f} Z{b.z:.3f} F{feed:.0f}"]

    def arc_move(self, ctx: PostKontext, b: Bewegung) -> list[str]:
        feed = b.feed or ctx.maschine.sicherer_vorschub
        cmd = "G2" if b.typ == BewegungsTyp.BOGEN_CW else "G3"
        return [
            f"{cmd} X{b.x:.3f} Y{b.y:.3f} Z{b.z:.3f} "
            f"I{b.i or 0:.3f} J{b.j or 0:.3f} F{feed:.0f}"
        ]
```

## Plugin laden

User-Postprozessoren werden aus einem Verzeichnis geladen — beim App-Start automatisch aus `data/postprocessors/user/`, oder manuell:

```python
from pathlib import Path
from camwosa.postprocessor import registry

anzahl = registry().lade_aus_verzeichnis(Path("./meine_posts"))
print(f"{anzahl} Postprozessoren geladen")
print(registry().list_ids())
```

## Anforderungen an ein Plugin

Jede Plugin-Datei muss:
1. Eine Modul-Konstante `POSTPROCESSOR_ID` (str) enthalten.
2. Genau eine Subklasse von `PostProcessor` exportieren.
3. Die abstrakten Methoden `rapid_move`, `linear_move`, `arc_move` implementieren.

## Verzeichnis-Konvention

```
data/
├── postprocessors/
│   ├── user/        # User-Plugins (update-resistent)
│   └── community/   # Community-PRs
```

Beide Verzeichnisse werden beim Start gescannt.

## Validierung

- Pflicht-Methoden werden via `abstractmethod`-Decorator durchgesetzt.
- Fehler beim Laden werfen `RuntimeError` mit Datei-Hinweis.
- `POSTPROCESSOR_ID`-Konstante fehlt → `ValueError`.
- Keine `PostProcessor`-Subklasse gefunden → `ValueError`.

## Was ein Postprozessor NICHT machen darf

- **Kein Datei-IO** ausserhalb der erlaubten Verzeichnisse.
- **Keine Subprocesse starten.**
- **Kein Netzwerk-Zugriff.**

Diese Regeln werden noch nicht technisch erzwungen (kommt mit dem Plugin-Validierungssystem), sind aber Voraussetzung fuer die Community-Aufnahme.

## Verwandt

- [Postprozessor-GRBL](Postprozessor-GRBL.md)
- [Postprozessor-GRBL-Genmitsu](Postprozessor-GRBL-Genmitsu.md)
- [Postprozessor-GRBL-Rotary](Postprozessor-GRBL-Rotary.md)
- [Contribution-Guide](Contribution.md)
