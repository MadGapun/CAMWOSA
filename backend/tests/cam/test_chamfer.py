"""Tests fuer Chamfering (A45 / E5)."""

from __future__ import annotations

import math

import pytest

from camwosa.cam.chamfer import (
    ChamferParameter,
    berechne_fasen_tiefe,
    erzeuge_chamfer_toolpath,
)
from camwosa.db.models import Werkzeug, WerkzeugTyp


def _vbit(winkel: float = 90) -> Werkzeug:
    return Werkzeug(
        id="vbit", name=f"V-Bit {winkel}", typ=WerkzeugTyp.V_BIT,
        durchmesser=10, schaft_durchmesser=6,
        schneidlaenge=15, gesamtlaenge=40, schneiden=2,
        spitzenwinkel=winkel,
    )


def _params(fasenbreite: float = 1.0) -> ChamferParameter:
    return ChamferParameter(
        werkzeug_id="vbit", spindel_rpm=18000, vorschub=600,
        eintauch_vorschub=200, fasenbreite_mm=fasenbreite,
    )


class TestFasenTiefe:
    def test_90_grad_v_bit_1mm_fase(self):
        # V-Bit 90° -> Halbwinkel 45° -> tan(45°)=1 -> tiefe = 1/(2*1) = 0.5
        wz = _vbit(90)
        t = berechne_fasen_tiefe(1.0, wz)
        assert t == pytest.approx(0.5, abs=0.01)

    def test_60_grad_v_bit_1mm_fase(self):
        # V-Bit 60° -> Halbwinkel 30° -> tan(30°)≈0.577 -> tiefe ≈ 0.866
        wz = _vbit(60)
        t = berechne_fasen_tiefe(1.0, wz)
        assert t == pytest.approx(1.0 / (2 * math.tan(math.radians(30))), abs=0.01)

    def test_nicht_v_bit_raises(self):
        wz = Werkzeug(
            id="x", name="Schaft", typ=WerkzeugTyp.SCHAFTFRAESER,
            durchmesser=6, schaft_durchmesser=6,
            schneidlaenge=10, gesamtlaenge=40, schneiden=2,
        )
        with pytest.raises(ValueError, match="kein V-Bit"):
            berechne_fasen_tiefe(1.0, wz)


class TestChamferToolpath:
    def test_einfache_linie(self):
        wz = _vbit(90)
        tp = erzeuge_chamfer_toolpath(
            [(0, 0), (50, 0)], wz, _params(fasenbreite=1.0),
        )
        assert tp.metadaten["fasenbreite_mm"] == 1.0
        assert tp.metadaten["fasen_tiefe_mm"] == pytest.approx(0.5, abs=0.01)
        # Mindestens 1 Plunge + 1 Linear + 1 Eilgang
        assert len(tp.bewegungen) >= 3

    def test_geschlossener_pfad(self):
        wz = _vbit(60)
        tp = erzeuge_chamfer_toolpath(
            [(0, 0), (10, 0), (10, 10), (0, 10)], wz, _params(),
            geschlossen=True,
        )
        # Geschlossen -> letzte Linear-Bewegung geht zum Anfang zurueck
        assert tp.metadaten["geschlossen"] is True

    def test_zu_wenig_punkte_raises(self):
        wz = _vbit()
        with pytest.raises(ValueError, match="Mindestens 2"):
            erzeuge_chamfer_toolpath([(0, 0)], wz, _params())

    def test_max_tiefe_blockiert(self):
        wz = _vbit(30)  # Sehr spitz -> tiefe wird gross
        p = _params(fasenbreite=5.0)
        p.max_tiefe_mm = 1.0
        with pytest.raises(ValueError, match="max_tiefe"):
            erzeuge_chamfer_toolpath([(0, 0), (50, 0)], wz, p)
