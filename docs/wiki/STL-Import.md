# STL-Import + Heightmap

> **Status:** ✅ Implementiert (Phase 2 vorgezogen).
> **Issue:** [#5](https://github.com/MadGapun/coffee/issues/5)
> **Code:** [backend/camwosa/stl/heightmap.py](../../backend/camwosa/stl/heightmap.py) · **Tests:** [backend/tests/stl/test_heightmap.py](../../backend/tests/stl/test_heightmap.py)

CAMWOSA importiert STL-Dateien als Eingabe fuer 2.5D-Relief-Operationen. Das STL wird in eine **Heightmap** (Z pro X/Y-Raster) umgerechnet.

## Verwendung

```python
from camwosa.stl import lade_stl, berechne_heightmap

dok = lade_stl("modell.stl")
print(dok.x_range, dok.y_range, dok.z_range)

hm = berechne_heightmap(dok, aufloesung=0.2, z_referenz="max")
print(hm.shape)              # (nx, ny)
print(hm.z_values[10, 10])   # Z am Punkt (x_min+10*aufl, y_min+10*aufl)
```

## Parameter

| Parameter | Default | Bedeutung |
|-----------|---------|-----------|
| `aufloesung` | 0.2 mm | Raster-Abstand. Kleiner = genauer, langsamer |
| `z_referenz` | "max" | "max" -> Werte 0 (oben) bis -tiefe; "min" -> 0 unten bis +hoehe |

## Algorithmus

1. Bounding-Box des Mesh ermitteln
2. Raster aus X/Y-Punkten aufspannen (gemaess Aufloesung)
3. Pro Raster-Punkt einen Strahl von oberhalb nach -Z schiessen (Ray-Casting via trimesh+rtree)
4. Treffer mit dem Mesh = Z-Hoehe an dieser Stelle
5. Kein Treffer = Material nicht vorhanden -> auf `z_min` setzen

## Performance

- 100x100 mm bei Aufloesung 0.2 -> 250.000 Strahlen, ~3 Sekunden.
- Fuer schnellere Vorschau: `aufloesung=1.0` -> ~10.000 Strahlen, <0.5s.
- Fuer Relief-Toolpath: typisch 0.1-0.5 mm.

## Bekannte Einschraenkungen

- Sehr grosse STLs (>50 MB) sind speicherintensiv. Geplant: Mesh-Reduktion via `open3d`.
- Aktuell nur **2.5D-Heightmap** (von oben). Echtes 3D-Multi-Setup-Cutting Phase 5+.
- STLs in Inch werden nicht automatisch skaliert. Nutzer muss es explizit umrechnen.

## Verwandt

- [Operation-Relief](Operation-Relief.md)
- [DXF-Import](DXF-Import.md)
