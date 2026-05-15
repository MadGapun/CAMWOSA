# Verschnittoptimierung (Nesting)

> **Status:** ✅ Bin-Packing implementiert. NO_FIT_POLYGON ueber optionales nest2D.
> **Issue:** [#14](https://github.com/MadGapun/CAMWOSA/issues/14)
> **Code:** [backend/camwosa/nesting/nester.py](../../backend/camwosa/nesting/nester.py) · **Tests:** [backend/tests/nesting/test_nester.py](../../backend/tests/nesting/test_nester.py)

Wenn mehrere Teile aus einer Platte gefraest werden, ordnet CAMWOSA sie automatisch verlustarm an.

## Verwendung

```python
from camwosa.nesting import neste, TeilDefinition, PlattenDefinition

teile = [
    TeilDefinition(id="rohling", breite=130, hoehe=130, anzahl=4),
]
platten = [
    PlattenDefinition(id="buche_600x400", breite=600, hoehe=400),
]

ergebnis = neste(teile, platten, abstand_zwischen_teilen=5)

print(f"{len(ergebnis.platzierungen)} Teile platziert")
print(f"Verschnitt: {ergebnis.verschnitt_prozent:.1f}%")
for p in ergebnis.platzierungen:
    print(f"  Teil {p.teil_id}#{p.instanz_index} auf {p.platte_id}: "
          f"X={p.x} Y={p.y} Rotation={p.rotation_grad}")
```

## Strategien

| Strategie | Status | Bibliothek | Lizenz | Geeignet fuer |
|-----------|--------|------------|--------|---------------|
| `BIN_PACKING` | ✅ | rectpack | MIT | rechteckige Bounding-Boxen, schnell |
| `NO_FIT_POLYGON` | ⬜ | nest2D | LGPL-3.0 (optional) | komplexe Konturen |

`nest2D` ist optional und LGPL — nur installieren wenn polygon-genaues Nesting gewuenscht.

## Faserrichtung (Holz)

Pro Teil definierbar:

```python
TeilDefinition(id="brett", breite=100, hoehe=200, faser_parallel_y=True)
```

Wenn `faser_parallel_y=True`, darf das Teil **nicht** rotiert werden — sonst wird's verworfen (in `nicht_platziert`).

## Sperrzonen

(Phase 1+) Bereiche der Platte als no-go markieren — z.B. Astloch, Spannfutter-Bereich. Aktuell noch nicht implementiert.

## Ergebnis

```python
class TeilPlatzierung:
    teil_id: str
    instanz_index: int       # bei mehreren Stueck: 0..n-1
    platte_id: str
    x: float                  # mm
    y: float                  # mm
    breite: float
    hoehe: float
    rotation_grad: float

class NestingErgebnis:
    platzierungen: list[TeilPlatzierung]
    nicht_platziert: list[tuple[str, int]]  # (teil_id, instanz_index)
    platten_genutzt: list[str]
    verschnitt_prozent: float
    genutzte_flaeche: float
    gesamt_flaeche: float
```

## Beispiel: Markus' Lotus-Schalen

```python
# 4 Rundscheiben Ø130 aus Buche 600x400
teile = [TeilDefinition(id="lotus_rohling", breite=130, hoehe=130, anzahl=4)]
platten = [PlattenDefinition(id="buche_600x400_18", breite=600, hoehe=400)]
ergebnis = neste(teile, platten, abstand_zwischen_teilen=5)

# Erwartetes Ergebnis: alle 4 nebeneinander, ~38% Verschnitt
```

## MCP-Tool

```
nesting_starten(teile_liste=[...], platte={...}, abstand=5)
```

## Verwandt

- [Material-Datenbank](Material-Datenbank.md)
- [Workflow-Modul](Workflow-Modul.md) — Nesting erzeugt Setup mit allen Teilen
- [Operation-Kontur](Operation-Kontur.md)
