# Circular + Radial Pocketing

> **Status:** ✅ Backend fertig (alpha.5). UI-Integration folgt.
> **Code:** [`backend/camwosa/cam/circular_radial.py`](../../backend/camwosa/cam/circular_radial.py)
> **Tests:** [`backend/tests/cam/test_circular_radial.py`](../../backend/tests/cam/test_circular_radial.py) (12/12 grün)
> **API:** `POST /api/spezial-ops/{circular,radial}-pocket-pfade`

## Wozu

Die normale Tasche-Op (`TaschenStrategie.PARALLEL` / `OFFSET_KONTUR` / `ADAPTIVE`)
deckt die meisten Standard-Fälle ab. Für **runde Taschen** sind aber zwei
zusätzliche Patterns klassisch:

- **CIRCULAR**: konzentrische Kreis-Spiralen — saubere konstante Werkzeug-
  Eingriffsgeometrie, ideal für runde Taschen, kleine Z-Spitzen am Spiral-
  Ende vermeidbar wenn man von innen nach außen fährt
- **RADIAL**: Sonnenstrahlen vom Mittelpunkt — gut für rotations-symmetrische
  Teile, kombiniert sich elegant mit Drehen-Operationen

Beides sind reine **Pfad-Generatoren** — die Z-Behandlung (Stepdown, Plunge,
Lead-In) macht weiterhin der allgemeine Tasche-Generator.

## Circular Pocketing

Konzentrische Kreis-Pfade, je nach Wahl von außen nach innen oder umgekehrt.
Der äußerste Kreis liegt **werkzeug_radius + aufmass** innerhalb der Aussen-
Kontur (Werkzeug-Kante berührt die Wand, nicht der Mittelpunkt).

```python
from camwosa.cam.circular_radial import (
    CircularPocketParameter,
    circular_pocket_pfade,
)

pfade = circular_pocket_pfade(CircularPocketParameter(
    mittelpunkt_x=50, mittelpunkt_y=50,
    aussen_radius=20.0,
    werkzeug_durchmesser=3.0,
    stepover_prozent=40,            # 1.2 mm pro Step bei 3mm Fraeser
    von_aussen_nach_innen=True,     # umgekehrt: ...=False
    segmente_pro_umdrehung=64,      # mehr = glatter
    fertigungs_aufmass=0.2,         # Material das stehen bleibt
))
# pfade = Liste von Polylinien, jede ist ein geschlossener Kreis
# (letzter Eintrag ist nur der Mittelpunkt)
```

## Radial Pocketing

Speichen vom Mittelpunkt nach außen, Anzahl der Speichen konfigurierbar.

```python
from camwosa.cam.circular_radial import (
    RadialPocketParameter,
    radial_pocket_pfade,
)

pfade = radial_pocket_pfade(RadialPocketParameter(
    mittelpunkt_x=50, mittelpunkt_y=50,
    aussen_radius=20.0,
    werkzeug_durchmesser=3.0,
    anzahl_speichen=24,             # 360° / 24 = 15° pro Speiche
    stepover_prozent=40,
    fertigungs_aufmass=0.0,
))
# pfade = Liste von 2-Punkt-Speichen
# [[(50,50), (69,50)], [(50,50), (68.7,54.9)], ...]
```

## REST-API

```
POST /api/spezial-ops/circular-pocket-pfade
Body:
{
  "mittelpunkt_x": 50, "mittelpunkt_y": 50,
  "aussen_radius": 20, "werkzeug_durchmesser": 3,
  "stepover_prozent": 40, "von_aussen_nach_innen": true,
  "segmente_pro_umdrehung": 64, "fertigungs_aufmass": 0.2
}

Response:
{
  "pfade": [
    [[50, 50], [50, 50]], ... // jeder Pfad ist Polyline
  ],
  "anzahl": 13
}
```

Analog `/radial-pocket-pfade`.

## Bekannte Einschränkungen

- **Nur runde Außen-Kontur** — keine beliebigen Polygone (für komplexe
  Formen die `PARALLEL`/`ADAPTIVE`-Strategien verwenden)
- **Keine Z-Behandlung im Modul** — Pfade sind reine 2D, die Z-Pässe müssen
  der Toolpath-Generator stricken (wird in alpha.6+ in die Tasche-Op
  integriert)
- **Keine Eintauch-Strategie-Auswahl** — Plunge-Logik kommt vom übergeordneten
  Tasche-Generator

## Verwandt

- [Operation-Tasche](Operation-Tasche)
- [Adaptive-Clearing](Adaptive-Clearing)
