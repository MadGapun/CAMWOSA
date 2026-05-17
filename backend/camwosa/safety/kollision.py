"""Kollisionsanalyse Werkzeughalter + Schaft (Phase E3, v2 mit Segmenten).

Prueft mehrere Sachen pro Bewegung:
1. Schaft taucht ins Material — passiert wenn Schnitttiefe > Schneidlaenge.
   Bei konischen Werkzeugen (Gravurstichel mit 0.3mm Spitze + 3.175mm Schaft):
   nicht nur "Halter-Unterkante < Material-OK" sondern jeder nicht-schneidende
   Bereich darf nicht eintauchen.
2. max_arbeitstiefe_mm pro Werkzeug — User-definiertes Limit pro Tool.
3. Konische Werkzeuge — Warnung dass die effektive Spur breiter wird als die
   Spitze suggeriert.
"""

from __future__ import annotations

from dataclasses import dataclass

from camwosa.db.models import Werkzeug
from camwosa.gcode.toolpath import Toolpath
from camwosa.safety.checks import CheckErgebnis, CheckStufe


@dataclass
class HalterGeometrie:
    """Werkzeughalter-Geometrie (Backwards-Kompat).

    Neuere Pruefung nutzt Werkzeug.halter_segmente und
    Werkzeug.effektive_segmente() — dieses hier ist Fallback.
    """

    durchmesser: float = 30.0
    hoehe: float = 50.0
    abstand_zum_werkzeug: float = 0.0


def pruefe_halter_kollision(
    toolpath: Toolpath,
    werkzeug: Werkzeug,
    halter: HalterGeometrie | None = None,
    *,
    z_oberkante_material: float = 0.0,
) -> list[CheckErgebnis]:
    """Segment-basierte Kollisionsanalyse.

    Liefert eine Liste von CheckErgebnis-Eintraegen. Mehrere Issue-Typen
    werden je einmal gemeldet (kein Spam).
    """
    ergebnisse: list[CheckErgebnis] = []
    if not toolpath.bewegungen:
        return ergebnisse

    schneid_segmente = [s for s in werkzeug.effektive_segmente() if s.ist_schneide]
    schneiden_max_z = max(
        (s.z_oben for s in schneid_segmente),
        default=werkzeug.schneidlaenge,
    )

    treffer_typen: set[str] = set()

    for i, b in enumerate(toolpath.bewegungen):
        if b.z >= z_oberkante_material - 1e-6:
            continue  # Werkzeug ueber Material — kein Eintauchen
        tiefe = z_oberkante_material - b.z

        # Check 1: max_arbeitstiefe_mm pro Werkzeug
        if not werkzeug.darf_in_tiefe(tiefe) and "max_tiefe" not in treffer_typen:
            ergebnisse.append(CheckErgebnis(
                check_id="werkzeug_max_tiefe",
                stufe=CheckStufe.KRITISCH,
                titel="Werkzeug-Max-Tiefe ueberschritten",
                beschreibung=(
                    f"Bei Bewegungs-Index {i}: Schnitttiefe {tiefe:.2f}mm > "
                    f"max_arbeitstiefe {werkzeug.max_arbeitstiefe_mm}mm "
                    f"vom Werkzeug '{werkzeug.name}'."
                ),
                bewegungs_index=i,
            ))
            treffer_typen.add("max_tiefe")

        # Check 2: Schaft taucht ins Material
        if tiefe > schneiden_max_z and "schaft_im_material" not in treffer_typen:
            ergebnisse.append(CheckErgebnis(
                check_id="schaft_im_material",
                stufe=CheckStufe.KRITISCH,
                titel="Schaft taucht ins Material",
                beschreibung=(
                    f"Bei Bewegungs-Index {i}: Eintauchtiefe {tiefe:.2f}mm > "
                    f"Schneidlaenge {schneiden_max_z:.1f}mm. "
                    f"Der nicht-schneidende Schaft drueckt sich ins Material — Werkzeug bricht."
                ),
                bewegungs_index=i,
            ))
            treffer_typen.add("schaft_im_material")

        # Check 3: Konisches Werkzeug warnen wenn Spur viel breiter wird
        spitzen_d = werkzeug.spitzendurchmesser
        if spitzen_d is not None and spitzen_d > 0 and "konus_warnung" not in treffer_typen:
            d_an_oberkante = werkzeug.durchmesser_bei_z(tiefe)
            if d_an_oberkante > spitzen_d * 5 and tiefe > schneiden_max_z * 0.7:
                ergebnisse.append(CheckErgebnis(
                    check_id="konus_zu_breit",
                    stufe=CheckStufe.WARNUNG,
                    titel="Konisches Werkzeug — Spur breiter als Spitze",
                    beschreibung=(
                        f"Bei Tiefe {tiefe:.2f}mm hat das Werkzeug "
                        f"{d_an_oberkante:.2f}mm Durchmesser (Spitze nur {spitzen_d}mm). "
                        f"Die Spur wird deutlich breiter als die Spitze suggeriert."
                    ),
                    bewegungs_index=i,
                ))
                treffer_typen.add("konus_warnung")

        if len(treffer_typen) >= 3:
            break  # alle Issues gemeldet
    return ergebnisse


__all__ = ["HalterGeometrie", "pruefe_halter_kollision"]
