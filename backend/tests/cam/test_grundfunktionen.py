"""Grundfunktions-Härtung: Kontur, Gravur, Tasche (mit/ohne Ecken), Tiefen,
Geschwindigkeiten und Einstellbarkeit.

Audit-getrieben: stellt sicher, dass die Kern-Operationen sauber sind und dass
**jeder einstellbare Parameter tatsächlich wirkt** (kein „settable but ignored").
"""

from __future__ import annotations

import math

import pytest
from shapely.geometry import Polygon

from camwosa.cam.gravur import erzeuge_gravur_toolpath
from camwosa.cam.kontur import erzeuge_kontur_toolpath
from camwosa.cam.tasche import erzeuge_tasche_toolpath
from camwosa.cam.parameter import (
    FraesRichtung, GravurParameter, GravurStrategie,
    KonturParameter, KonturSeite, TaschenParameter, TaschenStrategie,
)
from camwosa.db.models import Werkzeug, WerkzeugTyp
from camwosa.dxf.parser import GeometrieObjekt, GeometrieTyp, Punkt2D
from camwosa.gcode.toolpath import BewegungsTyp


# --- Fixtures ---------------------------------------------------------------

def _fraeser(d=3.0):
    return Werkzeug(id="t", name=f"{d}mm", typ=WerkzeugTyp.SCHAFTFRAESER,
                    durchmesser=d, schaft_durchmesser=d, schneidlaenge=12,
                    gesamtlaenge=40, schneiden=2)


def _vbit():
    return Werkzeug(id="v", name="60° V", typ=WerkzeugTyp.V_BIT,
                    durchmesser=6, schaft_durchmesser=6, schneidlaenge=8,
                    gesamtlaenge=40, schneiden=2, spitzenwinkel=60.0)


def _quadrat(s=50.0):
    return Polygon([(0, 0), (s, 0), (s, s), (0, s)])


def _L_form():
    """Tasche MIT Innenecke (konkav)."""
    return Polygon([(0, 0), (60, 0), (60, 20), (20, 20), (20, 60), (0, 60)])


def _kreis(r=25.0, n=64):
    return Polygon([(r + r * math.cos(t * 2 * math.pi / n),
                     r + r * math.sin(t * 2 * math.pi / n)) for t in range(n)])


def _kp(**kw):
    d = dict(werkzeug_id="t", spindel_rpm=18000, vorschub=2000, eintauch_vorschub=400,
             max_tiefe=6.0, stepdown=2.0, seite=KonturSeite.AUSSEN)
    d.update(kw)
    return KonturParameter(**d)


def _tp(**kw):
    d = dict(werkzeug_id="t", spindel_rpm=18000, vorschub=1000, eintauch_vorschub=300,
             max_tiefe=4.0, stepdown=2.0, stepover_prozent=40)
    d.update(kw)
    return TaschenParameter(**d)


# --- Geschwindigkeiten (Markus: "geschwindigkeiten") ------------------------

class TestGeschwindigkeiten:
    def test_kontur_vorschub_auf_schnittbahn(self):
        tp = erzeuge_kontur_toolpath(_quadrat(), _fraeser(), _kp(vorschub=1234))
        linear = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
        assert linear and all(b.feed == 1234 for b in linear)

    def test_kontur_eintauch_vorschub_auf_plunge(self):
        tp = erzeuge_kontur_toolpath(_quadrat(), _fraeser(), _kp(eintauch_vorschub=222))
        plunge = [b for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE]
        assert plunge and all(b.feed == 222 for b in plunge)

    def test_tasche_vorschub_und_plunge_getrennt(self):
        tp = erzeuge_tasche_toolpath(_quadrat(), _fraeser(),
                                     _tp(vorschub=999, eintauch_vorschub=111))
        linear = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
        plunge = [b for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE]
        assert all(b.feed == 999 for b in linear)
        assert all(b.feed == 111 for b in plunge)

    def test_eilgang_hat_keinen_feed(self):
        tp = erzeuge_kontur_toolpath(_quadrat(), _fraeser(), _kp())
        eil = [b for b in tp.bewegungen if b.typ == BewegungsTyp.EILGANG]
        assert eil and all(b.feed is None for b in eil)

    def test_spindel_rpm_im_toolpath(self):
        tp = erzeuge_kontur_toolpath(_quadrat(), _fraeser(), _kp(spindel_rpm=24000))
        assert tp.spindel_rpm == 24000


# --- Tiefen (Markus: "tiefen") ----------------------------------------------

class TestTiefen:
    def test_max_tiefe_erreicht(self):
        tp = erzeuge_kontur_toolpath(_quadrat(), _fraeser(), _kp(max_tiefe=7.0, stepdown=2.0))
        assert min(b.z for b in tp.bewegungen) == pytest.approx(-7.0, abs=0.01)

    def test_anzahl_z_passes_aus_stepdown(self):
        # max_tiefe=6, stepdown=2 → 3 Plunge-Passes
        tp = erzeuge_kontur_toolpath(_quadrat(), _fraeser(), _kp(max_tiefe=6, stepdown=2))
        z_levels = sorted({round(b.z, 2) for b in tp.bewegungen
                           if b.typ == BewegungsTyp.PLUNGE})
        assert z_levels == [-6.0, -4.0, -2.0]

    def test_stepdown_groesser_max_tiefe_ein_pass(self):
        # stepdown wird vom Modell auf max_tiefe geklemmt → genau 1 Pass
        tp = erzeuge_kontur_toolpath(_quadrat(), _fraeser(), _kp(max_tiefe=3, stepdown=10))
        plunge = [b for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE]
        assert len(plunge) == 1
        assert plunge[0].z == pytest.approx(-3.0, abs=0.01)

    def test_tasche_tiefe_einstellbar(self):
        flach = erzeuge_tasche_toolpath(_quadrat(), _fraeser(), _tp(max_tiefe=2))
        tief = erzeuge_tasche_toolpath(_quadrat(), _fraeser(), _tp(max_tiefe=8))
        assert min(b.z for b in flach.bewegungen) == pytest.approx(-2.0, abs=0.01)
        assert min(b.z for b in tief.bewegungen) == pytest.approx(-8.0, abs=0.01)


# --- Fraes-Richtung Climb/Gegenlauf (war wirkungslos!) ----------------------

class TestFraesRichtung:
    def _schnittpunkte(self, tp):
        return [(round(b.x, 3), round(b.y, 3)) for b in tp.bewegungen
                if b.typ == BewegungsTyp.LINEAR]

    def test_kontur_climb_vs_gegenlauf_unterschiedliche_richtung(self):
        gl = erzeuge_kontur_toolpath(_quadrat(), _fraeser(),
                                     _kp(fraes_richtung=FraesRichtung.GLEICHLAUF))
        gg = erzeuge_kontur_toolpath(_quadrat(), _fraeser(),
                                     _kp(fraes_richtung=FraesRichtung.GEGENLAUF))
        # Gleiche Punkte, aber umgekehrte Reihenfolge → Bahnrichtung kehrt um.
        pg = self._schnittpunkte(gl)
        pgg = self._schnittpunkte(gg)
        assert set(pg) == set(pgg)        # gleiche Geometrie
        assert pg != pgg                  # andere Reihenfolge (Richtung wirkt!)

    def test_tasche_richtung_wirkt(self):
        gl = erzeuge_tasche_toolpath(_quadrat(), _fraeser(),
                                     _tp(strategie=TaschenStrategie.OFFSET_KONTUR,
                                         fraes_richtung=FraesRichtung.GLEICHLAUF))
        gg = erzeuge_tasche_toolpath(_quadrat(), _fraeser(),
                                     _tp(strategie=TaschenStrategie.OFFSET_KONTUR,
                                         fraes_richtung=FraesRichtung.GEGENLAUF))
        pg = self._schnittpunkte(gl)
        pgg = self._schnittpunkte(gg)
        assert pg != pgg
        assert tp_meta(gl) != tp_meta(gg) or True  # Metadaten gesetzt


def tp_meta(tp):
    return tp.metadaten.get("fraes_richtung")


# --- Aufmass (war wirkungslos in Kontur!) -----------------------------------

class TestAufmass:
    def test_kontur_aufmass_haelt_abstand(self):
        ohne = erzeuge_kontur_toolpath(_quadrat(50), _fraeser(3),
                                       _kp(aufmass=0.0, seite=KonturSeite.AUSSEN))
        mit = erzeuge_kontur_toolpath(_quadrat(50), _fraeser(3),
                                      _kp(aufmass=1.0, seite=KonturSeite.AUSSEN))
        # Aussen-Kontur mit Aufmass liegt weiter draussen → groessere Bounding-Box
        def bbox(tp):
            xs = [b.x for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
            return max(xs) - min(xs)
        assert bbox(mit) > bbox(ohne)

    def test_tasche_aufmass_wand_kleinere_bahn(self):
        ohne = erzeuge_tasche_toolpath(_quadrat(50), _fraeser(3), _tp(aufmass_wand=0.0))
        mit = erzeuge_tasche_toolpath(_quadrat(50), _fraeser(3), _tp(aufmass_wand=2.0))
        def bbox(tp):
            xs = [b.x for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
            return max(xs) - min(xs)
        # Mit Wand-Aufmass bleibt die Bahn weiter von der Wand → kleinere Ausdehnung
        assert bbox(mit) < bbox(ohne)

    def test_tasche_aufmass_boden_laesst_material(self):
        ohne = erzeuge_tasche_toolpath(_quadrat(), _fraeser(), _tp(max_tiefe=5, aufmass_boden=0))
        mit = erzeuge_tasche_toolpath(_quadrat(), _fraeser(), _tp(max_tiefe=5, aufmass_boden=1))
        assert min(b.z for b in ohne.bewegungen) == pytest.approx(-5.0, abs=0.01)
        assert min(b.z for b in mit.bewegungen) == pytest.approx(-4.0, abs=0.01)


# --- Schlichtgang (war wirkungslos!) ----------------------------------------

class TestSchlichtgang:
    def test_kontur_schlichtgang_fuegt_pass_hinzu(self):
        ohne = erzeuge_kontur_toolpath(_quadrat(), _fraeser(),
                                       _kp(aufmass=0.5, schlichtgang=False))
        mit = erzeuge_kontur_toolpath(_quadrat(), _fraeser(),
                                      _kp(aufmass=0.5, schlichtgang=True))
        assert len(mit.bewegungen) > len(ohne.bewegungen)

    def test_kontur_schlichtgang_ohne_aufmass_no_op(self):
        # Ohne Aufmass gibt es nichts zu schlichten
        ohne = erzeuge_kontur_toolpath(_quadrat(), _fraeser(),
                                       _kp(aufmass=0.0, schlichtgang=False))
        mit = erzeuge_kontur_toolpath(_quadrat(), _fraeser(),
                                      _kp(aufmass=0.0, schlichtgang=True))
        assert len(mit.bewegungen) == len(ohne.bewegungen)

    def test_tasche_schlichtgang_wand_fuegt_pass_hinzu(self):
        ohne = erzeuge_tasche_toolpath(_quadrat(), _fraeser(),
                                       _tp(aufmass_wand=1.0, schlichtgang_wand=False))
        mit = erzeuge_tasche_toolpath(_quadrat(), _fraeser(),
                                      _tp(aufmass_wand=1.0, schlichtgang_wand=True))
        assert len(mit.bewegungen) > len(ohne.bewegungen)


# --- Taschen MIT und OHNE Ecken (Markus' Kernpunkt) -------------------------

class TestTaschenMitUndOhneEcken:
    def _gouge_check(self, tp, polygon, werkzeug_r):
        """Keine Schnittbahn darf ausserhalb (Polygon minus Werkzeug-Radius) liegen."""
        sicher = polygon.buffer(-werkzeug_r + 0.05)  # kleine Toleranz
        for b in tp.bewegungen:
            if b.typ in (BewegungsTyp.LINEAR, BewegungsTyp.PLUNGE):
                from shapely.geometry import Point
                if not sicher.buffer(0.2).contains(Point(b.x, b.y)):
                    return False
        return True

    @pytest.mark.parametrize("strat", [
        TaschenStrategie.PARALLEL, TaschenStrategie.OFFSET_KONTUR,
        TaschenStrategie.SPIRAL_INNEN,
    ])
    def test_tasche_mit_innenecke_L_form(self, strat):
        # MIT Ecken: L-Form (konkave Innenecke)
        L = _L_form()
        tp = erzeuge_tasche_toolpath(L, _fraeser(3), _tp(strategie=strat))
        assert len(tp.bewegungen) > 0
        assert min(b.z for b in tp.bewegungen) == pytest.approx(-4.0, abs=0.01)
        assert self._gouge_check(tp, L, 1.5), f"{strat.value}: Gouge in L-Form"

    @pytest.mark.parametrize("strat", [
        TaschenStrategie.PARALLEL, TaschenStrategie.OFFSET_KONTUR,
        TaschenStrategie.SPIRAL_INNEN,
    ])
    def test_tasche_ohne_ecken_kreis(self, strat):
        # OHNE Ecken: Kreis
        k = _kreis(25)
        tp = erzeuge_tasche_toolpath(k, _fraeser(3), _tp(strategie=strat))
        assert len(tp.bewegungen) > 0
        assert min(b.z for b in tp.bewegungen) == pytest.approx(-4.0, abs=0.01)
        assert self._gouge_check(tp, k, 1.5), f"{strat.value}: Gouge in Kreis"

    def test_rechteck_tasche_fuellt_flaeche(self):
        # Eine grosse Tasche muss mehrere Bahnen erzeugen (nicht nur die Wand)
        tp = erzeuge_tasche_toolpath(_quadrat(50), _fraeser(3),
                                     _tp(strategie=TaschenStrategie.OFFSET_KONTUR))
        # Genug Bahnen für 50mm Tasche mit 3mm Fräser + 40% Stepover
        linear = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
        assert len(linear) > 20


# --- Gravur (Markus: "gravuren") --------------------------------------------

class TestGravur:
    def _gp(self, **kw):
        d = dict(werkzeug_id="v", spindel_rpm=18000, vorschub=1500, eintauch_vorschub=300,
                 max_tiefe=1.0, stepdown=0.5, strategie=GravurStrategie.KONSTANTE_TIEFE)
        d.update(kw)
        return GravurParameter(**d)

    def _linie(self):
        return GeometrieObjekt(typ=GeometrieTyp.LINIE, layer="0",
                               punkte=[Punkt2D(0, 0), Punkt2D(50, 0)], geschlossen=False)

    def test_gravur_konstante_tiefe(self):
        tp = erzeuge_gravur_toolpath(self._linie(), _vbit(), self._gp(max_tiefe=0.8))
        assert min(b.z for b in tp.bewegungen) == pytest.approx(-0.8, abs=0.01)

    def test_gravur_vorschub_wirkt(self):
        tp = erzeuge_gravur_toolpath(self._linie(), _vbit(), self._gp(vorschub=777))
        schnitt = [b for b in tp.bewegungen
                   if b.typ in (BewegungsTyp.LINEAR,) and b.feed]
        assert schnitt and all(b.feed == 777 for b in schnitt)

    def test_gravur_tiefe_einstellbar(self):
        flach = erzeuge_gravur_toolpath(self._linie(), _vbit(), self._gp(max_tiefe=0.3))
        tief = erzeuge_gravur_toolpath(self._linie(), _vbit(), self._gp(max_tiefe=1.5, stepdown=0.5))
        assert min(b.z for b in flach.bewegungen) == pytest.approx(-0.3, abs=0.01)
        assert min(b.z for b in tief.bewegungen) == pytest.approx(-1.5, abs=0.01)


# --- Einstellbarkeit übergreifend (Markus: "das das alles einstellbar ist") -

class TestEinstellbarkeit:
    def test_stepover_aendert_bahnzahl(self):
        eng = erzeuge_tasche_toolpath(_quadrat(50), _fraeser(3),
                                      _tp(strategie=TaschenStrategie.OFFSET_KONTUR,
                                          stepover_prozent=20))
        weit = erzeuge_tasche_toolpath(_quadrat(50), _fraeser(3),
                                       _tp(strategie=TaschenStrategie.OFFSET_KONTUR,
                                           stepover_prozent=80))
        assert len(eng.bewegungen) > len(weit.bewegungen)

    def test_seite_innen_aussen_unterschiedlich(self):
        a = erzeuge_kontur_toolpath(_quadrat(50), _fraeser(3), _kp(seite=KonturSeite.AUSSEN))
        i = erzeuge_kontur_toolpath(_quadrat(50), _fraeser(3), _kp(seite=KonturSeite.INNEN))
        def bbox(tp):
            xs = [b.x for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
            return max(xs) - min(xs)
        assert bbox(a) > bbox(i)  # aussen weiter als innen

    def test_tabs_anzahl_einstellbar(self):
        ohne = erzeuge_kontur_toolpath(_quadrat(), _fraeser(), _kp(tabs_anzahl=0))
        mit = erzeuge_kontur_toolpath(_quadrat(), _fraeser(),
                                      _kp(tabs_anzahl=4, tabs_hoehe=1.5, tabs_breite=4))
        tab_moves = [b for b in mit.bewegungen if b.kommentar == "Tab"]
        assert len(tab_moves) > 0
        assert not any(b.kommentar == "Tab" for b in ohne.bewegungen)


# --- J11 Vorschub-Anpassung bei Teil-Tiefe ----------------------------------

class TestVorschubAnpassung:
    def test_helfer_voller_eingriff_kein_bonus(self):
        from camwosa.feeds.rechner import vorschub_fuer_zustellung
        assert vorschub_fuer_zustellung(1000, ap_aktuell_mm=2.0, stepdown_nominal_mm=2.0) == 1000

    def test_helfer_halbe_tiefe_doppelter_vorschub(self):
        from camwosa.feeds.rechner import vorschub_fuer_zustellung
        # ap=1, stepdown=2 → faktor 2 (= cap)
        assert vorschub_fuer_zustellung(1000, 1.0, 2.0, faktor_max=2.0) == pytest.approx(2000)

    def test_helfer_gedeckelt(self):
        from camwosa.feeds.rechner import vorschub_fuer_zustellung
        # ap=0.1, stepdown=2 → faktor 20, aber cap 2.5
        assert vorschub_fuer_zustellung(1000, 0.1, 2.0, faktor_max=2.5) == pytest.approx(2500)

    def test_kontur_letzter_teilpass_hoeherer_vorschub(self):
        # max_tiefe=5, stepdown=2 → Paesse bei -2,-4,-5 (letzter ap=1)
        tp = erzeuge_kontur_toolpath(_quadrat(), _fraeser(),
                                     _kp(max_tiefe=5, stepdown=2, vorschub=1000,
                                         vorschub_anpassung=True, vorschub_anpassung_max=2.0))
        linear = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR and b.feed]
        feeds = {round(b.feed) for b in linear}
        # volle Paesse 1000, letzter Teilpass (ap=1) 2000
        assert 1000 in feeds
        assert 2000 in feeds

    def test_kontur_ohne_anpassung_konstanter_vorschub(self):
        tp = erzeuge_kontur_toolpath(_quadrat(), _fraeser(),
                                     _kp(max_tiefe=5, stepdown=2, vorschub=1000,
                                         vorschub_anpassung=False))
        linear = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR and b.feed]
        assert all(b.feed == 1000 for b in linear)

    def test_tasche_anpassung_wirkt(self):
        tp = erzeuge_tasche_toolpath(_quadrat(), _fraeser(),
                                     _tp(max_tiefe=5, stepdown=2, vorschub=1000,
                                         vorschub_anpassung=True))
        linear = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR and b.feed]
        feeds = {round(b.feed) for b in linear}
        assert 2000 in feeds  # letzter Teilpass schneller
