# 3D-Frässtrategien

> **Status:** 🟨 3D-Parallel fertig (alpha.6, Cluster I2). Scallop/Adaptive/
> Steilheits-Trennung/Rest-Material geplant.
> **Code:** [`backend/camwosa/cam/strategie_3d.py`](../../backend/camwosa/cam/strategie_3d.py)
> **Tests:** [`backend/tests/cam/test_strategie_3d.py`](../../backend/tests/cam/test_strategie_3d.py) (14/14 grün)
> **API:** `POST /api/spezial-ops/3d-parallel`
> **Quelle:** [Fusion-CAM-Vergleich](../FUSION-CAM-VERGLEICH.md), Issue #45

## Hintergrund

Die echte 3D-Frässtrategien-Familie ist Fusions Kernstärke. CAMWOSA hatte
bisher nur `relief` (RASTER_X/Y) + `waterline`. Cluster I bringt
Fusion-Niveau-Parameter auf CAMWOSAs STL-Heightmap.

### Warum Heightmap (nicht Mesh-direkt)?

Für **3-Achs-Fräsen** (ProVerXL) ist „höchster Z pro XY" die korrekte +
ausreichende Repräsentation — Hinterschnitte kann die Maschine ohnehin nicht.
Die Heightmap wird aus STL erzeugt (`stl/heightmap.py` → `lade_stl` via
trimesh). Mesh-direktes Surface-Following bräuchte man nur für 4/5-Achs.

→ **STL-Input ist voll abgedeckt:** STL → Heightmap → 3D-Strategie.

## Werkzeug-Form-Kompensation (der Kern)

Der Heightmap-Wert ist der **Oberflächen-Z**. Der Werkzeug-**Mittelpunkt** muss
so liegen, dass das Werkzeug die Oberfläche berührt aber nicht eindringt. Das
ist eine morphologische Dilation der Heightmap mit dem Werkzeug-Profil:

```
z_center(x,y) = max über Nachbarn (xi,yi) im Werkzeug-Radius von:
                z_surface(xi,yi) + profil_offset(distanz)
```

- **Kugelfräser:** `profil_offset(d) = r − √(r²−d²)` (sphärisch)
- **Schaftfräser:** `profil_offset(d) = 0` (flacher Boden)
- **Torusfräser:** flach bis Eckenradius, dann sphärisch

Implementiert in numpy (kein scipy), vektorisiert über Kernel-Offsets.

## 3D-Parallel-Schlichten

Parallele Bahnen folgen der Oberfläche. Fusion-Kern-Parameter:

```python
from camwosa.cam.strategie_3d import (
    Strategie3DParameter, StepoverModus, erzeuge_3d_parallel_toolpath,
)
from camwosa.stl.heightmap import lade_stl, berechne_heightmap

doc = lade_stl("figur.stl")
hm = berechne_heightmap(doc, aufloesung=0.2)

p = Strategie3DParameter(
    werkzeug_id="t_kugel_3mm",
    spindel_rpm=18000, vorschub=1500, eintauch_vorschub=400,
    stepover_modus=StepoverModus.SCALLOP,   # oder DISTANZ
    scallop_hoehe_mm=0.01,                   # Riefenhöhe → Stepover
    bahn_winkel_grad=0,                      # 0=entlang X, 45=diagonal
    aufmass_mm=0.0,                          # Material stehen lassen
    toleranz_mm=0.01,                        # Bahn-Approximationsfehler
    zickzack=True,
)
tp = erzeuge_3d_parallel_toolpath(hm, werkzeug, p)
```

### Parameter im Detail

| Parameter | Fusion-Pendant | Was es tut |
|---|---|---|
| `stepover_modus` | stepover / cuspHeightStepover | Bahnabstand fest (DISTANZ) oder aus Riefenhöhe (SCALLOP) |
| `scallop_hoehe_mm` | cuspHeightStepover | gewünschte Riefenhöhe bei SCALLOP |
| `bahn_winkel_grad` | passAngle | Richtung der parallelen Bahnen (0–180°) |
| `aufmass_mm` | stockToLeave | Material das stehen bleibt (für Schlicht-Pass danach) |
| `toleranz_mm` | tolerance | Bahn-Vereinfachung — gröber = weniger G-Code |
| `zickzack` | direction | Zickzack (schnell) vs. eine Richtung (saubere Oberfläche) |
| `slope_min_grad` / `slope_max_grad` | slopeAngleFrom/To | Steilheits-Fenster (I3) — nur Bereiche in diesem Steigungs-Bereich bearbeiten |

## Steilheits-Trennung (I3)

Fusion trennt 3D-Schlichten nach Oberflächen-**Steigung**: flache Bereiche
werden mit Parallel sauber, steile mit Waterline/Contour. CAMWOSA bildet das
über das **Slope-Fenster** `slope_min_grad` / `slope_max_grad` ab — die
3D-Parallel-Bahnen bearbeiten nur Punkte, deren lokale Oberflächen-Steigung
im Fenster liegt. Außerhalb wird die Bahn unterbrochen (Werkzeug hebt ab).

Typischer Zwei-Operationen-Workflow:

```python
# 1. Flache Bereiche mit Parallel (sauber)
flach = Strategie3DParameter(..., slope_min_grad=0, slope_max_grad=30)
tp_flach = erzeuge_3d_parallel_toolpath(hm, kugelfraeser, flach)

# 2. Steile Bereiche separat (engerer Stepover oder Waterline)
steil = Strategie3DParameter(..., slope_min_grad=30, slope_max_grad=90,
                             scallop_hoehe_mm=0.005)  # feiner für steile Wände
tp_steil = erzeuge_3d_parallel_toolpath(hm, kugelfraeser, steil)
```

Der Steigungswinkel wird auf der Original-Oberfläche berechnet
(`berechne_steigungswinkel`, aus dem numpy-Gradienten): flach = 0°,
senkrechte Wand = 90°. Voll-Fenster (0–90°) = keine Filterung (kein Overhead).

### Scallop-Formel

Bei Kugelfräser Radius r, gewünschte Riefenhöhe h:
```
stepover = 2·√(r² − (r−h)²) = 2·√(2·r·h − h²)
```
Kleinere Riefenhöhe → engerer Bahnabstand → glattere Oberfläche, mehr Bahnen.

## REST-API

```
POST /api/spezial-ops/3d-parallel
Body:
{
  "parameter": { ...Strategie3DParameter... },
  "heightmap": {
    "shape": [nx, ny], "aufloesung": 0.2,
    "x_min": 0, "y_min": 0, "z_max": 10,
    "z_values_dtype": "float32", "z_values_base64": "..."
  }
}
```

Die Heightmap im base64-Format kommt z.B. aus `/api/heightmap/aus-bild` oder
aus dem STL-Import.

## Roadmap (Issue #45)

| Sub | Strategie | Status |
|---|---|---|
| I1 | Planfräsen ([eigene Seite](Planfraesen)) | ✅ alpha.6 |
| I2 | 3D-Parallel | ✅ alpha.6 |
| I3 | Steilheits-Trennung (Slope-Fenster slope_min/max_grad) | ✅ alpha.7 |
| I4 | 3D-Scallop (konstante Riefenhöhe entlang Surface-Offset) | ⬜ |
| I5 | 3D-Adaptive-Schruppen (konstanter Eingriff, trochoidal) | ⬜ |
| I6 | Rest-Material-Tracking zwischen Operationen | ⬜ |

## Verwandt

- [Operation-Relief](Operation-Relief) — die einfachere RASTER-Variante
- [STL-Import](STL-Import) — Heightmap-Erzeugung
- [Planfräsen](Planfraesen)
- [Fusion-CAM-Vergleich](../FUSION-CAM-VERGLEICH.md)
