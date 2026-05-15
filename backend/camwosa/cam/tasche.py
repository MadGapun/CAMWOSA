"""CAM-Operation: Tasche (Pocket).

Raeumt eine geschlossene Flaeche aus.

Strategien:
- PARALLEL (Zickzack)         : default, schnell, gleichmaessig
- SPIRAL_AUSSEN               : von innen nach aussen (rund)
- SPIRAL_INNEN                : von aussen nach innen (rechteckig)
- OFFSET_KONTUR               : geschachtelte Konturen
- ADAPTIVE                    : trochoidaler Pfad (Phase E4)

Phase 1 implementiert PARALLEL und OFFSET_KONTUR.
SPIRAL und ADAPTIVE folgen in spaeteren Phasen.

Siehe Wiki: docs/wiki/Operation-Tasche.md
"""

from __future__ import annotations

import math

from shapely.geometry import LineString, MultiPolygon, Polygon

from camwosa.cam.geometry import objekt_zu_shapely, offset_polygon
from camwosa.cam.parameter import TaschenParameter, TaschenStrategie
from camwosa.db.models import Werkzeug
from camwosa.dxf.parser import GeometrieObjekt
from camwosa.gcode.toolpath import (
    Bewegung,
    BewegungsTyp,
    OperationsTyp,
    Toolpath,
)


def erzeuge_tasche_toolpath(
    geometrie: GeometrieObjekt | Polygon,
    werkzeug: Werkzeug,
    parameter: TaschenParameter,
    *,
    operation_id: str = "tasche",
) -> Toolpath:
    geo = _als_polygon(geometrie)

    if parameter.strategie == TaschenStrategie.OFFSET_KONTUR:
        bahnen = _offset_kontur_bahnen(geo, werkzeug, parameter)
    else:
        # Default: parallele Zickzack-Bahnen
        bahnen = _parallel_bahnen(geo, werkzeug, parameter)

    bewegungen = _generiere_bewegungen(bahnen, werkzeug, parameter)

    return Toolpath(
        operation_id=operation_id,
        operation_typ=OperationsTyp.TASCHE,
        werkzeug_id=werkzeug.id,
        spindel_rpm=parameter.spindel_rpm,
        sicherheitshoehe=parameter.sicherheitshoehe,
        bewegungen=bewegungen,
        kommentar=f"Tasche ({parameter.strategie.value})",
        metadaten={"strategie": parameter.strategie.value},
    )


# ---------------------------------------------------------------------------
# Bahn-Generierung
# ---------------------------------------------------------------------------


def _als_polygon(g) -> Polygon:
    if isinstance(g, GeometrieObjekt):
        sh = objekt_zu_shapely(g)
        if not isinstance(sh, Polygon):
            raise ValueError("Tasche braucht eine geschlossene Kontur (Polygon).")
        return sh
    if isinstance(g, Polygon):
        return g
    raise ValueError(f"Geometrie-Typ nicht unterstuetzt fuer Tasche: {type(g)}")


def _offset_kontur_bahnen(
    polygon: Polygon, werkzeug: Werkzeug, parameter: TaschenParameter
) -> list[list[tuple[float, float]]]:
    """Erzeugt geschachtelte Konturen mit jeweils einem Stepover-Abstand."""
    r = werkzeug.durchmesser / 2.0
    stepover = werkzeug.durchmesser * (parameter.stepover_prozent / 100.0)

    # Erste Bahn: Aussenkante minus Werkzeug-Radius minus Aufmass
    aussen_offset = -(r + parameter.aufmass_wand)
    bahn = offset_polygon(polygon, aussen_offset)

    bahnen: list[list[tuple[float, float]]] = []
    while bahn is not None and not bahn.is_empty:
        if isinstance(bahn, Polygon):
            bahnen.append(list(bahn.exterior.coords))
        elif isinstance(bahn, MultiPolygon):
            for p in bahn.geoms:
                bahnen.append(list(p.exterior.coords))
        bahn = offset_polygon(bahn, -stepover)
        # Sicherheits-Bremse: Wenn Bahn nicht weiter schrumpft
        if bahn is not None and bahn.area < 1e-6:
            break

    return bahnen


def _parallel_bahnen(
    polygon: Polygon, werkzeug: Werkzeug, parameter: TaschenParameter
) -> list[list[tuple[float, float]]]:
    """Erzeugt parallele Linien-Bahnen (Zickzack-Schraffur).

    Die Bahnen verlaufen entlang der X-Achse mit Abstand stepover.
    """
    r = werkzeug.durchmesser / 2.0
    stepover = werkzeug.durchmesser * (parameter.stepover_prozent / 100.0)

    # Innenraum (Polygon minus Aufmass-Wand minus Werkzeug-Radius)
    innen = offset_polygon(polygon, -(r + parameter.aufmass_wand))
    if innen is None or innen.is_empty:
        return []

    bb = innen.bounds  # minx, miny, maxx, maxy
    minx, miny, maxx, maxy = bb

    bahnen: list[list[tuple[float, float]]] = []
    y = miny
    richtung = 1
    while y <= maxy + 1e-9:
        linie = LineString([(minx - 1, y), (maxx + 1, y)])
        clip = linie.intersection(innen)
        if not clip.is_empty:
            segmente = _linestring_zu_segmente(clip)
            for seg in segmente:
                if richtung == -1:
                    seg = list(reversed(seg))
                bahnen.append(seg)
        richtung *= -1
        y += stepover

    return bahnen


def _linestring_zu_segmente(geo) -> list[list[tuple[float, float]]]:
    """Konvertiert einen MultiLineString/LineString in Listen von Punkten."""
    geom_typ = geo.geom_type
    if geom_typ == "LineString":
        return [list(geo.coords)]
    if geom_typ == "MultiLineString":
        return [list(g.coords) for g in geo.geoms]
    if geom_typ == "GeometryCollection":
        out: list[list[tuple[float, float]]] = []
        for g in geo.geoms:
            out.extend(_linestring_zu_segmente(g))
        return out
    return []


def _generiere_bewegungen(
    bahnen: list[list[tuple[float, float]]],
    werkzeug: Werkzeug,
    parameter: TaschenParameter,
) -> list[Bewegung]:
    bewegungen: list[Bewegung] = []
    z_oben = 0.0
    z_unten = -abs(parameter.max_tiefe) + parameter.aufmass_boden
    stepdown = abs(parameter.stepdown)

    z_aktuell = z_oben
    while z_aktuell > z_unten + 1e-9:
        z_aktuell = max(z_aktuell - stepdown, z_unten)
        for bahn in bahnen:
            if len(bahn) < 2:
                continue
            start_x, start_y = bahn[0]
            bewegungen.append(
                Bewegung(BewegungsTyp.EILGANG, start_x, start_y, parameter.sicherheitshoehe)
            )
            bewegungen.append(
                Bewegung(BewegungsTyp.PLUNGE, start_x, start_y, z_aktuell,
                         feed=parameter.eintauch_vorschub)
            )
            for x, y in bahn[1:]:
                bewegungen.append(
                    Bewegung(BewegungsTyp.LINEAR, x, y, z_aktuell, feed=parameter.vorschub)
                )
            bewegungen.append(
                Bewegung(BewegungsTyp.EILGANG, x, y, parameter.sicherheitshoehe)
            )
    return bewegungen


__all__ = ["erzeuge_tasche_toolpath"]
