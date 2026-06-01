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
| `stepover_modus` | stepover / cuspHeightStepover | DISTANZ (fest) / SCALLOP (Riefenhöhe, XY-projiziert) / SCALLOP_3D (Riefenhöhe auf 3D-Oberfläche) |
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

## 3D-Scallop — konstante Riefenhöhe (I4)

Beim normalen `SCALLOP`-Stepover (I2) wird der Bahnabstand auf die XY-Ebene
projiziert. Auf **steilen Flächen** liegen die Bahnen entlang der geneigten
Oberfläche dann weiter auseinander → der Grat (Scallop) wird größer als
gewünscht.

`SCALLOP_3D` hält die Riefenhöhe auf der **echten 3D-Oberfläche** konstant:
der XY-Bahnabstand wird mit `cos(lokale Steigung)` skaliert. Steile Flächen →
engere Bahnen → gleichmäßige Oberflächengüte überall.

```python
p = Strategie3DParameter(
    ...,
    stepover_modus=StepoverModus.SCALLOP_3D,
    scallop_hoehe_mm=0.01,   # gilt jetzt auf der 3D-Oberflaeche
)
```

Implementierung: adaptive Bahn-Schleife (while statt fester Schrittzahl). Nach
jeder Bahn wird aus der mittleren Steigung der nächste Offset bestimmt:
`stepover_xy = scallop_stepover · cos(θ)`, geklemmt auf min. Rasterauflösung
und `cos θ ≥ 0.15` (verhindert Endlos-Schleife an fast senkrechten Wänden).

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

## V-Carve aus Tiefenbild/Modell (Cluster M1 + M2)

Power-User-Workflow: ein **V-Bit** (oder Gravierstichel/Ballnose-V-Bit) folgt
einer Heightmap-Oberfläche mit **variabler Tiefe** — das ergibt 3D-V-Carving
aus einem Modell oder Tiefenbild.

### Werkzeug-Form-Dilation (M1)

Die 3D-Strategien modellieren die echte Werkzeug-Form (`_werkzeug_kernel_offsets`):
- **Kugelfräser** — sphärisches Profil
- **Torusfräser** — flach + Eckenradius
- **Schaftfräser/Einschneider** — flacher Boden
- **V-Bit / Gravierstichel / Diamant-/Drag-Gravierer** — **Kegel** (M1):
  Spitzenwinkel → konische Wände, optionale Spitzendurchmesser-Flachfläche.
  TIP-Referenz (die Spitze sitzt unter dem Kontaktpunkt — so wird ein V-Bit
  auch real genullt). Ein spitzerer V-Bit taucht tiefer in Rillen.
- **Ballnose-V-Bit** — Kugelspitze + tangential verbundene Kegelwand.

### Pipeline-Rezept (M2)

```python
from camwosa.stl.bild_heightmap import heightmap_aus_bild, BildHeightmapParameter
from camwosa.cam.strategie_3d import v_carve_parameter_vorschlag, erzeuge_3d_parallel_toolpath

# 1. Bild/Modell → Heightmap
hm = heightmap_aus_bild(bild_bytes, BildHeightmapParameter(max_tiefe_mm=4, pixel_pro_mm=8))
#    (oder: lade_stl + berechne_heightmap für ein 3D-Modell)

# 2. V-Carve-Parameter-Vorschlag (feiner 3D-Scallop + V-Bit-Kegel)
params = v_carve_parameter_vorschlag(
    v_bit, spindel_rpm=18000, vorschub=1200, eintauch_vorschub=300,
    riefenhoehe_mm=0.02,
)

# 3. Toolpath — der V-Bit folgt der Oberfläche mit variabler Tiefe
tp = erzeuge_3d_parallel_toolpath(hm, v_bit, params)
```

Über REST/MCP identisch: das V-Bit greift automatisch im bestehenden
`/api/spezial-ops/3d-parallel` (bzw. MCP `operation_3d_parallel`), sobald das
gewählte Werkzeug ein konischer Typ mit `spitzenwinkel` ist.

**Abgrenzung:** Dies ist *3D*-V-Carving (V-Bit folgt einer Fläche). Das
klassische *2D*-V-Carving (variable Tiefe aus der Medialachse von Vektoren)
ist die Gravur-Strategie `V_CARVING` (A11).

## Roadmap (Issue #45)

| Sub | Strategie | Status |
|---|---|---|
| I1 | Planfräsen ([eigene Seite](Planfraesen)) | ✅ alpha.6 |
| I2 | 3D-Parallel | ✅ alpha.6 |
| I3 | Steilheits-Trennung (Slope-Fenster slope_min/max_grad) | ✅ alpha.7 |
| I4 | 3D-Scallop (StepoverModus.SCALLOP_3D, Stepover ∝ cos θ) | ✅ alpha.7 |
| I5 | 3D-Adaptive-Schruppen (konstanter Eingriff, trochoidal) | ⬜ |
| I6 | Rest-Material-Tracking zwischen Operationen | ⬜ |

## Verwandt

- [Operation-Relief](Operation-Relief) — die einfachere RASTER-Variante
- [STL-Import](STL-Import) — Heightmap-Erzeugung
- [Planfräsen](Planfraesen)
- [Fusion-CAM-Vergleich](../FUSION-CAM-VERGLEICH.md)
