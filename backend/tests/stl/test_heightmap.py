"""Tests fuer STL-Parser und Heightmap-Berechnung.

Wir generieren STL zur Laufzeit mit trimesh.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import trimesh

from camwosa.cam.parameter import OperationParameter
from camwosa.cam.relief import ReliefStrategie, erzeuge_relief_toolpath
from camwosa.gcode.toolpath import OperationsTyp
from camwosa.stl import STLFehler, berechne_heightmap, lade_stl


@pytest.fixture
def stl_pyramide(tmp_path: Path) -> Path:
    """Pyramide 100x100x20."""
    vertices = [
        [0, 0, 0],
        [100, 0, 0],
        [100, 100, 0],
        [0, 100, 0],
        [50, 50, 20],
    ]
    faces = [
        [0, 1, 4],
        [1, 2, 4],
        [2, 3, 4],
        [3, 0, 4],
        [0, 1, 2],
        [0, 2, 3],
    ]
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
    pfad = tmp_path / "pyramide.stl"
    mesh.export(str(pfad))
    return pfad


@pytest.fixture
def stl_quader(tmp_path: Path) -> Path:
    mesh = trimesh.creation.box(extents=[50, 50, 10])
    pfad = tmp_path / "box.stl"
    mesh.export(str(pfad))
    return pfad


class TestLadeStl:
    def test_pyramide_geladen(self, stl_pyramide: Path) -> None:
        dok = lade_stl(stl_pyramide)
        assert dok.bounding_box[0] == (0, 0, 0)
        assert dok.bounding_box[1] == (100, 100, 20)

    def test_quader_geladen(self, stl_quader: Path) -> None:
        dok = lade_stl(stl_quader)
        # box() zentriert um Origin -> -25..25, -25..25, -5..5
        assert dok.x_range[1] - dok.x_range[0] == pytest.approx(50)
        assert dok.z_range[1] - dok.z_range[0] == pytest.approx(10)

    def test_nicht_existent(self, tmp_path: Path) -> None:
        with pytest.raises(STLFehler):
            lade_stl(tmp_path / "gibts_nicht.stl")


class TestHeightmap:
    def test_pyramide_spitze_in_der_mitte(self, stl_pyramide: Path) -> None:
        dok = lade_stl(stl_pyramide)
        hm = berechne_heightmap(dok, aufloesung=5.0, z_referenz="max")
        # Spitze bei (50, 50) sollte hoechster Punkt sein (Z=0 nach Referenz max)
        nx, ny = hm.shape
        center_i = nx // 2
        center_j = ny // 2
        assert hm.z_values[center_i, center_j] == pytest.approx(0.0, abs=0.5)
        # Ecken sollten tiefer sein
        ecke = hm.z_values[0, 0]
        assert ecke < hm.z_values[center_i, center_j]


class TestRelief:
    def test_relief_toolpath_raster_x(
        self, stl_pyramide: Path, schaftfraeser_6mm
    ) -> None:
        dok = lade_stl(stl_pyramide)
        hm = berechne_heightmap(dok, aufloesung=5.0)
        param = OperationParameter(
            werkzeug_id=schaftfraeser_6mm.id,
            spindel_rpm=18000,
            vorschub=1500,
            eintauch_vorschub=300,
            sicherheitshoehe=5,
            max_tiefe=20,
            stepdown=20,
        )
        tp = erzeuge_relief_toolpath(hm, schaftfraeser_6mm, param,
                                     strategie=ReliefStrategie.RASTER_X)
        assert tp.operation_typ == OperationsTyp.RELIEF
        assert len(tp.bewegungen) > 10
        assert tp.metadaten["strategie"] == "raster_x"

    def test_kontur_parallel_nicht_implementiert(
        self, stl_pyramide: Path, schaftfraeser_6mm
    ) -> None:
        dok = lade_stl(stl_pyramide)
        hm = berechne_heightmap(dok, aufloesung=10.0)
        param = OperationParameter(
            werkzeug_id=schaftfraeser_6mm.id,
            spindel_rpm=18000,
            vorschub=1500,
            eintauch_vorschub=300,
            sicherheitshoehe=5,
            max_tiefe=20,
            stepdown=20,
        )
        with pytest.raises(NotImplementedError):
            erzeuge_relief_toolpath(hm, schaftfraeser_6mm, param,
                                    strategie=ReliefStrategie.KONTUR_PARALLEL)
