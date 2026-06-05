"""Q2: Getrennter Rampen-Eintauch-Feed in kontur/tasche + Parameter-Property.

Stellt sicher, dass die CAM-Operationen den Rampen-Wunschfeed auf die PLUNGE-
Bewegung legen (``rampe_feed``), waehrend der senkrechte ``feed`` weiter
``eintauch_vorschub`` bleibt. Rueckwaertskompatibel: Default Rampe = Plunge.
"""

from __future__ import annotations

from shapely.geometry import Polygon

from camwosa.cam.kontur import erzeuge_kontur_toolpath
from camwosa.cam.tasche import erzeuge_tasche_toolpath
from camwosa.cam.parameter import KonturParameter, TaschenParameter
from camwosa.db.models import Werkzeug, WerkzeugTyp
from camwosa.gcode.toolpath import BewegungsTyp


def _fraeser(d=3.0):
    return Werkzeug(id="t", name=f"{d}mm", typ=WerkzeugTyp.SCHAFTFRAESER,
                    durchmesser=d, schaft_durchmesser=d, schneidlaenge=12,
                    gesamtlaenge=40, schneiden=2)


def _quadrat(s=50.0):
    return Polygon([(0, 0), (s, 0), (s, s), (0, s)])


class TestParameterProperty:
    def test_default_rampe_gleich_plunge(self):
        p = KonturParameter(werkzeug_id="t", spindel_rpm=12000, vorschub=1000,
                            eintauch_vorschub=300, max_tiefe=5, stepdown=2)
        assert p.rampe_eintauch_vorschub == 300

    def test_faktor(self):
        p = KonturParameter(werkzeug_id="t", spindel_rpm=12000, vorschub=1000,
                            eintauch_vorschub=300, max_tiefe=5, stepdown=2,
                            rampe_vorschub_faktor=2.0)
        assert p.rampe_eintauch_vorschub == 600

    def test_absolut_hat_vorrang(self):
        p = KonturParameter(werkzeug_id="t", spindel_rpm=12000, vorschub=1000,
                            eintauch_vorschub=300, max_tiefe=5, stepdown=2,
                            rampe_vorschub=900, rampe_vorschub_faktor=2.0)
        assert p.rampe_eintauch_vorschub == 900

    def test_alte_projekte_ohne_felder_laden(self):
        # extra=ignore + Defaults: Konstruktion ohne die neuen Felder klappt.
        p = TaschenParameter(werkzeug_id="t", spindel_rpm=12000, vorschub=1000,
                             eintauch_vorschub=250, max_tiefe=5, stepdown=2)
        assert p.rampe_vorschub is None
        assert p.rampe_vorschub_faktor == 1.0
        assert p.rampe_eintauch_vorschub == 250


class TestKonturRampeFeed:
    def test_plunge_traegt_rampe_feed(self):
        p = KonturParameter(werkzeug_id="t", spindel_rpm=12000, vorschub=1000,
                            eintauch_vorschub=300, max_tiefe=4, stepdown=2,
                            rampe_vorschub_faktor=2.0)
        tp = erzeuge_kontur_toolpath(_quadrat(), _fraeser(), p)
        plunges = [b for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE]
        assert plunges
        for b in plunges:
            assert abs(b.feed - 300) < 1e-6          # senkrecht = Plunge-Feed
            assert abs(b.rampe_feed - 600) < 1e-6    # Rampe = 2×


class TestTascheRampeFeed:
    def test_plunge_traegt_rampe_feed(self):
        p = TaschenParameter(werkzeug_id="t", spindel_rpm=12000, vorschub=1000,
                             eintauch_vorschub=250, max_tiefe=4, stepdown=2,
                             rampe_vorschub=800)
        tp = erzeuge_tasche_toolpath(_quadrat(), _fraeser(), p)
        plunges = [b for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE]
        assert plunges
        for b in plunges:
            assert abs(b.feed - 250) < 1e-6
            assert abs(b.rampe_feed - 800) < 1e-6
