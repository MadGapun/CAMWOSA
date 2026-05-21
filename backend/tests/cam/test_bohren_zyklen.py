"""Tests fuer erweiterte Bohr-Zyklen (Cluster J2): Anbohren, Senken, Gewindebohren."""

from __future__ import annotations

import pytest

from camwosa.cam.bohren import erzeuge_bohren_toolpath
from camwosa.cam.parameter import BohrParameter, BohrStrategie
from camwosa.db.models import Werkzeug, WerkzeugTyp
from camwosa.dxf.parser import Punkt2D
from camwosa.gcode.toolpath import BewegungsTyp


def _werkzeug(d: float = 6.0, typ: WerkzeugTyp = WerkzeugTyp.SCHAFTFRAESER) -> Werkzeug:
    return Werkzeug(
        id="t_bohr", name=f"Werkzeug {d}", typ=typ,
        durchmesser=d, schaft_durchmesser=d,
        schneidlaenge=15, gesamtlaenge=40, schneiden=2,
    )


def _param(strategie: BohrStrategie, **kw) -> BohrParameter:
    defaults = dict(
        werkzeug_id="t_bohr", spindel_rpm=10000, vorschub=600, eintauch_vorschub=200,
        sicherheitshoehe=5.0, max_tiefe=10.0, stepdown=10.0, strategie=strategie,
    )
    defaults.update(kw)
    return BohrParameter(**defaults)


_PUNKTE = [Punkt2D(0, 0), Punkt2D(20, 0)]


class TestAnbohren:
    def test_anbohren_kurze_tiefe(self):
        tp = erzeuge_bohren_toolpath(_PUNKTE, _werkzeug(), _param(
            BohrStrategie.ANBOHREN, anbohr_tiefe=1.5,
        ))
        plunges = [b for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE]
        # Anbohr-Tiefe = 1.5, NICHT max_tiefe (10)
        assert all(b.z == pytest.approx(-1.5) for b in plunges)

    def test_anbohren_zwei_loecher(self):
        tp = erzeuge_bohren_toolpath(_PUNKTE, _werkzeug(), _param(
            BohrStrategie.ANBOHREN, anbohr_tiefe=1.0,
        ))
        plunges = [b for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE]
        assert len(plunges) == 2


class TestSenken:
    def test_senken_konisch_tiefe_aus_winkel(self):
        # 90° Senker, Senk-Ø 10mm → Tiefe = (10/2)/tan(45°) = 5/1 = 5mm
        tp = erzeuge_bohren_toolpath(_PUNKTE[:1], _werkzeug(d=10), _param(
            BohrStrategie.SENKEN, senk_durchmesser=10.0, senk_winkel_grad=90.0,
        ))
        plunge = next(b for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE)
        assert plunge.z == pytest.approx(-5.0, abs=0.1)

    def test_senken_zylindrisch_ausfraesen(self):
        # Counterbore: Senk-Ø 12mm, Werkzeug 6mm → Kreis-Bahn mit Radius 3mm
        tp = erzeuge_bohren_toolpath(_PUNKTE[:1], _werkzeug(d=6), _param(
            BohrStrategie.SENKEN, senk_durchmesser=12.0, senk_winkel_grad=0.0,
            max_tiefe=4.0,
        ))
        linear = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
        assert len(linear) > 10  # Kreis-Schlichtbahn
        # Schnitt-Z auf Senk-Tiefe
        assert all(b.z == pytest.approx(-4.0) for b in linear)

    def test_senken_zylindrisch_klein_nur_plunge(self):
        # Senk-Ø ≈ Werkzeug → kein Ausfraesen, nur Plunge
        tp = erzeuge_bohren_toolpath(_PUNKTE[:1], _werkzeug(d=6), _param(
            BohrStrategie.SENKEN, senk_durchmesser=6.0, senk_winkel_grad=0.0, max_tiefe=3.0,
        ))
        assert any(b.typ == BewegungsTyp.PLUNGE for b in tp.bewegungen)


class TestGewindebohren:
    def test_synchron_feed_aus_steigung(self):
        # M6: Steigung 1.0mm, 1000 RPM → sync-feed 1000 mm/min
        tp = erzeuge_bohren_toolpath(_PUNKTE[:1], _werkzeug(d=5), _param(
            BohrStrategie.GEWINDEBOHREN, spindel_rpm=1000, gewinde_steigung=1.0, max_tiefe=12.0,
        ))
        plunge = next(b for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE)
        assert plunge.feed == pytest.approx(1000.0)
        assert plunge.z == pytest.approx(-12.0)

    def test_rein_und_raus(self):
        tp = erzeuge_bohren_toolpath(_PUNKTE[:1], _werkzeug(d=5), _param(
            BohrStrategie.GEWINDEBOHREN, spindel_rpm=800, gewinde_steigung=1.25, max_tiefe=10.0,
        ))
        # rein (PLUNGE) + raus (LINEAR auf Sicherheitshoehe mit sync-feed)
        raus = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR and b.kommentar and "raus" in b.kommentar]
        assert len(raus) == 1
        assert raus[0].feed == pytest.approx(800 * 1.25)

    def test_reverse_hinweis_im_kommentar(self):
        tp = erzeuge_bohren_toolpath(_PUNKTE[:1], _werkzeug(d=5), _param(
            BohrStrategie.GEWINDEBOHREN, spindel_rpm=1000, gewinde_steigung=1.0,
        ))
        kommentare = " ".join(b.kommentar for b in tp.bewegungen if b.kommentar)
        assert "Reverse" in kommentare or "M4" in kommentare
