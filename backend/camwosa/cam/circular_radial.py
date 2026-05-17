"""Circular + Radial Pocketing-Strategien (A43-Rest, Cluster B).

Erweitert die bestehenden Taschen-Strategien um:

- **CIRCULAR**: konzentrische Kreis-Spiralen von aussen nach innen (oder umgekehrt).
  Saubere konstante Werkzeug-Eingriffsgeometrie, ideal fuer runde Taschen.

- **RADIAL**: Speichen vom Mittelpunkt nach aussen, dann Drehung um stepover.
  Gut fuer rotationssymmetrische Geometrien, kombiniert gut mit Drehen.

Beide sind klassische 2.5D-Pocketing-Patterns, die im bestehenden tasche.py
(PARALLEL/SPIRAL/OFFSET/ADAPTIVE) noch nicht da sind.

Diese Implementation liefert die **Pfade** (Liste von (x,y)-Tupeln) — die
Z-Behandlung (stepdown, Plunge etc.) macht der allgemeine Taschen-Generator.

Issue: #36 (Cluster B)
"""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict, Field
from shapely.geometry import Point


class CircularPocketParameter(BaseModel):
    """Parameter fuer Circular-Pocketing."""

    model_config = ConfigDict(extra="ignore")

    mittelpunkt_x: float = 0.0
    mittelpunkt_y: float = 0.0
    aussen_radius: float = Field(gt=0)
    werkzeug_durchmesser: float = Field(gt=0)
    stepover_prozent: float = Field(default=40.0, gt=0, le=95)
    von_aussen_nach_innen: bool = True
    segmente_pro_umdrehung: int = Field(default=64, ge=12, le=360)
    fertigungs_aufmass: float = Field(default=0.0, ge=0)


class RadialPocketParameter(BaseModel):
    """Parameter fuer Radial-Pocketing."""

    model_config = ConfigDict(extra="ignore")

    mittelpunkt_x: float = 0.0
    mittelpunkt_y: float = 0.0
    aussen_radius: float = Field(gt=0)
    werkzeug_durchmesser: float = Field(gt=0)
    anzahl_speichen: int = Field(default=24, ge=4, le=720)
    stepover_prozent: float = Field(
        default=40.0, gt=0, le=95,
        description="Bei Radial: wie eng aufeinanderfolgende Speichen-Tiefen",
    )
    fertigungs_aufmass: float = Field(default=0.0, ge=0)


def circular_pocket_pfade(p: CircularPocketParameter) -> list[list[tuple[float, float]]]:
    """Konzentrische Kreis-Pfade von aussen (oder innen) zur jeweils anderen Seite.

    Jeder Pfad ist ein geschlossener Kreis (segmente_pro_umdrehung Punkte).
    Der erste Pfad liegt **werkzeug_radius + aufmass** innerhalb der Aussen-Kontur,
    weil die Werkzeug-Kante die Kontur beruehrt (nicht der Mittelpunkt).
    """
    werkzeug_radius = p.werkzeug_durchmesser / 2.0
    stepover = p.werkzeug_durchmesser * (p.stepover_prozent / 100.0)
    r_aussen = p.aussen_radius - werkzeug_radius - p.fertigungs_aufmass
    if r_aussen <= 0:
        return []

    # Liste von Radien — von gross nach klein (oder umgekehrt)
    radien: list[float] = []
    r = r_aussen
    while r > 0.01:
        radien.append(r)
        r -= stepover
    radien.append(0.0)  # Mittelpunkt

    # Wenn von INNEN nach AUSSEN, Reihenfolge umdrehen
    if not p.von_aussen_nach_innen:
        radien.reverse()

    pfade: list[list[tuple[float, float]]] = []
    for r in radien:
        if r < 0.01:
            # Mittelpunkt selbst — ein einziger Punkt
            pfade.append([(p.mittelpunkt_x, p.mittelpunkt_y)])
            continue
        pfad = _kreis_pfad(
            p.mittelpunkt_x, p.mittelpunkt_y, r, p.segmente_pro_umdrehung,
        )
        pfade.append(pfad)
    return pfade


def radial_pocket_pfade(p: RadialPocketParameter) -> list[list[tuple[float, float]]]:
    """Radial-Speichen — vom Mittelpunkt nach aussen, mit Stepover.

    Jede Speiche ist ein Segment von (mittelpunkt) zu (Punkt auf Aussenradius).
    Stepover bewegt den Aussenpunkt entlang einer aeusseren Kreisbahn.

    Resultat ist klassisches Sonnenstrahlen-Muster.
    """
    werkzeug_radius = p.werkzeug_durchmesser / 2.0
    r_aussen = p.aussen_radius - werkzeug_radius - p.fertigungs_aufmass
    if r_aussen <= 0:
        return []

    # Speichen mit gleichem Winkel-Abstand
    winkel_schritt = 2 * math.pi / p.anzahl_speichen
    pfade: list[list[tuple[float, float]]] = []
    for i in range(p.anzahl_speichen):
        winkel = i * winkel_schritt
        ende_x = p.mittelpunkt_x + r_aussen * math.cos(winkel)
        ende_y = p.mittelpunkt_y + r_aussen * math.sin(winkel)
        pfade.append([
            (p.mittelpunkt_x, p.mittelpunkt_y),
            (ende_x, ende_y),
        ])
    return pfade


def _kreis_pfad(
    cx: float, cy: float, r: float, n: int,
) -> list[tuple[float, float]]:
    """Geschlossener Kreis als Polyline mit n Punkten + Rueckkehrpunkt."""
    pfad = [
        (cx + r * math.cos(2 * math.pi * i / n),
         cy + r * math.sin(2 * math.pi * i / n))
        for i in range(n)
    ]
    pfad.append(pfad[0])  # geschlossen
    return pfad


__all__ = [
    "CircularPocketParameter",
    "RadialPocketParameter",
    "circular_pocket_pfade",
    "radial_pocket_pfade",
]
