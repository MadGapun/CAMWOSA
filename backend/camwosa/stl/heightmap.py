"""STL-Parser + Heightmap-Berechnung fuer 2.5D-Relief.

Eingabe: STL-Datei (binary oder ASCII).
Ausgabe: 2D-Numpy-Array mit Z-Werten pro X/Y-Raster.

Das Heightmap dient als Basis fuer die Relief-Operation.

Siehe Wiki: docs/wiki/STL-Import.md
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import trimesh


@dataclass
class STLDokument:
    pfad: Path
    mesh: trimesh.Trimesh
    bounding_box: tuple[tuple[float, float, float], tuple[float, float, float]]

    @property
    def x_range(self) -> tuple[float, float]:
        return (self.bounding_box[0][0], self.bounding_box[1][0])

    @property
    def y_range(self) -> tuple[float, float]:
        return (self.bounding_box[0][1], self.bounding_box[1][1])

    @property
    def z_range(self) -> tuple[float, float]:
        return (self.bounding_box[0][2], self.bounding_box[1][2])


@dataclass
class Heightmap:
    """Z-Hoehen pro X/Y-Raster.

    z_values[i, j] = Z-Hoehe am Raster-Punkt (x_min + i*aufloesung, y_min + j*aufloesung).
    """

    z_values: np.ndarray  # 2D, shape (nx, ny)
    aufloesung: float  # mm pro Raster-Schritt
    x_min: float
    y_min: float
    z_max: float  # max Z aus dem Mesh

    @property
    def shape(self) -> tuple[int, int]:
        return self.z_values.shape

    def position(self, i: int, j: int) -> tuple[float, float]:
        return (self.x_min + i * self.aufloesung, self.y_min + j * self.aufloesung)


class STLFehler(Exception):
    pass


def lade_stl(pfad: str | Path) -> STLDokument:
    """Liest eine STL-Datei und gibt das Mesh + Bounding-Box zurueck."""
    pfad_obj = Path(pfad)
    if not pfad_obj.exists():
        raise STLFehler(f"STL-Datei nicht gefunden: {pfad_obj}")
    try:
        mesh = trimesh.load(str(pfad_obj), force="mesh")
    except Exception as e:  # noqa: BLE001
        raise STLFehler(f"STL nicht lesbar: {e}") from e
    if not isinstance(mesh, trimesh.Trimesh):
        raise STLFehler("STL enthaelt kein gueltiges Mesh.")
    bb = mesh.bounds  # ((minx, miny, minz), (maxx, maxy, maxz))
    return STLDokument(
        pfad=pfad_obj,
        mesh=mesh,
        bounding_box=(tuple(bb[0]), tuple(bb[1])),
    )


def berechne_heightmap(
    dokument: STLDokument,
    *,
    aufloesung: float = 0.2,
    z_referenz: str = "max",
) -> Heightmap:
    """Berechnet ein Hoehenfeld (Heightmap) aus dem STL-Mesh.

    Args:
        aufloesung: Raster-Abstand in mm.
        z_referenz: "max" (Default) -> Werte sind 0 an der Oberflaeche und negativ ins Material.
                    "min" -> Werte sind 0 am tiefsten Punkt und positiv nach oben.
    """
    x_min, y_min, z_min = dokument.bounding_box[0]
    x_max, y_max, z_max = dokument.bounding_box[1]

    nx = max(2, int(np.ceil((x_max - x_min) / aufloesung)) + 1)
    ny = max(2, int(np.ceil((y_max - y_min) / aufloesung)) + 1)

    # Raster von Strahlen von oberhalb nach unten schiessen
    xs = np.linspace(x_min, x_max, nx)
    ys = np.linspace(y_min, y_max, ny)
    XX, YY = np.meshgrid(xs, ys, indexing="ij")
    origins = np.column_stack([
        XX.ravel(),
        YY.ravel(),
        np.full(XX.size, z_max + 1.0),
    ])
    directions = np.tile([0, 0, -1], (origins.shape[0], 1))

    # Ray-Casting
    locations, ray_indices, _ = dokument.mesh.ray.intersects_location(
        ray_origins=origins,
        ray_directions=directions,
        multiple_hits=False,
    )

    z_grid = np.full((nx, ny), np.nan)
    for loc, ridx in zip(locations, ray_indices):
        i = ridx // ny
        j = ridx % ny
        z_grid[i, j] = loc[2]

    # Fehlende Werte (kein Treffer): auf z_min setzen (kein Material da)
    np.nan_to_num(z_grid, copy=False, nan=z_min)

    if z_referenz == "max":
        # auf 0 referenzieren: Oberflaeche=0, Material wandert nach -Z
        z_grid = z_grid - z_max

    return Heightmap(
        z_values=z_grid,
        aufloesung=aufloesung,
        x_min=x_min,
        y_min=y_min,
        z_max=z_max,
    )


__all__ = [
    "Heightmap",
    "STLDokument",
    "STLFehler",
    "berechne_heightmap",
    "lade_stl",
]
