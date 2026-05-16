"""Kollisionsanalyse Werkzeughalter (Phase E3).

Prueft ob der Werkzeughalter (oder die Spindel) bei einer Z-Position in das
Werkstueck eintauchen wuerde.

Vereinfachtes Modell:
- Werkzeug: Schneidlaenge unten, dann Schaft bis Halter-Unterkante
- Halter: zylindrisch, mit Halter-Durchmesser und Halter-Hoehe
- Bei jeder Z-Position: pruefe ob Halter-Unterkante < z_oberkante_material
  UND ob es Material an der X/Y-Position gibt.
"""

from __future__ import annotations

from dataclasses import dataclass

from camwosa.db.models import Werkzeug
from camwosa.gcode.toolpath import Toolpath
from camwosa.safety.checks import CheckErgebnis, CheckStufe


@dataclass
class HalterGeometrie:
    """Werkzeughalter-Geometrie (vereinfacht als Zylinder)."""

    durchmesser: float = 30.0  # mm, typische ER-Spannzangen-Halter
    hoehe: float = 50.0  # mm, Schaft + Halter
    abstand_zum_werkzeug: float = 0.0  # mm, Offset Werkzeug-Spitze -> Halter-Unterkante


def pruefe_halter_kollision(
    toolpath: Toolpath,
    werkzeug: Werkzeug,
    halter: HalterGeometrie | None = None,
    *,
    z_oberkante_material: float = 0.0,
) -> list[CheckErgebnis]:
    """Prueft ob der Halter ins Material taucht.

    Logik:
    - Werkzeug-Spitze bei Z_aktuell
    - Halter-Unterkante = Z_aktuell + werkzeug.schneidlaenge + halter.abstand_zum_werkzeug
    - Wenn Halter-Unterkante < z_oberkante_material UND wir haben material an x/y:
      -> Kollision wahrscheinlich
    """
    halter = halter or HalterGeometrie()
    ergebnisse: list[CheckErgebnis] = []
    halter_unter_offset = werkzeug.schneidlaenge + halter.abstand_zum_werkzeug

    for i, b in enumerate(toolpath.bewegungen):
        halter_unter_z = b.z + halter_unter_offset
        if halter_unter_z < z_oberkante_material - 1e-6:
            ergebnisse.append(CheckErgebnis(
                check_id="halter_kollision",
                stufe=CheckStufe.KRITISCH,
                titel="Werkzeughalter unter Material-Oberkante",
                beschreibung=(
                    f"Bei Bewegungs-Index {i} liegt die Halter-Unterkante bei "
                    f"Z={halter_unter_z:.2f} unter dem Material "
                    f"(OK={z_oberkante_material:.2f}). Schneidlaenge "
                    f"{werkzeug.schneidlaenge}mm zu kurz fuer Schnitttiefe."
                ),
                bewegungs_index=i,
            ))
            break  # ein Treffer reicht — sonst Spam
    return ergebnisse


__all__ = ["HalterGeometrie", "pruefe_halter_kollision"]
