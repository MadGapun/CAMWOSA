# Operation: Kontur

> **Status:** ✅ Implementiert (Phase 1).
> **Issue:** [#1](https://github.com/MadGapun/CAMWOSA/issues/1)
> **Code:** [backend/camwosa/cam/kontur.py](../../backend/camwosa/cam/kontur.py) · **Tests:** [backend/tests/cam/test_operations.py](../../backend/tests/cam/test_operations.py)

Fraest entlang einer Kurve, mit Werkzeug-Kompensation auf gewuenschter Seite.

## Verwendung

```python
from camwosa.cam import erzeuge_kontur_toolpath
from camwosa.cam.parameter import KonturParameter, KonturSeite

param = KonturParameter(
    werkzeug_id="schaft_6mm_2s_hm",
    spindel_rpm=18000,
    vorschub=2000,
    eintauch_vorschub=400,
    sicherheitshoehe=5.0,
    max_tiefe=6.0,        # Bearbeitungstiefe in mm
    stepdown=2.0,         # Tiefe pro Z-Pass
    seite=KonturSeite.AUSSEN,   # AUSSEN | INNEN | AUF_LINIE
)

toolpath = erzeuge_kontur_toolpath(geometrie, werkzeug, param)
```

## Parameter

| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| `seite` | `AUSSEN` | Werkzeug-Kompensation |
| `fraes_richtung` | `GLEICHLAUF` | Climb / Conventional |
| `eintauch_strategie` | `RAMPE` | senkrecht / Rampe / Helix |
| `rampe_winkel_grad` | 15 | Winkel bei Rampe |
| `tabs_anzahl` | 0 | Haltestege pro Kontur |
| `tabs_hoehe` | 1.5 mm | Hoehe der Tabs |
| `tabs_breite` | 4.0 mm | Breite der Tabs |
| `aufmass` | 0.0 mm | Material das stehen bleibt |
| `schlichtgang` | False | letzter Spring-Pass |
| `lead_in_laenge` | 0.0 mm | Werkzeug-Anfahrt-Strecke |
| `lead_out_laenge` | 0.0 mm | Werkzeug-Abfahrt-Strecke |

(Phase 1 implementiert: alle obigen ausser Tabs/Lead-In/Out und Schlichtgang — die kommen mit Folge-Iteration.)

## Werkzeug-Kompensation

| Seite | Werkzeug-Mittelpunkt liegt |
|-------|---------------------------|
| `AUSSEN` | auf Polygon-Aussenkante + Werkzeug-Radius |
| `INNEN` | auf Polygon-Aussenkante - Werkzeug-Radius |
| `AUF_LINIE` | direkt auf der Linie |

## Fehler

- `ValueError("Werkzeug zu gross fuer Innen-Offset")`: Wenn Polygon kleiner ist als der Werkzeug-Durchmesser.

## Verwandt

- [Geometrie](Geometrie.md)
- [Postprozessor-GRBL](Postprozessor-GRBL.md)
- [Operation-Tasche](Operation-Tasche.md)
- [Sicherheits-Checks](Sicherheits-Checks.md)
