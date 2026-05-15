"""CAM-Operation: Gravur.

Folgt einer Kurve mit definierter Tiefe.

Strategien:
- KONSTANTE_TIEFE: einfaches Folgen mit fester Z-Tiefe
- V_CARVING: variable Tiefe entlang medialer Achse (V-Bit)

Phase 1 implementiert KONSTANTE_TIEFE.
V_CARVING braucht medial-axis-Algorithmus (kommt in Phase 1+).

Siehe Wiki: docs/wiki/Operation-Gravur.md
"""

from __future__ import annotations

from shapely.geometry import LineString, Polygon

from camwosa.cam.geometry import objekt_zu_shapely
from camwosa.cam.parameter import GravurParameter, GravurStrategie
from camwosa.db.models import Werkzeug
from camwosa.dxf.parser import GeometrieObjekt
from camwosa.gcode.toolpath import (
    Bewegung,
    BewegungsTyp,
    OperationsTyp,
    Toolpath,
)


def erzeuge_gravur_toolpath(
    geometrie: GeometrieObjekt | LineString | Polygon,
    werkzeug: Werkzeug,
    parameter: GravurParameter,
    *,
    operation_id: str = "gravur",
) -> Toolpath:
    if parameter.strategie == GravurStrategie.V_CARVING:
        raise NotImplementedError(
            "V-Carving wird in einem Folge-Schritt implementiert "
            "(braucht medial-axis-Algorithmus)."
        )

    pfade = _als_pfade(geometrie)
    bewegungen = _generiere_bewegungen(pfade, werkzeug, parameter)
    return Toolpath(
        operation_id=operation_id,
        operation_typ=OperationsTyp.GRAVUR,
        werkzeug_id=werkzeug.id,
        spindel_rpm=parameter.spindel_rpm,
        sicherheitshoehe=parameter.sicherheitshoehe,
        bewegungen=bewegungen,
        kommentar=f"Gravur ({parameter.strategie.value})",
        metadaten={"strategie": parameter.strategie.value},
    )


def _als_pfade(g) -> list[list[tuple[float, float]]]:
    """Wandelt eine Eingabe-Geometrie in eine Liste von Punktpfaden."""
    if isinstance(g, GeometrieObjekt):
        sh = objekt_zu_shapely(g)
        if sh is None:
            return []
        g = sh
    if isinstance(g, LineString):
        return [list(g.coords)]
    if isinstance(g, Polygon):
        pfade = [list(g.exterior.coords)]
        for innen in g.interiors:
            pfade.append(list(innen.coords))
        return pfade
    raise ValueError(f"Geometrie-Typ nicht unterstuetzt fuer Gravur: {type(g)}")


def _generiere_bewegungen(
    pfade: list[list[tuple[float, float]]],
    werkzeug: Werkzeug,
    parameter: GravurParameter,
) -> list[Bewegung]:
    bewegungen: list[Bewegung] = []
    z_unten = -abs(parameter.max_tiefe)
    zustellung = min(parameter.max_zustellung, parameter.max_tiefe)
    for pfad in pfade:
        if len(pfad) < 2:
            continue
        start_x, start_y = pfad[0]
        bewegungen.append(
            Bewegung(BewegungsTyp.EILGANG, start_x, start_y, parameter.sicherheitshoehe)
        )
        z_aktuell = 0.0
        while z_aktuell > z_unten + 1e-9:
            z_aktuell = max(z_aktuell - zustellung, z_unten)
            bewegungen.append(
                Bewegung(BewegungsTyp.PLUNGE, start_x, start_y, z_aktuell,
                         feed=parameter.eintauch_vorschub)
            )
            for x, y in pfad[1:]:
                bewegungen.append(
                    Bewegung(BewegungsTyp.LINEAR, x, y, z_aktuell, feed=parameter.vorschub)
                )
        bewegungen.append(
            Bewegung(BewegungsTyp.EILGANG, x, y, parameter.sicherheitshoehe)
        )
    return bewegungen


__all__ = ["erzeuge_gravur_toolpath"]
