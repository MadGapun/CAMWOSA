# Kollisionsanalyse Werkzeughalter

> **Status:** ✅ Phase E3 Backend implementiert (vereinfachtes Zylinder-Modell).
> **Code:** [backend/camwosa/safety/kollision.py](../../backend/camwosa/safety/kollision.py)

## Idee

Beim Fraesen sieht das Werkzeug zwar in den Schnitt, aber bei zu kleiner Schneidlaenge stoesst der **Werkzeughalter** (Spannzangenmutter, Halter) ins Material — der Schaden ist oft groesser als beim Werkzeugbruch.

## Vereinfachtes Modell

```
   ┌──┐  <- Halter-Oberkante
   │  │  
   │  │  hoehe
   └──┘  <- Halter-Unterkante (Z_aktuell + schneidlaenge + abstand)
    ||
    ||   schneidlaenge
    ╲╱   <- Werkzeug-Spitze (Z_aktuell)
   ═════ <- Material-Oberkante (z_oberkante_material)
```

Check: **Halter-Unterkante < z_oberkante_material → Kollision**

## Verwendung

```python
from camwosa.safety import pruefe_toolpath

bericht = pruefe_toolpath(
    toolpath, maschine, werkzeug,
    z_oberkante_material=0.0,
    halter_kollision_pruefen=True,   # standardmaessig aus
)
```

## Erweiterung (geplant)

- Echte 3D-Geometrie des Halters (statt nur Zylinder)
- X/Y-Verprobung: Halter taucht NUR ein wenn an X/Y auch Material steht
- 3D-Voxel-basierte Kollisionserkennung
- Anti-Kollisions-Vorschlag: Werkzeug-Wechsel zu laengerer Variante

## Verwandt

- [Sicherheits-Checks](Sicherheits-Checks)
- [Werkzeug-Bibliothek](Werkzeug-Bibliothek)
