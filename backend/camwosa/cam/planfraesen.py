"""Planfraesen / Face-Milling (Cluster I1, Issue #45).

Aus der Fusion-360-CAM-Analyse — `face`-Strategie. Ebnet eine rechteckige
Flaeche (Spoilboard-Surfacing, Stock-Top planen).

**Synergie mit Z-Grid-Diagnose (alpha.5):** Wenn die Diagnose
„unebene_oberflaeche → Werkstueck planen" meldet, ist genau diese Op die
Antwort. `aus_z_grid_befund()` erzeugt sinnvolle Default-Parameter.

Fusion-Kern-Parameter (aus Live-API): stepover, passAngle, maximumStepdown,
stockOffset, bothSides, passExtension.

Bewegungsmuster: parallele Zickzack-Bahnen ueber das Rechteck, optional in
mehreren Z-Pässen (maximumStepdown), mit Ueberstand (passExtension) damit das
Werkzeug sauber ein-/austritt.
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


class PlanfraesRichtung(str, Enum):
    X = "x"   # Bahnen entlang X
    Y = "y"   # Bahnen entlang Y


class PlanfraesParameter(BaseModel):
    """Parameter fuer Planfraesen."""

    model_config = ConfigDict(extra="ignore")

    werkzeug_id: str
    spindel_rpm: float = Field(gt=0)
    vorschub: float = Field(gt=0, description="mm/min")
    eintauch_vorschub: float = Field(gt=0, description="mm/min")
    sicherheitshoehe: float = Field(default=5.0, gt=0)

    # Flaeche (Rechteck in XY)
    x_min: float = 0.0
    y_min: float = 0.0
    x_max: float = Field(gt=0)
    y_max: float = Field(gt=0)

    # Tiefen
    z_start: float = Field(default=0.0, description="Z der Materialoberkante")
    abtrag: float = Field(gt=0, description="Wieviel runtergefraest wird (mm)")
    maximaler_stepdown: float = Field(default=1.0, gt=0, description="max. Z-Zustellung pro Pass")

    # Bahnen
    richtung: PlanfraesRichtung = PlanfraesRichtung.X
    stepover_prozent: float = Field(
        default=70.0, gt=0, le=95, description="% vom Werkzeug-Durchmesser",
    )
    ueberstand_mm: float = Field(
        default=2.0, ge=0, description="Wieviel das Werkzeug ueber die Kante faehrt",
    )


class PlanfraesFehler(Exception):
    pass


def erzeuge_planfraes_toolpath(
    werkzeug: Werkzeug,
    parameter: PlanfraesParameter,
    *,
    operation_id: str = "planfraesen",
) -> Toolpath:
    """Generiert Zickzack-Planfraes-Bahnen in N Z-Pässen."""
    if parameter.x_max <= parameter.x_min or parameter.y_max <= parameter.y_min:
        raise PlanfraesFehler("Ungueltiges Rechteck (max <= min).")

    durchmesser = werkzeug.durchmesser
    if durchmesser <= 0:
        raise PlanfraesFehler("Werkzeug-Durchmesser muss > 0 sein.")
    stepover = durchmesser * (parameter.stepover_prozent / 100.0)

    z_safe = parameter.z_start + parameter.sicherheitshoehe
    bewegungen: list[Bewegung] = []

    # Anzahl Z-Pässe
    n_zpaesse = max(1, int(math.ceil(parameter.abtrag / parameter.maximaler_stepdown)))

    ue = parameter.ueberstand_mm
    erste = True
    for zp in range(1, n_zpaesse + 1):
        z = parameter.z_start - min(parameter.abtrag, zp * parameter.maximaler_stepdown)

        if parameter.richtung == PlanfraesRichtung.X:
            # Bahnen entlang X, Versatz in Y
            quer_min, quer_max = parameter.y_min, parameter.y_max
            n_bahnen = max(1, int(math.ceil((quer_max - quer_min) / stepover)) + 1)
            for b in range(n_bahnen):
                y = quer_min + min(b * stepover, quer_max - quer_min)
                # Hin oder zurueck (Zickzack)
                if b % 2 == 0:
                    x_a, x_b = parameter.x_min - ue, parameter.x_max + ue
                else:
                    x_a, x_b = parameter.x_max + ue, parameter.x_min - ue
                _bahn(bewegungen, x_a, y, x_b, y, z, z_safe, parameter, erste)
                erste = False
        else:
            quer_min, quer_max = parameter.x_min, parameter.x_max
            n_bahnen = max(1, int(math.ceil((quer_max - quer_min) / stepover)) + 1)
            for b in range(n_bahnen):
                x = quer_min + min(b * stepover, quer_max - quer_min)
                if b % 2 == 0:
                    y_a, y_b = parameter.y_min - ue, parameter.y_max + ue
                else:
                    y_a, y_b = parameter.y_max + ue, parameter.y_min - ue
                _bahn(bewegungen, x, y_a, x, y_b, z, z_safe, parameter, erste)
                erste = False

    if bewegungen:
        last = bewegungen[-1]
        bewegungen.append(Bewegung(
            typ=BewegungsTyp.EILGANG, x=last.x, y=last.y, z=z_safe,
            kommentar="Rueckzug",
        ))

    return Toolpath(
        operation_id=operation_id,
        operation_typ=OperationsTyp.TASCHE,
        werkzeug_id=werkzeug.id,
        spindel_rpm=parameter.spindel_rpm,
        sicherheitshoehe=parameter.sicherheitshoehe,
        bewegungen=bewegungen,
        kommentar=f"Planfraesen ({n_zpaesse} Z-Pässe, Richtung {parameter.richtung.value})",
        metadaten={
            "strategie": "planfraesen",
            "abtrag_mm": parameter.abtrag,
            "z_paesse": n_zpaesse,
            "stepover_mm": stepover,
        },
    )


def _bahn(
    bewegungen: list[Bewegung],
    x_a: float, y_a: float, x_b: float, y_b: float,
    z: float, z_safe: float, parameter: PlanfraesParameter, erste: bool,
) -> None:
    """Eine Zickzack-Bahn. Bei der ersten Bahn eines Z-Passes: Plunge."""
    if erste or not bewegungen:
        bewegungen.append(Bewegung(typ=BewegungsTyp.EILGANG, x=x_a, y=y_a, z=z_safe))
        bewegungen.append(Bewegung(
            typ=BewegungsTyp.PLUNGE, x=x_a, y=y_a, z=z,
            feed=parameter.eintauch_vorschub,
        ))
    else:
        # Werkzeug bleibt unten, faehrt zur naechsten Bahn
        bewegungen.append(Bewegung(
            typ=BewegungsTyp.LINEAR, x=x_a, y=y_a, z=z, feed=parameter.vorschub,
        ))
    bewegungen.append(Bewegung(
        typ=BewegungsTyp.LINEAR, x=x_b, y=y_b, z=z, feed=parameter.vorschub,
    ))


def aus_z_grid_befund(
    werkzeug_id: str,
    x_min: float, y_min: float, x_max: float, y_max: float,
    *,
    z_spreizung_mm: float,
    spindel_rpm: float = 18000,
    vorschub: float = 2000,
) -> PlanfraesParameter:
    """Erzeugt Planfraes-Parameter aus einem Z-Grid-Diagnose-Befund.

    Die Z-Spreizung (max-min der Probing-Punkte) bestimmt den Abtrag:
    etwas mehr als die Spreizung, damit auch der hoechste Punkt sauber
    abgetragen wird.
    """
    abtrag = max(0.2, z_spreizung_mm + 0.2)
    return PlanfraesParameter(
        werkzeug_id=werkzeug_id,
        spindel_rpm=spindel_rpm,
        vorschub=vorschub,
        eintauch_vorschub=vorschub / 3.0,
        x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max,
        z_start=0.0,
        abtrag=abtrag,
        maximaler_stepdown=min(0.5, abtrag),
    )


__all__ = [
    "PlanfraesFehler",
    "PlanfraesParameter",
    "PlanfraesRichtung",
    "aus_z_grid_befund",
    "erzeuge_planfraes_toolpath",
]
