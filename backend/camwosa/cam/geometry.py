"""Geometrie-Hilfsfunktionen fuer CAM-Operationen.

Wraps shapely und pyclipper. Stellt Funktionen bereit fuer:
- Konvertierung DXF-Geometrie -> shapely
- Offset (Werkzeug-Kompensation)
- Boolean (Vereinigung, Differenz, Schnitt)
- Segmentierung von Kreis/Bogen/Spline in Polylinien
- Bounding-Box-Berechnung

Siehe Wiki: docs/wiki/Geometrie.md
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.ops import unary_union

from camwosa.dxf.parser import GeometrieObjekt, GeometrieTyp, Punkt2D


# ---------------------------------------------------------------------------
# Diskretisierung (Bogen / Kreis -> Polyline-Punkte)
# ---------------------------------------------------------------------------


def diskretisiere_kreis(
    mittelpunkt: Punkt2D, radius: float, *, segmente: int = 64
) -> list[Punkt2D]:
    """Erzeugt Polyline-Punkte fuer einen Kreis (geschlossen)."""
    pts: list[Punkt2D] = []
    for i in range(segmente):
        winkel = 2 * math.pi * i / segmente
        pts.append(Punkt2D(
            mittelpunkt.x + radius * math.cos(winkel),
            mittelpunkt.y + radius * math.sin(winkel),
        ))
    return pts


def diskretisiere_bogen(
    mittelpunkt: Punkt2D,
    radius: float,
    start_winkel_grad: float,
    end_winkel_grad: float,
    *,
    segmente_pro_360: int = 64,
) -> list[Punkt2D]:
    """Erzeugt Polyline-Punkte fuer einen Bogen.

    GRBL-Konvention: Winkel wachsen gegen den Uhrzeigersinn (CCW).
    """
    if end_winkel_grad < start_winkel_grad:
        end_winkel_grad += 360.0
    spanne = end_winkel_grad - start_winkel_grad
    n = max(2, int(round(segmente_pro_360 * spanne / 360.0)))
    pts: list[Punkt2D] = []
    for i in range(n + 1):
        winkel_grad = start_winkel_grad + spanne * i / n
        winkel_rad = math.radians(winkel_grad)
        pts.append(Punkt2D(
            mittelpunkt.x + radius * math.cos(winkel_rad),
            mittelpunkt.y + radius * math.sin(winkel_rad),
        ))
    return pts


def diskretisiere_ellipse(
    mittelpunkt: Punkt2D,
    haupt: float,
    neben: float,
    rotation_grad: float,
    *,
    segmente: int = 96,
) -> list[Punkt2D]:
    rot = math.radians(rotation_grad)
    cos_r, sin_r = math.cos(rot), math.sin(rot)
    pts: list[Punkt2D] = []
    for i in range(segmente):
        t = 2 * math.pi * i / segmente
        x = haupt * math.cos(t)
        y = neben * math.sin(t)
        # rotieren
        xr = x * cos_r - y * sin_r
        yr = x * sin_r + y * cos_r
        pts.append(Punkt2D(mittelpunkt.x + xr, mittelpunkt.y + yr))
    return pts


# ---------------------------------------------------------------------------
# Geometrie -> shapely
# ---------------------------------------------------------------------------


def objekt_zu_shapely(
    obj: GeometrieObjekt,
    *,
    segmente: int = 64,
) -> Polygon | LineString | None:
    """Konvertiert ein GeometrieObjekt zu shapely.

    Geschlossene Konturen werden Polygon, offene werden LineString.
    POINT wird als None zurueckgegeben (eigene Behandlung in Bohren).
    """
    if obj.typ == GeometrieTyp.LINIE:
        return LineString([p.to_tuple() for p in obj.punkte])

    if obj.typ == GeometrieTyp.POLYLINIE:
        if obj.geschlossen and len(obj.punkte) >= 3:
            return Polygon([p.to_tuple() for p in obj.punkte])
        return LineString([p.to_tuple() for p in obj.punkte])

    if obj.typ == GeometrieTyp.KREIS:
        pts = diskretisiere_kreis(obj.punkte[0], obj.attribute["radius"], segmente=segmente)
        return Polygon([p.to_tuple() for p in pts])

    if obj.typ == GeometrieTyp.BOGEN:
        pts = diskretisiere_bogen(
            obj.punkte[0],
            obj.attribute["radius"],
            obj.attribute["start_winkel"],
            obj.attribute["end_winkel"],
            segmente_pro_360=segmente,
        )
        return LineString([p.to_tuple() for p in pts])

    if obj.typ == GeometrieTyp.ELLIPSE:
        pts = diskretisiere_ellipse(
            obj.punkte[0],
            obj.attribute["hauptachse"],
            obj.attribute["nebenachse"],
            obj.attribute["rotation"],
            segmente=segmente,
        )
        return Polygon([p.to_tuple() for p in pts])

    if obj.typ == GeometrieTyp.SPLINE:
        if len(obj.punkte) < 2:
            return None
        return LineString([p.to_tuple() for p in obj.punkte])

    if obj.typ == GeometrieTyp.PUNKT:
        return None

    return None


# ---------------------------------------------------------------------------
# Offset (Werkzeug-Kompensation)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OffsetSeite:
    """Auf welcher Seite einer Kontur das Werkzeug entlang faehrt."""

    INNEN: str = "innen"
    AUSSEN: str = "aussen"
    AUF_LINIE: str = "auf_linie"


def offset_polygon(
    polygon: Polygon, distanz: float, *, join_style: int = 2
) -> Polygon | MultiPolygon | None:
    """Offset eines Polygons um eine Distanz.

    Positives Offset = nach aussen, negatives = nach innen.

    join_style: 1=round, 2=mitre, 3=bevel (shapely).
    """
    if distanz == 0:
        return polygon
    res = polygon.buffer(distanz, join_style=join_style)
    if res.is_empty:
        return None
    return res


def offset_kontur(
    polygon: Polygon, werkzeug_durchmesser: float, seite: str
) -> Polygon | MultiPolygon | None:
    """Werkzeug-Offset fuer Kontur-Operation.

    AUSSEN: Werkzeug-Mittelpunkt liegt auf Polygon-Aussenkante + r
    INNEN: Werkzeug-Mittelpunkt liegt auf Polygon-Aussenkante - r
    AUF_LINIE: kein Offset
    """
    r = werkzeug_durchmesser / 2.0
    if seite == OffsetSeite.AUSSEN:
        return offset_polygon(polygon, r)
    if seite == OffsetSeite.INNEN:
        return offset_polygon(polygon, -r)
    if seite == OffsetSeite.AUF_LINIE:
        return polygon
    raise ValueError(f"Unbekannte Offset-Seite: {seite}")


# ---------------------------------------------------------------------------
# Bounding-Box
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BoundingBox:
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @property
    def breite(self) -> float:
        return self.max_x - self.min_x

    @property
    def hoehe(self) -> float:
        return self.max_y - self.min_y


def bounding_box(geometrien: Iterable[Polygon | LineString]) -> BoundingBox | None:
    minx, miny, maxx, maxy = float("inf"), float("inf"), float("-inf"), float("-inf")
    leer = True
    for g in geometrien:
        if g is None or g.is_empty:
            continue
        leer = False
        b = g.bounds  # (minx, miny, maxx, maxy)
        minx = min(minx, b[0])
        miny = min(miny, b[1])
        maxx = max(maxx, b[2])
        maxy = max(maxy, b[3])
    if leer:
        return None
    return BoundingBox(minx, miny, maxx, maxy)


# ---------------------------------------------------------------------------
# Skalierung Inch -> mm
# ---------------------------------------------------------------------------


INCH_ZU_MM = 25.4


def skaliere_inch_zu_mm(obj: GeometrieObjekt) -> GeometrieObjekt:
    """Erzeugt eine skalierte Kopie eines Objekts (inch -> mm)."""
    neue_punkte = [Punkt2D(p.x * INCH_ZU_MM, p.y * INCH_ZU_MM) for p in obj.punkte]
    neue_attribute = dict(obj.attribute)
    for skalar_feld in ("radius", "hauptachse", "nebenachse"):
        if skalar_feld in neue_attribute:
            neue_attribute[skalar_feld] = neue_attribute[skalar_feld] * INCH_ZU_MM
    return GeometrieObjekt(
        typ=obj.typ,
        layer=obj.layer,
        punkte=neue_punkte,
        geschlossen=obj.geschlossen,
        attribute=neue_attribute,
        farbe=obj.farbe,
    )


def signierte_flaeche(coords: list[tuple[float, float]]) -> float:
    """Shoelace-Flaeche eines Polygonzugs. >0 = CCW (gegen Uhrzeiger), <0 = CW."""
    n = len(coords)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        x1, y1 = coords[i][0], coords[i][1]
        x2, y2 = coords[(i + 1) % n][0], coords[(i + 1) % n][1]
        s += x1 * y2 - x2 * y1
    return s / 2.0


def orientiere_bahn(
    coords: list[tuple[float, float]], im_uhrzeigersinn: bool,
) -> list[tuple[float, float]]:
    """Dreht einen geschlossenen Polygonzug in die gewuenschte Umlaufrichtung.

    Wird fuer Gleichlauf/Gegenlauf-Fraesen verwendet: die Umlaufrichtung der
    Bahn bestimmt, auf welcher Seite die Schneide ins Material greift.
    """
    flaeche = signierte_flaeche(coords)
    if abs(flaeche) < 1e-12:
        return coords
    ist_cw = flaeche < 0.0
    if ist_cw != im_uhrzeigersinn:
        return list(reversed(coords))
    return coords


__all__ = [
    "BoundingBox",
    "INCH_ZU_MM",
    "OffsetSeite",
    "bounding_box",
    "diskretisiere_bogen",
    "diskretisiere_ellipse",
    "diskretisiere_kreis",
    "objekt_zu_shapely",
    "offset_kontur",
    "offset_polygon",
    "orientiere_bahn",
    "signierte_flaeche",
    "skaliere_inch_zu_mm",
]


def vereinige(polygone: list[Polygon]) -> Polygon | MultiPolygon:
    return unary_union(polygone)
