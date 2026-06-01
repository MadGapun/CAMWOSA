# Bitmap → Vektor-Trace

> **Status:** ✅ Backend fertig (alpha.9, Cluster L1). UI folgt.
> **Code:** [`backend/camwosa/cad/bitmap_trace.py`](../../backend/camwosa/cad/bitmap_trace.py)
> **Tests:** [`backend/tests/cad/test_bitmap_trace.py`](../../backend/tests/cad/test_bitmap_trace.py) (11/11 grün)
> **API:** `POST /api/cad/bitmap-trace` · **MCP:** `bitmap_trace`

## Wozu

Ein PNG/JPG-Logo (schwarz/weiß) in eine **2D-Schneid-Kontur** umwandeln — zum
**Ausschneiden**, **Aushöhlen** (Tasche) oder als **Gravur-Outline**. Ein sehr
häufiger Hobby-Wunsch: „ich hab dieses Logo als Bild, mach mir eine Frässpur
draus." EstlCAM und Carbide Create haben beide ein „image trace".

## Abgrenzung zu Bild-zu-Relief

| | Bild-zu-Relief | **Bitmap-Trace** |
|---|---|---|
| Eingabe | Graustufenbild | Schwarz/Weiß-Logo |
| Ausgabe | **Heightmap** (Z-Tiefe, 3D-Relief) | **2D-Outline** (Vektor-Kontur) |
| Nutzung | 3D-schnitzen | ausschneiden / aushöhlen / gravieren |
| Modul | `stl/bild_heightmap.py` | `cad/bitmap_trace.py` |

Zwei komplett verschiedene Wünsche — ein Foto wird ein Relief, ein Logo wird
eine Schneidkontur.

## Wie es funktioniert

1. Bild laden + Graustufe
2. **Schwellwert** → Binär-Maske (dunkel = Form, oder invertiert)
3. Maske als Heightmap verpacken → die vorhandene **Marching-Squares-Kontur-
   findung** aus `cam/waterline.py` nutzen (kein potrace/scipy nötig)
4. Polygone **vereinfachen** (Douglas-Peucker) + Mini-Flecken verwerfen
5. optional auf **Ziel-Breite** skalieren → `GeometrieObjekt` (geschlossene
   Polylinien)

## Benutzung (Python)

```python
from camwosa.cad.bitmap_trace import trace_bitmap, BitmapTraceParameter

geos = trace_bitmap("logo.png", BitmapTraceParameter(
    schwelle=0.5,              # Graustufen-Grenze 0-1
    invertieren=False,         # False: dunkle Form (schwarzes Logo auf weiß)
    pixel_pro_mm=4.0,          # interne Auflösung
    ziel_breite_mm=80.0,       # Ausgabe auf 80mm Breite skalieren
    glaettung_toleranz_mm=0.2, # Douglas-Peucker
    min_flaeche_mm2=1.0,       # Flecken kleiner verwerfen
))
# geos = Liste von GeometrieObjekt (geschlossene Polylinien)
# → direkt als Geometrie in eine Kontur-/Tasche-/Gravur-Operation
```

## REST-API

```
POST /api/cad/bitmap-trace   (multipart/form-data)
  datei: <Bild>
  schwelle, invertieren, pixel_pro_mm, ziel_breite_mm,
  glaettung_toleranz_mm, min_flaeche_mm2  (alle optional)
→ { anzahl, objekte: [{ typ, layer, geschlossen, punkte }] }
```

MCP: `bitmap_trace(datei_pfad, schwelle=..., ziel_breite_mm=...)`.

## Tipps für gute Ergebnisse

- **Sauberes Schwarz/Weiß** liefert die beste Kontur. Graustufen/Anti-Aliasing
  → Schwelle anpassen.
- **`invertieren`** umschalten, wenn die Form weiß auf schwarz ist.
- **`pixel_pro_mm` höher** = feinere Kontur, aber mehr Punkte. Für scharfe Ecken
  4–8, für glatte Logos reicht 2–4.
- **`min_flaeche_mm2`** filtert JPEG-Artefakte / Staub.

## Bekannte Einschränkungen

- **Outline-Trace, kein Centerline-Trace.** Eine Strich-Gravur entlang der
  Medialachse (Skelett) ist ein separater, aufwändigerer Schritt — Outline
  (Umriss) ist der 80 %-Fall (ausschneiden, aushöhlen, Umriss gravieren).
- **Löcher** (z.B. das Innere eines „O") entstehen als eigene Polygone — die
  Innen/Außen-Zuordnung macht die nutzende Operation (z.B. Tasche mit Inseln).
- **Keine Farb-Trennung** — das Bild wird auf Graustufe reduziert.

## Verwandt

- [Bild-zu-Relief](Bild-zu-Relief.md) — der 3D-Pendant
- [CAD-Import](CAD-Import.md) · [Operation-Kontur](Operation-Kontur.md)
- [Cluster L Design-Eingabe](Master-Plan.md) (L1)
