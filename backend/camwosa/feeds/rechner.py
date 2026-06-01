"""Feeds & Speeds Rechner.

Berechnet aus Material + Werkzeug + Maschine + Operation die optimalen Schnittparameter.

Grundformeln:
    Vc = pi * D * n / 1000           (Schnittgeschwindigkeit in m/min)
    Vf = fz * z * n                  (Vorschub in mm/min)
    Q  = ap * ae * Vf / 1000         (Spanvolumen in cm3/min)

Heuristik:
- Wenn fuer Werkzeug-Material-Kombination ein Preset existiert -> uebernehmen.
- Sonst aus Vc-Bereich des Materials Vorschub schaetzen.
- Warnungen bei: Maschine-Vorschub-Limit, Werkzeug zu klein, Material-WZ-Inkompat.

Siehe Wiki: docs/wiki/Feeds-Speeds.md
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

from camwosa.db.models import Maschine, Material, Spindel, Werkzeug, WerkzeugTyp


class WarnungsStufe(str, Enum):
    INFO = "info"
    WARNUNG = "warnung"
    KRITISCH = "kritisch"


@dataclass
class FeedsSpeedsWarnung:
    stufe: WarnungsStufe
    text: str


@dataclass
class FeedsSpeedsErgebnis:
    rpm: float
    vorschub: float          # mm/min
    eintauch_vorschub: float # mm/min
    stepdown: float          # mm
    stepover_prozent: float  # %
    schnittgeschwindigkeit_vc: float  # m/min
    spanvolumen_q: float      # cm3/min
    quelle: str               # "preset" | "berechnet"
    warnungen: list[FeedsSpeedsWarnung] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Default-Zahnvorschuebe als Heuristik wenn kein Preset existiert
# ---------------------------------------------------------------------------


_FZ_HEURISTIK: dict[tuple[str, WerkzeugTyp], dict[float, float]] = {
    # Material-Kategorie + Werkzeug-Typ -> {Werkzeug-Durchmesser: fz in mm/Zahn}
    ("holz", WerkzeugTyp.SCHAFTFRAESER): {3: 0.04, 6: 0.06, 8: 0.08},
    ("holz", WerkzeugTyp.KUGELFRAESER): {3: 0.03, 6: 0.05},
    ("holzwerkstoff", WerkzeugTyp.SCHAFTFRAESER): {3: 0.05, 6: 0.07, 8: 0.09},
    ("kunststoff", WerkzeugTyp.SCHAFTFRAESER): {3: 0.05, 6: 0.07, 8: 0.08},
    ("kunststoff", WerkzeugTyp.EINSCHNEIDER): {3: 0.10, 6: 0.12},
    ("ne_metall", WerkzeugTyp.SCHAFTFRAESER): {3: 0.025, 6: 0.04, 8: 0.05},
    ("ne_metall", WerkzeugTyp.EINSCHNEIDER): {3: 0.04, 6: 0.06},
}


def _waehle_fz(material: Material, werkzeug: Werkzeug) -> float | None:
    """Findet einen Heuristik-fz fuer Material-Werkzeug-Kombi."""
    key = (material.kategorie.value, werkzeug.typ)
    table = _FZ_HEURISTIK.get(key)
    if not table:
        return None
    # Naechstgelegener Durchmesser
    durchmesser = sorted(table.keys(), key=lambda d: abs(d - werkzeug.durchmesser))[0]
    return table[durchmesser]


# ---------------------------------------------------------------------------
# Hauptfunktion
# ---------------------------------------------------------------------------


def berechne_feeds_speeds(
    maschine: Maschine,
    werkzeug: Werkzeug,
    material: Material,
    *,
    rpm_wunsch: float | None = None,
    spindel: Spindel | None = None,
) -> FeedsSpeedsErgebnis:
    """Berechnet Feeds & Speeds fuer eine Werkzeug/Material/Maschine-Kombination.

    Args:
        rpm_wunsch: Gewuenschte Spindel-RPM. Wenn None -> aus Material/Werkzeug-Default.
        spindel: Aktive Spindel — bestimmt RPM-Range. Wenn None: Maschinen-Inline-RPM.

    Returns:
        FeedsSpeedsErgebnis mit Werten + Warnungen.
    """
    warnungen: list[FeedsSpeedsWarnung] = []
    # RPM-Range entweder aus Spindel oder aus Maschinen-Inline
    if spindel:
        rpm_min, rpm_max = spindel.rpm_min, spindel.rpm_max
        rpm_quelle = f"Spindel '{spindel.name}'"
    else:
        rpm_min, rpm_max = maschine.spindel_rpm_min, maschine.spindel_rpm_max
        rpm_quelle = "Maschine"

    # 1. Preset suchen
    preset = next((p for p in material.presets if p.werkzeug_id == werkzeug.id), None)
    if preset is not None:
        rpm = rpm_wunsch or preset.rpm
        vorschub = preset.vorschub
        plunge = preset.plunge
        stepdown = preset.stepdown
        stepover = preset.stepover_prozent
        quelle = "preset"
    else:
        # 2. Heuristik
        rpm = rpm_wunsch or _default_rpm(maschine, material)
        fz = _waehle_fz(material, werkzeug)
        if fz is None:
            warnungen.append(FeedsSpeedsWarnung(
                WarnungsStufe.WARNUNG,
                f"Keine Heuristik fuer {material.kategorie.value} + {werkzeug.typ.value}. "
                "Bitte Werte manuell setzen."
            ))
            fz = 0.05
        vorschub = fz * werkzeug.schneiden * rpm
        plunge = vorschub * 0.2
        stepdown = werkzeug.durchmesser * 0.3
        stepover = 40.0
        quelle = "berechnet"

    # 3. RPM-Limits durchsetzen (Spindel-Range)
    if rpm < rpm_min:
        warnungen.append(FeedsSpeedsWarnung(
            WarnungsStufe.WARNUNG,
            f"RPM {rpm:.0f} unter Min von {rpm_quelle} ({rpm_min:.0f}). "
            "Auf Min angehoben."
        ))
        rpm = rpm_min
    if rpm > rpm_max:
        warnungen.append(FeedsSpeedsWarnung(
            WarnungsStufe.WARNUNG,
            f"RPM {rpm:.0f} ueber Max von {rpm_quelle} ({rpm_max:.0f}). "
            "Auf Max begrenzt."
        ))
        rpm = rpm_max

    if vorschub > maschine.max_vorschub:
        warnungen.append(FeedsSpeedsWarnung(
            WarnungsStufe.WARNUNG,
            f"Vorschub {vorschub:.0f} ueber Maschinen-Max ({maschine.max_vorschub:.0f}). "
            "Auf Max begrenzt."
        ))
        vorschub = maschine.max_vorschub

    if vorschub > maschine.sicherer_vorschub:
        warnungen.append(FeedsSpeedsWarnung(
            WarnungsStufe.INFO,
            f"Vorschub {vorschub:.0f} ueber empfohlenem sicheren Wert "
            f"({maschine.sicherer_vorschub:.0f})."
        ))

    # 4. Berechnete Hilfsgroessen
    vc = math.pi * werkzeug.durchmesser * rpm / 1000.0
    ae = werkzeug.durchmesser * stepover / 100.0
    q = stepdown * ae * vorschub / 1000.0

    # 5. Material-Range-Pruefung
    if material.schnittgeschwindigkeit_min and vc < material.schnittgeschwindigkeit_min:
        warnungen.append(FeedsSpeedsWarnung(
            WarnungsStufe.INFO,
            f"Schnittgeschwindigkeit {vc:.0f} m/min unter Material-Empfehlung "
            f"({material.schnittgeschwindigkeit_min:.0f}-"
            f"{material.schnittgeschwindigkeit_max:.0f}). Werkzeug rubbelt evtl."
        ))
    if material.schnittgeschwindigkeit_max and vc > material.schnittgeschwindigkeit_max:
        warnungen.append(FeedsSpeedsWarnung(
            WarnungsStufe.WARNUNG,
            f"Schnittgeschwindigkeit {vc:.0f} m/min ueber Material-Empfehlung. "
            f"Werkzeug ueberhitzt evtl."
        ))

    # 6. Werkzeug-zu-klein
    if werkzeug.durchmesser < 1.5 and vorschub > 1500:
        warnungen.append(FeedsSpeedsWarnung(
            WarnungsStufe.KRITISCH,
            f"Werkzeug D={werkzeug.durchmesser}mm bei Vorschub {vorschub:.0f}mm/min: "
            "Bruchgefahr."
        ))

    return FeedsSpeedsErgebnis(
        rpm=rpm,
        vorschub=vorschub,
        eintauch_vorschub=plunge,
        stepdown=stepdown,
        stepover_prozent=stepover,
        schnittgeschwindigkeit_vc=vc,
        spanvolumen_q=q,
        quelle=quelle,
        warnungen=warnungen,
    )


def _default_rpm(maschine: Maschine, material: Material) -> float:
    # Mittelwert der Maschinen-RPM-Range, an Material angepasst
    mid = (maschine.spindel_rpm_min + maschine.spindel_rpm_max) / 2
    if material.kategorie.value == "ne_metall":
        return min(mid * 0.7, maschine.spindel_rpm_max)
    if material.kategorie.value == "kunststoff":
        return min(mid * 0.85, maschine.spindel_rpm_max)
    return mid


# ---------------------------------------------------------------------------
# Spanausduennung / Radial Chip Thinning (Cluster J3, Issue #46)
# ---------------------------------------------------------------------------


def chip_thinning_faktor(stepover_mm: float, werkzeug_durchmesser_mm: float) -> float:
    """Radialer Spanausduennungs-Faktor (RCTF).

    Bei radialem Eingriff ae < d/2 (kleiner Stepover, z.B. Adaptiv/Schlichten)
    ist die mittlere Spandicke kleiner als der Zahnvorschub fz vermuten laesst —
    das Werkzeug "rutscht" mehr als es schneidet. Um die Soll-Spandicke (und
    damit Werkzeug-Standzeit + Oberflaeche) zu halten, muss der Vorschub um
    diesen Faktor erhoeht werden.

    Formel: RCTF = 1 / sqrt(1 - (1 - 2·ae/d)²)   fuer ae < d/2
            RCTF = 1                              fuer ae >= d/2 (Voll-Eingriff)

    Args:
        stepover_mm: radialer Eingriff ae (mm).
        werkzeug_durchmesser_mm: Werkzeug-Durchmesser d (mm).

    Returns:
        Faktor >= 1.0. Geklemmt auf max. 4.0 (sehr kleiner Eingriff → sonst
        explodiert der Vorschub unrealistisch).
    """
    d = werkzeug_durchmesser_mm
    ae = stepover_mm
    if d <= 0:
        return 1.0
    ae = max(0.0, min(ae, d))  # ae in [0, d]
    if ae >= d / 2.0:
        return 1.0
    rest = 1.0 - (1.0 - 2.0 * ae / d) ** 2
    if rest <= 1e-9:
        return 4.0  # ae→0: theoretisch unendlich → praktisch klemmen
    faktor = 1.0 / math.sqrt(rest)
    return min(faktor, 4.0)


def korrigiere_vorschub_spanausduennung(
    vorschub_mm_min: float, stepover_mm: float, werkzeug_durchmesser_mm: float,
) -> float:
    """Wendet den Spanausduennungs-Faktor auf einen Basis-Vorschub an."""
    return vorschub_mm_min * chip_thinning_faktor(stepover_mm, werkzeug_durchmesser_mm)


# ---------------------------------------------------------------------------
# Axiale Vorschub-Anpassung bei Teil-Tiefe (Cluster J11, Issue #52)
# ---------------------------------------------------------------------------


def vorschub_fuer_zustellung(
    vorschub_mm_min: float,
    ap_aktuell_mm: float,
    stepdown_nominal_mm: float,
    *,
    faktor_max: float = 2.0,
) -> float:
    """Passt den Vorschub an die tatsaechliche axiale Zustellung eines Passes an.

    Der konfigurierte Vorschub gilt fuer die **volle** Zustellung
    (``stepdown_nominal``). Ein Pass mit geringerer Tiefe (z.B. der letzte
    Teil-Pass oder eine prozentuale Tiefe) hat weniger Werkzeug-Eingriff
    (kuerzere eingreifende Schneidenlaenge → kleinere Schnittkraft) und vertraegt
    daher einen hoeheren Vorschub.

    Modell: Vorschub ~ stepdown/ap (konstante Schnittkraft), gedeckelt auf
    ``faktor_max`` (Default 2x — konservativ; sonst wuerde ein hauchduenner Pass
    den Vorschub explodieren lassen).

    Args:
        vorschub_mm_min: Nominal-Vorschub (fuer volle Zustellung).
        ap_aktuell_mm: tatsaechliche axiale Tiefe dieses Passes.
        stepdown_nominal_mm: nominale Zustellung pro Pass.
        faktor_max: Obergrenze des Anpassungsfaktors.

    Returns:
        Angepasster Vorschub (>= Nominal-Vorschub).
    """
    if ap_aktuell_mm <= 1e-9 or stepdown_nominal_mm <= 1e-9:
        return vorschub_mm_min
    if ap_aktuell_mm >= stepdown_nominal_mm:
        return vorschub_mm_min  # voller Eingriff → kein Bonus
    faktor = min(stepdown_nominal_mm / ap_aktuell_mm, faktor_max)
    return vorschub_mm_min * faktor


__all__ = [
    "FeedsSpeedsErgebnis",
    "FeedsSpeedsWarnung",
    "WarnungsStufe",
    "berechne_feeds_speeds",
    "chip_thinning_faktor",
    "korrigiere_vorschub_spanausduennung",
    "vorschub_fuer_zustellung",
]
