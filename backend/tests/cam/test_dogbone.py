"""Tests fuer Dogbone-Slots (A45 / E3)."""

from __future__ import annotations

import math

import pytest
from shapely.geometry import Polygon

from camwosa.cam.dogbone import (
    DogboneStil,
    berechne_dogbone_kreis,
    dogbone_polygon,
    erkenne_innenecken,
)
from camwosa.db.models import Werkzeug, WerkzeugTyp


def _werkzeug(d: float = 6.0) -> Werkzeug:
    return Werkzeug(
        id="wz", name="Test", typ=WerkzeugTyp.SCHAFTFRAESER,
        durchmesser=d, schaft_durchmesser=d,
        schneidlaenge=15, gesamtlaenge=40, schneiden=2,
    )


class TestErkenneInnenecken:
    def test_rechteck_4_ecken(self):
        rect = Polygon([(0, 0), (50, 0), (50, 30), (0, 30)])
        ecken = erkenne_innenecken(rect)
        assert len(ecken) == 4

    def test_dreieck_3_ecken(self):
        tri = Polygon([(0, 0), (50, 0), (25, 40)])
        ecken = erkenne_innenecken(tri)
        assert len(ecken) == 3

    def test_l_form_hat_5_innen_1_aussen(self):
        # L-Form (rein-eckig): 5 Innen-Ecken + 1 Aussen-Ecke
        l_form = Polygon([(0, 0), (50, 0), (50, 30), (30, 30), (30, 50), (0, 50)])
        ecken = erkenne_innenecken(l_form)
        # 5 Innen-Ecken (Drehung +90°), 1 Aussen-Ecke (Drehung -90°)
        assert len(ecken) == 5


class TestBerechneDogboneKreis:
    def test_dogbone_auf_ecke(self):
        rect = Polygon([(0, 0), (50, 0), (50, 30), (0, 30)])
        # Ecke 0 = (0, 0). DOGBONE-Mittelpunkt liegt EXAKT auf dem Vertex
        kreis = berechne_dogbone_kreis(rect, 0, werkzeug_radius=3.0,
                                        stil=DogboneStil.DOGBONE)
        assert kreis is not None
        mx, my, r = kreis
        assert r == 3.0
        assert mx == pytest.approx(0.0)
        assert my == pytest.approx(0.0)

    def test_t_bone_versetzt(self):
        rect = Polygon([(0, 0), (50, 0), (50, 30), (0, 30)])
        # Ecke 0 = (0, 0). T-Bone soll entlang der laengeren Seite (horizontal)
        # verschoben sein
        kreis = berechne_dogbone_kreis(rect, 0, werkzeug_radius=3.0,
                                        stil=DogboneStil.T_BONE)
        assert kreis is not None
        mx, my, r = kreis
        assert r == 3.0
        # T-Bone-Mittelpunkt ist entlang X verschoben (laengere Seite)
        assert mx > 0
        assert abs(my) < 0.01  # nicht in Y verschoben (vertikale Seite ist kuerzer)

    def test_invalid_vertex(self):
        rect = Polygon([(0, 0), (50, 0), (50, 30), (0, 30)])
        kreis = berechne_dogbone_kreis(rect, 99, werkzeug_radius=3.0)
        assert kreis is None


class TestDogbonePolygon:
    def test_polygon_wird_groesser(self):
        rect = Polygon([(0, 0), (50, 0), (50, 30), (0, 30)])
        wz = _werkzeug(d=4.0)
        erweitert = dogbone_polygon(rect, wz)
        assert erweitert.area > rect.area

    def test_polygon_ist_polygon(self):
        rect = Polygon([(0, 0), (50, 0), (50, 30), (0, 30)])
        wz = _werkzeug(d=4.0)
        erweitert = dogbone_polygon(rect, wz)
        assert erweitert.geom_type == "Polygon"

    def test_keine_innenecken_polygon_unveraendert(self):
        # Kreis hat keine Innen-Ecken
        from shapely.geometry import Point
        kreis = Point(50, 50).buffer(20)  # 64-segment Polygon
        wz = _werkzeug(d=4.0)
        result = dogbone_polygon(kreis, wz)
        # Da alle Vertex-Winkel sehr klein (~5.6°), keine Innen-Ecken erkannt
        # -> result == kreis (oder sehr aehnlich)
        assert abs(result.area - kreis.area) < 1.0

    def test_werkzeug_durchmesser_null_raises(self):
        rect = Polygon([(0, 0), (50, 0), (50, 30), (0, 30)])
        wz = _werkzeug(d=4.0)
        wz.durchmesser = 0  # circumvent validation
        with pytest.raises(ValueError, match="> 0"):
            dogbone_polygon(rect, wz)

    def test_t_bone_stil_geht_durch(self):
        rect = Polygon([(0, 0), (50, 0), (50, 30), (0, 30)])
        wz = _werkzeug(d=4.0)
        erweitert = dogbone_polygon(rect, wz, stil=DogboneStil.T_BONE)
        assert erweitert.area > rect.area
        assert erweitert.geom_type == "Polygon"
