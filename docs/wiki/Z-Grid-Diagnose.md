# Z-Grid-Diagnose

> **Status:** ✅ Backend fertig (alpha.5). UI-Komponente folgt in alpha.6+.
> **Code:** [`backend/camwosa/diagnostics/z_grid.py`](../../backend/camwosa/diagnostics/z_grid.py)
> **Tests:** [`backend/tests/diagnostics/test_z_grid.py`](../../backend/tests/diagnostics/test_z_grid.py) (10/10 grün)
> **API:** `POST /api/diagnostics/z-grid`

## Wozu

Bevor ein 3D-Reliefjob startet (oder bei Schlichten allgemein), prüft man
typischerweise per Z-Probing mehrere Punkte auf der Werkstücks-Oberfläche.
**Wenn das Werkstück schief liegt, wird das Relief falsch — und du merkst
es erst, wenn das Werkstück schon teilweise zerstört ist.**

Dieses Tool nimmt die Z-Probing-Ergebnisse, analysiert die Ebenheit und sagt
dir in Klartext, ob du

- direkt loslegen kannst,
- mit leichter Neigung leben kannst (z.B. nur Schruppen),
- besser neu aufspannen solltest,
- oder das Werkstück vorher planen musst.

## Eingabe

Eine Liste von gemessenen Punkten + optional welcher Werkzeug-Typ als
nächstes verwendet wird (Schlichten-Werkzeuge bekommen strengere Schwellen).

```python
from camwosa.diagnostics.z_grid import ZGridDaten, ZMessPunkt, analyse

daten = ZGridDaten(
    messpunkte=[
        ZMessPunkt(x=0,   y=0,   z=0.00),
        ZMessPunkt(x=50,  y=0,   z=0.02),
        ZMessPunkt(x=100, y=0,   z=-0.01),
        ZMessPunkt(x=0,   y=50,  z=-0.03),
        # ...
    ],
    werkzeug_typ="kugelfraeser",  # = Schlichten, strenger
)
ergebnis = analyse(daten)
print(ergebnis.befund)        # "eben_ok" | "leichte_neigung" | ...
print(ergebnis.klartext)      # "Werkstueck ist eben (max 0.03 mm ...)"
print(ergebnis.empfehlung)    # "Job kann starten — keine Anpassung noetig."
```

## Befund-Stufen

| Befund | Spreizung (Schaftfräser) | Spreizung (Schlichten) | Empfehlung |
|---|---|---|---|
| `eben_ok` | < 0.15 mm | < 0.08 mm | Job kann starten |
| `leichte_neigung` | < 0.5 mm | < 0.3 mm | Schruppen OK, Schlichten kompensieren |
| `starke_neigung` | < 2.5 mm | < 1.5 mm | Neu aufspannen empfohlen |
| `unebene_oberflaeche` | > 2.5 mm | > 1.5 mm | Werkstück planen vor dem Job |

Werkzeug-typ-Erkennung: `kugelfraeser`, `torusfraeser`, `v_bit`, `gravierstichel`
= Schlichten-strenger. Alle anderen Typen = Schrupp-Schwellen.

## Ausgabe-Details

```python
ergebnis.anzahl_punkte         # 9
ergebnis.z_min                 # -0.03
ergebnis.z_max                 # 0.02
ergebnis.z_spreizung           # 0.05
ergebnis.z_std                 # Standardabweichung
ergebnis.neigung_grad          # Winkel zur XY-Ebene (best-fit-Plane)
ergebnis.neigung_richtung_grad # Azimut der Neigung (0=+X, 90=+Y)
ergebnis.max_lokale_abweichung_mm  # max |z_punkt - z_plane(x,y)|
ergebnis.abweichungen          # Liste pro Punkt — fürs Heatmap-Rendering
```

## REST-API

```
POST /api/diagnostics/z-grid
Body:
{
  "messpunkte": [{"x": 0, "y": 0, "z": 0.0}, ...],
  "werkzeug_typ": "kugelfraeser"
}

Response 200:
{
  "befund": "eben_ok",
  "klartext": "...",
  "empfehlung": "...",
  "z_min": ..., "z_max": ..., "z_spreizung": ...,
  "neigung_grad": ..., "neigung_richtung_grad": ...,
  "max_lokale_abweichung_mm": ...,
  "abweichungen": [...]
}
```

## Implementation

- **Plane-Fit** via least-squares (3×3-Normalengleichungs-System, eigene Gauss-Jordan-Implementation, kein numpy nötig)
- **Schwellen** sind bewusst konservativ — lieber einmal zu viel warnen als ein zerstörtes Werkstück
- **Degenerierte Daten** (alle Punkte kollinear) führen nicht zum Crash — fallback auf reinen Mittelwert

## Verwandt

- [Sicherheits-Checks](Sicherheits-Checks)
- [STL-Import](STL-Import) — Heightmap-basiertes Relief profitiert besonders
- [Operation-Relief](Operation-Relief)
