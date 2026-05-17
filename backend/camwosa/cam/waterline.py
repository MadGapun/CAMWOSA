"""Waterline-Strategie fuer 3D-Reliefs (A43 / Cluster B).

Statt parallele Raster-Bahnen entlang einer Achse (= Raster X/Y), bewegt
sich der Cutter horizontal auf konstanten Z-Levels — wie Hoehenlinien
einer geographischen Karte.

Vorteil: bei steilen Wänden (z.B. Seitenwand einer Vase) macht Raster
Stairsteps. Waterline-Bahn folgt die Wand sauber auf festen Z-Levels.

Parameter:
- stepdown (mm pro Z-Level)
- waterline_strategie: nur Aussenkonturen (Outside) oder auch innere Inseln (All)

Wiki: docs/wiki/Operation-Relief.md
"""

from __future__ import annotations

import numpy as np

from camwosa.cam.parameter import OperationParameter
from camwosa.db.models import Werkzeug
from camwosa.gcode.toolpath import (
    Bewegung,
    BewegungsTyp,
    OperationsTyp,
    Toolpath,
)
from camwosa.stl.heightmap import Heightmap


def heightmap_zu_contour_polygone(
    heightmap: Heightmap, z_level: float,
) -> list[list[tuple[float, float]]]:
    """Berechnet alle Konturen einer Heightmap auf einem bestimmten Z-Level.

    Marching-Squares-aehnlich: pro Grid-Cell pruefen wo der Z-Level die
    Cell-Z-Werte schneidet. Liefert eine Liste von Polygonen (= geschlossene
    Konturen) plus eventuell offene Linien-Segmente.

    Vereinfachte Implementation: Schwellwert-Operation auf der Heightmap,
    dann via Find-Contours.

    Args:
        heightmap: die Heightmap
        z_level: Z-Wert fuer den die Kontur gesucht wird (typisch negativ)

    Returns:
        Liste von Polygon-Punkt-Listen ``[(x, y), ...]`` in mm.
    """
    nx, ny = heightmap.shape
    if nx < 2 or ny < 2:
        return []

    # Binary-Mask: True wo Z >= z_level (= Material auf dieser Hoehe noch da)
    mask = heightmap.z_values >= z_level

    # Eigene Marching-Squares-Implementation (kein scipy/skimage noetig).
    # Pro 2x2-Cell die 4 Eckwerte gegen Z-Level vergleichen -> 16 Faelle.
    # Wir sammeln Liniensegmente, dann verbinden wir sie zu Polygonen.
    segmente = _marching_squares_segmente(mask, heightmap.x_min, heightmap.y_min,
                                           heightmap.aufloesung)
    polygone = _segmente_zu_polygonen(segmente)
    # Mindestens 3 Punkte pro Polygon
    return [p for p in polygone if len(p) >= 3]


def _marching_squares_segmente(
    mask: np.ndarray, x_min: float, y_min: float, aufl: float,
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Liefert Liniensegmente (start, end) auf Cell-Granularitaet.

    Mask-Konvention: True = inside (Material da), False = outside.
    Linie verlaeuft entlang Cell-Kanten wo mask sich aendert.
    """
    nx, ny = mask.shape
    segmente: list[tuple[tuple[float, float], tuple[float, float]]] = []

    # Pro 2x2-Cell-Square: 4 Ecken, 16 Codes
    for i in range(nx - 1):
        for j in range(ny - 1):
            # Ecken (im uns interessant: top-left, top-right, bottom-right,
            # bottom-left in (i,j)+(i+1,j)+(i+1,j+1)+(i,j+1)
            tl = mask[i, j]
            tr = mask[i + 1, j]
            br = mask[i + 1, j + 1]
            bl = mask[i, j + 1]
            code = (int(tl) << 3) | (int(tr) << 2) | (int(br) << 1) | int(bl)
            if code in (0, 15):
                continue  # alle inside oder alle outside

            # Mittelpunkte der 4 Kanten in mm-Coords
            top = ((x_min + (i + 0.5) * aufl), (y_min + j * aufl))
            right = ((x_min + (i + 1) * aufl), (y_min + (j + 0.5) * aufl))
            bottom = ((x_min + (i + 0.5) * aufl), (y_min + (j + 1) * aufl))
            left = ((x_min + i * aufl), (y_min + (j + 0.5) * aufl))

            # 14 Faelle (1-14)
            if code in (1, 14): segmente.append((left, bottom))
            elif code in (2, 13): segmente.append((bottom, right))
            elif code in (3, 12): segmente.append((left, right))
            elif code in (4, 11): segmente.append((top, right))
            elif code == 5: segmente.append((left, top)); segmente.append((bottom, right))
            elif code in (6, 9): segmente.append((bottom, top))
            elif code in (7, 8): segmente.append((left, top))
            elif code == 10: segmente.append((left, bottom)); segmente.append((top, right))
    return segmente


def _segmente_zu_polygonen(
    segmente: list[tuple[tuple[float, float], tuple[float, float]]],
    tol: float = 0.01,
) -> list[list[tuple[float, float]]]:
    """Verbindet Liniensegmente zu zusammenhaengenden Polygonen.

    Greedy: nimm erstes Segment, haenge Segmente an deren Endpunkte zum
    Anfang/Ende passen, bis geschlossen oder nichts mehr passt.
    """
    rest = list(segmente)
    polygone: list[list[tuple[float, float]]] = []

    def gleich(p: tuple[float, float], q: tuple[float, float]) -> bool:
        return abs(p[0] - q[0]) < tol and abs(p[1] - q[1]) < tol

    while rest:
        seg = rest.pop(0)
        pfad = [seg[0], seg[1]]
        geaendert = True
        while geaendert and rest:
            geaendert = False
            for i, s in enumerate(rest):
                if gleich(s[0], pfad[-1]):
                    pfad.append(s[1])
                    rest.pop(i)
                    geaendert = True
                    break
                if gleich(s[1], pfad[-1]):
                    pfad.append(s[0])
                    rest.pop(i)
                    geaendert = True
                    break
                if gleich(s[0], pfad[0]):
                    pfad.insert(0, s[1])
                    rest.pop(i)
                    geaendert = True
                    break
                if gleich(s[1], pfad[0]):
                    pfad.insert(0, s[0])
                    rest.pop(i)
                    geaendert = True
                    break
        if len(pfad) >= 3:
            polygone.append(pfad)
    return polygone


def erzeuge_waterline_toolpath(
    heightmap: Heightmap,
    werkzeug: Werkzeug,
    parameter: OperationParameter,
    *,
    z_levels: list[float] | None = None,
    operation_id: str = "waterline",
) -> Toolpath:
    """Erzeugt einen Waterline-Toolpath aus einer Heightmap.

    Algorithmus:
    1. Liste der Z-Levels von z_max (Oberkante) nach z_min (Materialboden)
       in stepdown-Schritten
    2. Pro Z-Level: alle Konturen berechnen
    3. Pro Kontur: Werkzeug auf Sicherheitshoehe -> Anfahrt -> Plunge auf
       Z-Level -> Kontur abfahren -> Rueckzug auf Sicher

    Args:
        heightmap: die Heightmap
        werkzeug: Werkzeug (durchmesser wird genutzt fuer Offset)
        parameter: Operation-Parameter (max_tiefe, stepdown, vorschuebe)
        z_levels: Wenn None, automatisch berechnen aus max_tiefe + stepdown.
                  Wenn gesetzt, werden diese Z-Levels genutzt.

    Returns:
        Toolpath mit Waterline-Bewegungen.
    """
    nx, ny = heightmap.shape
    if nx < 2 or ny < 2:
        raise ValueError("Heightmap zu klein fuer Waterline")

    if z_levels is None:
        # Z-Levels: von 0 (Oberkante) bis -max_tiefe in stepdown-Schritten
        z_max = 0.0
        z_min = -parameter.max_tiefe
        anzahl_schritte = max(1, int(parameter.max_tiefe / parameter.stepdown))
        z_levels = [
            z_max - parameter.stepdown * (i + 1) for i in range(anzahl_schritte)
        ]
        if z_levels[-1] > z_min:
            z_levels.append(z_min)

    bewegungen: list[Bewegung] = []

    # Anfahrt
    bewegungen.append(Bewegung(
        BewegungsTyp.EILGANG,
        x=heightmap.x_min, y=heightmap.y_min,
        z=parameter.sicherheitshoehe,
        kommentar="Waterline: Anfahrt",
    ))

    pro_level_konturen = 0
    for z_level in z_levels:
        konturen = heightmap_zu_contour_polygone(heightmap, z_level)
        if not konturen:
            continue
        pro_level_konturen += 1

        for kontur in konturen:
            if not kontur:
                continue
            # Anfahrt auf Sicherheitshoehe
            x0, y0 = kontur[0]
            bewegungen.append(Bewegung(
                BewegungsTyp.EILGANG,
                x=x0, y=y0, z=parameter.sicherheitshoehe,
            ))
            # Plunge auf Z-Level
            bewegungen.append(Bewegung(
                BewegungsTyp.PLUNGE,
                x=x0, y=y0, z=z_level,
                feed=parameter.eintauch_vorschub,
            ))
            # Kontur abfahren
            for x, y in kontur[1:]:
                bewegungen.append(Bewegung(
                    BewegungsTyp.LINEAR,
                    x=x, y=y, z=z_level,
                    feed=parameter.vorschub,
                ))
            # Rueckzug
            bewegungen.append(Bewegung(
                BewegungsTyp.EILGANG,
                x=kontur[-1][0], y=kontur[-1][1],
                z=parameter.sicherheitshoehe,
            ))

    return Toolpath(
        operation_id=operation_id,
        operation_typ=OperationsTyp.RELIEF,
        werkzeug_id=werkzeug.id,
        spindel_rpm=parameter.spindel_rpm,
        sicherheitshoehe=parameter.sicherheitshoehe,
        bewegungen=bewegungen,
        kommentar=(
            f"Waterline ({len(z_levels)} Z-Levels, "
            f"{pro_level_konturen} mit Konturen)"
        ),
        metadaten={
            "strategie": "waterline",
            "z_levels": z_levels,
            "konturen_pro_level": pro_level_konturen,
        },
    )


__all__ = [
    "erzeuge_waterline_toolpath",
    "heightmap_zu_contour_polygone",
]
