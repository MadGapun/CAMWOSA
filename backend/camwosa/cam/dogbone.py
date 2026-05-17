"""Dogbone-Slots: Tasche mit Eckenausgleich fuer Holzverbindungen (A45 / E3).

Problem: Normale Pockets haben **runde Innen-Ecken** wegen Werkzeug-Radius.
Wenn ein Zapfen mit scharfen Aussen-Ecken in die Tasche passen soll,
muessen die Tasche-Ecken erweitert werden — ein zusaetzlicher Kreis pro
Ecke, dessen Mittelpunkt entlang der Diagonalen liegt. Ergebnis sieht aus
wie ein Hundeknochen (= dogbone) oder T-Bone.

3 Stile:
- DOGBONE (klassisch): Kreis-Mittelpunkt auf der Ecke, Radius = Werkzeug-Radius
- T_BONE: Kreis nach innen verschoben in die laengere Seite (sieht aus wie ein T)
- LANGSAM (zwei Schritte): zuerst Pocket, dann pro Ecke nur das Material in
  der Ecke ausnehmen (mehr Steuerung, langsamer)

Use-Case: Schubladen-Zinken, Holzverbindungen, Steck-Verbindungen.

Wiki: docs/wiki/Dogbone-Slots.md
"""

from __future__ import annotations

import math
from enum import Enum

from shapely.geometry import Point, Polygon

from camwosa.db.models import Werkzeug


class DogboneStil(str, Enum):
    """Wie wird der Eckenausgleich angesetzt?"""

    DOGBONE = "dogbone"  # Kreis-Mittelpunkt auf der Ecke (auf Diagonale)
    T_BONE = "t_bone"  # Kreis nach innen verschoben (sichtbar entlang einer Seite)


def erkenne_innenecken(
    polygon: Polygon, tol_grad: float = 5.0,
) -> list[tuple[int, tuple[float, float]]]:
    """Findet alle „inside corners" eines Polygons.

    Eine Innen-Ecke ist eine konvexe Vertex der Aussenkontur (= das Polygon
    knickt nach innen). Im Sinne der Tasche ist das eine Stelle wo der
    Werkzeug-Radius einen Kreis statt einer scharfen Ecke hinterlaesst.

    Args:
        polygon: das Tasche-Polygon (CCW-Orientation erwartet)
        tol_grad: Toleranz fuer „scharfe" Ecke (Winkel weniger als 180° - tol)

    Returns:
        Liste von ``(vertex_index, (x, y))`` fuer jede Innen-Ecke.
    """
    coords = list(polygon.exterior.coords)
    if coords[0] == coords[-1]:
        coords = coords[:-1]
    n = len(coords)
    if n < 3:
        return []

    innenecken: list[tuple[int, tuple[float, float]]] = []
    for i in range(n):
        prev = coords[(i - 1) % n]
        cur = coords[i]
        nxt = coords[(i + 1) % n]
        # Vektoren prev->cur und cur->nxt
        v1 = (cur[0] - prev[0], cur[1] - prev[1])
        v2 = (nxt[0] - cur[0], nxt[1] - cur[1])
        # Innen-Winkel via Kreuzprodukt + Skalarprodukt
        cross = v1[0] * v2[1] - v1[1] * v2[0]
        dot = v1[0] * v2[0] + v1[1] * v2[1]
        # atan2 liefert Drehwinkel von v1 zu v2 in [-pi, pi]
        winkel_drehung = math.degrees(math.atan2(cross, dot))
        # Bei CCW-Polygon: Innen-Ecke wenn Drehung positiv (links-knick)
        # = Aussen-Winkel < 180°
        if winkel_drehung > tol_grad:
            innenecken.append((i, cur))
    return innenecken


def berechne_dogbone_kreis(
    polygon: Polygon, vertex_idx: int, werkzeug_radius: float,
    stil: DogboneStil = DogboneStil.DOGBONE,
) -> tuple[float, float, float] | None:
    """Berechnet Mittelpunkt + Radius fuer einen Dogbone-Kreis.

    Args:
        polygon: das Tasche-Polygon
        vertex_idx: Index der Innen-Ecke
        werkzeug_radius: Radius des Cutters
        stil: DOGBONE (auf Ecke) oder T_BONE (nach innen verschoben)

    Returns:
        ``(x_mittel, y_mittel, radius)`` oder None wenn nicht berechnet werden kann.
    """
    coords = list(polygon.exterior.coords)
    if coords[0] == coords[-1]:
        coords = coords[:-1]
    n = len(coords)
    if vertex_idx >= n:
        return None

    cur = coords[vertex_idx]
    prev = coords[(vertex_idx - 1) % n]
    nxt = coords[(vertex_idx + 1) % n]

    # Vektor vom Vertex weg in den Innenraum (= Halb-Diagonale)
    # Normalisiere die beiden eingehenden Vektoren + addiere sie
    v1 = (prev[0] - cur[0], prev[1] - cur[1])
    v2 = (nxt[0] - cur[0], nxt[1] - cur[1])
    l1 = math.hypot(*v1) or 1.0
    l2 = math.hypot(*v2) or 1.0
    n1 = (v1[0] / l1, v1[1] / l1)
    n2 = (v2[0] / l2, v2[1] / l2)
    diag = (n1[0] + n2[0], n1[1] + n2[1])
    diag_len = math.hypot(*diag) or 1.0
    diag_norm = (diag[0] / diag_len, diag[1] / diag_len)

    # diag_norm zeigt vom Vertex weg in den Innenraum (bisects inside angle).
    # Der Dogbone-Kreis muss aber teilweise NACH AUSSEN ragen, sodass
    # zusaetzlich Material in der Ecke entfernt wird. Mittelpunkt also
    # genau auf dem Vertex (DOGBONE) bzw. entlang einer Seite (T_BONE).

    if stil == DogboneStil.DOGBONE:
        # Klassisches Dogbone: Mittelpunkt liegt EXAKT auf dem Vertex.
        # Der Kreis (Radius r) ragt diagonal nach aussen, die innere Haelfte
        # ist eh schon im Polygon -> Union vergroessert die Tasche um die
        # aeussere Haelfte des Kreises.
        # Alternative: leicht nach innen versetzt, sodass weniger Material
        # ausserhalb der Original-Form weggenommen wird.
        # Hier: Mittelpunkt auf Vertex.
        return (cur[0], cur[1], werkzeug_radius)

    if stil == DogboneStil.T_BONE:
        # T_BONE: Mittelpunkt entlang der laengeren Seite leicht versetzt.
        # Sieht aus wie ein T statt eines Knochens (= Hundeknochen).
        if l1 >= l2:
            seite = n1
        else:
            seite = n2
        # Tangentialer Versatz vom Vertex entlang der laengeren Seite
        # = sqrt(2) * r / 2 damit der Kreis die andere Seite gerade beruehrt
        dist = werkzeug_radius * math.sqrt(2) / 2
        mx = cur[0] + seite[0] * dist
        my = cur[1] + seite[1] * dist
        return (mx, my, werkzeug_radius)

    return None


def dogbone_polygon(
    polygon: Polygon, werkzeug: Werkzeug,
    stil: DogboneStil = DogboneStil.DOGBONE,
) -> Polygon:
    """Erweitert ein Polygon um Dogbone-Kreise an allen Innen-Ecken.

    Liefert ein neues Polygon, das die zusaetzlichen Kreise als Union enthaelt.
    Dieses Polygon kann dann mit Standard-Pocketing bearbeitet werden, und
    die Tasche hat exakte 90°-Ecken.

    Args:
        polygon: Original-Tasche
        werkzeug: Werkzeug fuer Radius-Berechnung
        stil: DOGBONE oder T_BONE

    Returns:
        Erweitertes Polygon mit Kreis-Union an allen Innen-Ecken.
    """
    if werkzeug.durchmesser <= 0:
        raise ValueError("Werkzeug-Durchmesser muss > 0 sein")
    r = werkzeug.durchmesser / 2.0

    innenecken = erkenne_innenecken(polygon)
    if not innenecken:
        return polygon

    result = polygon
    for idx, _vertex in innenecken:
        kreis_info = berechne_dogbone_kreis(polygon, idx, r, stil)
        if kreis_info is None:
            continue
        mx, my, kreis_r = kreis_info
        kreis = Point(mx, my).buffer(kreis_r)
        result = result.union(kreis)

    # Konvertiere wieder zu Polygon (kann GeometryCollection geworden sein)
    if result.geom_type == "Polygon":
        return result
    if result.geom_type == "MultiPolygon":
        # Wir nehmen den groessten (= die Tasche, kleine Kreise sind absorbiert)
        polygone = list(result.geoms)
        return max(polygone, key=lambda p: p.area)
    return polygon  # Fallback


__all__ = [
    "DogboneStil",
    "berechne_dogbone_kreis",
    "dogbone_polygon",
    "erkenne_innenecken",
]
