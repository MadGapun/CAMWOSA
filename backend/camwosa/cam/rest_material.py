"""Rest-Material-Heightmap (Cluster I6, verschränkt mit A49).

Nach dem Abtrag eines oder mehrerer Toolpaths bleibt **Restmaterial** stehen.
Für die dominante Schruppen→Schlichten-Reihenfolge (und für 2-/N-seitige
Aufspannungen aus A49) ist die entscheidende Frage: *Wo* und *wie hoch* steht
nach dem vorherigen Pass noch Material?

Dieses Modul liefert die **Rest-Höhe-Karte** — pro XY-Zelle die höchste noch
vorhandene Material-Z. Sie ist die Datengrundlage für:
- Visualisierung „was ist noch da" (2D-Overlay über der Vorschau),
- Rest-Bearbeitung (eine Schlicht-/Räum-Bahn, die nur dort schneidet, wo noch
  Material steht — folgt als eigener Schritt),
- Stock-Übergabe zwischen Setups (A49).

Aufbauend auf der vorhandenen Voxel-Simulation (`cam/simulation.py`) — bewusst
kein neues Geometrie-Modell, sondern dieselbe robuste Voxel-Maschinerie.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from camwosa.cam.simulation import WerkstueckQuader, simuliere_grid
from camwosa.db.models import Werkzeug
from camwosa.gcode.toolpath import Toolpath


@dataclass
class RestHeightmap:
    """Rest-Höhe-Karte nach dem Abtrag.

    ``hoehen_mm[ix][iy]`` = höchste verbleibende Material-Z (mm) der Spalte
    (0.0 = bis zum Tisch abgetragen). Index → Welt:
    ``x = nullpunkt_x + (ix + 0.5) * aufloesung_mm``.
    """

    aufloesung_mm: float
    nx: int
    ny: int
    werkstueck: WerkstueckQuader
    hoehen_mm: list[list[float]]
    max_rest_mm: float
    """Höchster verbleibender Materialpunkt (mm)."""
    rest_volumen_mm3: float
    abgetragenes_volumen_mm3: float
    bewegungen_simuliert: int


def rest_hoehen_aus_grid(grid: np.ndarray, aufloesung_mm: float) -> np.ndarray:
    """Berechnet die Rest-Höhe pro XY-Spalte aus einem Voxel-Grid.

    Returns: 2D-Array (nx, ny) mit der Z-Oberkante des höchsten Material-Voxels
    je Spalte in mm (0.0 wenn die Spalte komplett abgetragen ist).
    """
    nx, ny, nz = grid.shape
    hat_material = grid.any(axis=2)  # (nx, ny)
    # Höchster True-Index je Spalte: über z gespiegelt den ersten True suchen.
    rev = grid[:, :, ::-1]
    erster_von_oben = rev.argmax(axis=2)  # 0 wenn Spalte leer (maskieren wir weg)
    hoechster_iz = (nz - 1) - erster_von_oben
    hoehen = np.where(hat_material, (hoechster_iz + 1).astype(float) * aufloesung_mm, 0.0)
    return hoehen


def rest_heightmap(
    toolpaths: list[Toolpath],
    werkzeug: Werkzeug,
    werkstueck: WerkstueckQuader,
    *,
    aufloesung_mm: float = 2.0,
    z_oberkante_material: float | None = None,
) -> RestHeightmap:
    """Simuliert den Abtrag der Toolpaths und liefert die Rest-Höhe-Karte.

    Mehrere Toolpaths werden auf demselben Grid verkettet (Schruppen +
    Schlichten / mehrere Werkzeuge teilen sich denselben Stock).
    """
    grid, voxel_anfang, sim_count = simuliere_grid(
        toolpaths, werkzeug, werkstueck,
        aufloesung_mm=aufloesung_mm, z_oberkante_material=z_oberkante_material,
    )
    hoehen = rest_hoehen_aus_grid(grid, aufloesung_mm)
    voxel_volumen = aufloesung_mm ** 3
    voxel_rest = int(grid.sum())
    nx, ny, _ = grid.shape
    return RestHeightmap(
        aufloesung_mm=aufloesung_mm,
        nx=nx,
        ny=ny,
        werkstueck=werkstueck,
        hoehen_mm=hoehen.tolist(),
        max_rest_mm=float(hoehen.max()) if hoehen.size else 0.0,
        rest_volumen_mm3=voxel_rest * voxel_volumen,
        abgetragenes_volumen_mm3=(voxel_anfang - voxel_rest) * voxel_volumen,
        bewegungen_simuliert=sim_count,
    )


__all__ = [
    "RestHeightmap",
    "rest_heightmap",
    "rest_hoehen_aus_grid",
]
