"""Tests fuer Rotary-Achse: Wrapping, Vorschub-Korrektur, Indexing."""

from __future__ import annotations

import math

import pytest

from camwosa.cam.rotary import (
    erzeuge_indexing_toolpath,
    vorschub_korrektur_grad,
    wrap_2d_auf_zylinder,
)
from camwosa.dxf.parser import Punkt2D


class TestWrapping:
    def test_punkt_auf_halbem_umfang_ist_180_grad(self) -> None:
        # Bei Radius 10 -> Umfang = 2*pi*10. Halber Umfang ~ 31.4 mm
        radius = 10
        halber_umfang = math.pi * radius
        ergebnis = wrap_2d_auf_zylinder([Punkt2D(0, halber_umfang)], radius=radius)
        assert ergebnis.punkte[0].x == 0
        assert ergebnis.punkte[0].y == pytest.approx(180.0)

    def test_x_bleibt_x(self) -> None:
        ergebnis = wrap_2d_auf_zylinder([Punkt2D(50, 0)], radius=15)
        assert ergebnis.punkte[0].x == 50

    def test_radius_negativ_fehler(self) -> None:
        with pytest.raises(ValueError):
            wrap_2d_auf_zylinder([Punkt2D(0, 0)], radius=-5)

    def test_voller_umfang_ist_360_grad(self) -> None:
        radius = 25
        umfang = 2 * math.pi * radius
        ergebnis = wrap_2d_auf_zylinder([Punkt2D(0, umfang)], radius=radius)
        assert ergebnis.punkte[0].y == pytest.approx(360.0)


class TestVorschubKorrektur:
    def test_konversion_einfach(self) -> None:
        # 1000 mm/min am Radius 10 -> 1000/10 rad/min = 100 * 180/pi = ~5730 grad/min
        v = vorschub_korrektur_grad(1000, 10)
        assert v == pytest.approx(5729.578, abs=0.1)

    def test_radius_0_fehler(self) -> None:
        with pytest.raises(ValueError):
            vorschub_korrektur_grad(1000, 0)


class TestIndexing:
    def test_vier_bohrungen_rundum(self) -> None:
        # 4 Indexpositionen: 0, 90, 180, 270 Grad bei X=50
        positionen = [
            Punkt2D(50, 0),
            Punkt2D(50, 90),
            Punkt2D(50, 180),
            Punkt2D(50, 270),
        ]
        tp = erzeuge_indexing_toolpath(
            positionen,
            werkzeug_id="t01",
            rpm=15000,
            sicherheits_radius=20,
            bohrtiefe=5,
            plunge_feed=300,
        )
        assert tp.metadaten["anzahl"] == 4
        assert tp.metadaten["modus"] == "rotary_y"
        # Pro Bohrung: Eilgang + Plunge + Rueckzug = 3 Bewegungen
        assert len(tp.bewegungen) == 12
