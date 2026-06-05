"""Tests fuer die Werkstueck-Transformation beim Umspannen (A49, Issue #44)."""

from __future__ import annotations

import math

from camwosa.cam.umspannung import (
    SpiegelAchse,
    WerkstueckTransformation,
    stabilitaets_hinweise,
    transformiere_punkt,
    transformiere_toolpath,
)
from camwosa.gcode.toolpath import Bewegung, BewegungsTyp, OperationsTyp, Toolpath


def _tp(bew):
    return Toolpath(
        operation_id="op", operation_typ=OperationsTyp.KONTUR, werkzeug_id="t",
        bewegungen=bew, spindel_rpm=12000, sicherheitshoehe=5.0,
    )


class TestPunkt:
    def test_spiegel_x_spiegelt_y(self):
        t = WerkstueckTransformation(spiegeln=SpiegelAchse.X, werkstueck_tiefe_mm=20)
        x, y, z = transformiere_punkt(10, 5, -2, t)
        assert (x, y, z) == (10, 15, -2)  # y: 20-5

    def test_spiegel_y_spiegelt_x(self):
        t = WerkstueckTransformation(spiegeln=SpiegelAchse.Y, werkstueck_breite_mm=40)
        x, y, _ = transformiere_punkt(10, 5, 0, t)
        assert (x, y) == (30, 5)  # x: 40-10

    def test_wenden_invertiert_z(self):
        t = WerkstueckTransformation(invertiere_z=True)
        _, _, z = transformiere_punkt(1, 2, -3, t)
        assert z == 3

    def test_offset(self):
        t = WerkstueckTransformation(offset=(100, 50, 1))
        assert transformiere_punkt(0, 0, 0, t) == (100, 50, 1)

    def test_drehung_180_um_mitte(self):
        t = WerkstueckTransformation(drehung_grad=180, werkstueck_breite_mm=40, werkstueck_tiefe_mm=20)
        x, y, _ = transformiere_punkt(10, 5, 0, t)
        assert abs(x - 30) < 1e-9 and abs(y - 15) < 1e-9  # punktgespiegelt an (20,10)

    def test_drehung_90(self):
        t = WerkstueckTransformation(drehung_grad=90, werkstueck_breite_mm=20, werkstueck_tiefe_mm=20)
        x, y, _ = transformiere_punkt(20, 10, 0, t)  # rel (10,0) -> (0,10)
        assert abs(x - 10) < 1e-9 and abs(y - 20) < 1e-9

    def test_doppelte_spiegelung_ist_identitaet(self):
        t = WerkstueckTransformation(spiegeln=SpiegelAchse.X, werkstueck_tiefe_mm=20)
        x, y, z = transformiere_punkt(*transformiere_punkt(7, 3, -1, t), t)
        assert (round(x, 6), round(y, 6), round(z, 6)) == (7, 3, -1)


class TestToolpath:
    def test_linear_transformiert(self):
        t = WerkstueckTransformation(spiegeln=SpiegelAchse.X, werkstueck_tiefe_mm=20)
        out = transformiere_toolpath(
            _tp([Bewegung(BewegungsTyp.LINEAR, 10, 5, -2, feed=800)]), t)
        b = out.bewegungen[0]
        assert (b.x, b.y) == (10, 15)
        assert out.metadaten["umspann_transformiert"] is True

    def test_bogen_drehrichtung_kippt_bei_spiegelung(self):
        t = WerkstueckTransformation(spiegeln=SpiegelAchse.Y, werkstueck_breite_mm=40)
        bogen = Bewegung(BewegungsTyp.BOGEN_CW, 10, 0, -1, i=5, j=0, feed=600)
        out = transformiere_toolpath(_tp([bogen]), t).bewegungen[0]
        assert out.typ == BewegungsTyp.BOGEN_CCW   # Spiegelung dreht Drehsinn
        assert abs(out.i - (-5)) < 1e-9            # I-Vektor gespiegelt
        assert abs(out.x - 30) < 1e-9              # Endpunkt gespiegelt (40-10)

    def test_bogen_drehrichtung_bleibt_bei_drehung(self):
        t = WerkstueckTransformation(drehung_grad=90, werkstueck_breite_mm=20, werkstueck_tiefe_mm=20)
        bogen = Bewegung(BewegungsTyp.BOGEN_CW, 20, 10, -1, i=1, j=0, feed=600)
        out = transformiere_toolpath(_tp([bogen]), t).bewegungen[0]
        assert out.typ == BewegungsTyp.BOGEN_CW    # reine Drehung: Drehsinn bleibt
        assert abs(out.i - 0) < 1e-9 and abs(out.j - 1) < 1e-9  # (1,0)->(0,1)


class TestStabilitaet:
    def test_wende_ohne_spannmittel_warnt(self):
        h = stabilitaets_hinweise(ist_wende_setup=True, ist_letztes_setup=False, spannmittel="")
        assert any("Spannmittel" in x for x in h)

    def test_letztes_setup_hinweis(self):
        h = stabilitaets_hinweise(ist_wende_setup=False, ist_letztes_setup=True, spannmittel="Schraubstock")
        assert any("Boden" in x or "Auflage" in x for x in h)

    def test_normales_setup_keine_warnung(self):
        h = stabilitaets_hinweise(ist_wende_setup=False, ist_letztes_setup=False, spannmittel="x")
        assert h == []
