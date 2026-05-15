"""Rotary-Achse Funktionen.

CAMWOSA-Rotary fuer Genmitsu-Setup:
- Y-Achse umgemappt auf Rotation
- $101 = 88.889 steps/deg
- Y-Werte werden im G-Code als Grad interpretiert

Hauptfunktionen:
- wrap_2d_auf_zylinder: Mappt 2D-Geometrie auf einen Zylinder mit Radius r
- vorschub_korrektur_grad: rechnet linearen Vorschub auf Winkel-Vorschub um
- erzeuge_indexing_toolpath: Bohrungen/Operationen rundum bei diskreten Winkeln

Siehe Wiki: docs/wiki/Postprozessor-GRBL-Rotary.md, docs/wiki/Rotary-Wrapping.md
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from camwosa.dxf.parser import Punkt2D
from camwosa.gcode.toolpath import (
    Bewegung,
    BewegungsTyp,
    OperationsTyp,
    Toolpath,
)


@dataclass(frozen=True)
class WrapErgebnis:
    """Wrapping-Ergebnis: 2D-Punkte (X, Winkel) statt (X, Y)."""

    punkte: list[Punkt2D]  # x in mm, y in Grad
    radius: float  # zugrundeliegender Radius


def wrap_2d_auf_zylinder(
    punkte_2d: list[Punkt2D], radius: float
) -> WrapErgebnis:
    """Wickelt eine 2D-Geometrie auf einen Zylinder.

    X bleibt X (entlang der Zylinder-Achse).
    Y wird in Winkel umgerechnet: winkel_grad = (Y / Umfang) * 360
    """
    if radius <= 0:
        raise ValueError("Radius muss positiv sein")
    umfang = 2 * math.pi * radius
    return WrapErgebnis(
        punkte=[
            Punkt2D(p.x, (p.y / umfang) * 360.0)
            for p in punkte_2d
        ],
        radius=radius,
    )


def vorschub_korrektur_grad(linearer_vorschub_mm_min: float, radius: float) -> float:
    """Rechnet linearen Vorschub am Zylinder-Umfang in Grad/min um.

    Linearer Pfad an Radius r mit v mm/min entspricht winkel/min:
        omega = v / r [rad/min]  ->  omega_deg = omega * 180/pi
    """
    if radius <= 0:
        raise ValueError("Radius muss positiv sein")
    return linearer_vorschub_mm_min / radius * (180.0 / math.pi)


def erzeuge_indexing_toolpath(
    operation_punkte: list[Punkt2D],
    werkzeug_id: str,
    *,
    rpm: float,
    sicherheits_radius: float,
    bohrtiefe: float,
    plunge_feed: float,
    operation_id: str = "rotary_indexing",
) -> Toolpath:
    """Erzeugt einen Indexing-Toolpath: Bohrungen rundum auf einem Zylinder.

    operation_punkte: Liste von (X, Winkel-in-Grad).
    sicherheits_radius: Z-Position bei der das Werkzeug sicher von der Oberflaeche entfernt ist.
    bohrtiefe: wie tief das Werkzeug eintaucht (negative Z relativ zur Oberflaeche).
    """
    bewegungen: list[Bewegung] = []
    for p in operation_punkte:
        # Eilgang in X/Winkel auf Sicherheitsabstand
        bewegungen.append(Bewegung(
            BewegungsTyp.EILGANG, p.x, p.y, sicherheits_radius,
            kommentar=f"Index Pos X={p.x:.1f} Winkel={p.y:.1f}",
        ))
        # Plunge bis Bohrtiefe (Z-Wert ist Distanz von der Spindelachse)
        bewegungen.append(Bewegung(
            BewegungsTyp.PLUNGE, p.x, p.y, sicherheits_radius - bohrtiefe,
            feed=plunge_feed,
        ))
        # Rueckzug
        bewegungen.append(Bewegung(
            BewegungsTyp.EILGANG, p.x, p.y, sicherheits_radius,
        ))
    return Toolpath(
        operation_id=operation_id,
        operation_typ=OperationsTyp.BOHREN,
        werkzeug_id=werkzeug_id,
        spindel_rpm=rpm,
        sicherheitshoehe=sicherheits_radius,
        bewegungen=bewegungen,
        kommentar=f"Rotary-Indexing {len(operation_punkte)} Positionen",
        metadaten={"modus": "rotary_y", "anzahl": len(operation_punkte)},
    )


__all__ = [
    "WrapErgebnis",
    "erzeuge_indexing_toolpath",
    "vorschub_korrektur_grad",
    "wrap_2d_auf_zylinder",
]
