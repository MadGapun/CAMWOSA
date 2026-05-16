"""Bohrbild-Erkennung aus DXF-Kreisen.

Filtert KREIS-Entities aus einer Geometrie-Liste und gruppiert sie nach
Durchmesser. Optional: erkennt regelmaessige Muster (Raster, Polar-Array).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from camwosa.dxf.parser import GeometrieObjekt, GeometrieTyp, Punkt2D


@dataclass
class Bohrgruppe:
    """Eine Gruppe von Bohrungen mit gleichem Durchmesser."""

    durchmesser: float
    punkte: list[Punkt2D]
    muster: str = "ungeordnet"  # ungeordnet | raster | polar
    raster_dx: float | None = None
    raster_dy: float | None = None
    polar_zentrum: Punkt2D | None = None
    polar_radius: float | None = None


def erkenne_bohrbilder(
    objekte: list[GeometrieObjekt],
    *,
    durchmesser_toleranz: float = 0.05,
    layer_filter: str | None = None,
) -> list[Bohrgruppe]:
    """Filtert Kreise und gruppiert sie nach Durchmesser.

    Args:
        objekte: Liste von GeometrieObjekten (z.B. aus DXF).
        durchmesser_toleranz: Durchmesser-Unterschied (mm) der noch als
            gleiche Gruppe gilt.
        layer_filter: Wenn gesetzt, nur Kreise dieses Layers verwenden.
    """
    kreise = [
        o for o in objekte
        if o.typ == GeometrieTyp.KREIS
        and (layer_filter is None or o.layer == layer_filter)
    ]
    if not kreise:
        return []

    # Nach Durchmesser sortieren und gruppieren
    kreise_sorted = sorted(kreise, key=lambda k: k.attribute["radius"])
    gruppen: list[Bohrgruppe] = []
    aktuelle_gruppe: Bohrgruppe | None = None
    for k in kreise_sorted:
        d = 2 * k.attribute["radius"]
        p = k.punkte[0]
        if aktuelle_gruppe is None or abs(d - aktuelle_gruppe.durchmesser) > durchmesser_toleranz:
            aktuelle_gruppe = Bohrgruppe(durchmesser=d, punkte=[p])
            gruppen.append(aktuelle_gruppe)
        else:
            aktuelle_gruppe.punkte.append(p)

    # Muster-Erkennung pro Gruppe
    for g in gruppen:
        _erkenne_muster(g)
    return gruppen


def _erkenne_muster(gruppe: Bohrgruppe) -> None:
    """Versucht Raster oder Polar-Array zu erkennen."""
    pts = gruppe.punkte
    if len(pts) < 4:
        return
    # Raster: alle X-Werte und Y-Werte sind regelmaessig verteilt
    xs = sorted({round(p.x, 3) for p in pts})
    ys = sorted({round(p.y, 3) for p in pts})
    if len(xs) >= 2 and len(ys) >= 2:
        dx = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
        dy = [ys[i + 1] - ys[i] for i in range(len(ys) - 1)]
        if dx and dy:
            dx_konstant = all(abs(d - dx[0]) < 0.1 for d in dx)
            dy_konstant = all(abs(d - dy[0]) < 0.1 for d in dy)
            # Erwartete Punktanzahl bei Raster = nx * ny
            if dx_konstant and dy_konstant and len(pts) == len(xs) * len(ys):
                gruppe.muster = "raster"
                gruppe.raster_dx = dx[0]
                gruppe.raster_dy = dy[0]
                return
    # Polar-Array: gleicher Radius zum Mittelpunkt
    cx = sum(p.x for p in pts) / len(pts)
    cy = sum(p.y for p in pts) / len(pts)
    radien = [math.hypot(p.x - cx, p.y - cy) for p in pts]
    if radien and (max(radien) - min(radien)) < 0.1:
        gruppe.muster = "polar"
        gruppe.polar_zentrum = Punkt2D(cx, cy)
        gruppe.polar_radius = radien[0]


__all__ = ["Bohrgruppe", "erkenne_bohrbilder"]
