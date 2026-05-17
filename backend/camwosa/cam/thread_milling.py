"""Thread-Milling: Gewinde fraesen mit Helix-Bewegung (A45-Rest, Cluster E).

Hintergrund (Markus' Workflow):
Statt mit einem Gewindebohrer (zerstoerend bei Fehler, hohe Drehmomente fuer kleine
Gewinde) kann man Gewinde mit einem Gewindefraeser herstellen — der ist:
- universell (ein Fraeser kann z.B. M3-M10)
- weniger Drehmoment-belastet
- besser fuer Sacklocher (keine Spaene unten)
- besser bei harten Materialien (Stahl, Alu)

Wie es funktioniert:
1. Werkzeug auf Mittelpunkt + Sicherheitshoehe positionieren
2. Schraeg auf den ersten Helix-Punkt absenken (rampe)
3. Helix mit GEWINDE-STEIGUNG und GEWINDE-RADIUS ausfahren
4. In Mitte zurueck + heben

Output ist eine Reihe von Bewegungen die ein Postprozessor in G2/G3-Bogen
oder feine Liniensegmente umwandelt. GRBL unterstuetzt G2/G3 — wir generieren
linear-interpolierte Punkte fuer maximale Kompatibilitaet.

Issue: #39 (Cluster E)
"""

from __future__ import annotations

import math
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from camwosa.db.models import Werkzeug
from camwosa.gcode.toolpath import (
    Bewegung,
    BewegungsTyp,
    OperationsTyp,
    Toolpath,
)


class GewindeRichtung(str, Enum):
    """Rechtsgewinde (Standard) vs Linksgewinde."""
    RECHTS = "rechts"
    LINKS = "links"


class GewindeArt(str, Enum):
    """Innen- vs Aussengewinde — Werkzeug-Bewegung gegenlaeufig."""
    INNEN = "innen"  # Werkzeug kreist innerhalb des Lochs
    AUSSEN = "aussen"  # Werkzeug kreist um einen Bolzen


class ThreadMillingParameter(BaseModel):
    """Parameter fuer eine Thread-Milling-Operation."""

    model_config = ConfigDict(extra="ignore")

    werkzeug_id: str
    spindel_rpm: float = Field(gt=0)
    vorschub: float = Field(gt=0, description="mm/min auf der Helix")
    eintauch_vorschub: float = Field(gt=0)
    sicherheitshoehe: float = Field(default=3.0, gt=0)

    # Gewinde-Spezifikation
    nenn_durchmesser: float = Field(gt=0, description="z.B. 6.0 fuer M6")
    gewinde_steigung: float = Field(
        gt=0, description="Steigung pro Umdrehung (mm). M6 = 1.0, M3 = 0.5",
    )
    gewinde_tiefe: float = Field(
        gt=0, description="Wie tief das Gewinde im Material liegt (Z-Richtung)",
    )
    art: GewindeArt = GewindeArt.INNEN
    richtung: GewindeRichtung = GewindeRichtung.RECHTS

    # Fraes-Strategie
    werkzeug_durchmesser_korrektur: float = Field(
        default=0.0,
        description="Plus = Fraeser kleiner als nominal (groesseres Gewinde-D)",
    )
    segmente_pro_umdrehung: int = Field(
        default=36, ge=8, le=360,
        description="Linear-Interpolation pro Helix-Umdrehung (mehr = glatter)",
    )
    mittelpunkt_x: float = 0.0
    mittelpunkt_y: float = 0.0
    z_oberkante: float = Field(
        default=0.0,
        description="Z der Werkstueck-Oberkante (Z des Gewinde-Eintritts)",
    )


class ThreadMillingFehler(Exception):
    """Vorbedingung verletzt (Werkzeug zu gross fuers Gewinde, etc.)."""


def erzeuge_thread_milling_toolpath(
    werkzeug: Werkzeug,
    parameter: ThreadMillingParameter,
    *,
    operation_id: str = "thread_milling",
) -> Toolpath:
    """Generiert Toolpath fuer Innen- oder Aussengewinde.

    Args:
        werkzeug: muss durchmesser < nenn_durchmesser haben (bei Innengewinde).
        parameter: Gewinde-Spezifikation + Fraes-Strategie.

    Raises:
        ThreadMillingFehler: wenn das Werkzeug nicht ins Loch passt.
    """
    nenn = parameter.nenn_durchmesser - parameter.werkzeug_durchmesser_korrektur

    if parameter.art == GewindeArt.INNEN:
        if werkzeug.durchmesser >= nenn * 0.95:
            raise ThreadMillingFehler(
                f"Werkzeug-Durchmesser ({werkzeug.durchmesser} mm) zu gross fuer "
                f"Innengewinde mit Nenn-D {nenn} mm. Fraeser muss deutlich kleiner sein."
            )
        bahn_radius = (nenn - werkzeug.durchmesser) / 2.0
    else:  # AUSSEN
        bahn_radius = (nenn + werkzeug.durchmesser) / 2.0

    # Anzahl Helix-Umdrehungen aus Gewindetiefe + Steigung
    n_umdrehungen = parameter.gewinde_tiefe / parameter.gewinde_steigung
    if n_umdrehungen < 0.5:
        raise ThreadMillingFehler(
            f"Gewinde-Tiefe ({parameter.gewinde_tiefe} mm) kleiner als halbe "
            f"Steigung ({parameter.gewinde_steigung} mm) — kein vollstaendiger Gang moeglich."
        )

    bewegungen: list[Bewegung] = []
    mx, my = parameter.mittelpunkt_x, parameter.mittelpunkt_y
    z_safe = parameter.sicherheitshoehe + parameter.z_oberkante

    # 1. Eilgang zum Mittelpunkt in Sicherheitshoehe
    bewegungen.append(Bewegung(
        typ=BewegungsTyp.EILGANG, x=mx, y=my, z=z_safe,
        kommentar=f"Zum Gewinde-Mittelpunkt ({nenn} mm Nenn)",
    ))

    # 2. Eilgang an den Helix-Startpunkt (Winkel 0°)
    start_x = mx + bahn_radius
    start_y = my
    bewegungen.append(Bewegung(
        typ=BewegungsTyp.EILGANG, x=start_x, y=start_y, z=z_safe,
    ))

    # 3. Plunge auf Z_oberkante (Beginn des Gewindes)
    z_start = parameter.z_oberkante
    bewegungen.append(Bewegung(
        typ=BewegungsTyp.PLUNGE, x=start_x, y=start_y, z=z_start,
        feed=parameter.eintauch_vorschub,
        kommentar="Eintauch zum Gewinde-Start",
    ))

    # 4. Helix abfahren
    # Innengewinde + Rechtsgewinde: G3 (CCW von oben gesehen, geht hoch wenn Rechtsgewinde
    #                                   gefraest wird — aber wir gehen NACH UNTEN beim Fraesen)
    # Konvention: Wir fraesen IMMER NACH UNTEN (Z negativ progressiv)
    # → Rechtsgewinde innen: CCW von oben (G3) wenn man von oben drauf schaut
    # → Linksgewinde innen: CW von oben (G2)
    if parameter.art == GewindeArt.INNEN:
        gegen_uhrzeiger = (parameter.richtung == GewindeRichtung.RECHTS)
    else:  # AUSSEN — gegenlaeufig
        gegen_uhrzeiger = (parameter.richtung == GewindeRichtung.LINKS)

    n_segmente = int(math.ceil(n_umdrehungen * parameter.segmente_pro_umdrehung))
    drehrichtung = 1 if gegen_uhrzeiger else -1
    for i in range(1, n_segmente + 1):
        t = i / n_segmente
        winkel = drehrichtung * 2 * math.pi * n_umdrehungen * t
        x = mx + bahn_radius * math.cos(winkel)
        y = my + bahn_radius * math.sin(winkel)
        z = z_start - parameter.gewinde_tiefe * t  # progressiv tiefer
        bewegungen.append(Bewegung(
            typ=BewegungsTyp.LINEAR, x=x, y=y, z=z,
            feed=parameter.vorschub,
        ))

    # 5. Zurueck in Mittelpunkt (wichtig bei Innengewinde — sonst kratzt das
    #    Werkzeug beim Hochziehen am Gewinde)
    z_ende = z_start - parameter.gewinde_tiefe
    bewegungen.append(Bewegung(
        typ=BewegungsTyp.LINEAR, x=mx, y=my, z=z_ende,
        feed=parameter.vorschub,
        kommentar="Zurueck zur Mitte (vermeidet Gewindeschaden beim Lift)",
    ))

    # 6. Lift auf Sicherheitshoehe
    bewegungen.append(Bewegung(
        typ=BewegungsTyp.EILGANG, x=mx, y=my, z=z_safe,
        kommentar="Lift",
    ))

    return Toolpath(
        operation_id=operation_id,
        operation_typ=OperationsTyp.GRAVUR,  # Closest fit; Postprozessor erkennt Thread-Milling via Metadata
        werkzeug_id=werkzeug.id,
        spindel_rpm=parameter.spindel_rpm,
        sicherheitshoehe=parameter.sicherheitshoehe,
        bewegungen=bewegungen,
        kommentar=(
            f"Thread-Milling {parameter.art.value} {parameter.nenn_durchmesser}x"
            f"{parameter.gewinde_steigung} ({parameter.richtung.value})"
        ),
        metadaten={
            "thread_milling": True,
            "art": parameter.art.value,
            "richtung": parameter.richtung.value,
            "nenn_durchmesser_mm": parameter.nenn_durchmesser,
            "gewinde_steigung_mm": parameter.gewinde_steigung,
            "anzahl_umdrehungen": n_umdrehungen,
            "bahn_radius_mm": bahn_radius,
        },
    )


__all__ = [
    "GewindeArt",
    "GewindeRichtung",
    "ThreadMillingFehler",
    "ThreadMillingParameter",
    "erzeuge_thread_milling_toolpath",
]
