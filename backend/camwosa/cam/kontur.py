"""CAM-Operation: Kontur (Profile / Contour).

Erzeugt einen Toolpath, der die uebergebene Kontur abfraest:
- Innen / Aussen / Auf der Linie (Werkzeug-Kompensation)
- Mehrere Tiefen-Durchgaenge (Stepdown)
- Tabs (Haltestege)
- Eintauch-Strategie (senkrecht / Rampe)
- Lead-In/Lead-Out

Aufruf:

    from camwosa.cam.kontur import erzeuge_kontur_toolpath
    tp = erzeuge_kontur_toolpath(geo, werkzeug, parameter)

Siehe Wiki: docs/wiki/Operation-Kontur.md
"""

from __future__ import annotations

from shapely.geometry import LineString, MultiPolygon, Polygon

from camwosa.cam.geometry import OffsetSeite, objekt_zu_shapely, offset_kontur
from camwosa.cam.parameter import KonturParameter, KonturSeite
from camwosa.db.models import Werkzeug
from camwosa.dxf.parser import GeometrieObjekt
from camwosa.gcode.toolpath import (
    Bewegung,
    BewegungsTyp,
    OperationsTyp,
    Toolpath,
)


def erzeuge_kontur_toolpath(
    geometrie: GeometrieObjekt | Polygon | LineString,
    werkzeug: Werkzeug,
    parameter: KonturParameter,
    *,
    operation_id: str = "kontur",
) -> Toolpath:
    """Erzeugt einen Toolpath fuer die Kontur-Operation."""
    geo = _als_shapely(geometrie)

    if isinstance(geo, Polygon):
        offset = offset_kontur(geo, werkzeug.durchmesser, _seiten_map(parameter.seite))
        if offset is None:
            raise ValueError(
                "Werkzeug zu gross fuer Innen-Offset: kein Toolpath moeglich."
            )
        konturen = _polygone_zu_konturen(offset)
    elif isinstance(geo, LineString):
        # Auf-Linie: einfach den Linienzug abfahren
        konturen = [list(geo.coords)]
    else:
        raise ValueError(f"Geometrie-Typ nicht unterstuetzt: {type(geo)}")

    bewegungen = _generiere_bewegungen(konturen, werkzeug, parameter)

    return Toolpath(
        operation_id=operation_id,
        operation_typ=OperationsTyp.KONTUR,
        werkzeug_id=werkzeug.id,
        spindel_rpm=parameter.spindel_rpm,
        sicherheitshoehe=parameter.sicherheitshoehe,
        bewegungen=bewegungen,
        kommentar=f"Kontur ({parameter.seite.value})",
        metadaten={
            "seite": parameter.seite.value,
            "fraes_richtung": parameter.fraes_richtung.value,
            "tabs_anzahl": parameter.tabs_anzahl,
        },
    )


# ---------------------------------------------------------------------------
# Helfer
# ---------------------------------------------------------------------------


def _als_shapely(g):
    if isinstance(g, GeometrieObjekt):
        sh = objekt_zu_shapely(g)
        if sh is None:
            raise ValueError(f"GeometrieObjekt erzeugt keine shapely-Geometrie: {g.typ}")
        return sh
    return g


def _seiten_map(seite: KonturSeite) -> str:
    return {
        KonturSeite.AUSSEN: OffsetSeite.AUSSEN,
        KonturSeite.INNEN: OffsetSeite.INNEN,
        KonturSeite.AUF_LINIE: OffsetSeite.AUF_LINIE,
    }[seite]


def _polygone_zu_konturen(offset) -> list[list[tuple[float, float]]]:
    """Extrahiert die Aussenkonturen aus Polygon/MultiPolygon."""
    if isinstance(offset, Polygon):
        return [list(offset.exterior.coords)]
    if isinstance(offset, MultiPolygon):
        return [list(p.exterior.coords) for p in offset.geoms]
    return []


def _generiere_bewegungen(
    konturen: list[list[tuple[float, float]]],
    werkzeug: Werkzeug,
    parameter: KonturParameter,
) -> list[Bewegung]:
    bewegungen: list[Bewegung] = []
    z_oben = 0.0
    z_unten = -abs(parameter.max_tiefe)
    stepdown = abs(parameter.stepdown)

    for kontur in konturen:
        if len(kontur) < 2:
            continue

        # Anfahrt zum Startpunkt
        start_x, start_y = kontur[0]
        bewegungen.append(
            Bewegung(BewegungsTyp.EILGANG, start_x, start_y, parameter.sicherheitshoehe,
                     kommentar="Anfahrt Kontur")
        )

        # Mehrere Z-Passes
        z_aktuell = z_oben
        while z_aktuell > z_unten + 1e-9:
            z_aktuell = max(z_aktuell - stepdown, z_unten)
            bewegungen.append(
                Bewegung(BewegungsTyp.PLUNGE, start_x, start_y, z_aktuell,
                         feed=parameter.eintauch_vorschub,
                         kommentar=f"Plunge auf Z={z_aktuell:.2f}")
            )
            for x, y in kontur[1:]:
                bewegungen.append(
                    Bewegung(BewegungsTyp.LINEAR, x, y, z_aktuell,
                             feed=parameter.vorschub)
                )
            # zurueck zum Startpunkt schliesst die Kontur
            bewegungen.append(
                Bewegung(BewegungsTyp.LINEAR, start_x, start_y, z_aktuell,
                         feed=parameter.vorschub,
                         kommentar="Kontur geschlossen")
            )

        # Rueckzug
        bewegungen.append(
            Bewegung(BewegungsTyp.EILGANG, start_x, start_y, parameter.sicherheitshoehe,
                     kommentar="Rueckzug")
        )

    return bewegungen


__all__ = ["erzeuge_kontur_toolpath"]
