"""Tests fuer intelligente Fahrwege (J9 kurze Wege + J10 knappe Freifahrten)."""

from __future__ import annotations

import pytest

from camwosa.gcode.fahrweg import (
    eilgang_weg,
    optimiere_fahrwege,
    optimiere_reihenfolge,
    senke_freifahrten,
)
from camwosa.gcode.toolpath import Bewegung, BewegungsTyp, OperationsTyp, Toolpath


def _bohrung(x, y, z_safe=5.0, z_unten=-3.0):
    """Anfahrt + Plunge + Rueckzug fuer eine Bohrung."""
    return [
        Bewegung(BewegungsTyp.EILGANG, x, y, z_safe),
        Bewegung(BewegungsTyp.PLUNGE, x, y, z_unten, feed=200),
        Bewegung(BewegungsTyp.EILGANG, x, y, z_safe),
    ]


def _tp(bewegungen):
    return Toolpath(
        operation_id="op", operation_typ=OperationsTyp.BOHREN, werkzeug_id="t",
        bewegungen=bewegungen, spindel_rpm=12000, sicherheitshoehe=5.0,
    )


class TestReihenfolge:
    def test_zickzack_bohrungen_werden_kuerzer(self):
        # Bohrungen in schlechter Reihenfolge (hin und her)
        punkte = [(0, 0), (100, 0), (10, 0), (90, 0), (20, 0), (80, 0)]
        bew = []
        for (x, y) in punkte:
            bew += _bohrung(x, y)
        tp = _tp(bew)
        weg_vorher = eilgang_weg(tp)
        opt = optimiere_reihenfolge(tp)
        weg_nachher = eilgang_weg(opt)
        # Nearest-Neighbor sortiert 0,10,20,80,90,100 → viel kuerzer
        assert weg_nachher < weg_vorher

    def test_alle_bohrungen_erhalten(self):
        punkte = [(0, 0), (50, 50), (10, 5)]
        bew = []
        for p in punkte:
            bew += _bohrung(*p)
        opt = optimiere_reihenfolge(_tp(bew))
        plunges = [b for b in opt.bewegungen if b.typ == BewegungsTyp.PLUNGE]
        assert len(plunges) == 3
        # alle Original-Positionen kommen vor
        xs = {round(b.x, 1) for b in plunges}
        assert xs == {0.0, 50.0, 10.0}

    def test_eine_gruppe_unveraendert(self):
        tp = _tp(_bohrung(5, 5))
        opt = optimiere_reihenfolge(tp)
        assert opt is tp  # < 2 Gruppen → unveraendert

    def test_metadaten_marker(self):
        bew = _bohrung(0, 0) + _bohrung(50, 0)
        opt = optimiere_reihenfolge(_tp(bew))
        assert opt.metadaten.get("fahrweg_optimiert") is True

    def test_nearest_neighbor_startet_nah_am_ursprung(self):
        # Bohrung bei (90,0) und (10,0); Start (0,0) → erst (10,0)
        bew = _bohrung(90, 0) + _bohrung(10, 0)
        opt = optimiere_reihenfolge(_tp(bew), start=(0, 0))
        plunges = [b for b in opt.bewegungen if b.typ == BewegungsTyp.PLUNGE]
        assert plunges[0].x == pytest.approx(10.0)


class TestFreifahrten:
    def test_zwischen_eilgaenge_gesenkt(self):
        bew = _bohrung(0, 0) + _bohrung(50, 0) + _bohrung(100, 0)
        tp = _tp(bew)
        opt = senke_freifahrten(tp, freifahrt_hoehe=1.0, sicherheitshoehe=5.0)
        # Zwischen-Eilgaenge auf 1.0, aber erste Anfahrt + letzter Rueckzug auf 5.0
        eilgaenge = [b for b in opt.bewegungen if b.typ == BewegungsTyp.EILGANG]
        assert eilgaenge[0].z == pytest.approx(5.0)    # erste Anfahrt sicher
        assert eilgaenge[-1].z == pytest.approx(5.0)   # letzter Rueckzug sicher
        # mind. ein Zwischen-Eilgang wurde gesenkt
        assert any(b.z == pytest.approx(1.0) for b in eilgaenge[1:-1])

    def test_freifahrt_hoehe_ueber_sicherheit_no_op(self):
        bew = _bohrung(0, 0) + _bohrung(50, 0)
        tp = _tp(bew)
        opt = senke_freifahrten(tp, freifahrt_hoehe=10.0, sicherheitshoehe=5.0)
        assert opt is tp  # nichts zu senken

    def test_metadaten(self):
        bew = _bohrung(0, 0) + _bohrung(50, 0)
        opt = senke_freifahrten(_tp(bew), freifahrt_hoehe=1.0, sicherheitshoehe=5.0)
        assert opt.metadaten["freifahrt_hoehe"] == 1.0


class TestKombiniert:
    def test_optimiere_fahrwege_beides(self):
        punkte = [(0, 0), (100, 0), (10, 0)]
        bew = []
        for p in punkte:
            bew += _bohrung(*p)
        tp = _tp(bew)
        opt = optimiere_fahrwege(tp, reihenfolge=True, freifahrt_hoehe=1.0)
        assert opt.metadaten.get("fahrweg_optimiert") is True
        assert opt.metadaten.get("freifahrt_hoehe") == 1.0
        # kuerzerer Eilgang-Weg als Original
        assert eilgang_weg(opt) < eilgang_weg(tp)
