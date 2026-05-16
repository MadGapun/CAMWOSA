"""Sicherheits-Checks fuer Toolpaths.

Prueft einen Toolpath auf typische Crash-Ursachen, BEVOR der G-Code an die
Maschine geht. Stufen:
- KRITISCH (Blocker): G-Code-Export verhindert ohne Override
- WARNUNG: Hinweis aber kein Blocker
- INFO: Empfehlungen

Implementierte Checks (Phase 1):
1. Eilbewegung (G0) im Material  [KRITISCH]
2. Toolpath verlaesst Arbeitsraum  [KRITISCH]
3. Werkzeug-Schneidlaenge zu kurz  [WARNUNG]
4. Plunge ohne Rampe bei nicht-Bohrer  [INFO]
5. Spindel-RPM ausserhalb Bereich  [WARNUNG]
6. Fehlende Spindel-Drehzahl  [KRITISCH]
7. Plunge-Vorschub > Vorschub  [INFO]

Siehe Wiki: docs/wiki/Sicherheits-Checks.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from camwosa.db.models import Maschine, Spindel, Werkzeug
from camwosa.gcode.toolpath import BewegungsTyp, OperationsTyp, Toolpath


class CheckStufe(str, Enum):
    INFO = "info"
    WARNUNG = "warnung"
    KRITISCH = "kritisch"


@dataclass
class CheckErgebnis:
    check_id: str
    stufe: CheckStufe
    titel: str
    beschreibung: str
    bewegungs_index: int | None = None  # Verweis auf betroffene Bewegung


@dataclass
class CheckBericht:
    ergebnisse: list[CheckErgebnis] = field(default_factory=list)

    @property
    def hat_blocker(self) -> bool:
        return any(e.stufe == CheckStufe.KRITISCH for e in self.ergebnisse)

    @property
    def anzahl_kritisch(self) -> int:
        return sum(1 for e in self.ergebnisse if e.stufe == CheckStufe.KRITISCH)

    @property
    def anzahl_warnung(self) -> int:
        return sum(1 for e in self.ergebnisse if e.stufe == CheckStufe.WARNUNG)


def pruefe_toolpath(
    toolpath: Toolpath,
    maschine: Maschine,
    werkzeug: Werkzeug,
    *,
    z_oberkante_material: float = 0.0,
    spindel: Spindel | None = None,
    halter_kollision_pruefen: bool = False,
) -> CheckBericht:
    """Fuehrt alle Sicherheits-Checks fuer einen Toolpath aus.

    Args:
        spindel: Wenn angegeben, wird die RPM-Pruefung gegen die Spindel-Range
            durchgefuehrt. Sonst gegen die (Inline-)Maschinen-RPM-Range.
        halter_kollision_pruefen: Wenn True, wird zusaetzlich die
            Werkzeughalter-Kollisionsanalyse durchgefuehrt (Phase E3).
    """
    bericht = CheckBericht()

    _check_g0_im_material(toolpath, z_oberkante_material, bericht)
    _check_arbeitsraum(toolpath, maschine, bericht)
    _check_werkzeug_schneidlaenge(toolpath, werkzeug, bericht)
    _check_plunge_ohne_rampe(toolpath, werkzeug, bericht)
    _check_rpm_im_bereich(toolpath, maschine, bericht, spindel=spindel)
    _check_spindel_drehzahl(toolpath, bericht)
    _check_plunge_vorschub(toolpath, bericht)
    _check_spindel_kuehlung(toolpath, spindel, bericht)

    if halter_kollision_pruefen:
        from camwosa.safety.kollision import pruefe_halter_kollision
        bericht.ergebnisse.extend(
            pruefe_halter_kollision(
                toolpath, werkzeug, z_oberkante_material=z_oberkante_material,
            )
        )

    return bericht


def pruefe_alle(
    toolpaths: list[Toolpath],
    maschine: Maschine,
    werkzeug: Werkzeug,
    *,
    z_oberkante_material: float = 0.0,
    spindel: Spindel | None = None,
) -> CheckBericht:
    bericht = CheckBericht()
    for tp in toolpaths:
        teilbericht = pruefe_toolpath(
            tp, maschine, werkzeug,
            z_oberkante_material=z_oberkante_material,
            spindel=spindel,
        )
        bericht.ergebnisse.extend(teilbericht.ergebnisse)
    return bericht


# ---------------------------------------------------------------------------
# Einzelne Checks
# ---------------------------------------------------------------------------


def _check_g0_im_material(
    toolpath: Toolpath, z_oberkante: float, bericht: CheckBericht
) -> None:
    """Eilgang unterhalb der Werkstueck-Oberkante = klassische Crash-Ursache."""
    for i, b in enumerate(toolpath.bewegungen):
        if b.typ == BewegungsTyp.EILGANG and b.z < z_oberkante - 1e-6:
            bericht.ergebnisse.append(CheckErgebnis(
                check_id="g0_im_material",
                stufe=CheckStufe.KRITISCH,
                titel="Eilbewegung im Material",
                beschreibung=(
                    f"Eilgang (G0) zu Z={b.z:.2f} unterhalb Material-Oberkante "
                    f"(Z={z_oberkante:.2f}). Klassische Crash-Ursache."
                ),
                bewegungs_index=i,
            ))


def _check_arbeitsraum(
    toolpath: Toolpath, maschine: Maschine, bericht: CheckBericht
) -> None:
    ar = maschine.arbeitsraum
    for i, b in enumerate(toolpath.bewegungen):
        if not (0 <= b.x <= ar.x):
            bericht.ergebnisse.append(CheckErgebnis(
                check_id="arbeitsraum_x",
                stufe=CheckStufe.KRITISCH,
                titel="Toolpath verlaesst Arbeitsraum (X)",
                beschreibung=f"X={b.x:.2f} ausserhalb 0..{ar.x:.0f}",
                bewegungs_index=i,
            ))
            return  # ein Treffer reicht
        if not (0 <= b.y <= ar.y):
            bericht.ergebnisse.append(CheckErgebnis(
                check_id="arbeitsraum_y",
                stufe=CheckStufe.KRITISCH,
                titel="Toolpath verlaesst Arbeitsraum (Y)",
                beschreibung=f"Y={b.y:.2f} ausserhalb 0..{ar.y:.0f}",
                bewegungs_index=i,
            ))
            return
        if b.z < -ar.z:
            bericht.ergebnisse.append(CheckErgebnis(
                check_id="arbeitsraum_z",
                stufe=CheckStufe.KRITISCH,
                titel="Toolpath verlaesst Arbeitsraum (Z)",
                beschreibung=f"Z={b.z:.2f} unter {-ar.z:.0f}",
                bewegungs_index=i,
            ))
            return


def _check_werkzeug_schneidlaenge(
    toolpath: Toolpath, werkzeug: Werkzeug, bericht: CheckBericht
) -> None:
    if not toolpath.bewegungen:
        return
    min_z = min(b.z for b in toolpath.bewegungen)
    schnittiefe = abs(min_z)
    if schnittiefe > werkzeug.schneidlaenge:
        bericht.ergebnisse.append(CheckErgebnis(
            check_id="werkzeug_zu_kurz",
            stufe=CheckStufe.WARNUNG,
            titel="Werkzeug zu kurz fuer Schnitttiefe",
            beschreibung=(
                f"Schnitttiefe {schnittiefe:.1f}mm ueberschreitet Schneidlaenge "
                f"{werkzeug.schneidlaenge:.1f}mm. Halter taucht ggf. ins Material."
            ),
        ))


def _check_plunge_ohne_rampe(
    toolpath: Toolpath, werkzeug: Werkzeug, bericht: CheckBericht
) -> None:
    """Bei nicht-Bohrer-Werkzeugen sollte senkrechtes Plunge vermieden werden."""
    from camwosa.db.models import WerkzeugTyp
    if werkzeug.typ in (WerkzeugTyp.BOHRER, WerkzeugTyp.FISCHSCHWANZ, WerkzeugTyp.EINSCHNEIDER):
        return
    plunge_count = sum(1 for b in toolpath.bewegungen if b.typ == BewegungsTyp.PLUNGE)
    if plunge_count > 0 and toolpath.operation_typ != OperationsTyp.BOHREN:
        bericht.ergebnisse.append(CheckErgebnis(
            check_id="plunge_ohne_rampe",
            stufe=CheckStufe.INFO,
            titel="Senkrechtes Eintauchen bei nicht-stirnschneidendem Werkzeug",
            beschreibung=(
                f"{plunge_count} senkrechte Plunge-Bewegungen mit "
                f"{werkzeug.typ.value}. Empfehlung: Rampe oder Helix-Eintauchen."
            ),
        ))


def _check_rpm_im_bereich(
    toolpath: Toolpath,
    maschine: Maschine,
    bericht: CheckBericht,
    *,
    spindel: Spindel | None = None,
) -> None:
    """RPM-Range pruefen — bevorzugt gegen aktive Spindel, sonst Maschinen-Inline."""
    if spindel is not None:
        rpm_min, rpm_max = spindel.rpm_min, spindel.rpm_max
        quelle = f"Spindel '{spindel.name}'"
    else:
        rpm_min, rpm_max = maschine.spindel_rpm_min, maschine.spindel_rpm_max
        quelle = "Maschine"

    if toolpath.spindel_rpm < rpm_min:
        bericht.ergebnisse.append(CheckErgebnis(
            check_id="rpm_zu_niedrig",
            stufe=CheckStufe.WARNUNG,
            titel="Spindel-RPM unter Min",
            beschreibung=(
                f"RPM {toolpath.spindel_rpm:.0f} < {rpm_min:.0f} ({quelle}). "
                "Spindel laeuft ggf. nicht stabil."
            ),
        ))
    if toolpath.spindel_rpm > rpm_max:
        bericht.ergebnisse.append(CheckErgebnis(
            check_id="rpm_zu_hoch",
            stufe=CheckStufe.WARNUNG,
            titel="Spindel-RPM ueber Max",
            beschreibung=(
                f"RPM {toolpath.spindel_rpm:.0f} > {rpm_max:.0f} ({quelle})."
            ),
        ))


def _check_spindel_kuehlung(
    toolpath: Toolpath, spindel: Spindel | None, bericht: CheckBericht
) -> None:
    """Bei wassergekuehlten Spindeln: Hinweis dass Pumpe an sein muss."""
    if spindel is None:
        return
    if spindel.kuehlung == "wasser" and toolpath.spindel_rpm > 0:
        bericht.ergebnisse.append(CheckErgebnis(
            check_id="wasserkuehlung_hinweis",
            stufe=CheckStufe.INFO,
            titel="Wassergekuehlte Spindel",
            beschreibung=(
                f"Spindel '{spindel.name}' ist wassergekuehlt. "
                "Pumpe vor dem Start einschalten und Durchfluss pruefen."
            ),
        ))


def _check_spindel_drehzahl(toolpath: Toolpath, bericht: CheckBericht) -> None:
    if toolpath.spindel_rpm <= 0:
        bericht.ergebnisse.append(CheckErgebnis(
            check_id="rpm_fehlt",
            stufe=CheckStufe.KRITISCH,
            titel="Spindel-Drehzahl nicht gesetzt",
            beschreibung="Toolpath ohne Spindel-RPM. M3 ohne S-Wert ist Crash-gefaehrlich.",
        ))


def _check_plunge_vorschub(toolpath: Toolpath, bericht: CheckBericht) -> None:
    """Plunge sollte langsamer als Schnittvorschub sein."""
    plunges = [b for b in toolpath.bewegungen if b.typ == BewegungsTyp.PLUNGE and b.feed]
    schnitt = [b for b in toolpath.bewegungen if b.typ == BewegungsTyp.LINEAR and b.feed]
    if plunges and schnitt:
        max_plunge = max(b.feed for b in plunges)
        min_schnitt = min(b.feed for b in schnitt)
        if max_plunge > min_schnitt:
            bericht.ergebnisse.append(CheckErgebnis(
                check_id="plunge_zu_schnell",
                stufe=CheckStufe.INFO,
                titel="Plunge schneller als Schnittvorschub",
                beschreibung=(
                    f"Plunge {max_plunge:.0f} > Schnitt {min_schnitt:.0f} mm/min. "
                    "Ueblich ist Plunge ~ 20-40% des Schnittvorschubs."
                ),
            ))


__all__ = [
    "CheckBericht",
    "CheckErgebnis",
    "CheckStufe",
    "pruefe_alle",
    "pruefe_toolpath",
]
