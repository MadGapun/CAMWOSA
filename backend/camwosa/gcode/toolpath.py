"""Toolpath-Datenmodell.

Ein Toolpath ist die postprozessor-unabhaengige Repraesentation einer
CAM-Operation. Operations erzeugen Toolpaths, der Postprozessor wandelt
sie in maschinenspezifischen G-Code.

Siehe Wiki: docs/wiki/Postprozessor-GRBL.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class BewegungsTyp(str, Enum):
    """Art einer einzelnen Toolpath-Bewegung."""

    EILGANG = "eilgang"  # G0 - kein Materialabtrag
    LINEAR = "linear"  # G1 - Schnittbewegung
    BOGEN_CW = "bogen_cw"  # G2
    BOGEN_CCW = "bogen_ccw"  # G3
    PLUNGE = "plunge"  # senkrechte Z-Bewegung in Material


class OperationsTyp(str, Enum):
    KONTUR = "kontur"
    TASCHE = "tasche"
    BOHREN = "bohren"
    GRAVUR = "gravur"
    RELIEF = "relief"
    EILGANG = "eilgang"


@dataclass
class Bewegung:
    """Eine einzelne Bewegung im Toolpath.

    Bei Bogen-Bewegungen (BOGEN_CW/BOGEN_CCW) sind I, J relativ zum Startpunkt
    (GRBL-Konvention).
    """

    typ: BewegungsTyp
    x: float
    y: float
    z: float
    feed: float | None = None  # mm/min, None = aus Kontext
    i: float | None = None  # nur fuer Boegen
    j: float | None = None  # nur fuer Boegen
    kommentar: str = ""


@dataclass
class Toolpath:
    """Komplette Bewegungsfolge fuer eine Operation.

    Enthaelt sowohl Eilgaenge als auch Schnittbewegungen.
    Postprozessor-agnostisch — der konkrete G-Code wird vom Postprozessor erzeugt.
    """

    operation_id: str
    operation_typ: OperationsTyp
    werkzeug_id: str
    bewegungen: list[Bewegung]
    spindel_rpm: float
    sicherheitshoehe: float
    kommentar: str = ""
    metadaten: dict = field(default_factory=dict)

    @property
    def gesamtlaenge(self) -> float:
        """Gesamter Verfahrweg (Eilgang + Schnitt) in mm."""
        if not self.bewegungen:
            return 0.0
        laenge = 0.0
        prev = self.bewegungen[0]
        for b in self.bewegungen[1:]:
            dx = b.x - prev.x
            dy = b.y - prev.y
            dz = b.z - prev.z
            laenge += (dx * dx + dy * dy + dz * dz) ** 0.5
            prev = b
        return laenge

    @property
    def schnittlaenge(self) -> float:
        """Verfahrweg ausschliesslich Schnitt-Bewegungen (G1/G2/G3/Plunge)."""
        if len(self.bewegungen) < 2:
            return 0.0
        laenge = 0.0
        prev = self.bewegungen[0]
        for b in self.bewegungen[1:]:
            if b.typ != BewegungsTyp.EILGANG:
                dx = b.x - prev.x
                dy = b.y - prev.y
                dz = b.z - prev.z
                laenge += (dx * dx + dy * dy + dz * dz) ** 0.5
            prev = b
        return laenge

    def zeitschaetzung_minuten(self, eilgang_mm_min: float) -> float:
        """Schaetzt die Bearbeitungszeit. Vorschub aus Bewegungen, sonst Default."""
        if not self.bewegungen:
            return 0.0
        zeit_min = 0.0
        prev = self.bewegungen[0]
        for b in self.bewegungen[1:]:
            dx = b.x - prev.x
            dy = b.y - prev.y
            dz = b.z - prev.z
            d = (dx * dx + dy * dy + dz * dz) ** 0.5
            speed = eilgang_mm_min if b.typ == BewegungsTyp.EILGANG else (b.feed or 1000.0)
            zeit_min += d / speed
            prev = b
        return zeit_min


__all__ = [
    "Bewegung",
    "BewegungsTyp",
    "OperationsTyp",
    "Toolpath",
]
