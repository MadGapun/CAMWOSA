# Operation: Tasche

> **Status:** ✅ Phase 1 (PARALLEL + OFFSET_KONTUR), Adaptive folgt.
> **Issue:** [#1](https://github.com/MadGapun/CAMWOSA/issues/1)
> **Code:** [backend/camwosa/cam/tasche.py](../../backend/camwosa/cam/tasche.py) · **Tests:** [backend/tests/cam/test_operations.py](../../backend/tests/cam/test_operations.py)

Raeumt eine geschlossene Flaeche aus.

## Verwendung

```python
from camwosa.cam import erzeuge_tasche_toolpath
from camwosa.cam.parameter import TaschenParameter, TaschenStrategie

param = TaschenParameter(
    werkzeug_id="schaft_6mm_2s_hm",
    spindel_rpm=18000,
    vorschub=2000,
    eintauch_vorschub=400,
    sicherheitshoehe=5.0,
    max_tiefe=4.0,
    stepdown=2.0,
    strategie=TaschenStrategie.PARALLEL,
    stepover_prozent=40,   # 40% vom Werkzeug-Durchmesser
)

tp = erzeuge_tasche_toolpath(polygon, werkzeug, param)
```

## Strategien

| Strategie | Status | Beschreibung |
|-----------|--------|--------------|
| `PARALLEL` | ✅ | Zickzack-Bahnen entlang X-Achse |
| `OFFSET_KONTUR` | ✅ | Geschachtelte Konturen, von aussen nach innen |
| `SPIRAL_AUSSEN` | ⬜ | Von innen nach aussen (gut fuer runde Taschen) |
| `SPIRAL_INNEN` | ⬜ | Von aussen nach innen (gut fuer rechteckige) |
| `ADAPTIVE` | ⬜ | Trochoidaler Pfad fuer konstanten Eingriff (Phase E4) |

## Parameter

| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| `strategie` | `PARALLEL` | siehe Tabelle |
| `stepover_prozent` | 40 | seitlicher Versatz in % vom Werkzeug-Durchmesser |
| `eintauch_strategie` | `HELIX` | senkrecht / Rampe / Helix |
| `aufmass_wand` | 0.0 mm | Material an Wand stehen lassen |
| `aufmass_boden` | 0.0 mm | Material am Boden stehen lassen |
| `schlichtgang_wand` | False | extra Pass an der Wand |
| `schlichtgang_boden` | False | extra Pass am Boden |
| `fraes_richtung` | `GLEICHLAUF` | Climb / Conventional |

## Eingabe-Geometrie

Tasche braucht ein **geschlossenes Polygon** (z.B. aus geschlossener LWPOLYLINE oder CIRCLE im DXF).

Polygone mit Loechern (Inseln) sind unterstuetzt — die Inseln werden ausgespart.

## Fehler

- `ValueError("nicht unterstuetzt")`: Eingabe ist keine geschlossene Kontur.

## Einstellbare Parameter + Ecken-Verhalten (Grundfunktions-Audit alpha.11)

Geprüft in `tests/cam/test_grundfunktionen.py` (inkl. Gouge-Check für Taschen
**mit Innenecken** (L-Form) und **ohne Ecken** (Kreis) über alle Strategien):

| Parameter | Wirkung |
|---|---|
| `strategie` | parallel / spiral_außen / spiral_innen / offset_kontur / adaptive |
| `stepover_prozent` | Bahnabstand → Anzahl Bahnen |
| `max_tiefe` + `stepdown` | Tiefe + Z-Pässe |
| `vorschub` / `eintauch_vorschub` | Feed Schnitt / Plunge |
| `aufmass_wand` | Wand-Material das stehen bleibt (Bahn weiter von der Wand) |
| `aufmass_boden` | Boden-Material (geringere Tiefe) |
| **`fraes_richtung`** | **Gleichlauf/Gegenlauf** — Tasche schneidet innen → Climb = gegen den Uhrzeigersinn. *Seit alpha.11 wirksam.* |
| **`schlichtgang_wand`** | **Schlicht-Pass entlang der Soll-Wand** (Aufmass=0) bei voller Tiefe. *Seit alpha.11 wirksam.* |

**Ecken:** Innenecken (konkav, z.B. L-Form) hinterlassen werkzeug-bedingt einen
Radius — der Fräser kann nicht in die scharfe Ecke. Für scharfe Steck-Ecken:
[Dogbone-Slots](Dogbone-Slots.md). Der Audit stellt sicher, dass **keine Bahn
über die Tasche hinaus schneidet** (kein Gouge), mit und ohne Ecken.

> Noch nicht wirksam (geplant): `eintauch_strategie` (Rampe/Helix statt
> senkrechtem Plunge), `schlichtgang_boden`.

## Verwandt

- [Operation-Kontur](Operation-Kontur.md)
- [Dogbone-Slots](Dogbone-Slots.md)
- [Geometrie](Geometrie.md)
