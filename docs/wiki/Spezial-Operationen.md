# Spezial-Operationen

> **Status:** ✅ Diverse Spezial-Ops verfuegbar, weitere folgen.
> **Code:** [`backend/camwosa/cam/spezial.py`](../../backend/camwosa/cam/spezial.py) +
> Module pro Op (siehe unten) · **Tests:** [`backend/tests/cam/`](../../backend/tests/cam/)

CAMWOSA enthaelt verschiedene Spezial-Operationen ueber die Standard-CAM-Ops
(Kontur / Tasche / Bohren / Gravur / Relief) hinaus. Die meisten haben ein
**eigenes Modul** mit dediziertem Datenmodell und Tests.

## Klassisch (T-Nut / Schwalbenschwanz / Fase)

In `cam/spezial.py` zusammengefasst. Brauchen **kein eigenes Modul** weil
sie nahe an den Standard-Ops sind und nur Werkzeug-spezifische Bewegungen
ergaenzen.

### T-Nut

Hinterschnitt-Nut. Vor-Schlitz muss zuerst mit normalem Fraeser angelegt
werden, dann taucht der T-Nut-Fraeser ein und schneidet links/rechts den
Hinterschnitt.

```python
from camwosa.cam.spezial import erzeuge_t_nut_toolpath, TNutParameter
from shapely.geometry import LineString

p = TNutParameter(
    werkzeug_id="t_nutenfraeser_10mm",
    spindel_rpm=15000, vorschub=1000, eintauch_vorschub=300,
    tiefe=8, stepdown=2, nut_breite=6,
)
tp = erzeuge_t_nut_toolpath(LineString([(0, 0), (100, 0)]), werkzeug, p)
```

⚠ Vor-Schlitz NICHT vergessen!

### Schwalbenschwanz

Schwalbenschwanz-Profil entlang einer geschlossenen Kontur. Hinterschnitt
entsteht durch die konische Geometrie des Schwalbenschwanz-Fraesers.

```python
from camwosa.cam.spezial import erzeuge_schwalbenschwanz_toolpath, SchwalbenschwanzParameter

p = SchwalbenschwanzParameter(
    werkzeug_id="schwalbenschwanz_60",
    spindel_rpm=15000, vorschub=1000, eintauch_vorschub=300,
    tiefe=5, stepdown=2, schwalbenschwanz_winkel_grad=60,
)
```

### Fase

Schraege entlang einer Kontur, mit V-Bit oder Fasenfraeser. Z-Tiefe wird
automatisch aus `fase_breite` und `spitzenwinkel_grad` berechnet.

```python
from camwosa.cam.spezial import erzeuge_fase_toolpath, FaseParameter

p = FaseParameter(
    werkzeug_id="vbit_90grad",
    spindel_rpm=18000, vorschub=1500, eintauch_vorschub=300,
    tiefe=3, stepdown=1, fase_breite=1.0, spitzenwinkel_grad=90,
)
```

Formel: `z = -fase_breite / tan(spitzenwinkel/2)`. Bei 90° und 1mm Fase: z = -1mm.

## Eigene Module (alpha.3 + alpha.5)

| Op | Modul | Wozu |
|---|---|---|
| [Dogbone-Slots](Dogbone-Slots) | `cam/dogbone.py` | Innenecken aufweiten fuer Steckverbindungen |
| Chamfering | `cam/chamfer.py` | V-Bit-basierte Fasen mit auto-berechneter Tiefe |
| [Lithophane](Lithophane) | `stl/lithophane.py` | Bild-zu-3D fuer Backlight-Effekt |
| [Drag-Engraving](Drag-Engraving) | `cam/drag_engraving.py` | Diamantgravierer mit Spindel-AUS + Ecken-Dwell |
| [Auto-Inlay](Auto-Inlay) | `cam/auto_inlay.py` | Tasche+Plug aus einer Kontur |
| [Thread-Milling](Thread-Milling) | `cam/thread_milling.py` | Gewinde mit Helix-Bewegung |
| [Circular+Radial Pocketing](Circular-Radial-Pocketing) | `cam/circular_radial.py` | Spiral- und Strahlen-Tasche |
| [Waterline](Operation-Relief) | `cam/waterline.py` | Z-Level-3D-Schalen-Strategie |

## In Arbeit / Geplant

| Op | Status | Wann |
|---|---|---|
| V-Carve-Inlay | offen | alpha.6+ |
| Rest-Machining | offen | alpha.6+ |
| Pencil-Trace | offen | alpha.6+ |
| Offset Pocketing detailliert | offen | alpha.6+ |

Siehe [Master-Plan](Master-Plan) Cluster B + Cluster E.

## Verwandt

- [Werkzeug-Typen](Werkzeug-Typen)
- [Operation-Kontur](Operation-Kontur)
- [Operation-Tasche](Operation-Tasche)
- [Operation-Gravur](Operation-Gravur)
- [Adaptive-Clearing](Adaptive-Clearing)
