# Bohrbild-Erkennung

> **Status:** ✅ Implementiert (Phase E6).
> **Code:** [backend/camwosa/cam/bohrbild.py](../../backend/camwosa/cam/bohrbild.py) · **Tests:** [backend/tests/cam/test_bohrbild.py](../../backend/tests/cam/test_bohrbild.py)

Filtert KREIS-Entities aus einer Geometrie-Liste, gruppiert sie nach Durchmesser und erkennt Raster- oder Polar-Array-Muster.

## Verwendung

```python
from camwosa.cam.bohrbild import erkenne_bohrbilder
from camwosa.dxf import lade_dxf

dok = lade_dxf("zeichnung.dxf")
gruppen = erkenne_bohrbilder(
    dok.objekte,
    durchmesser_toleranz=0.05,
    layer_filter="BOHRUNGEN",  # optional
)

for g in gruppen:
    print(f"Durchmesser {g.durchmesser}: {len(g.punkte)} Bohrungen, Muster: {g.muster}")
    if g.muster == "raster":
        print(f"  Raster {g.raster_dx}x{g.raster_dy} mm")
    elif g.muster == "polar":
        print(f"  Polar um {g.polar_zentrum} mit Radius {g.polar_radius}")
```

## Mustererkennung

| Muster | Bedingung |
|--------|-----------|
| **raster** | Alle X-Werte gleichmaessig + alle Y-Werte gleichmaessig + Anzahl = nx*ny |
| **polar** | Alle Punkte haben gleichen Abstand zum Mittelpunkt (toleranz 0.1 mm) |
| **ungeordnet** | sonst |

## Verwandt

- [Operation-Bohren](Operation-Bohren)
- [DXF-Import](DXF-Import)
