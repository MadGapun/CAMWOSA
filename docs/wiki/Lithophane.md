# Lithophane

> **Status:** ✅ Backend fertig (alpha.3).
> **Code:** [`backend/camwosa/stl/lithophane.py`](../../backend/camwosa/stl/lithophane.py)
> **Tests:** [`backend/tests/stl/test_lithophane.py`](../../backend/tests/stl/test_lithophane.py) (5/5 grün)

## Wozu

Eine Lithophane ist ein **durchscheinendes Bild im Material** (Holz, Kunststoff,
dünner Marmor). Vor Licht gehalten zeigt es das ursprüngliche Foto, weil
dünnere Stellen mehr Licht durchlassen.

Das CAM-Modul nimmt eine Heightmap (Graustufen-Bild) und erzeugt eine
**invertierte 3D-Geometrie**:

- **Helle Pixel** → dünn (viel Licht durch)
- **Dunkle Pixel** → dick (wenig Licht durch)

Mit einem **Mindest-Dicke-Sockel** für mechanische Stabilität und einem
**Maximal-Dicke-Limit** für das Material.

## Konzept

```
Original-Heightmap (von Foto):
  Hell = 255 → max_dicke (Vordergrund)
  Dunkel = 0 → min_dicke (Hintergrund)

Für Lithophane invertiert:
  Hell = 255 → min_dicke (Licht durch!)
  Dunkel = 0 → max_dicke (Schatten)

Endgeometrie:
  Sockel (Plate) + variable Dicke pro Pixel
  → kann mit normaler Relief-Op gefräst werden
```

## Benutzung (Python)

```python
from camwosa.stl.lithophane import (
    LithophaneParameter,
    erzeuge_lithophane_heightmap,
)

heightmap = lade_heightmap_aus_bild("foto.jpg")  # 2D-numpy-Array

params = LithophaneParameter(
    min_dicke_mm=0.6,      # so dünn wie's noch hält
    max_dicke_mm=3.5,      # so dick wie das Material erlaubt
    pixel_pro_mm=4,        # Auflösung
    invertieren_quelle=True,   # Standard: hell = dünn
)

lithoplane_heightmap = erzeuge_lithophane_heightmap(heightmap, params)
# → kann mit erzeuge_relief_toolpath gefräst werden
```

## Material-Tipps

| Material | min_dicke | max_dicke | Notiz |
|---|---|---|---|
| Lindenholz | 1.0 mm | 4.0 mm | Schöne Maserung, beleuchtet warm |
| Hartholz | 1.5 mm | 5.0 mm | Stabil, aber weniger lichtdurchlässig |
| Acryl (weiß) | 0.5 mm | 3.0 mm | Brillanter Effekt, scharf |
| Corian | 0.8 mm | 4.0 mm | Klassisch — am stärksten verbreitet |

## Bekannte Einschränkungen

- **Nur Graustufen** — Farbkanäle werden gemittelt
- **Keine automatische Histogramm-Korrektur** — wenn das Foto sehr dunkel
  ist, ist die Lithophane auch dunkel. Vorher in `cam/heightmap_filter.py`
  Gamma/Stretch anwenden.
- **Aspect-Ratio kommt von der Heightmap** — Skalierung machen die folgenden
  CAM-Schritte (Relief-Op)

## Verwandt

- [Bild-zu-Relief](Bild-zu-Relief) — die volle Pipeline mit 6 Filtern
- [Operation-Relief](Operation-Relief) — das eigentliche Fraesen
- [STL-Import](STL-Import)
