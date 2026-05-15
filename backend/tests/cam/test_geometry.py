"""Tests fuer das Geometrie-Hilfsmodul."""

from __future__ import annotations

import math

import pytest
from shapely.geometry import LineString, Polygon

from camwosa.cam.geometry import (
    OffsetSeite,
    bounding_box,
    diskretisiere_bogen,
    diskretisiere_kreis,
    objekt_zu_shapely,
    offset_kontur,
    skaliere_inch_zu_mm,
)
from camwosa.dxf.parser import GeometrieObjekt, GeometrieTyp, Punkt2D


class TestDiskretisierung:
    def test_kreis_punkte_anzahl(self) -> None:
        pts = diskretisiere_kreis(Punkt2D(0, 0), 10, segmente=32)
        assert len(pts) == 32

    def test_kreis_alle_punkte_auf_radius(self) -> None:
        pts = diskretisiere_kreis(Punkt2D(0, 0), 10, segmente=64)
        for p in pts:
            assert math.isclose(math.hypot(p.x, p.y), 10, rel_tol=1e-9)

    def test_bogen_start_und_endpunkt(self) -> None:
        pts = diskretisiere_bogen(Punkt2D(0, 0), 10, 0, 90)
        assert math.isclose(pts[0].x, 10, abs_tol=1e-9)
        assert math.isclose(pts[0].y, 0, abs_tol=1e-9)
        assert math.isclose(pts[-1].x, 0, abs_tol=1e-9)
        assert math.isclose(pts[-1].y, 10, abs_tol=1e-9)


class TestObjektZuShapely:
    def test_linie(self) -> None:
        obj = GeometrieObjekt(
            typ=GeometrieTyp.LINIE,
            layer="0",
            punkte=[Punkt2D(0, 0), Punkt2D(10, 0)],
        )
        geo = objekt_zu_shapely(obj)
        assert isinstance(geo, LineString)
        assert geo.length == 10

    def test_kreis_wird_polygon(self) -> None:
        obj = GeometrieObjekt(
            typ=GeometrieTyp.KREIS,
            layer="0",
            punkte=[Punkt2D(0, 0)],
            geschlossen=True,
            attribute={"radius": 10},
        )
        geo = objekt_zu_shapely(obj, segmente=128)
        assert isinstance(geo, Polygon)
        # Flaeche eines diskretisierten Kreises ist nahe pi*r^2
        assert math.isclose(geo.area, math.pi * 100, rel_tol=0.01)

    def test_geschlossene_polylinie(self) -> None:
        obj = GeometrieObjekt(
            typ=GeometrieTyp.POLYLINIE,
            layer="0",
            punkte=[Punkt2D(0, 0), Punkt2D(10, 0), Punkt2D(10, 10), Punkt2D(0, 10)],
            geschlossen=True,
        )
        geo = objekt_zu_shapely(obj)
        assert isinstance(geo, Polygon)
        assert geo.area == 100

    def test_punkt_wird_none(self) -> None:
        obj = GeometrieObjekt(
            typ=GeometrieTyp.PUNKT,
            layer="0",
            punkte=[Punkt2D(5, 5)],
        )
        assert objekt_zu_shapely(obj) is None


class TestOffset:
    def test_offset_aussen_macht_polygon_groesser(self) -> None:
        quadrat = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        offset = offset_kontur(quadrat, werkzeug_durchmesser=2, seite=OffsetSeite.AUSSEN)
        assert offset is not None
        assert offset.area > quadrat.area

    def test_offset_innen_macht_polygon_kleiner(self) -> None:
        quadrat = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        offset = offset_kontur(quadrat, werkzeug_durchmesser=2, seite=OffsetSeite.INNEN)
        assert offset is not None
        assert offset.area < quadrat.area

    def test_offset_auf_linie_unveraendert(self) -> None:
        quadrat = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        offset = offset_kontur(quadrat, werkzeug_durchmesser=2, seite=OffsetSeite.AUF_LINIE)
        assert offset.area == quadrat.area

    def test_offset_unbekannte_seite_fehler(self) -> None:
        quadrat = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        with pytest.raises(ValueError):
            offset_kontur(quadrat, 2, "diagonal")


class TestBoundingBox:
    def test_box_ueber_zwei_geometrien(self) -> None:
        geos = [
            LineString([(0, 0), (10, 5)]),
            Polygon([(20, 20), (30, 20), (30, 30), (20, 30)]),
        ]
        bb = bounding_box(geos)
        assert bb is not None
        assert bb.min_x == 0
        assert bb.max_x == 30
        assert bb.min_y == 0
        assert bb.max_y == 30
        assert bb.breite == 30
        assert bb.hoehe == 30

    def test_leere_box_ist_none(self) -> None:
        assert bounding_box([]) is None


class TestSkalierung:
    def test_inch_zu_mm_skaliert_punkte_und_radius(self) -> None:
        obj = GeometrieObjekt(
            typ=GeometrieTyp.KREIS,
            layer="0",
            punkte=[Punkt2D(1, 2)],
            geschlossen=True,
            attribute={"radius": 0.5},
        )
        skaliert = skaliere_inch_zu_mm(obj)
        assert math.isclose(skaliert.punkte[0].x, 25.4)
        assert math.isclose(skaliert.punkte[0].y, 50.8)
        assert math.isclose(skaliert.attribute["radius"], 12.7)
