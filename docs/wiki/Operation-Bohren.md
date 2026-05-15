# Operation: Bohren

> **Status:** ✅ Phase 1 (STANDARD, PECK, TIEF_PECK), HELIX/REIB folgen.
> **Issue:** [#1](https://github.com/MadGapun/CAMWOSA/issues/1)
> **Code:** [backend/camwosa/cam/bohren.py](../../backend/camwosa/cam/bohren.py) · **Tests:** [backend/tests/cam/test_operations.py](../../backend/tests/cam/test_operations.py)

Erzeugt Bohrungen an X/Y-Positionen.

## Verwendung

```python
from camwosa.cam import erzeuge_bohren_toolpath
from camwosa.cam.parameter import BohrParameter, BohrStrategie
from camwosa.dxf import Punkt2D

param = BohrParameter(
    werkzeug_id="bohrer_3mm",
    spindel_rpm=15000,
    vorschub=500,
    eintauch_vorschub=300,
    sicherheitshoehe=5.0,
    max_tiefe=10.0,
    stepdown=10.0,
    strategie=BohrStrategie.PECK,
    peck_tiefe=2.0,
    rueckzugs_hoehe=2.0,
)

# Eingabe: Liste von Punkt2D oder GeometrieObjekt (Kreise/Punkte aus DXF)
tp = erzeuge_bohren_toolpath([Punkt2D(0, 0), Punkt2D(50, 0)], werkzeug, param)
```

## Strategien

| Strategie | Status | Beschreibung |
|-----------|--------|--------------|
| `STANDARD` | ✅ | direkt nach unten und hoch |
| `PECK` | ✅ | schrittweise mit kleinem Rueckzug zur Spanabfuhr |
| `TIEF_PECK` | ✅ | schrittweise mit Rueckzug auf Sicherheitshoehe |
| `HELIX` | ⬜ | Schraubendes Helix-Bohren (auch fuer Loecher > Fraeser) |
| `REIB` | ⬜ | Konturbohren mit kleinerem Werkzeug |

## Eingabe

Die Funktion akzeptiert:
- Liste von `Punkt2D`
- Liste von `GeometrieObjekt` mit `typ in {PUNKT, KREIS, POLYLINIE}` — bei KREIS wird der Mittelpunkt verwendet (klassisches Bohrbild aus DXF).

## Parameter

| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| `strategie` | `PECK` | siehe Tabelle |
| `peck_tiefe` | 2.0 mm | Tiefe pro Peck-Pass |
| `dwell_sekunden` | 0.0 | Pause am Bohrgrund (fuer saubere Boeden) |
| `rueckzugs_hoehe` | 2.0 mm | Bei PECK: Rueckzug-Distanz zwischen Pecks |

## Verwandt

- [Operation-Kontur](Operation-Kontur.md)
- [Bohrbild-Erkennung](Bohrbild-Erkennung.md) (Phase E6)
