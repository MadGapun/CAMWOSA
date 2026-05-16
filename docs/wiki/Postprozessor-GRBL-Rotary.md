# GRBL Genmitsu Rotary Y (3,5-Achs-Setup)

> **Status:** ✅ Postprozessor + Wrapping + Vorschub-Korrektur + Indexing implementiert.
> **Issue:** [#12](https://github.com/MadGapun/CAMWOSA/issues/12)
> **Code:** [backend/camwosa/postprocessor/grbl_genmitsu_rotary_y.py](../../backend/camwosa/postprocessor/grbl_genmitsu_rotary_y.py), [backend/camwosa/cam/rotary.py](../../backend/camwosa/cam/rotary.py)

## Was ist „3,5-Achs"?

Bei diesem Setup hat die Maschine **kein** echtes 4-Achs-System, sondern einen
**Achs-Tausch**: waehrend des Rotary-Modus wird die **Y-Linearachse durch eine
Drehachse (A) ersetzt**. Die Maschine kann gleichzeitig X, Z und A bewegen — aber
ein gleichzeitiges X/Y/Z/A ist nicht moeglich, weil Y und A dieselbe Hardware
sind.

Daher die Bezeichnung **3,5-Achs**:
- 3 echte Achsen aktiv (X, Z, A)
- die „halbe" steht fuer den Achs-Tausch (Y kann nicht parallel laufen)

## Maschinen-Voraussetzungen

| GRBL-Setting | Wert | Bedeutung |
|--------------|------|-----------|
| `$101` | 88.889 | steps/mm fuer Y → wirkt jetzt als steps/Grad |
| `$131` | 9999 | Y-Soft-Limit deaktivieren (sonst kein endloses Drehen) |
| CNCjs-Macro | `ROTARY EIN` / `ROTARY AUS` | Settings-Wechsel |

CAMWOSA prueft diese Werte **nicht** technisch — der Postprozessor schreibt aber einen Hinweis in den G-Code-Header:

```
; ROTARY-MODUS aktiv (Y in Grad)
; Pruefe: $101=88.889  $131=9999
; CNCjs-Macro 'ROTARY EIN' muss aktiv sein
```

## Wrapping

```python
from camwosa.cam.rotary import wrap_2d_auf_zylinder
from camwosa.dxf.parser import Punkt2D

# Gravur die normalerweise auf einer flachen Platte 100x80 mm laeuft
flach = [Punkt2D(0, 0), Punkt2D(100, 0), Punkt2D(100, 80), Punkt2D(0, 80)]

# Auf Zylinder Radius 25 mm wickeln
ergebnis = wrap_2d_auf_zylinder(flach, radius=25)
# ergebnis.punkte: X bleibt, Y wird Winkel in Grad
# Bei R=25 entspricht Y=80mm einem Winkel von 80/(2*pi*25)*360 = ~183°
```

## Vorschub-Korrektur

Linearer Vorschub am Zylinder-Umfang muss in **Grad/min** umgerechnet werden, sonst wird die Drehrate falsch:

```python
from camwosa.cam.rotary import vorschub_korrektur_grad

omega = vorschub_korrektur_grad(linearer_vorschub_mm_min=1500, radius=25)
# 1500 mm/min am Radius 25 -> ~3438 grad/min
```

In der Praxis schreibt der Postprozessor diese Werte selbstaendig — das Wrapping liefert (X, Winkel)-Punkte, der Postprozessor die korrekten F-Werte.

## Indexing (3,5-Achs-Positionierung)

Diskrete Winkel-Positionen rundum (z.B. 4 Bohrungen alle 90°). Da die Y-Achse
durch die Drehung ersetzt ist, wird **rotiert + danach in X/Z gefraest**, nicht
gleichzeitig:

```python
from camwosa.cam.rotary import erzeuge_indexing_toolpath
from camwosa.dxf.parser import Punkt2D

positionen = [Punkt2D(50, w) for w in (0, 90, 180, 270)]
tp = erzeuge_indexing_toolpath(
    positionen, werkzeug_id="bohrer_3mm",
    rpm=15000, sicherheits_radius=20,
    bohrtiefe=5, plunge_feed=300,
)
```

## Bekannte Einschraenkungen

- Boegen (G2/G3) im Wrapping werden noch nicht aufgeloest — werden als Linien-Approximation gewickelt.
- Drechsel-Operationen (Plandrehen, Laengsdrehen, Spirale) sind separat (Phase 4).
- Kein gleichzeitiges Y- + A-Verfahren — siehe „Was ist 3,5-Achs?" oben.

## Verwandt

- [Postprozessor-GRBL](Postprozessor-GRBL.md)
- [Postprozessor-Plugins](Postprozessor-Plugins.md)
- [docs/ROTARY.md](../ROTARY.md) — vollstaendige Spezifikation
- [Drechseln](Drechseln.md) — Phase 4
