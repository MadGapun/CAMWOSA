# Geometrie-Hilfsmodul

> **Status:** ✅ Implementiert.
> **Code:** [backend/camwosa/cam/geometry.py](../../backend/camwosa/cam/geometry.py) · **Tests:** [backend/tests/cam/test_geometry.py](../../backend/tests/cam/test_geometry.py)

Das Geometrie-Modul kapselt shapely-Operationen und bietet folgende Funktionen:

- Konvertierung von DXF-`GeometrieObjekt` zu shapely-Geometrien
- Diskretisierung von Kreisen, Boegen, Ellipsen
- Werkzeug-Offset (innen/aussen/auf Linie)
- Bounding-Box ueber mehrere Geometrien
- Skalierung Inch -> mm

## Konvertierung

```python
from camwosa.cam.geometry import objekt_zu_shapely
from camwosa.dxf import lade_dxf

dok = lade_dxf("zeichnung.dxf")
for obj in dok.objekte:
    geo = objekt_zu_shapely(obj, segmente=64)
    # geo ist Polygon (geschlossene Kontur), LineString (offene), oder None (Punkt)
```

## Diskretisierung

```python
from camwosa.cam.geometry import (
    diskretisiere_kreis, diskretisiere_bogen, diskretisiere_ellipse,
)
from camwosa.dxf import Punkt2D

pts = diskretisiere_kreis(Punkt2D(0, 0), radius=10, segmente=64)
pts = diskretisiere_bogen(Punkt2D(0, 0), radius=10, start_winkel_grad=0, end_winkel_grad=90)
pts = diskretisiere_ellipse(Punkt2D(0, 0), haupt=10, neben=5, rotation_grad=45)
```

## Offset

Werkzeug-Kompensation fuer Kontur-Operationen:

```python
from camwosa.cam.geometry import OffsetSeite, offset_kontur
from shapely.geometry import Polygon

quadrat = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])

aussen = offset_kontur(quadrat, werkzeug_durchmesser=2, seite=OffsetSeite.AUSSEN)
innen = offset_kontur(quadrat, werkzeug_durchmesser=2, seite=OffsetSeite.INNEN)
auf_linie = offset_kontur(quadrat, werkzeug_durchmesser=2, seite=OffsetSeite.AUF_LINIE)
```

**Konvention:**
- `AUSSEN`: Werkzeug-Mittelpunkt liegt auf Polygon-Aussenkante + Radius (klassische Aussen-Kontur)
- `INNEN`: Werkzeug-Mittelpunkt auf Aussenkante - Radius (Tasche / innere Kontur)
- `AUF_LINIE`: keine Kompensation (z.B. Gravur)

## Bounding-Box

```python
from camwosa.cam.geometry import bounding_box

bb = bounding_box([geo1, geo2, geo3])
print(bb.min_x, bb.max_x, bb.breite, bb.hoehe)
```

## Skalierung

DXFs in Inch werden umgerechnet:

```python
from camwosa.cam.geometry import skaliere_inch_zu_mm

if dok.einheit == "inch":
    objekte_mm = [skaliere_inch_zu_mm(o) for o in dok.objekte]
```

## Bekannte Einschraenkungen

- Aktuell nur 2D (XY-Ebene). Z-Tiefen werden in den Operations gehandhabt, nicht im Geometrie-Modul.
- Keine Behandlung von Kollinearitaet bei Polylinien (geht durch shapely-Union).
- ELLIPSE-Bogen-Segmente (start_param != 0, end_param != 2pi) werden noch als Voll-Ellipse behandelt — wird in Phase 1 ergaenzt.

## Verwandt

- [DXF-Import](DXF-Import.md)
- [Operation-Kontur](Operation-Kontur.md)
- [Operation-Tasche](Operation-Tasche.md)
