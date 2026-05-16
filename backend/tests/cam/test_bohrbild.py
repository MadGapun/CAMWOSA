"""Tests fuer Bohrbild-Erkennung."""

from __future__ import annotations

from camwosa.cam.bohrbild import erkenne_bohrbilder
from camwosa.dxf.parser import GeometrieObjekt, GeometrieTyp, Punkt2D


def _kreis(x: float, y: float, r: float, layer: str = "0") -> GeometrieObjekt:
    return GeometrieObjekt(
        typ=GeometrieTyp.KREIS,
        layer=layer,
        punkte=[Punkt2D(x, y)],
        geschlossen=True,
        attribute={"radius": r},
    )


class TestGruppierung:
    def test_zwei_durchmesser_zwei_gruppen(self) -> None:
        objekte = [
            _kreis(0, 0, 3), _kreis(10, 0, 3),   # D=6
            _kreis(20, 0, 5), _kreis(30, 0, 5),  # D=10
        ]
        gruppen = erkenne_bohrbilder(objekte)
        assert len(gruppen) == 2
        durchmessern = {g.durchmesser for g in gruppen}
        assert 6 in durchmessern
        assert 10 in durchmessern

    def test_toleranz_zusammenfassung(self) -> None:
        objekte = [_kreis(0, 0, 3.0), _kreis(10, 0, 3.02)]
        gruppen = erkenne_bohrbilder(objekte, durchmesser_toleranz=0.1)
        assert len(gruppen) == 1
        assert len(gruppen[0].punkte) == 2

    def test_layer_filter(self) -> None:
        objekte = [_kreis(0, 0, 3, "BOHRUNGEN"), _kreis(10, 0, 3, "KONTUR")]
        gruppen = erkenne_bohrbilder(objekte, layer_filter="BOHRUNGEN")
        assert len(gruppen) == 1
        assert len(gruppen[0].punkte) == 1


class TestMuster:
    def test_raster_erkannt(self) -> None:
        # 3x4-Raster
        objekte = [
            _kreis(x, y, 3)
            for x in (0, 10, 20)
            for y in (0, 10, 20, 30)
        ]
        gruppen = erkenne_bohrbilder(objekte)
        assert gruppen[0].muster == "raster"
        assert gruppen[0].raster_dx == 10
        assert gruppen[0].raster_dy == 10

    def test_polar_array_erkannt(self) -> None:
        import math
        # 8 Bohrungen rund um (50,50) bei Radius 20
        objekte = []
        for i in range(8):
            winkel = 2 * math.pi * i / 8
            objekte.append(_kreis(50 + 20 * math.cos(winkel), 50 + 20 * math.sin(winkel), 3))
        gruppen = erkenne_bohrbilder(objekte)
        assert gruppen[0].muster == "polar"
        assert gruppen[0].polar_zentrum.x == 50
        assert gruppen[0].polar_zentrum.y == 50
        assert abs(gruppen[0].polar_radius - 20) < 0.1

    def test_ungeordnet(self) -> None:
        objekte = [
            _kreis(0, 0, 3), _kreis(13, 5, 3), _kreis(7, 22, 3), _kreis(33, 17, 3),
        ]
        gruppen = erkenne_bohrbilder(objekte)
        assert gruppen[0].muster == "ungeordnet"
