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

import math

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


def _kontur_laenge(kontur: list[tuple[float, float]]) -> float:
    """Summe der Segment-Laengen (geschlossen — letzter Punkt verbindet zum ersten)."""
    if len(kontur) < 2:
        return 0.0
    laenge = 0.0
    for i in range(len(kontur)):
        p1 = kontur[i]
        p2 = kontur[(i + 1) % len(kontur)]
        laenge += math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    return laenge


def _ist_in_tab(
    s_aktuell: float,
    s_segment_start: float,
    s_segment_ende: float,
    tab_positionen: list[float],
    tab_breite: float,
) -> tuple[bool, float | None]:
    """Prueft ob die Bogenlaenge ``s_aktuell`` in einem Tab-Bereich liegt.

    Liefert (in_tab, distanz_bis_tab_ende).
    """
    halbe = tab_breite / 2.0
    for s_tab in tab_positionen:
        if s_tab - halbe <= s_aktuell <= s_tab + halbe:
            return True, (s_tab + halbe) - s_aktuell
    return False, None


def _generiere_bewegungen(
    konturen: list[list[tuple[float, float]]],
    werkzeug: Werkzeug,
    parameter: KonturParameter,
) -> list[Bewegung]:
    bewegungen: list[Bewegung] = []
    z_oben = 0.0
    z_unten = -abs(parameter.max_tiefe)
    stepdown = abs(parameter.stepdown)

    for kontur_idx, kontur in enumerate(konturen):
        if len(kontur) < 2:
            continue
        # Backplot-Annotation: Kommentar woraus Operation kommt
        bewegungen.append(
            Bewegung(BewegungsTyp.EILGANG, kontur[0][0], kontur[0][1],
                     parameter.sicherheitshoehe,
                     kommentar=f"--- Kontur {kontur_idx + 1}/{len(konturen)} "
                               f"({parameter.seite.value}) ---")
        )

        # Anfahrt zum Startpunkt
        start_x, start_y = kontur[0]

        # Tabs: Positionen gleichmaessig auf der Bogenlaenge verteilen
        tab_positionen: list[float] = []
        if parameter.tabs_anzahl > 0 and parameter.tabs_hoehe > 0:
            kontur_laenge = _kontur_laenge(kontur)
            for i in range(parameter.tabs_anzahl):
                tab_positionen.append(
                    (i + 0.5) * (kontur_laenge / parameter.tabs_anzahl)
                )
        # Tab-Z = z_unten + tabs_hoehe (Werkzeug haengt etwas hoeher = Steg)
        z_tab = z_unten + parameter.tabs_hoehe

        # Mehrere Z-Passes
        z_aktuell = z_oben
        pass_nr = 0
        while z_aktuell > z_unten + 1e-9:
            pass_nr += 1
            z_aktuell = max(z_aktuell - stepdown, z_unten)
            ist_letzter_pass = abs(z_aktuell - z_unten) < 1e-6

            bewegungen.append(
                Bewegung(BewegungsTyp.PLUNGE, start_x, start_y, z_aktuell,
                         feed=parameter.eintauch_vorschub,
                         kommentar=f"Pass {pass_nr} Z={z_aktuell:.2f}")
            )

            # Tab-Logik: nur im letzten Pass (wenn z_aktuell unter z_tab liegen wuerde)
            tab_aktiv = (tab_positionen and ist_letzter_pass and z_aktuell < z_tab)

            if not tab_aktiv:
                # Standard: normal entlang der Kontur
                for x, y in kontur[1:]:
                    bewegungen.append(
                        Bewegung(BewegungsTyp.LINEAR, x, y, z_aktuell,
                                 feed=parameter.vorschub)
                    )
            else:
                # Mit Tabs: Kontur in feine Sub-Segmente (1 mm) zerlegen
                # damit Tab-Bereiche nicht uebersprungen werden.
                schrittweite = 1.0
                s_aktuell = 0.0
                prev_x, prev_y = start_x, start_y
                kontur_geschlossen = kontur + [(start_x, start_y)]
                halbe = parameter.tabs_breite / 2.0
                for x, y in kontur_geschlossen[1:]:
                    seg_laenge = math.hypot(x - prev_x, y - prev_y)
                    if seg_laenge < 1e-9:
                        continue
                    n_steps = max(1, int(math.ceil(seg_laenge / schrittweite)))
                    dx = (x - prev_x) / n_steps
                    dy = (y - prev_y) / n_steps
                    for k in range(1, n_steps + 1):
                        sub_x = prev_x + dx * k
                        sub_y = prev_y + dy * k
                        sub_s_mitte = s_aktuell + (k - 0.5) * (seg_laenge / n_steps)
                        in_tab = any(
                            (s_tab - halbe) <= sub_s_mitte <= (s_tab + halbe)
                            for s_tab in tab_positionen
                        )
                        z_ziel = z_tab if in_tab else z_aktuell
                        bewegungen.append(
                            Bewegung(BewegungsTyp.LINEAR, sub_x, sub_y, z_ziel,
                                     feed=parameter.vorschub,
                                     kommentar="Tab" if in_tab else "")
                        )
                    s_aktuell += seg_laenge
                    prev_x, prev_y = x, y
                continue  # Schleife bewusst beenden — bewegungen schon erzeugt
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
