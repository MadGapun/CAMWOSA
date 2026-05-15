"""Tests fuer Sicherheits-Checks."""

from __future__ import annotations

import pytest

from camwosa.gcode.toolpath import (
    Bewegung,
    BewegungsTyp,
    OperationsTyp,
    Toolpath,
)
from camwosa.safety import CheckStufe, pruefe_toolpath


def _toolpath(bewegungen: list[Bewegung], rpm: float = 18000) -> Toolpath:
    return Toolpath(
        operation_id="t",
        operation_typ=OperationsTyp.KONTUR,
        werkzeug_id="t01",
        spindel_rpm=rpm,
        sicherheitshoehe=5.0,
        bewegungen=bewegungen,
    )


class TestG0ImMaterial:
    def test_g0_unter_z_oberkante_ist_kritisch(
        self, proverxl_maschine, schaftfraeser_6mm
    ) -> None:
        # Eilgang zu Z=-2 obwohl Material-OK bei Z=0
        tp = _toolpath([
            Bewegung(BewegungsTyp.EILGANG, 50, 50, -2.0),  # CRASH!
        ])
        bericht = pruefe_toolpath(tp, proverxl_maschine, schaftfraeser_6mm)
        assert bericht.hat_blocker
        assert any(e.check_id == "g0_im_material" for e in bericht.ergebnisse)

    def test_g0_ueber_oberkante_kein_problem(
        self, proverxl_maschine, schaftfraeser_6mm
    ) -> None:
        tp = _toolpath([
            Bewegung(BewegungsTyp.EILGANG, 50, 50, 5.0),
            Bewegung(BewegungsTyp.EILGANG, 100, 50, 5.0),
        ])
        bericht = pruefe_toolpath(tp, proverxl_maschine, schaftfraeser_6mm)
        assert not any(e.check_id == "g0_im_material" for e in bericht.ergebnisse)


class TestArbeitsraum:
    def test_x_ausserhalb(self, proverxl_maschine, schaftfraeser_6mm) -> None:
        tp = _toolpath([Bewegung(BewegungsTyp.EILGANG, 500, 50, 5.0)])  # X > 400
        bericht = pruefe_toolpath(tp, proverxl_maschine, schaftfraeser_6mm)
        assert any(e.check_id == "arbeitsraum_x" for e in bericht.ergebnisse)
        assert bericht.hat_blocker

    def test_y_negativ(self, proverxl_maschine, schaftfraeser_6mm) -> None:
        tp = _toolpath([Bewegung(BewegungsTyp.EILGANG, 50, -10, 5.0)])
        bericht = pruefe_toolpath(tp, proverxl_maschine, schaftfraeser_6mm)
        assert any(e.check_id == "arbeitsraum_y" for e in bericht.ergebnisse)

    def test_z_zu_tief(self, proverxl_maschine, schaftfraeser_6mm) -> None:
        tp = _toolpath([Bewegung(BewegungsTyp.LINEAR, 50, 50, -200, feed=1000)])
        bericht = pruefe_toolpath(tp, proverxl_maschine, schaftfraeser_6mm)
        assert any(e.check_id == "arbeitsraum_z" for e in bericht.ergebnisse)


class TestWerkzeugLaenge:
    def test_schnitt_tiefer_als_schneidlaenge(
        self, proverxl_maschine, schaftfraeser_6mm
    ) -> None:
        # schaftfraeser_6mm hat schneidlaenge=22, max_tiefe=30
        tp = _toolpath([
            Bewegung(BewegungsTyp.PLUNGE, 50, 50, -30, feed=300),
        ])
        bericht = pruefe_toolpath(tp, proverxl_maschine, schaftfraeser_6mm)
        assert any(e.check_id == "werkzeug_zu_kurz" for e in bericht.ergebnisse)


class TestRPM:
    def test_rpm_zu_hoch(self, proverxl_maschine, schaftfraeser_6mm) -> None:
        tp = _toolpath([Bewegung(BewegungsTyp.LINEAR, 50, 50, -2, feed=1000)], rpm=50000)
        bericht = pruefe_toolpath(tp, proverxl_maschine, schaftfraeser_6mm)
        assert any(e.check_id == "rpm_zu_hoch" for e in bericht.ergebnisse)

    def test_rpm_null_ist_kritisch(self, proverxl_maschine, schaftfraeser_6mm) -> None:
        tp = _toolpath([Bewegung(BewegungsTyp.LINEAR, 50, 50, -2, feed=1000)], rpm=0)
        bericht = pruefe_toolpath(tp, proverxl_maschine, schaftfraeser_6mm)
        assert bericht.hat_blocker
        assert any(e.check_id == "rpm_fehlt" for e in bericht.ergebnisse)


class TestPlungeVorschub:
    def test_plunge_schneller_als_schnitt(
        self, proverxl_maschine, schaftfraeser_6mm
    ) -> None:
        tp = _toolpath([
            Bewegung(BewegungsTyp.PLUNGE, 50, 50, -2, feed=2000),
            Bewegung(BewegungsTyp.LINEAR, 100, 50, -2, feed=1000),
        ])
        bericht = pruefe_toolpath(tp, proverxl_maschine, schaftfraeser_6mm)
        assert any(e.check_id == "plunge_zu_schnell" for e in bericht.ergebnisse)


class TestKeineProbleme:
    def test_sauberer_toolpath_ohne_blocker(
        self, proverxl_maschine, schaftfraeser_6mm
    ) -> None:
        tp = _toolpath([
            Bewegung(BewegungsTyp.EILGANG, 50, 50, 5),
            Bewegung(BewegungsTyp.PLUNGE, 50, 50, -2, feed=400),
            Bewegung(BewegungsTyp.LINEAR, 100, 50, -2, feed=2000),
            Bewegung(BewegungsTyp.LINEAR, 100, 100, -2, feed=2000),
            Bewegung(BewegungsTyp.EILGANG, 100, 100, 5),
        ])
        bericht = pruefe_toolpath(tp, proverxl_maschine, schaftfraeser_6mm)
        assert not bericht.hat_blocker
