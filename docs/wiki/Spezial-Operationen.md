# Spezial-Operationen

> **Status:** ✅ T-Nut, Schwalbenschwanz, Fase implementiert.
> **Code:** [backend/camwosa/cam/spezial.py](../../backend/camwosa/cam/spezial.py) · **Tests:** [backend/tests/cam/test_spezial.py](../../backend/tests/cam/test_spezial.py)

## T-Nut

Hinterschnitt-Nut. Vor-Schlitz muss zuerst mit normalem Fraeser angelegt werden, dann taucht der T-Nut-Fraeser ein und schneidet links/rechts den Hinterschnitt.

```python
from camwosa.cam.spezial import erzeuge_t_nut_toolpath, TNutParameter
from shapely.geometry import LineString

p = TNutParameter(
    werkzeug_id="t_nutenfraeser_10mm",
    spindel_rpm=15000, vorschub=1000, eintauch_vorschub=300,
    tiefe=8, stepdown=2, nut_breite=6,
)
tp = erzeuge_t_nut_toolpath(LineString([(0, 0), (100, 0)]), werkzeug, p)
```

⚠ Vor-Schlitz NICHT vergessen!

## Schwalbenschwanz

Schwalbenschwanz-Profil entlang einer geschlossenen Kontur. Hinterschnitt entsteht durch die konische Geometrie des Schwalbenschwanz-Fraesers.

```python
from camwosa.cam.spezial import erzeuge_schwalbenschwanz_toolpath, SchwalbenschwanzParameter

p = SchwalbenschwanzParameter(
    werkzeug_id="schwalbenschwanz_60",
    spindel_rpm=15000, vorschub=1000, eintauch_vorschub=300,
    tiefe=5, stepdown=2, schwalbenschwanz_winkel_grad=60,
)
```

## Fase

Schraege entlang einer Kontur, mit V-Bit oder Fasenfraeser. Z-Tiefe wird automatisch aus `fase_breite` und `spitzenwinkel_grad` berechnet.

```python
from camwosa.cam.spezial import erzeuge_fase_toolpath, FaseParameter

p = FaseParameter(
    werkzeug_id="vbit_90grad",
    spindel_rpm=18000, vorschub=1500, eintauch_vorschub=300,
    tiefe=3, stepdown=1, fase_breite=1.0, spitzenwinkel_grad=90,
)
```

Formel: `z = -fase_breite / tan(spitzenwinkel/2)`.
Bei 90° und 1mm Fase: z = -1mm.

## Verwandt

- [Operation-Kontur](Operation-Kontur)
- [Operation-Gravur](Operation-Gravur)
- [Werkzeug-Bibliothek](Werkzeug-Bibliothek)
