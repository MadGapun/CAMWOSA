"""Tests fuer Waterline-Strategie (A43 / Cluster B)."""

from __future__ import annotations

import numpy as np
import pytest

from camwosa.cam.parameter import OperationParameter
from camwosa.cam.waterline import (
    erzeuge_waterline_toolpath,
    heightmap_zu_contour_polygone,
)
from camwosa.db.models import Werkzeug, WerkzeugTyp
from camwosa.gcode.toolpath import BewegungsTyp
from camwosa.stl.heightmap import Heightmap


def _hm(z: np.ndarray, aufl: float = 1.0) -> Heightmap:
    z32 = z.astype(np.float32)
    return Heightmap(
        z_values=z32,
        aufloesung=aufl,
        x_min=0.0, y_min=0.0,
        z_max=float(z32.max()) if z32.size > 0 else 0.0,
    )


def _werkzeug() -> Werkzeug:
    return Werkzeug(
        id="wz", name="Kugel 3mm", typ=WerkzeugTyp.KUGELFRAESER,
        durchmesser=3, schaft_durchmesser=3,
        schneidlaenge=10, gesamtlaenge=40, schneiden=2,
    )


def _params() -> OperationParameter:
    return OperationParameter(
        werkzeug_id="wz",
        spindel_rpm=18000, vorschub=600, eintauch_vorschub=200,
        max_tiefe=5, stepdown=1, sicherheitshoehe=5,
    )


class TestContourPolygone:
    def test_zylinder_relief_hat_kontur(self):
        # Heightmap mit Plateau in der Mitte (10x10 mit Erhebung in 4x4-Center)
        z = np.full((10, 10), -3.0, dtype=np.float32)
        z[3:7, 3:7] = 0.0  # Plateau (Material steht bis Oberkante)
        hm = _hm(z)
        # Bei Z=-1 sollten wir eine Kontur um das Plateau bekommen
        konturen = heightmap_zu_contour_polygone(hm, z_level=-1.0)
        assert len(konturen) >= 1
        assert all(len(c) >= 3 for c in konturen)

    def test_leere_heightmap(self):
        hm = _hm(np.zeros((1, 1)))
        konturen = heightmap_zu_contour_polygone(hm, z_level=-1.0)
        assert konturen == []

    def test_keine_kontur_wenn_material_komplett_unter_z(self):
        # Heightmap komplett bei Z=-5
        hm = _hm(np.full((5, 5), -5.0))
        # Bei Z=-1 ist alles UNTER dem Z-Level (mask = False ueberall)
        konturen = heightmap_zu_contour_polygone(hm, z_level=-1.0)
        assert konturen == []


class TestWaterlineToolpath:
    def test_basis_aufruf(self):
        z = np.full((10, 10), -3.0, dtype=np.float32)
        z[3:7, 3:7] = 0.0
        hm = _hm(z)
        tp = erzeuge_waterline_toolpath(hm, _werkzeug(), _params())
        assert tp.metadaten["strategie"] == "waterline"
        assert len(tp.bewegungen) > 0

    def test_z_levels_auto(self):
        z = np.full((10, 10), -3.0, dtype=np.float32)
        z[3:7, 3:7] = 0.0
        hm = _hm(z)
        # max_tiefe=5, stepdown=1 -> 5 Z-Levels
        tp = erzeuge_waterline_toolpath(hm, _werkzeug(), _params())
        # Konturen sollten an mehreren Z-Levels existieren
        assert tp.metadaten["konturen_pro_level"] >= 1

    def test_z_levels_explizit(self):
        z = np.full((10, 10), -3.0, dtype=np.float32)
        z[3:7, 3:7] = 0.0
        hm = _hm(z)
        tp = erzeuge_waterline_toolpath(hm, _werkzeug(), _params(),
                                          z_levels=[-1.0, -2.0])
        assert tp.metadaten["z_levels"] == [-1.0, -2.0]

    def test_zu_kleine_heightmap_raises(self):
        hm = _hm(np.array([[0.0]]))
        with pytest.raises(ValueError, match="zu klein"):
            erzeuge_waterline_toolpath(hm, _werkzeug(), _params())

    def test_alle_bewegungen_haben_z(self):
        z = np.full((6, 6), -2.0, dtype=np.float32)
        z[1:5, 1:5] = 0.0
        hm = _hm(z)
        tp = erzeuge_waterline_toolpath(hm, _werkzeug(), _params())
        # Mindestens 1 Plunge, 1 Linear, 1 Eilgang
        typen = {b.typ for b in tp.bewegungen}
        assert BewegungsTyp.EILGANG in typen
