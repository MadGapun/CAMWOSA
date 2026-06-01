"""Bitmap → Vektor-Trace (Cluster L1, Issue #48).

Ein PNG/JPG-Logo (schwarz/weiß) in eine **2D-Schneid-Kontur** umwandeln —
zum Ausschneiden, Aushöhlen (Tasche) oder als Gravur-Outline.

**Abgrenzung zu Bild-zu-Relief:** `stl/bild_heightmap.py` macht eine *Heightmap*
(Graustufe → Z-Tiefe, 3D-Relief). Bitmap-Trace macht eine *2D-Outline* (die
Grenze zwischen schwarz und weiß als Polygon). Komplett anderer, sehr häufiger
Hobby-Wunsch (EstlCAM + Carbide Create haben beide „image trace").

**Ansatz (reine numpy, kein potrace/scipy):**
1. Bild laden + Graustufe (wie `bild_heightmap`)
2. Schwellwert → Binär-Maske
3. Maske als Heightmap verpacken + die vorhandene Marching-Squares-Kontur-
   Findung aus `cam/waterline.py` (`heightmap_zu_contour_polygone`) nutzen
4. Polygone vereinfachen (Douglas-Peucker) + Mini-Flecken verwerfen
5. auf Ziel-Größe skalieren → `GeometrieObjekt` (geschlossene Polylinien)

Centerline-Trace (Skelett/Medialachse für Strichgravur) ist ein separater,
aufwändigerer Schritt — hier ist der Outline-Trace (80 %-Fall) umgesetzt.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

from camwosa.cam.waterline import heightmap_zu_contour_polygone
from camwosa.dxf.parser import GeometrieObjekt, GeometrieTyp, Punkt2D
from camwosa.stl.heightmap import Heightmap


@dataclass
class BitmapTraceParameter:
    """Konfiguration für den Bitmap-Trace."""

    schwelle: float = 0.5
    """Graustufen-Schwelle 0-1. Pixel dunkler als das gelten als „Form"."""
    invertieren: bool = False
    """False: dunkle Bereiche tracen (schwarzes Logo auf weiß). True: helle."""
    pixel_pro_mm: float = 4.0
    """Auflösung des internen Rasters (höher = feiner, langsamer)."""
    ziel_breite_mm: float | None = None
    """Wenn gesetzt: Ausgabe auf diese Breite skalieren (Höhe proportional)."""
    glaettung_toleranz_mm: float = 0.2
    """Douglas-Peucker-Vereinfachung — größer = weniger Punkte, gröber."""
    min_flaeche_mm2: float = 1.0
    """Polygone kleiner als das werden als Rauschen/Flecken verworfen."""


class BitmapTraceFehler(Exception):
    pass


def trace_bitmap(
    quelle: bytes | str | Path,
    parameter: BitmapTraceParameter | None = None,
) -> list[GeometrieObjekt]:
    """Traced ein Bitmap zu geschlossenen Vektor-Konturen.

    Args:
        quelle: Bilddaten (bytes), Dateipfad oder Path.
        parameter: Trace-Konfiguration.

    Returns:
        Liste von GeometrieObjekt (geschlossene Polylinien), in mm.

    Raises:
        BitmapTraceFehler: Bild nicht lesbar oder leer.
    """
    p = parameter or BitmapTraceParameter()
    if not 0.0 < p.schwelle < 1.0:
        raise BitmapTraceFehler("schwelle muss zwischen 0 und 1 liegen.")
    if p.pixel_pro_mm <= 0:
        raise BitmapTraceFehler("pixel_pro_mm muss > 0 sein.")

    # 1. Bild laden + Graustufe
    try:
        if isinstance(quelle, bytes):
            img = Image.open(BytesIO(quelle))
        else:
            img = Image.open(quelle)
        img = img.convert("L")
    except Exception as e:  # noqa: BLE001
        raise BitmapTraceFehler(f"Bild nicht lesbar: {e}") from e

    arr = np.asarray(img, dtype=np.float32) / 255.0  # (H, W), 0=schwarz 1=weiß
    if arr.size == 0:
        raise BitmapTraceFehler("Bild ist leer.")

    # 2. Binär-Maske. Bildkoordinaten (y nach unten) → CNC (y nach oben):
    #    flipud, dann transponieren auf (nx=W, ny=H) für die Heightmap-Konvention.
    if p.invertieren:
        bin_mask = arr >= p.schwelle  # helle Bereiche
    else:
        bin_mask = arr < p.schwelle   # dunkle Bereiche (typisch: schwarzes Logo)
    mask = np.flipud(bin_mask).T.astype(np.float64)  # (nx, ny), y-up

    if not mask.any():
        raise BitmapTraceFehler(
            "Keine Form gefunden — Schwelle anpassen oder 'invertieren' umschalten."
        )

    # 3. Maske als Heightmap → vorhandene Marching-Squares-Konturfindung.
    aufl = 1.0 / p.pixel_pro_mm  # mm pro Pixel
    heightmap = Heightmap(
        z_values=mask, aufloesung=aufl, x_min=0.0, y_min=0.0, z_max=1.0,
    )
    polygone = heightmap_zu_contour_polygone(heightmap, z_level=0.5)

    # 4. Vereinfachen + Mini-Flecken filtern
    ergebnis: list[GeometrieObjekt] = []
    for poly in polygone:
        vereinfacht = _douglas_peucker(poly, p.glaettung_toleranz_mm)
        if len(vereinfacht) < 3:
            continue
        if abs(_polygon_flaeche(vereinfacht)) < p.min_flaeche_mm2:
            continue
        ergebnis.append(vereinfacht)

    if not ergebnis:
        raise BitmapTraceFehler(
            "Keine verwertbaren Konturen — Bild zu klein/fein oder min_flaeche zu groß."
        )

    # 5. Optional skalieren auf Ziel-Breite
    if p.ziel_breite_mm is not None and p.ziel_breite_mm > 0:
        ergebnis = _skaliere_auf_breite(ergebnis, p.ziel_breite_mm)

    # → GeometrieObjekt
    return [
        GeometrieObjekt(
            typ=GeometrieTyp.POLYLINIE,
            layer="bitmap_trace",
            punkte=[Punkt2D(x, y) for (x, y) in poly],
            geschlossen=True,
            attribute={},
        )
        for poly in ergebnis
    ]


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def _polygon_flaeche(poly: list[tuple[float, float]]) -> float:
    """Shoelace-Fläche (vorzeichenbehaftet)."""
    n = len(poly)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return s / 2.0


def _douglas_peucker(
    punkte: list[tuple[float, float]], toleranz: float,
) -> list[tuple[float, float]]:
    """2D-Polygon-Vereinfachung (iterativer Douglas-Peucker)."""
    if len(punkte) < 3 or toleranz <= 0:
        return punkte
    # geschlossenes Polygon: an die zwei am weitesten entfernten Punkte aufspalten
    n = len(punkte)
    # Start: Punkt 0 + der am weitesten entfernte Punkt
    a = 0
    b = max(range(1, n), key=lambda k: _dist2(punkte[0], punkte[k]))
    keep = set()
    keep.add(a)
    keep.add(b)
    _dp_segment(punkte, a, b, toleranz, keep)
    _dp_segment(punkte, b, a + n, toleranz, keep, modulo=n)
    idx = sorted(keep)
    return [punkte[i % n] for i in idx]


def _dp_segment(punkte, start, ende, toleranz, keep, modulo=None):
    """Rekursiver Douglas-Peucker-Schritt zwischen Index start..ende."""
    n = len(punkte)
    if ende - start < 2:
        return
    a = punkte[start % n]
    b = punkte[ende % n]
    max_dist = -1.0
    max_idx = -1
    for i in range(start + 1, ende):
        d = _punkt_zu_strecke(punkte[i % n], a, b)
        if d > max_dist:
            max_dist = d
            max_idx = i
    if max_dist > toleranz and max_idx >= 0:
        keep.add(max_idx % n)
        _dp_segment(punkte, start, max_idx, toleranz, keep, modulo)
        _dp_segment(punkte, max_idx, ende, toleranz, keep, modulo)


def _dist2(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def _punkt_zu_strecke(p, a, b):
    """Senkrechter Abstand Punkt p zur Strecke a-b."""
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    laenge2 = dx * dx + dy * dy
    if laenge2 < 1e-12:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / laenge2
    t = max(0.0, min(1.0, t))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)


def _skaliere_auf_breite(
    polygone: list[list[tuple[float, float]]], ziel_breite_mm: float,
) -> list[list[tuple[float, float]]]:
    """Skaliert alle Polygone gemeinsam, sodass die Gesamtbreite = ziel_breite."""
    alle_x = [x for poly in polygone for (x, _) in poly]
    alle_y = [y for poly in polygone for (_, y) in poly]
    breite = max(alle_x) - min(alle_x)
    if breite < 1e-9:
        return polygone
    faktor = ziel_breite_mm / breite
    minx, miny = min(alle_x), min(alle_y)
    return [
        [((x - minx) * faktor, (y - miny) * faktor) for (x, y) in poly]
        for poly in polygone
    ]


__all__ = [
    "BitmapTraceFehler",
    "BitmapTraceParameter",
    "trace_bitmap",
]
