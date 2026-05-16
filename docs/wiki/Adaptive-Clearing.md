# Adaptive Clearing

> **Status:** 🟨 Vereinfachte Implementierung (kleines Stepover + Offset-Konturen). Echtes trochoidales Pathing kommt in Folge-Iteration.
> **Code:** [backend/camwosa/cam/tasche.py](../../backend/camwosa/cam/tasche.py) (Funktion `_adaptive_bahnen`)

Adaptive Clearing ist trochoidales Fraesen — Werkzeug haelt konstanten Eingriffswinkel, was hoeheren Materialabtrag bei gleicher Belastung erlaubt.

## Aktuelle Implementierung

Vereinfacht: Offset-Kontur-Bahnen mit sehr kleinem Stepover (12% vom Werkzeug-Durchmesser statt der ueblichen 40%). Echte Adaptive-Clearing-Implementierungen (Autodesk HSM, Fusion 360) berechnen pro Schritt den Eingriffswinkel und passen die Bahn adaptiv an — das kommt in einer Folge-Iteration.

```python
from camwosa.cam.tasche import erzeuge_tasche_toolpath
from camwosa.cam.parameter import TaschenParameter, TaschenStrategie

param = TaschenParameter(
    werkzeug_id="schaft_6mm_2s_hm",
    spindel_rpm=18000, vorschub=3000,  # Adaptive vertraegt hoehere Vorschuebe!
    eintauch_vorschub=400,
    max_tiefe=10, stepdown=5,  # ... und tiefere Stepdowns
    strategie=TaschenStrategie.ADAPTIVE,
)
tp = erzeuge_tasche_toolpath(polygon, werkzeug, param)
```

## Vorteile gegenueber Standard-Tasche

- Konstanter Werkzeug-Eingriff → geringere Belastung → laengere Standzeit
- Vollstaendige Schnittlaenge wird genutzt (tiefer Stepdown moeglich)
- Schnellere Bearbeitungszeit insgesamt (trotz kleinem Stepover)

## TODO (Echte Adaptive)

- Eingriffswinkel-Berechnung pro Schritt (Voronoi-basiert)
- Trochoidale Modulation der Bahn
- Engagement-Calculator fuer Material-Abtragsrate
- Restmaterial-Tracking (z.B. via Pixel-Grid)

## Verwandt

- [Operation-Tasche](Operation-Tasche)
- [Werkzeug-Standzeit-Tracking](Standzeit-Tracking)
