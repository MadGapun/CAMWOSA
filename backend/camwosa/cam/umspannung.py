"""Werkstück-Transformation zwischen Aufspannungen (Cluster A49, Issue #44).

Bei Multi-Setup-Jobs wird das Werkstück oft **umgespannt** — nicht nur der
Nullpunkt verschoben, sondern das Teil **gewendet** (2-seitig), **gespiegelt**
oder **gedreht** (N-seitig indexiert). Damit Seite B / die nächste Indexierung
geometrisch passt, müssen die Toolpath-Koordinaten entsprechend transformiert
werden.

Dieses Modul liefert das saubere, getestete Transformations-Primitiv:
- ``WerkstueckTransformation`` — beschreibt Spiegelung + Drehung (um die
  Werkstück-Mitte) + Z-Invertierung (Wenden) + zusätzlichen Offset.
- ``transformiere_punkt`` / ``transformiere_toolpath`` — wenden es an.
  Bei Spiegelung wird die **Bogen-Drehrichtung** (G2↔G3) korrekt getauscht und
  die relativen I/J-Zentren mit-transformiert.

Welche konkrete Transformation für die jeweilige Aufspannung/Spannmittel richtig
ist, entscheidet der Nutzer (Umspann-Wizard) — das Primitiv ist neutral + exakt.
"""

from __future__ import annotations

import math
from dataclasses import replace
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from camwosa.gcode.toolpath import BewegungsTyp, Toolpath


class SpiegelAchse(str, Enum):
    """Spiegel-Achse beim Umspannen (Spiegellinie parallel zur genannten Achse)."""

    KEINE = "keine"
    X = "x"  # Spiegellinie = X-Achse → Y-Koordinate spiegelt (Wenden vorn/hinten)
    Y = "y"  # Spiegellinie = Y-Achse → X-Koordinate spiegelt (Wenden links/rechts)


class WerkstueckTransformation(BaseModel):
    """Wie das Werkstück zwischen zwei Setups umgelegt wird.

    Reihenfolge der Anwendung auf einen Punkt: Spiegeln → Drehen (beides um die
    Werkstück-Mitte) → Z invertieren (Wenden) → Offset.
    """

    model_config = ConfigDict(extra="ignore")

    spiegeln: SpiegelAchse = SpiegelAchse.KEINE
    drehung_grad: float = Field(default=0.0, description="Drehung in XY um die Werkstück-Mitte")
    invertiere_z: bool = Field(default=False, description="Oberseite↔Unterseite (Wenden)")
    offset: tuple[float, float, float] = (0.0, 0.0, 0.0)
    werkstueck_breite_mm: float = Field(default=0.0, ge=0, description="X-Ausdehnung (für Mitte/Spiegel)")
    werkstueck_tiefe_mm: float = Field(default=0.0, ge=0, description="Y-Ausdehnung (für Mitte/Spiegel)")

    @property
    def spiegelt(self) -> bool:
        return self.spiegeln != SpiegelAchse.KEINE


def _rot(dx: float, dy: float, rad: float) -> tuple[float, float]:
    c, s = math.cos(rad), math.sin(rad)
    return dx * c - dy * s, dx * s + dy * c


def transformiere_punkt(
    x: float, y: float, z: float, t: WerkstueckTransformation,
) -> tuple[float, float, float]:
    """Transformiert einen Punkt gemäß der Umspann-Transformation."""
    cx = t.werkstueck_breite_mm / 2.0
    cy = t.werkstueck_tiefe_mm / 2.0
    # 1. Spiegeln um die Werkstück-Mitte
    if t.spiegeln == SpiegelAchse.X:
        y = 2.0 * cy - y
    elif t.spiegeln == SpiegelAchse.Y:
        x = 2.0 * cx - x
    # 2. Drehen um die Mitte
    if t.drehung_grad:
        dx, dy = _rot(x - cx, y - cy, math.radians(t.drehung_grad))
        x, y = cx + dx, cy + dy
    # 3. Wenden (Z invertieren)
    if t.invertiere_z:
        z = -z
    # 4. Offset
    ox, oy, oz = t.offset
    return (x + ox, y + oy, z + oz)


def _transformiere_vektor(i: float, j: float, t: WerkstueckTransformation) -> tuple[float, float]:
    """Transformiert einen RELATIVEN Vektor (Bogen-Zentrum I/J) — ohne Translation."""
    if t.spiegeln == SpiegelAchse.X:
        j = -j
    elif t.spiegeln == SpiegelAchse.Y:
        i = -i
    if t.drehung_grad:
        i, j = _rot(i, j, math.radians(t.drehung_grad))
    return i, j


def transformiere_toolpath(toolpath: Toolpath, t: WerkstueckTransformation) -> Toolpath:
    """Wendet die Transformation auf alle Bewegungen an (inkl. Bogen-Korrektur)."""
    neu = []
    for b in toolpath.bewegungen:
        x, y, z = transformiere_punkt(b.x, b.y, b.z, t)
        typ = b.typ
        i, j = b.i, b.j
        if typ in (BewegungsTyp.BOGEN_CW, BewegungsTyp.BOGEN_CCW):
            if i is not None and j is not None:
                i, j = _transformiere_vektor(i, j, t)
            # Genau EINE Spiegelung dreht den Drehsinn um (G2 <-> G3).
            if t.spiegelt:
                typ = (BewegungsTyp.BOGEN_CCW if typ == BewegungsTyp.BOGEN_CW
                       else BewegungsTyp.BOGEN_CW)
        neu.append(replace(b, typ=typ, x=x, y=y, z=z, i=i, j=j))
    meta = dict(toolpath.metadaten)
    meta["umspann_transformiert"] = True
    return replace(toolpath, bewegungen=neu, metadaten=meta)


def stabilitaets_hinweise(
    *, ist_wende_setup: bool, ist_letztes_setup: bool, spannmittel: str,
) -> list[str]:
    """Einfache Stabilitäts-Heuristik fürs Umspannen (advisory).

    - Wende-Setups (invertiere_z) brauchen sichere Spannung der bereits
      bearbeiteten Seite.
    - Das letzte Setup bearbeitet idealerweise die Referenz-/Bodenfläche.
    """
    hinweise: list[str] = []
    if ist_wende_setup:
        if not spannmittel.strip():
            hinweise.append(
                "Wende-Setup ohne benanntes Spannmittel — die bereits bearbeitete "
                "Seite muss sicher und plan gespannt werden (z.B. weiche Backen / "
                "Opferplatte mit Passstiften).")
        hinweise.append(
            "Beim Wenden: Referenzkante/Passstifte nutzen, damit Seite B exakt "
            "zur Seite A registriert ist.")
    if ist_letztes_setup:
        hinweise.append(
            "Letztes Setup: hier idealerweise die Auflage-/Bodenfläche fertig "
            "bearbeiten — danach gibt es keine stabile Referenz mehr.")
    return hinweise


__all__ = [
    "SpiegelAchse",
    "WerkstueckTransformation",
    "stabilitaets_hinweise",
    "transformiere_punkt",
    "transformiere_toolpath",
]
