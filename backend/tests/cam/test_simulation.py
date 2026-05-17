"""Tests fuer die Voxel-Material-Abtrag-Simulation."""

from __future__ import annotations

import pytest

from camwosa.cam.simulation import (
    SimulationsErgebnis,
    WerkstueckQuader,
    simuliere_toolpath,
    surface_voxel,
    voxelisiere_werkstueck,
    werkzeug_radius_an_z,
)
from camwosa.db.models import Werkzeug, WerkzeugTyp
from camwosa.gcode.toolpath import Bewegung, BewegungsTyp, OperationsTyp, Toolpath


def _wz(id_: str = "f6", durchmesser: float = 6.0, typ: WerkzeugTyp = WerkzeugTyp.SCHAFTFRAESER) -> Werkzeug:
    return Werkzeug(
        id=id_, name=id_, typ=typ,
        durchmesser=durchmesser, schaft_durchmesser=max(durchmesser, 6),
        schneidlaenge=20, gesamtlaenge=50, schneiden=2,
    )


def _werkstueck(l: float = 100, b: float = 100, h: float = 20) -> WerkstueckQuader:
    return WerkstueckQuader(laenge_x=l, breite_y=b, hoehe_z=h)


def _tp(bewegungen: list[Bewegung]) -> Toolpath:
    return Toolpath(
        operation_id="op", operation_typ=OperationsTyp.KONTUR,
        werkzeug_id="f6", bewegungen=bewegungen,
        spindel_rpm=18000, sicherheitshoehe=5.0,
    )


class TestVoxelisierung:
    def test_grid_dimensionen(self):
        grid = voxelisiere_werkstueck(_werkstueck(100, 50, 20), aufloesung_mm=2.0)
        assert grid.shape == (50, 25, 10)
        assert grid.all()  # alles Material

    def test_kleine_aufloesung(self):
        grid = voxelisiere_werkstueck(_werkstueck(10, 10, 10), aufloesung_mm=1.0)
        assert grid.shape == (10, 10, 10)


class TestWerkzeugRadius:
    def test_schaftfraeser_konstant(self):
        wz = _wz(durchmesser=6.0)
        assert werkzeug_radius_an_z(wz, 0.0) == pytest.approx(3.0, abs=0.5)
        assert werkzeug_radius_an_z(wz, 10.0) == pytest.approx(3.0, abs=0.5)

    def test_oberhalb_gesamtlaenge_schaft_radius(self):
        wz = _wz(durchmesser=3.0)
        # Bei z > gesamtlaenge → schaft_durchmesser / 2
        r = werkzeug_radius_an_z(wz, wz.gesamtlaenge + 5)
        assert r == wz.schaft_durchmesser / 2

    def test_negative_z_radius_0(self):
        assert werkzeug_radius_an_z(_wz(), -1.0) == 0.0


class TestEinzelStempel:
    def test_einstecher_traegt_material_ab(self):
        """G0 nach (50,50,5) + G1 auf (50,50,-5) — sollte ein Loch erzeugen."""
        wz = _wz(durchmesser=6.0)
        ws = _werkstueck(100, 100, 20)
        tp = _tp([
            Bewegung(BewegungsTyp.EILGANG, 50, 50, 25),
            Bewegung(BewegungsTyp.PLUNGE, 50, 50, 5, feed=400),
        ])
        # Feinere Aufloesung gibt genauere Approximation (sonst grobe Voxel-Treppen)
        erg = simuliere_toolpath(tp, wz, ws, aufloesung_mm=1.0)
        assert erg.abgetragenes_volumen_mm3 > 0
        # Loch hat ungefaehr pi*r^2 * (20-5) mm³ = 28.3 * 15 ≈ 424 mm³
        assert erg.abgetragenes_volumen_mm3 > 300
        assert erg.abgetragenes_volumen_mm3 < 600


class TestLinearer_Bahn:
    def test_horizontaler_pass(self):
        """G1 von (10,50,15) bis (90,50,15) — Schlitz in 15 mm Hoehe."""
        wz = _wz(durchmesser=6.0)
        ws = _werkstueck(100, 100, 20)
        tp = _tp([
            Bewegung(BewegungsTyp.EILGANG, 10, 50, 25),
            Bewegung(BewegungsTyp.PLUNGE, 10, 50, 15, feed=400),
            Bewegung(BewegungsTyp.LINEAR, 90, 50, 15, feed=2000),
        ])
        erg = simuliere_toolpath(tp, wz, ws, aufloesung_mm=2.0)
        # Schlitz: 80 mm lang × 6 mm breit × 5 mm tief = 2400 mm³
        # Plus Ein-Plunge (~150 mm³)
        assert erg.abgetragenes_volumen_mm3 > 1500
        assert erg.abgetragenes_volumen_mm3 < 4000


class TestEilgangSkip:
    def test_eilgang_in_luft_ueberspringt(self):
        """G0 oberhalb der Werkstueck-Oberkante darf nichts abtragen."""
        wz = _wz()
        ws = _werkstueck(100, 100, 20)
        tp = _tp([
            Bewegung(BewegungsTyp.EILGANG, 0, 0, 50),
            Bewegung(BewegungsTyp.EILGANG, 100, 100, 50),  # quer drueberher
        ])
        erg = simuliere_toolpath(tp, wz, ws, aufloesung_mm=2.0)
        assert erg.abgetragenes_volumen_mm3 == 0


class TestSurfaceVoxel:
    def test_voller_quader_nur_oberflaeche(self):
        grid = voxelisiere_werkstueck(_werkstueck(20, 20, 20), aufloesung_mm=2.0)
        surface = surface_voxel(grid)
        # Bei einem 10×10×10 Voxel-Quader ist das Innere 8×8×8 = 512,
        # Oberflaeche = 1000 - 512 = 488. Wir tolerieren grob.
        assert len(surface) >= 400
        assert len(surface) < 1000

    def test_leerer_grid_keine_surface(self):
        import numpy as np
        grid = np.zeros((10, 10, 10), dtype=bool)
        assert surface_voxel(grid) == []


class TestSimulationsErgebnis:
    def test_metadaten_korrekt(self):
        wz = _wz()
        ws = _werkstueck(100, 100, 20)
        tp = _tp([
            Bewegung(BewegungsTyp.EILGANG, 50, 50, 25),
            Bewegung(BewegungsTyp.PLUNGE, 50, 50, 15, feed=400),
        ])
        erg = simuliere_toolpath(tp, wz, ws, aufloesung_mm=2.0)
        assert erg.aufloesung_mm == 2.0
        assert erg.nx == 50 and erg.ny == 50 and erg.nz == 10
        assert erg.bewegungen_simuliert > 0
        assert isinstance(erg.boundary_voxel, list)
