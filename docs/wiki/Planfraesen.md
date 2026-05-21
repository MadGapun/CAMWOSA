# Planfräsen (Face-Milling)

> **Status:** ✅ Backend fertig (alpha.6, Cluster I1). UI folgt.
> **Code:** [`backend/camwosa/cam/planfraesen.py`](../../backend/camwosa/cam/planfraesen.py)
> **Tests:** [`backend/tests/cam/test_planfraesen.py`](../../backend/tests/cam/test_planfraesen.py) (11/11 grün)
> **API:** `POST /api/spezial-ops/planfraesen`

## Wozu

Eine rechteckige Fläche eben fräsen:
- **Spoilboard-Surfacing** — die Opferplatte plan ziehen, damit sie wieder
  perfekt parallel zur Maschinenachse ist
- **Stock-Top planen** — die Oberkante eines Rohlings glätten bevor der
  eigentliche Job startet

## Synergie mit Z-Grid-Diagnose

Wenn die [Z-Grid-Diagnose](Z-Grid-Diagnose) `unebene_oberflaeche` meldet
(„Werkstück planen vor dem Job"), liefert `aus_z_grid_befund()` direkt
passende Planfräs-Parameter — der Abtrag wird aus der gemessenen Z-Spreizung
abgeleitet:

```python
from camwosa.cam.planfraesen import aus_z_grid_befund, erzeuge_planfraes_toolpath

params = aus_z_grid_befund(
    werkzeug_id="t_planfraeser_6mm",
    x_min=0, y_min=0, x_max=200, y_max=200,
    z_spreizung_mm=0.8,   # aus der Z-Grid-Diagnose
)
tp = erzeuge_planfraes_toolpath(werkzeug, params)
```

## Parameter

```python
from camwosa.cam.planfraesen import PlanfraesParameter, PlanfraesRichtung

p = PlanfraesParameter(
    werkzeug_id="t_planfraeser_6mm",
    spindel_rpm=18000, vorschub=2000, eintauch_vorschub=600,
    x_min=0, y_min=0, x_max=200, y_max=200,   # Rechteck
    z_start=0.0,              # Materialoberkante
    abtrag=1.0,               # wieviel runter (mm)
    maximaler_stepdown=0.5,   # max. Z-Zustellung pro Pass → 2 Pässe
    richtung=PlanfraesRichtung.X,   # Bahnen entlang X
    stepover_prozent=70,      # 70% vom Werkzeug-Durchmesser
    ueberstand_mm=2.0,        # Werkzeug fährt 2mm über die Kante
)
```

## Bewegungsmuster

Zickzack-Bahnen über das Rechteck, in N Z-Pässen (aus `abtrag` /
`maximaler_stepdown`). `ueberstand_mm` sorgt dafür, dass das Werkzeug
sauber ein- und austritt (kein Anschneiden an der Kante).

## REST-API

```
POST /api/spezial-ops/planfraesen
Body: { "parameter": { ...PlanfraesParameter... } }
Response: Toolpath mit metadaten.strategie = "planfraesen"
```

## Verwandt

- [Z-Grid-Diagnose](Z-Grid-Diagnose) — wann Planfräsen sinnvoll ist
- [3D-Strategien](3D-Strategien) — die anderen Cluster-I-Strategien
- [Operation-Tasche](Operation-Tasche)
