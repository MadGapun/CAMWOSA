"""Tests fuer Spezial-Operationen."""

from __future__ import annotations

import pytest
from shapely.geometry import LineString, Polygon

from camwosa.cam.spezial import (
    FaseParameter,
    SchwalbenschwanzParameter,
    TNutParameter,
    erzeuge_fase_toolpath,
    erzeuge_schwalbenschwanz_toolpath,
    erzeuge_t_nut_toolpath,
)


class TestTNut:
    def test_t_nut_auf_linie(self, schaftfraeser_6mm) -> None:
        linie = LineString([(0, 0), (50, 0)])
        p = TNutParameter(
            werkzeug_id=schaftfraeser_6mm.id,
            spindel_rpm=15000, vorschub=1000, eintauch_vorschub=300,
            tiefe=8, stepdown=2, nut_breite=6,
        )
        tp = erzeuge_t_nut_toolpath(linie, schaftfraeser_6mm, p)
        assert tp.metadaten["operation"] == "t_nut"
        assert any("Plunge" in b.kommentar for b in tp.bewegungen)


class TestSchwalbenschwanz:
    def test_auf_polygon(self, schaftfraeser_6mm) -> None:
        polygon = Polygon([(0, 0), (50, 0), (50, 50), (0, 50)])
        p = SchwalbenschwanzParameter(
            werkzeug_id=schaftfraeser_6mm.id,
            spindel_rpm=15000, vorschub=1000, eintauch_vorschub=300,
            tiefe=5, stepdown=2, schwalbenschwanz_winkel_grad=60,
        )
        tp = erzeuge_schwalbenschwanz_toolpath(polygon, schaftfraeser_6mm, p)
        assert tp.metadaten["winkel_grad"] == 60

    def test_braucht_polygon(self, schaftfraeser_6mm) -> None:
        linie = LineString([(0, 0), (50, 0)])
        p = SchwalbenschwanzParameter(
            werkzeug_id=schaftfraeser_6mm.id,
            spindel_rpm=15000, vorschub=1000, eintauch_vorschub=300,
            tiefe=5, stepdown=2,
        )
        with pytest.raises(ValueError, match="geschlossene"):
            erzeuge_schwalbenschwanz_toolpath(linie, schaftfraeser_6mm, p)


class TestFase:
    def test_fase_auf_linie(self, vbit_60grad) -> None:
        linie = LineString([(0, 0), (100, 0)])
        p = FaseParameter(
            werkzeug_id=vbit_60grad.id,
            spindel_rpm=18000, vorschub=1500, eintauch_vorschub=300,
            tiefe=3, stepdown=1, fase_breite=1.5, spitzenwinkel_grad=60,
        )
        tp = erzeuge_fase_toolpath(linie, vbit_60grad, p)
        assert tp.metadaten["operation"] == "fase"
        # z = 1.5 / tan(30°) = 1.5 / 0.577 = 2.598
        assert abs(tp.metadaten["z_berechnet"] - (-2.598)) < 0.1

    def test_fase_auf_polygon(self, vbit_60grad) -> None:
        polygon = Polygon([(0, 0), (50, 0), (50, 50), (0, 50)])
        p = FaseParameter(
            werkzeug_id=vbit_60grad.id,
            spindel_rpm=18000, vorschub=1500, eintauch_vorschub=300,
            tiefe=3, stepdown=1, fase_breite=1.0, spitzenwinkel_grad=90,
        )
        tp = erzeuge_fase_toolpath(polygon, vbit_60grad, p)
        # z = 1 / tan(45°) = 1
        assert abs(tp.metadaten["z_berechnet"] - (-1.0)) < 0.01
