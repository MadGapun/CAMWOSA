"""CAM-Operation: Bohren.

Erzeugt einen Toolpath fuer Bohrungen an definierten X/Y-Positionen.

Strategien:
- STANDARD: direkt nach unten und hoch
- PECK: schrittweise mit kleinem Rueckzug zur Spanabfuhr
- TIEF_PECK: schrittweise mit Rueckzug auf Sicherheitshoehe
- HELIX: schraubendes Helix-Bohren (auch fuer Loecher groesser als Fraeser)
- REIB: Konturbohren mit kleinerem Werkzeug

Phase 1 implementiert STANDARD, PECK, TIEF_PECK.
HELIX und REIB folgen.

Siehe Wiki: docs/wiki/Operation-Bohren.md
"""

from __future__ import annotations

from camwosa.cam.parameter import BohrParameter, BohrStrategie
from camwosa.db.models import Werkzeug
from camwosa.dxf.parser import GeometrieObjekt, GeometrieTyp, Punkt2D
from camwosa.gcode.toolpath import (
    Bewegung,
    BewegungsTyp,
    OperationsTyp,
    Toolpath,
)


def erzeuge_bohren_toolpath(
    punkte: list[Punkt2D] | list[GeometrieObjekt],
    werkzeug: Werkzeug,
    parameter: BohrParameter,
    *,
    operation_id: str = "bohren",
) -> Toolpath:
    bohrungen = _extrahiere_bohrungen(punkte)
    bewegungen: list[Bewegung] = []
    for x, y in bohrungen:
        bewegungen.extend(_bohrung_bewegungen(x, y, werkzeug, parameter))
    return Toolpath(
        operation_id=operation_id,
        operation_typ=OperationsTyp.BOHREN,
        werkzeug_id=werkzeug.id,
        spindel_rpm=parameter.spindel_rpm,
        sicherheitshoehe=parameter.sicherheitshoehe,
        bewegungen=bewegungen,
        kommentar=f"Bohren {len(bohrungen)} Loecher ({parameter.strategie.value})",
        metadaten={"strategie": parameter.strategie.value, "anzahl": len(bohrungen)},
    )


def _extrahiere_bohrungen(
    eingabe: list[Punkt2D] | list[GeometrieObjekt],
) -> list[tuple[float, float]]:
    bohrungen: list[tuple[float, float]] = []
    for e in eingabe:
        if isinstance(e, Punkt2D):
            bohrungen.append((e.x, e.y))
        elif isinstance(e, GeometrieObjekt):
            if e.typ == GeometrieTyp.PUNKT:
                bohrungen.append((e.punkte[0].x, e.punkte[0].y))
            elif e.typ == GeometrieTyp.KREIS:
                bohrungen.append((e.punkte[0].x, e.punkte[0].y))
            else:
                # Polylinie -> verwende ersten Punkt
                bohrungen.append((e.punkte[0].x, e.punkte[0].y))
    return bohrungen


def _bohrung_bewegungen(
    x: float, y: float, werkzeug: Werkzeug, parameter: BohrParameter
) -> list[Bewegung]:
    z_unten = -abs(parameter.max_tiefe)
    bewegungen: list[Bewegung] = [
        Bewegung(BewegungsTyp.EILGANG, x, y, parameter.sicherheitshoehe,
                 kommentar=f"Bohrung X={x:.2f} Y={y:.2f}"),
    ]

    if parameter.strategie == BohrStrategie.STANDARD:
        bewegungen.append(
            Bewegung(BewegungsTyp.PLUNGE, x, y, z_unten,
                     feed=parameter.eintauch_vorschub)
        )
    elif parameter.strategie == BohrStrategie.PECK:
        z_aktuell = 0.0
        while z_aktuell > z_unten + 1e-9:
            z_aktuell = max(z_aktuell - parameter.peck_tiefe, z_unten)
            bewegungen.append(
                Bewegung(BewegungsTyp.PLUNGE, x, y, z_aktuell,
                         feed=parameter.eintauch_vorschub)
            )
            if z_aktuell > z_unten + 1e-9:
                # kurzer Rueckzug
                bewegungen.append(
                    Bewegung(BewegungsTyp.EILGANG, x, y,
                             z_aktuell + parameter.rueckzugs_hoehe,
                             kommentar="Peck Rueckzug")
                )
    elif parameter.strategie == BohrStrategie.TIEF_PECK:
        z_aktuell = 0.0
        while z_aktuell > z_unten + 1e-9:
            z_aktuell = max(z_aktuell - parameter.peck_tiefe, z_unten)
            bewegungen.append(
                Bewegung(BewegungsTyp.PLUNGE, x, y, z_aktuell,
                         feed=parameter.eintauch_vorschub)
            )
            if z_aktuell > z_unten + 1e-9:
                bewegungen.append(
                    Bewegung(BewegungsTyp.EILGANG, x, y,
                             parameter.sicherheitshoehe,
                             kommentar="Tief-Peck Rueckzug")
                )
                bewegungen.append(
                    Bewegung(BewegungsTyp.EILGANG, x, y, z_aktuell + 0.5)
                )
    else:
        raise NotImplementedError(
            f"Bohr-Strategie {parameter.strategie} noch nicht implementiert"
        )

    bewegungen.append(
        Bewegung(BewegungsTyp.EILGANG, x, y, parameter.sicherheitshoehe,
                 kommentar="Rueckzug")
    )
    return bewegungen


__all__ = ["erzeuge_bohren_toolpath"]
