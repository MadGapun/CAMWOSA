# Adaptive Clearing

> **Status:** ✅ Implementiert (kleines Stepover + trochoidale Sinus-Modulation senkrecht zur Bahn). Engagement-gesteuertes Pathing wie Fusion HSM ist Folge-Iteration.
> **Code:** [backend/camwosa/cam/tasche.py](../../backend/camwosa/cam/tasche.py) (Funktionen `_adaptive_bahnen`, `_modulieren`)
> **Tests:** [test_operations.py - TestAdaptiveClearing](../../backend/tests/cam/test_operations.py) (5 Tests)
> **Master-Plan-Position:** [E4](Master-Plan.md)

Adaptive Clearing ist trochoidales Fraesen — Werkzeug haelt konstanten Eingriffswinkel, was hoeheren Materialabtrag bei gleicher Belastung erlaubt.

## Aktuelle Implementierung

Zweistufig:

1. **Kleiner Stepover** — 12 % vom Werkzeug-Durchmesser statt der ueblichen 40 %.
   Mehr Bahnen, dafuer konstanter Werkzeug-Eingriff.
2. **Trochoidale Sinus-Modulation** senkrecht zur Bahnrichtung — fuer jeden
   Pfad-Punkt wird die Normale berechnet und der Punkt um
   ``amplitude * sin(2π * weg * wellen_pro_mm)`` verschoben. Erster + letzter
   Punkt bleiben fix damit die Bahn geschlossen bleibt.

Parameter (in `TaschenParameter`):

| Feld | Default | Bedeutung |
|------|---------|-----------|
| `adaptive_amplitude_faktor` | None (= 0.05) | Amplitude als Faktor des Werkzeug-Durchmessers. 0 = nur Stepover-Vorteil. 0.05-0.15 = sichtbare Trochoide. |
| `adaptive_wellen_pro_mm` | 0.5 | Wellen pro mm. Hoehere Werte = engere Trochoide. |

Echte Adaptive-Implementierungen (Autodesk HSM, Fusion 360) berechnen pro
Schritt den **Eingriffswinkel** mittels Voronoi-Diagramm + Restmaterial-
Tracking und passen die Bahn engagement-gesteuert an. Das ist die naechste
Iteration und nicht im Scope von E4.

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

## TODO (Folge-Iteration: echte Engagement-Steuerung)

- Eingriffswinkel-Berechnung pro Schritt (Voronoi-basiert)
- ~~Trochoidale Modulation der Bahn~~ ✅ E4 fertig
- Engagement-Calculator fuer Material-Abtragsrate
- Restmaterial-Tracking (z.B. via Pixel-Grid)

## Verwandt

- [Operation-Tasche](Operation-Tasche)
- [Werkzeug-Standzeit-Tracking](Standzeit-Tracking)
