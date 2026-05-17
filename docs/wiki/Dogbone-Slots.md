# Dogbone-Slots

> **Status:** ✅ Backend fertig (alpha.3).
> **Code:** [`backend/camwosa/cam/dogbone.py`](../../backend/camwosa/cam/dogbone.py)
> **Tests:** [`backend/tests/cam/test_dogbone.py`](../../backend/tests/cam/test_dogbone.py) (11/11 grün)

## Wozu

Ein Fräser ist **rund** — innen-Ecken einer Tasche oder Aussparung können
deshalb keine 90°-scharfen Innenkanten bekommen. Es entsteht immer ein Radius
von Werkzeug-Größe.

**Problem**: ein eingesteckter Plug mit scharfen Außenkanten passt nicht in
die Tasche — er stößt an den Radien an.

**Lösung Dogbone-Slot**: an jeder Innenecke wird zusätzlich Material
weggenommen — entweder als **Kreis auf der Vertex** (DOGBONE) oder als
**Verlängerung entlang einer Seite** (T_BONE). Damit verschwindet der
störende Radius.

```
   Original-Innenecke:       Mit DOGBONE:           Mit T_BONE:
    +-------+                  +-------+              +-------+
    |       |                  |   o   |              |       |
    |       |                  |  /    |              |       |
    +------ -+                 +---+---+              +---+   +
            ^                                             v
        Plug stößt an              Plug passt rein     Plug passt rein
```

## Stile

- **DOGBONE**: Kreis-Loch mit Werkzeug-Durchmesser, Mittelpunkt direkt
  auf der Innenecke (Vertex). Optisch sichtbar als "Hundeknochen"-Form.
- **T_BONE**: Mittelpunkt entlang der **längeren** der zwei anliegenden
  Kanten verschoben. Weniger auffällig, aber Plug muss eine kleine Nase
  in diese Richtung haben.

## Benutzung (Python)

```python
from camwosa.cam.dogbone import (
    DogboneParameter, DogboneStil,
    erkenne_innenecken,
    erzeuge_dogbones,
)
from shapely.geometry import Polygon

# 1. Polygon mit Innenecken
poly = Polygon([(0,0), (50,0), (50,30), (30,30), (30,10), (0,10)])

# 2. Innenecken erkennen (Drehwinkel-Analyse)
ecken = erkenne_innenecken(poly)
# → [(30, 30), (30, 10)] mit jeweiligen Drehwinkeln

# 3. Dogbones an diese Ecken setzen
dogbones = erzeuge_dogbones(
    poly,
    werkzeug_durchmesser=3.0,
    parameter=DogboneParameter(stil=DogboneStil.T_BONE),
)
# → Liste von Kreis-Geometrien an den Ecken
```

## Innenecken-Erkennung

Die Funktion `erkenne_innenecken()` analysiert jeden Vertex eines Polygons
und prüft per **Kreuzprodukt + Skalarprodukt** ob der Drehwinkel an dieser
Stelle eine Innen-Kante (konkav) oder Außen-Kante (konvex) ist. Nur konkave
Vertizes bekommen einen Dogbone.

## Bekannte Einschränkungen

- **Nur Polygone** — bei offenen Polylinien gibt's keine Innenecken im
  klassischen Sinn
- **Nur konkave Vertizes** — alle anderen werden ignoriert
- **T_BONE wählt automatisch die längere Seite** — falls beide Seiten gleich
  lang sind, gewinnt die erste (deterministisch)

## Verwandt

- [Operation-Tasche](Operation-Tasche)
- [Operation-Kontur](Operation-Kontur)
- [Spezial-Operationen](Spezial-Operationen)
- [Auto-Inlay](Auto-Inlay) — Inlay-Workflow mit Dogbone-Hinweis bei scharfen Ecken
