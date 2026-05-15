# Operation: Relief (2.5D)

> **Status:** ✅ RASTER_X / RASTER_Y. KONTUR_PARALLEL folgt.
> **Issue:** [#5](https://github.com/MadGapun/CAMWOSA/issues/5)
> **Code:** [backend/camwosa/cam/relief.py](../../backend/camwosa/cam/relief.py) · **Tests:** [backend/tests/stl/test_heightmap.py](../../backend/tests/stl/test_heightmap.py)

Fraest eine STL-Geometrie schichtweise als Heightmap-Abtastung.

## Verwendung

```python
from camwosa.cam.relief import erzeuge_relief_toolpath, ReliefStrategie
from camwosa.cam.parameter import OperationParameter
from camwosa.stl import berechne_heightmap, lade_stl

dok = lade_stl("modell.stl")
hm = berechne_heightmap(dok, aufloesung=0.2)

param = OperationParameter(
    werkzeug_id="kugel_3mm_2s_hm",
    spindel_rpm=22000,
    vorschub=1500,
    eintauch_vorschub=300,
    sicherheitshoehe=5,
    max_tiefe=20,
    stepdown=20,
)
tp = erzeuge_relief_toolpath(hm, werkzeug, param,
                              strategie=ReliefStrategie.RASTER_X)
```

## Strategien

| Strategie | Status | Beschreibung |
|-----------|--------|--------------|
| `RASTER_X` | ✅ | Bahnen parallel zu X-Achse, Zickzack-Reihenfolge |
| `RASTER_Y` | ✅ | Bahnen parallel zu Y-Achse |
| `KONTUR_PARALLEL` | ⬜ | Folgt 3D-Konturen (komplexer, kommt in Phase 1+) |

## Werkzeug

Fuer Relief sind **Kugelfraeser** ideal — die Halbkugel-Spitze gibt sanfte Uebergaenge zwischen Raster-Punkten.

Spitze Werkzeuge (V-Bit, Schaftfraeser flach) erzeugen Stufen-Effekte.

## Aufloesung-Empfehlung

| Werkzeug-Durchmesser | Empfohlene Aufloesung |
|----------------------|-----------------------|
| 6 mm Kugelfraeser | 0.5 - 1.0 mm |
| 3 mm Kugelfraeser | 0.2 - 0.5 mm |
| 1 mm Gravurfraeser | 0.1 mm |

Faustregel: Aufloesung ~ Werkzeug-Durchmesser / 6.

## Schrupp-/Schlicht-Trennung

Empfohlen:
1. **Schruppen** mit grossem Schaftfraeser (z.B. 6 mm), Aufloesung 1.0 mm
2. **Schlichten** mit Kugelfraeser (z.B. 3 mm), Aufloesung 0.2 mm

Beide als eigene Operations im selben Setup, mit Werkzeugwechsel-Pause.

## Performance

Toolpath fuer 100x100 mm bei Aufloesung 0.2 hat ~250.000 Bewegungen. Erzeugung in <1 s, G-Code-Datei ~10 MB.

## Verwandt

- [STL-Import](STL-Import.md)
- [Operation-Tasche](Operation-Tasche.md)
- [Werkzeug-Bibliothek](Werkzeug-Bibliothek.md) (Kugelfraeser)
