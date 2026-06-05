"""Tests für die Rest-Material-Heightmap (Cluster I6)."""

from __future__ import annotations

import numpy as np
import pytest

from camwosa.cam.rest_material import rest_heightmap, rest_hoehen_aus_grid
from camwosa.cam.simulation import WerkstueckQuader
from camwosa.db.models import Werkzeug, WerkzeugTyp
from camwosa.gcode.toolpath import Bewegung, BewegungsTyp, OperationsTyp, Toolpath


def _wz(durchmesser: float = 6.0) -> Werkzeug:
    return Werkzeug(
        id="f6", name="f6", typ=WerkzeugTyp.SCHAFTFRAESER,
        durchmesser=durchmesser, schaft_durchmesser=max(durchmesser, 6),
        schneidlaenge=20, gesamtlaenge=50, schneiden=2,
    )


def _tp(bewegungen: list[Bewegung]) -> Toolpath:
    return Toolpath(
        operation_id="op", operation_typ=OperationsTyp.KONTUR,
        werkzeug_id="f6", bewegungen=bewegungen,
        spindel_rpm=18000, sicherheitshoehe=5.0,
    )


class TestRestHoehenAusGrid:
    """Deterministischer Unit-Test der Höhen-Extraktion aus einem Voxel-Grid."""

    def test_volles_grid_volle_hoehe(self):
        grid = np.ones((2, 2, 3), dtype=bool)
        hoehen = rest_hoehen_aus_grid(grid, aufloesung_mm=2.0)
        assert hoehen.shape == (2, 2)
        # 3 Lagen × 2 mm = 6 mm überall
        assert np.allclose(hoehen, 6.0)

    def test_abgetragene_spalte_niedriger(self):
        grid = np.ones((2, 2, 3), dtype=bool)
        # Spalte (0,0): obere zwei Lagen abgetragen → höchstes Material iz=0
        grid[0, 0, 2] = False
        grid[0, 0, 1] = False
        hoehen = rest_hoehen_aus_grid(grid, aufloesung_mm=2.0)
        assert hoehen[0, 0] == pytest.approx(2.0)  # (0+1)*2
        assert hoehen[1, 1] == pytest.approx(6.0)  # unberührt

    def test_leere_spalte_null(self):
        grid = np.ones((2, 2, 3), dtype=bool)
        grid[0, 0, :] = False  # komplett bis Tisch abgetragen
        hoehen = rest_hoehen_aus_grid(grid, aufloesung_mm=2.0)
        assert hoehen[0, 0] == pytest.approx(0.0)


class TestRestHeightmapSimulation:
    def test_unberuehrt_volle_hoehe(self):
        """Werkzeug nur in der Luft → nichts abgetragen, Rest = volle Höhe."""
        ws = WerkstueckQuader(laenge_x=20, breite_y=20, hoehe_z=10)
        tp = _tp([
            Bewegung(BewegungsTyp.EILGANG, 0, 0, 25),
            Bewegung(BewegungsTyp.EILGANG, 20, 20, 25),
        ])
        erg = rest_heightmap([tp], _wz(), ws, aufloesung_mm=1.0)
        assert erg.max_rest_mm == pytest.approx(10.0, abs=1.0)
        assert erg.abgetragenes_volumen_mm3 == pytest.approx(0.0, abs=1.0)

    def test_bohrung_senkt_rest_lokal(self):
        """Einstich in der Mitte bis tip-z=4 → Rest dort ~4 mm, Ecken voll."""
        ws = WerkstueckQuader(laenge_x=20, breite_y=20, hoehe_z=10)
        tp = _tp([
            Bewegung(BewegungsTyp.EILGANG, 10, 10, 25),
            Bewegung(BewegungsTyp.PLUNGE, 10, 10, 4, feed=300),
        ])
        erg = rest_heightmap([tp], _wz(durchmesser=6.0), ws, aufloesung_mm=1.0)
        # Ecke unberührt = volle Höhe
        assert erg.max_rest_mm == pytest.approx(10.0, abs=1.0)
        assert erg.hoehen_mm[0][0] == pytest.approx(10.0, abs=1.0)
        # Mitte gebohrt → deutlich abgesenkt
        assert erg.hoehen_mm[10][10] < 5.0
        assert erg.abgetragenes_volumen_mm3 > 0.0

    def test_zwei_paesse_verketten_stock(self):
        """Schruppen + tieferes Schlichten am selben Punkt: zweiter Pass senkt weiter."""
        ws = WerkstueckQuader(laenge_x=20, breite_y=20, hoehe_z=10)
        schrupp = _tp([
            Bewegung(BewegungsTyp.EILGANG, 10, 10, 25),
            Bewegung(BewegungsTyp.PLUNGE, 10, 10, 6, feed=300),
        ])
        schlicht = _tp([
            Bewegung(BewegungsTyp.EILGANG, 10, 10, 25),
            Bewegung(BewegungsTyp.PLUNGE, 10, 10, 2, feed=300),
        ])
        nur_schrupp = rest_heightmap([schrupp], _wz(), ws, aufloesung_mm=1.0)
        beide = rest_heightmap([schrupp, schlicht], _wz(), ws, aufloesung_mm=1.0)
        # Zweiter, tieferer Pass entfernt mehr Material
        assert beide.abgetragenes_volumen_mm3 > nur_schrupp.abgetragenes_volumen_mm3
        assert beide.hoehen_mm[10][10] < nur_schrupp.hoehen_mm[10][10]
