"""Spannmittel-Modell pro Setup (A47 Cluster H).

Strukturiertes Spannmittel statt Freitext. Wichtig fuer:
- Sicherheitszonen (wo darf Toolpath nicht hin?)
- Visualisierung im 2D/3D-Preview
- Pre-Generation-Check (Crash mit Spannmittel?)

Typen:
- SCHRAUBSTOCK: parallele Backen (typisch fuer Metall)
- SCHRAUBZWINGEN: einzelne Zwingen (Holz, mehrere Positionen)
- VAKUUM_TISCH: Vakuum-Saugplatte (kein Bereich gesperrt, aber Mindest-Z)
- SPANNFUTTER: Rotary 3- oder 4-Backen-Futter
- REITSTOCK: Rotary-Gegenpunkt
- T_NUT: T-Nut-Spanner in Maschinen-Tisch
- DOUBLE_FACE_TAPE: doppelseitiges Klebeband (kein Sperrbereich)
- FRAES_FREUND: lasercut Spann-Geometrie

Wiki: docs/wiki/Spannmittel.md
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SpannmittelTyp(str, Enum):
    SCHRAUBSTOCK = "schraubstock"
    SCHRAUBZWINGE = "schraubzwinge"
    VAKUUM_TISCH = "vakuum_tisch"
    SPANNFUTTER = "spannfutter"  # Rotary
    REITSTOCK = "reitstock"  # Rotary
    T_NUT = "t_nut"
    DOPPELKLEBE = "doppelseitiges_klebeband"
    FRAES_FREUND = "fraes_freund"  # custom


class Spannmittel(BaseModel):
    """Ein Spannmittel an einer bestimmten Position auf dem Maschinen-Tisch.

    Position-Konvention: ``position_x/y/z`` ist die MITTE des Spannmittels.
    Sicherheits-Radius/Box definiert wo der Cutter NICHT hin darf.

    Beispiel - Schraubzwinge an X=50 Y=10:
    ```
    Spannmittel(
        typ=SpannmittelTyp.SCHRAUBZWINGE,
        position_x=50, position_y=10, position_z=0,
        sicherheits_radius_mm=15,  # Zwinge selbst 30 mm Backe
        hoehe_mm=80,  # ragt 80 mm ueber Tisch nach oben
    )
    ```
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    typ: SpannmittelTyp
    name: str = ""  # Optional: User-defined Name
    position_x: float = Field(description="Mittelpunkt X in mm")
    position_y: float = Field(description="Mittelpunkt Y in mm")
    position_z: float = Field(default=0.0, description="Z-Position der Auflage (= Tisch-OK + Spannmittel-Hoehe)")

    # Sicherheits-Geometrie
    sicherheits_radius_mm: float = Field(
        default=0.0, ge=0,
        description="Radius (kreisfoermig) wo der Cutter nicht hin darf. "
                    "0 = kein Sperrbereich (z.B. Vakuum, Tape).",
    )
    sicherheits_box_x_mm: float | None = Field(
        default=None, gt=0,
        description="Alternative zu Radius: Box-Breite. Wenn gesetzt, "
                    "wird radius ignoriert.",
    )
    sicherheits_box_y_mm: float | None = Field(default=None, gt=0)

    # Spannmittel-Hoehe ueber Tisch-Oberkante
    hoehe_mm: float = Field(
        default=0.0, ge=0,
        description="Wie hoch ragt das Spannmittel ueber den Tisch? "
                    "Cutter darf in diesem Bereich nicht auf Z=0 fahren.",
    )

    notizen: str = ""


def punkt_in_sperrzone(
    spannmittel: Spannmittel, x: float, y: float, z: float | None = None,
    cutter_radius: float = 0.0,
) -> bool:
    """Prueft ob ein Punkt in der Sperrzone eines Spannmittels liegt.

    Mit cutter_radius wird zusaetzlich der Werkzeug-Radius beruecksichtigt
    (Cutter darf auch nicht in die Sperrzone hineinragen).

    Wenn z angegeben + Spannmittel-Hoehe > 0: Sperre nur wenn Cutter
    unterhalb der Spannmittel-Oberkante.
    """
    # Z-Check: wenn z ueber Spannmittel-Hoehe, kein Problem
    if z is not None and spannmittel.hoehe_mm > 0:
        if z > spannmittel.position_z + spannmittel.hoehe_mm:
            return False

    dx = x - spannmittel.position_x
    dy = y - spannmittel.position_y

    if spannmittel.sicherheits_box_x_mm and spannmittel.sicherheits_box_y_mm:
        # Box-Check
        halb_x = spannmittel.sicherheits_box_x_mm / 2 + cutter_radius
        halb_y = spannmittel.sicherheits_box_y_mm / 2 + cutter_radius
        return abs(dx) <= halb_x and abs(dy) <= halb_y

    # Radius-Check
    if spannmittel.sicherheits_radius_mm <= 0:
        return False
    import math
    dist = math.hypot(dx, dy)
    return dist <= spannmittel.sicherheits_radius_mm + cutter_radius


def pruefe_toolpath_gegen_spannmittel(
    bewegungen: list,  # list of Bewegung
    spannmittel_liste: list[Spannmittel],
    cutter_radius: float,
) -> list[tuple[int, str]]:
    """Prueft eine Liste von Bewegungen gegen alle Spannmittel.

    Returns:
        Liste von ``(bewegungs_index, fehler_text)`` fuer alle Bewegungen
        die in Sperrzonen fallen. Leer wenn alles OK.
    """
    fehler: list[tuple[int, str]] = []
    for i, b in enumerate(bewegungen):
        for sp in spannmittel_liste:
            if punkt_in_sperrzone(sp, b.x, b.y, getattr(b, "z", None), cutter_radius):
                fehler.append((
                    i,
                    f"Bewegung {i} (X={b.x:.1f} Y={b.y:.1f}) in Sperrzone "
                    f"von '{sp.id}' ({sp.typ.value})",
                ))
    return fehler


__all__ = [
    "Spannmittel",
    "SpannmittelTyp",
    "punkt_in_sperrzone",
    "pruefe_toolpath_gegen_spannmittel",
]
