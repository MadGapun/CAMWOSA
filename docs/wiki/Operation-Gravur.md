# Operation: Gravur

> **Status:** ✅ KONSTANTE_TIEFE; ⬜ V_CARVING in Folge-Iteration.
> **Issue:** [#1](https://github.com/MadGapun/CAMWOSA/issues/1)
> **Code:** [backend/camwosa/cam/gravur.py](../../backend/camwosa/cam/gravur.py)

Folgt einer Kurve mit definierter Tiefe.

## Verwendung

```python
from camwosa.cam import erzeuge_gravur_toolpath
from camwosa.cam.parameter import GravurParameter, GravurStrategie

param = GravurParameter(
    werkzeug_id="vbit_60grad",
    spindel_rpm=18000,
    vorschub=1500,
    eintauch_vorschub=300,
    sicherheitshoehe=5.0,
    max_tiefe=1.0,
    stepdown=0.5,
    strategie=GravurStrategie.KONSTANTE_TIEFE,
    max_zustellung=0.5,
)

tp = erzeuge_gravur_toolpath(linestring, vbit, param)
```

## Strategien

| Strategie | Status | Beschreibung |
|-----------|--------|--------------|
| `KONSTANTE_TIEFE` | ✅ | Folgt der Kurve mit fester Z-Tiefe |
| `V_CARVING` | ⬜ | Variable Tiefe entlang medialer Achse (V-Bit) |

V-Carving braucht einen medial-axis-Algorithmus (z.B. via Voronoi auf dem Polygon-Inneren). Implementierung in Phase 1+ geplant.

## Eingabe

- `LineString` (offene Kontur) — Werkzeug folgt direkt
- `Polygon` — Werkzeug folgt Aussenkontur **und** allen Innenringen

## Parameter

| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| `strategie` | `KONSTANTE_TIEFE` | siehe Tabelle |
| `spitzenwinkel_grad` | None | Pflicht bei V_CARVING; uebernimmt vom Werkzeug |
| `max_zustellung` | 0.5 mm | Max. Z-Zustellung pro Pass |

## Verwandt

- [Operation-Kontur](Operation-Kontur.md)
- [Werkzeug-Bibliothek](Werkzeug-Bibliothek.md) (V-Bits)
