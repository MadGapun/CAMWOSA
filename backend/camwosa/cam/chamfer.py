"""Chamfering (Fasenfraesen, A45 / E5).

Erzeugt eine Fase entlang einer Kontur. Nutzt typischerweise einen V-Bit
oder Fasenfraeser, der entlang der Kontur lauft, aber bei reduzierter
Tiefe (statt voll eintauchen).

Parameter:
- fasenbreite_mm: gewuenschte Breite der Fase (horizontal)
- fasenwinkel_grad: Winkel der Fase zur Werkstueck-Oberkante (typ. 45°)
  -> ergibt automatisch die noetige Tiefe und Werkzeug-Spitze-Position
- max_tiefe_mm: Sicherheits-Limit (Cutter darf nicht tiefer)

Beziehung Fase ↔ Werkzeug:
Bei einem V-Bit mit Spitzenwinkel α (Halbwinkel = α/2):
- Fasenwinkel zur Oberkante = (90° - α/2)
- Beispiel: V-Bit 90° -> Fasenwinkel 45°
- Beispiel: V-Bit 60° -> Fasenwinkel 60°

Bei einem 45°-Fasen-Cutter ist der Winkel im Werkzeug bereits 45°.

Wiki: docs/wiki/Spezial-Operationen.md
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from camwosa.db.models import Werkzeug, WerkzeugTyp
from camwosa.gcode.toolpath import (
    Bewegung,
    BewegungsTyp,
    OperationsTyp,
    Toolpath,
)


@dataclass
class ChamferParameter:
    """Parameter fuer Chamfering."""

    werkzeug_id: str
    spindel_rpm: float
    vorschub: float
    eintauch_vorschub: float
    sicherheitshoehe_mm: float = 5.0
    fasenbreite_mm: float = 1.0
    """Gewuenschte horizontale Breite der Fase."""
    max_tiefe_mm: float | None = None
    """Sicherheits-Limit. Wenn None, automatisch aus Fasenbreite + Werkzeug-Winkel."""
    werkstueck_oberkante_mm: float = 0.0


def berechne_fasen_tiefe(
    fasenbreite_mm: float, werkzeug: Werkzeug,
) -> float:
    """Berechnet die Z-Tiefe damit ein V-Bit eine bestimmte Fasenbreite macht.

    Geometrie: V-Bit mit Halbwinkel a = spitzenwinkel/2.
    Bei Eintauchtiefe t ist die Schnittbreite an der Oberkante:
        breite = 2 * t * tan(a)
    Umgekehrt:
        t = breite / (2 * tan(a))

    Args:
        fasenbreite_mm: gewuenschte horizontale Fasen-Breite
        werkzeug: V-Bit oder Fasenfraeser

    Returns:
        Tiefe in mm (positiv).
    """
    if werkzeug.typ not in (WerkzeugTyp.V_BIT, WerkzeugTyp.BALLNOSE_V_BIT,
                            WerkzeugTyp.GRAVIERSTICHEL, WerkzeugTyp.DIAMANTGRAVIERER):
        raise ValueError(
            f"Werkzeug-Typ {werkzeug.typ.value} ist kein V-Bit / Fasenfraeser"
        )
    if werkzeug.spitzenwinkel is None or werkzeug.spitzenwinkel <= 0:
        raise ValueError("Werkzeug braucht spitzenwinkel > 0")
    halb_winkel_rad = math.radians(werkzeug.spitzenwinkel / 2.0)
    tan_halb = math.tan(halb_winkel_rad)
    if tan_halb <= 0:
        raise ValueError(f"Werkzeug-Winkel zu klein: {werkzeug.spitzenwinkel}")
    return fasenbreite_mm / (2 * tan_halb)


def erzeuge_chamfer_toolpath(
    punkte_xy: list[tuple[float, float]],
    werkzeug: Werkzeug,
    parameter: ChamferParameter,
    *,
    geschlossen: bool = False,
    operation_id: str = "chamfer",
) -> Toolpath:
    """Erzeugt Chamfer-Toolpath entlang einer Kontur.

    Algorithmus:
    1. Berechne Eintauchtiefe aus Fasenbreite + Werkzeug-Winkel
    2. Anfahrt auf Sicherheitshoehe ueber erstem Punkt
    3. Plunge auf Fasen-Tiefe
    4. Linear durch alle Konturpunkte
    5. (Optional) zum Anfang zurueck wenn geschlossen
    6. Rueckzug

    Args:
        punkte_xy: Kontur als Punktliste
        werkzeug: V-Bit oder Fasenfraeser
        parameter: Chamfer-Parameter
        geschlossen: Soll Pfad geschlossen werden?

    Returns:
        Toolpath
    """
    if len(punkte_xy) < 2:
        raise ValueError("Mindestens 2 Punkte fuer Chamfer noetig")

    tiefe = berechne_fasen_tiefe(parameter.fasenbreite_mm, werkzeug)
    if parameter.max_tiefe_mm and tiefe > parameter.max_tiefe_mm:
        raise ValueError(
            f"Berechnete Fasen-Tiefe {tiefe:.2f} mm uebersteigt max_tiefe "
            f"{parameter.max_tiefe_mm} mm. Fasenbreite reduzieren oder "
            f"max_tiefe erhoehen."
        )

    z_fase = parameter.werkstueck_oberkante_mm - tiefe
    z_safe = parameter.werkstueck_oberkante_mm + parameter.sicherheitshoehe_mm

    bewegungen: list[Bewegung] = [
        Bewegung(BewegungsTyp.EILGANG,
                 x=punkte_xy[0][0], y=punkte_xy[0][1], z=z_safe,
                 kommentar=f"Chamfer: Anfahrt (Fase {parameter.fasenbreite_mm}mm)"),
        Bewegung(BewegungsTyp.PLUNGE,
                 x=punkte_xy[0][0], y=punkte_xy[0][1], z=z_fase,
                 feed=parameter.eintauch_vorschub),
    ]
    for x, y in punkte_xy[1:]:
        bewegungen.append(Bewegung(
            BewegungsTyp.LINEAR, x=x, y=y, z=z_fase,
            feed=parameter.vorschub,
        ))
    if geschlossen:
        bewegungen.append(Bewegung(
            BewegungsTyp.LINEAR, x=punkte_xy[0][0], y=punkte_xy[0][1],
            z=z_fase, feed=parameter.vorschub,
        ))
    bewegungen.append(Bewegung(
        BewegungsTyp.EILGANG, x=punkte_xy[-1][0], y=punkte_xy[-1][1], z=z_safe,
        kommentar="Chamfer: Rueckzug",
    ))

    return Toolpath(
        operation_id=operation_id,
        operation_typ=OperationsTyp.GRAVUR,
        werkzeug_id=werkzeug.id,
        spindel_rpm=parameter.spindel_rpm,
        sicherheitshoehe=parameter.sicherheitshoehe_mm,
        bewegungen=bewegungen,
        kommentar=f"Chamfer Fasenbreite {parameter.fasenbreite_mm}mm Tiefe {tiefe:.2f}mm",
        metadaten={
            "fasenbreite_mm": parameter.fasenbreite_mm,
            "fasen_tiefe_mm": tiefe,
            "werkzeug_spitzenwinkel": werkzeug.spitzenwinkel,
            "geschlossen": geschlossen,
        },
    )


__all__ = [
    "ChamferParameter",
    "berechne_fasen_tiefe",
    "erzeuge_chamfer_toolpath",
]
