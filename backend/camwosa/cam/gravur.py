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
        return _erzeuge_v_carving_toolpath(geometrie, werkzeug, parameter, operation_id)

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


def _erzeuge_v_carving_toolpath(
    geometrie, werkzeug: Werkzeug, parameter: GravurParameter, operation_id: str,
) -> Toolpath:
    """V-Carving: Werkzeug folgt geschlossener Kontur mit variabler Tiefe.

    Naeherung der medial axis durch wiederholtes Offset nach innen. Pro
    Offset-Stufe ist der Abstand zur Wand bekannt → das gibt die Z-Tiefe
    via Spitzenwinkel des V-Bits:

        z = -abstand_zur_wand / tan(spitzenwinkel/2)
    """
    import math
    from camwosa.cam.geometry import objekt_zu_shapely, offset_polygon

    if isinstance(geometrie, GeometrieObjekt):
        sh = objekt_zu_shapely(geometrie)
    else:
        sh = geometrie
    if not isinstance(sh, Polygon):
        raise ValueError("V-Carving braucht eine geschlossene Polygon-Kontur.")

    spitze = parameter.spitzenwinkel_grad
    if spitze is None and werkzeug.spitzenwinkel is not None:
        spitze = werkzeug.spitzenwinkel
    if spitze is None:
        raise ValueError("V-Carving braucht spitzenwinkel_grad (oder Werkzeug mit Spitzenwinkel)")
    halb_winkel = math.radians(spitze / 2.0)
    tan_halb = math.tan(halb_winkel)
    if tan_halb < 1e-6:
        raise ValueError("Spitzenwinkel zu spitz")

    bewegungen: list[Bewegung] = []
    bewegungen.append(Bewegung(
        BewegungsTyp.EILGANG, sh.exterior.coords[0][0], sh.exterior.coords[0][1],
        parameter.sicherheitshoehe,
        kommentar=f"--- V-Carving (Spitzenwinkel {spitze}°) ---",
    ))

    # Step 1: Aussenkontur entlang fraesen (Z=0)
    aussen = list(sh.exterior.coords)
    if aussen:
        bewegungen.append(Bewegung(
            BewegungsTyp.PLUNGE, aussen[0][0], aussen[0][1], 0,
            feed=parameter.eintauch_vorschub,
        ))
        for x, y in aussen[1:]:
            bewegungen.append(Bewegung(
                BewegungsTyp.LINEAR, x, y, 0, feed=parameter.vorschub,
            ))

    # Step 2: Wiederhol-Offset nach innen mit feiner Schrittweite
    schrittweite = max(parameter.max_zustellung, 0.1)
    distanz = schrittweite
    aktuell = sh
    z_min = -abs(parameter.max_tiefe)
    while True:
        offset = offset_polygon(aktuell, -schrittweite)
        if offset is None or offset.is_empty:
            break
        # Tiefe an dieser Offset-Stufe
        z = -distanz / tan_halb
        if z < z_min:
            z = z_min
        # Konturen extrahieren
        polys = []
        if isinstance(offset, Polygon):
            polys = [offset]
        elif hasattr(offset, "geoms"):
            polys = [g for g in offset.geoms if isinstance(g, Polygon)]
        for p in polys:
            pts = list(p.exterior.coords)
            if not pts:
                continue
            # Eilanfahrt
            bewegungen.append(Bewegung(
                BewegungsTyp.EILGANG, pts[0][0], pts[0][1], parameter.sicherheitshoehe,
            ))
            bewegungen.append(Bewegung(
                BewegungsTyp.PLUNGE, pts[0][0], pts[0][1], z,
                feed=parameter.eintauch_vorschub,
            ))
            for x, y in pts[1:]:
                bewegungen.append(Bewegung(
                    BewegungsTyp.LINEAR, x, y, z, feed=parameter.vorschub,
                ))
        if z <= z_min + 1e-6:
            break
        distanz += schrittweite
        aktuell = offset

    # Rueckzug
    if bewegungen:
        last = bewegungen[-1]
        bewegungen.append(Bewegung(
            BewegungsTyp.EILGANG, last.x, last.y, parameter.sicherheitshoehe,
        ))

    return Toolpath(
        operation_id=operation_id,
        operation_typ=OperationsTyp.GRAVUR,
        werkzeug_id=werkzeug.id,
        spindel_rpm=parameter.spindel_rpm,
        sicherheitshoehe=parameter.sicherheitshoehe,
        bewegungen=bewegungen,
        kommentar=f"V-Carving Spitzenwinkel={spitze}°",
        metadaten={"strategie": "v_carving", "spitzenwinkel_grad": spitze},
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
