"""Voxel-basierte Material-Abtrag-Simulation.

Idee: das Werkstueck als 3D-Boolean-Grid (Material vorhanden / nicht). Beim
Durchlaufen des Toolpath wird an jeder Werkzeug-Position der Werkzeug-Stempel
als „material entfernt"-Maske auf das Grid angewandt. Am Ende koennen wir
entweder das volle Grid zurueckgeben (fuer kleine Werkstuecke) oder nur die
Boundary-Voxel (sichtbare Oberflaeche — viel weniger Daten, reicht zum Rendern).

Bewusst KEIN echtes CSG (Mesh-Boolean). Voxel ist:
- Robust gegen Toolpath-Eigenheiten (selbst-schneidende Pfade, sehr feine Schritte)
- Performant in numpy
- Aufloesungs-skalierbar — User kann grob/fein waehlen

Aufloesung: typisch 1.0–2.0 mm. Bei 400×400×100 mm Werkstueck und 2 mm Aufloesung
= 200×200×50 = 2 Mio Voxel — gut handhabbar.

Nicht-Ziele:
- Pixel-genaue Material-Abtrag (fuer Endkontrolle gehoert das in ein echtes CAM mit Mesh-Boolean)
- Mehrkernige Werkstuecke / Holzmaserung / Texturen
- Werkzeug-Verschleiss-Modellierung
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from camwosa.db.models import Werkzeug, WerkzeugTyp
from camwosa.gcode.toolpath import Bewegung, BewegungsTyp, Toolpath


@dataclass
class WerkstueckQuader:
    """Achsen-paralleler Werkstueck-Quader fuer die Simulation.

    Koordinaten in mm. Z=0 ist die Werkstueck-Unterseite (= Aufspann-Tisch).
    """

    laenge_x: float
    breite_y: float
    hoehe_z: float
    nullpunkt_x: float = 0.0
    nullpunkt_y: float = 0.0


@dataclass
class SimulationsErgebnis:
    """Ergebnis einer Voxel-Simulation."""

    aufloesung_mm: float
    nx: int
    ny: int
    nz: int
    werkstueck: WerkstueckQuader
    # Boundary-Voxel (sichtbare Oberflaeche) — Liste von (ix, iy, iz)-Tupeln
    boundary_voxel: list[tuple[int, int, int]]
    voxel_volumen_mm3: float
    """Restmaterial-Volumen in mm³."""
    abgetragenes_volumen_mm3: float
    bewegungen_simuliert: int


def voxelisiere_werkstueck(
    werkstueck: WerkstueckQuader, aufloesung_mm: float
) -> np.ndarray:
    """Erzeugt ein volles Boolean-Grid (alle True = Material da).

    Returns: 3D-numpy-Array mit Shape (nx, ny, nz).
    """
    nx = max(1, int(round(werkstueck.laenge_x / aufloesung_mm)))
    ny = max(1, int(round(werkstueck.breite_y / aufloesung_mm)))
    nz = max(1, int(round(werkstueck.hoehe_z / aufloesung_mm)))
    return np.ones((nx, ny, nz), dtype=bool)


def werkzeug_radius_an_z(werkzeug: Werkzeug, z_von_spitze: float) -> float:
    """Werkzeug-Radius an Position z (von der Spitze nach oben gemessen).

    Nutzt vorhandene `durchmesser_bei_z`-Methode des Werkzeug-Modells.
    """
    if z_von_spitze < 0:
        return 0.0
    if z_von_spitze >= werkzeug.gesamtlaenge:
        return werkzeug.schaft_durchmesser / 2.0
    return werkzeug.durchmesser_bei_z(z_von_spitze) / 2.0


def _werkzeug_stempel(
    grid: np.ndarray,
    werkzeug: Werkzeug,
    wz_x: float, wz_y: float, wz_z: float,
    werkstueck: WerkstueckQuader,
    aufloesung_mm: float,
) -> None:
    """Setzt alle Voxel die im Werkzeug-Volumen liegen auf False (= abgetragen).

    Werkzeug-Spitze sitzt auf (wz_x, wz_y, wz_z) in Welt-Koordinaten. Das
    Werkzeug zeigt nach OBEN aus der Werkstueck-Oberflaeche raus — wir
    simulieren also die Vertikal-Eingriffe.
    """
    nx, ny, nz = grid.shape
    # Welt → Voxel-Index
    def w2v_x(x: float) -> int:
        return int((x - werkstueck.nullpunkt_x) / aufloesung_mm)
    def w2v_y(y: float) -> int:
        return int((y - werkstueck.nullpunkt_y) / aufloesung_mm)
    def w2v_z(z: float) -> int:
        return int(z / aufloesung_mm)

    # Maximaler Werkzeug-Radius bestimmt die XY-BBox des Stempels
    max_r = werkzeug.schaft_durchmesser / 2.0
    bb_min_x = w2v_x(wz_x - max_r) - 1
    bb_max_x = w2v_x(wz_x + max_r) + 1
    bb_min_y = w2v_y(wz_y - max_r) - 1
    bb_max_y = w2v_y(wz_y + max_r) + 1

    # In Z: vom Werkzeug-Spitzen-Z bis zur Werkstueck-Oberflaeche nach oben
    bb_min_z = max(0, w2v_z(wz_z))
    bb_max_z = nz  # bis ganz oben

    # Loop ueber die BBox
    for ix in range(max(0, bb_min_x), min(nx, bb_max_x + 1)):
        x_world = werkstueck.nullpunkt_x + (ix + 0.5) * aufloesung_mm
        dx = x_world - wz_x
        for iy in range(max(0, bb_min_y), min(ny, bb_max_y + 1)):
            y_world = werkstueck.nullpunkt_y + (iy + 0.5) * aufloesung_mm
            dy = y_world - wz_y
            dist_xy_sq = dx * dx + dy * dy
            for iz in range(bb_min_z, bb_max_z):
                if not grid[ix, iy, iz]:
                    continue
                z_world = (iz + 0.5) * aufloesung_mm
                z_relativ = z_world - wz_z  # ab Werkzeug-Spitze nach oben
                if z_relativ < 0:
                    continue  # Voxel ist unter der Werkzeug-Spitze
                r = werkzeug_radius_an_z(werkzeug, z_relativ)
                if dist_xy_sq <= r * r:
                    grid[ix, iy, iz] = False


def _interpoliere_bewegung(
    von: tuple[float, float, float],
    nach: tuple[float, float, float],
    schrittweite_mm: float,
) -> list[tuple[float, float, float]]:
    """Teilt eine Linear-Bewegung in feine Schritte auf.

    Vermeidet dass der Werkzeug-Stempel zwischen weit entfernten Punkten
    ausgesetzt wird (Streifen-Artefakte).
    """
    dx = nach[0] - von[0]
    dy = nach[1] - von[1]
    dz = nach[2] - von[2]
    laenge = (dx * dx + dy * dy + dz * dz) ** 0.5
    if laenge < 1e-6:
        return [nach]
    n = max(1, int(laenge / schrittweite_mm) + 1)
    return [
        (von[0] + dx * i / n, von[1] + dy * i / n, von[2] + dz * i / n)
        for i in range(1, n + 1)
    ]


def simuliere_toolpath(
    toolpath: Toolpath,
    werkzeug: Werkzeug,
    werkstueck: WerkstueckQuader,
    *,
    aufloesung_mm: float = 2.0,
    ueberspringe_eilgang_ueber_material: bool = True,
    z_oberkante_material: float | None = None,
) -> SimulationsErgebnis:
    """Simuliert einen kompletten Toolpath als Material-Abtrag.

    - ``z_oberkante_material``: ueber dieser Hoehe gilt eine Z-Bewegung als
      „in der Luft" und der Stempel wird uebersprungen. Wenn None: =
      werkstueck.hoehe_z.
    - ``ueberspringe_eilgang_ueber_material``: G0-Bewegungen mit z >
      Oberkante werden ignoriert (Eilgang in der Luft).
    """
    grid = voxelisiere_werkstueck(werkstueck, aufloesung_mm)
    voxel_volumen = aufloesung_mm ** 3
    voxel_anfang = int(grid.sum())
    z_oberkante = z_oberkante_material if z_oberkante_material is not None else werkstueck.hoehe_z

    if not toolpath.bewegungen:
        return _baue_ergebnis(grid, werkstueck, aufloesung_mm, voxel_volumen, voxel_anfang, 0)

    aktuelle_pos = (toolpath.bewegungen[0].x, toolpath.bewegungen[0].y, toolpath.bewegungen[0].z)
    sim_count = 0

    for b in toolpath.bewegungen[1:]:
        ziel = (b.x, b.y, b.z)
        # Eilgang ueber Material → skippen wenn Z eindeutig drueber
        if (
            ueberspringe_eilgang_ueber_material
            and b.typ == BewegungsTyp.EILGANG
            and aktuelle_pos[2] > z_oberkante
            and ziel[2] > z_oberkante
        ):
            aktuelle_pos = ziel
            continue
        # Bewegung in Schritte teilen (Schrittweite < halbe Werkzeug-Radius)
        schrittweite = max(aufloesung_mm * 0.5, werkzeug.durchmesser / 4.0)
        schritte = _interpoliere_bewegung(aktuelle_pos, ziel, schrittweite)
        for px, py, pz in schritte:
            _werkzeug_stempel(grid, werkzeug, px, py, pz, werkstueck, aufloesung_mm)
            sim_count += 1
        aktuelle_pos = ziel

    return _baue_ergebnis(grid, werkstueck, aufloesung_mm, voxel_volumen, voxel_anfang, sim_count)


def _baue_ergebnis(
    grid: np.ndarray,
    werkstueck: WerkstueckQuader,
    aufloesung_mm: float,
    voxel_volumen: float,
    voxel_anfang: int,
    sim_count: int,
) -> SimulationsErgebnis:
    voxel_aktuell = int(grid.sum())
    abgetragen = (voxel_anfang - voxel_aktuell) * voxel_volumen
    rest = voxel_aktuell * voxel_volumen
    boundary = surface_voxel(grid)
    nx, ny, nz = grid.shape
    return SimulationsErgebnis(
        aufloesung_mm=aufloesung_mm,
        nx=nx, ny=ny, nz=nz,
        werkstueck=werkstueck,
        boundary_voxel=boundary,
        voxel_volumen_mm3=rest,
        abgetragenes_volumen_mm3=abgetragen,
        bewegungen_simuliert=sim_count,
    )


def simuliere_grid(
    toolpaths: list[Toolpath],
    werkzeug: Werkzeug,
    werkstueck: WerkstueckQuader,
    *,
    aufloesung_mm: float = 2.0,
    z_oberkante_material: float | None = None,
) -> tuple[np.ndarray, int, int]:
    """Traegt mehrere Toolpaths auf EINEM Voxel-Grid ab.

    Gibt das rohe Grid zurueck (``(grid, voxel_anfang, sim_count)``) — die
    Basis sowohl fuer die Boundary-Visualisierung (``simuliere_toolpaths``) als
    auch fuer die Rest-Material-Heightmap (``cam/rest_material.py``, I6).
    """
    grid = voxelisiere_werkstueck(werkstueck, aufloesung_mm)
    voxel_anfang = int(grid.sum())
    z_oberkante = z_oberkante_material if z_oberkante_material is not None else werkstueck.hoehe_z

    sim_count = 0
    for tp in toolpaths:
        if not tp.bewegungen:
            continue
        aktuelle_pos = (tp.bewegungen[0].x, tp.bewegungen[0].y, tp.bewegungen[0].z)
        for b in tp.bewegungen[1:]:
            ziel = (b.x, b.y, b.z)
            if (
                b.typ == BewegungsTyp.EILGANG
                and aktuelle_pos[2] > z_oberkante
                and ziel[2] > z_oberkante
            ):
                aktuelle_pos = ziel
                continue
            schrittweite = max(aufloesung_mm * 0.5, werkzeug.durchmesser / 4.0)
            for px, py, pz in _interpoliere_bewegung(aktuelle_pos, ziel, schrittweite):
                _werkzeug_stempel(grid, werkzeug, px, py, pz, werkstueck, aufloesung_mm)
                sim_count += 1
            aktuelle_pos = ziel

    return grid, voxel_anfang, sim_count


def simuliere_toolpaths(
    toolpaths: list[Toolpath],
    werkzeug: Werkzeug,
    werkstueck: WerkstueckQuader,
    *,
    aufloesung_mm: float = 2.0,
    z_oberkante_material: float | None = None,
) -> SimulationsErgebnis:
    """Verkettet mehrere Toolpaths auf demselben Werkstueck-Grid.

    Verwendet das gleiche Grid fuer alle Toolpaths — Abtrag des ersten
    bleibt fuer den zweiten erhalten. Ideal fuer Multi-Werkzeug-Setups
    (Schruppen + Schlichten).
    """
    grid, voxel_anfang, sim_count = simuliere_grid(
        toolpaths, werkzeug, werkstueck,
        aufloesung_mm=aufloesung_mm, z_oberkante_material=z_oberkante_material,
    )
    return _baue_ergebnis(
        grid, werkstueck, aufloesung_mm, aufloesung_mm ** 3, voxel_anfang, sim_count
    )


def surface_voxel(grid: np.ndarray) -> list[tuple[int, int, int]]:
    """Extrahiert nur die Voxel die mindestens einen leeren Nachbarn haben.

    Das sind die fuers Rendering sichtbaren — innere Voxel werden weggelassen,
    weil man sie eh nicht sieht. Reduziert die Datenmenge dramatisch.
    """
    if not grid.any():
        return []
    # Voll-Voxel die einen leeren Nachbarn haben (6-Nachbarn-Test)
    shifted_neighbors = np.zeros_like(grid)
    # Wir markieren ein True wenn es einen LEEREN Nachbarn gibt — d.h. shift
    # vom Negativ-Gitter
    nicht_material = ~grid
    # X-Nachbarn
    shifted_neighbors[1:, :, :] |= nicht_material[:-1, :, :]
    shifted_neighbors[:-1, :, :] |= nicht_material[1:, :, :]
    # Y
    shifted_neighbors[:, 1:, :] |= nicht_material[:, :-1, :]
    shifted_neighbors[:, :-1, :] |= nicht_material[:, 1:, :]
    # Z
    shifted_neighbors[:, :, 1:] |= nicht_material[:, :, :-1]
    shifted_neighbors[:, :, :-1] |= nicht_material[:, :, 1:]
    # Aussenraender zaehlen auch als „sichtbar"
    shifted_neighbors[0, :, :] = True
    shifted_neighbors[-1, :, :] = True
    shifted_neighbors[:, 0, :] = True
    shifted_neighbors[:, -1, :] = True
    shifted_neighbors[:, :, 0] = True
    shifted_neighbors[:, :, -1] = True

    surface_mask = grid & shifted_neighbors
    ixs, iys, izs = np.where(surface_mask)
    return list(zip(ixs.tolist(), iys.tolist(), izs.tolist()))


__all__ = [
    "SimulationsErgebnis",
    "WerkstueckQuader",
    "simuliere_grid",
    "simuliere_toolpath",
    "simuliere_toolpaths",
    "surface_voxel",
    "voxelisiere_werkstueck",
    "werkzeug_radius_an_z",
]
