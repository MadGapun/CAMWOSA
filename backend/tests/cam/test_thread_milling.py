"""Tests fuer Thread-Milling."""

from __future__ import annotations

import math

import pytest

from camwosa.cam.thread_milling import (
    GewindeArt,
    GewindeRichtung,
    ThreadMillingFehler,
    ThreadMillingParameter,
    erzeuge_thread_milling_toolpath,
)
from camwosa.db.models import Werkzeug, WerkzeugTyp
from camwosa.gcode.toolpath import BewegungsTyp


def _werkzeug(d: float = 3.0) -> Werkzeug:
    return Werkzeug(
        id="t_thread", name=f"Gewindefraeser Ø{d}",
        typ=WerkzeugTyp.SCHAFTFRAESER,
        durchmesser=d, schaft_durchmesser=max(d, 6),
        schneidlaenge=10, gesamtlaenge=40, schneiden=2,
    )


class TestVorbedingungen:
    def test_werkzeug_zu_gross_fuer_innengewinde(self):
        # M6-Innengewinde mit 6mm Fraeser → kein Platz
        with pytest.raises(ThreadMillingFehler, match="zu gross"):
            erzeuge_thread_milling_toolpath(
                _werkzeug(6),
                ThreadMillingParameter(
                    werkzeug_id="t_thread", spindel_rpm=10000, vorschub=400,
                    eintauch_vorschub=100,
                    nenn_durchmesser=6, gewinde_steigung=1.0, gewinde_tiefe=10,
                    art=GewindeArt.INNEN,
                ),
            )

    def test_gewinde_tiefe_zu_klein_wirft(self):
        # Tiefe < halbe Steigung
        with pytest.raises(ThreadMillingFehler, match="kleiner als halbe"):
            erzeuge_thread_milling_toolpath(
                _werkzeug(3),
                ThreadMillingParameter(
                    werkzeug_id="t_thread", spindel_rpm=10000, vorschub=400,
                    eintauch_vorschub=100,
                    nenn_durchmesser=6, gewinde_steigung=1.0, gewinde_tiefe=0.3,
                ),
            )


class TestM6Innengewinde:
    def _param(self, **kw) -> ThreadMillingParameter:
        defaults = dict(
            werkzeug_id="t_thread", spindel_rpm=12000, vorschub=400,
            eintauch_vorschub=80,
            nenn_durchmesser=6.0, gewinde_steigung=1.0, gewinde_tiefe=8.0,
            art=GewindeArt.INNEN, richtung=GewindeRichtung.RECHTS,
        )
        defaults.update(kw)
        return ThreadMillingParameter(**defaults)

    def test_toolpath_metadaten_korrekt(self):
        tp = erzeuge_thread_milling_toolpath(_werkzeug(3.0), self._param())
        assert tp.metadaten["thread_milling"] is True
        assert tp.metadaten["nenn_durchmesser_mm"] == 6.0
        assert tp.metadaten["gewinde_steigung_mm"] == 1.0
        assert tp.metadaten["anzahl_umdrehungen"] == pytest.approx(8.0)
        # Bahn-Radius = (nenn - werkzeug)/2 = (6 - 3)/2 = 1.5
        assert tp.metadaten["bahn_radius_mm"] == pytest.approx(1.5)

    def test_bewegungs_struktur_korrekt(self):
        tp = erzeuge_thread_milling_toolpath(_werkzeug(3.0), self._param())
        typen = [b.typ for b in tp.bewegungen]
        # Erwartet: 2x Eilgang am Anfang, Plunge, viele Linear, Linear-zur-Mitte, Eilgang
        assert typen.count(BewegungsTyp.EILGANG) >= 2
        assert typen.count(BewegungsTyp.PLUNGE) == 1
        assert typen.count(BewegungsTyp.LINEAR) > 100  # 8 Umdr × 36 Segmente + Rueckweg

    def test_z_geht_progressiv_runter(self):
        tp = erzeuge_thread_milling_toolpath(_werkzeug(3.0), self._param())
        # Erste Helix-Bewegungen sammeln (alle Linear bis "zurueck zur Mitte")
        helix = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR
                 and (b.kommentar is None or "Zurueck" not in b.kommentar)]
        z_werte = [b.z for b in helix]
        for i in range(1, len(z_werte)):
            assert z_werte[i] <= z_werte[i - 1] + 1e-6, "Z muss progressiv tiefer"

    def test_radius_konstant(self):
        tp = erzeuge_thread_milling_toolpath(_werkzeug(3.0), self._param(
            mittelpunkt_x=10, mittelpunkt_y=20,
        ))
        bahn_radius = 1.5
        helix = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR
                 and (b.kommentar is None or "Zurueck" not in b.kommentar)]
        for b in helix:
            r = math.hypot(b.x - 10, b.y - 20)
            assert r == pytest.approx(bahn_radius, abs=1e-6)

    def test_zurueck_zur_mitte_vor_lift(self):
        tp = erzeuge_thread_milling_toolpath(_werkzeug(3.0), self._param())
        # Vorletzter Linear-Move soll auf Mittelpunkt (0,0 default) sein
        last_linear = next(b for b in reversed(tp.bewegungen) if b.typ == BewegungsTyp.LINEAR)
        assert last_linear.x == pytest.approx(0.0, abs=1e-6)
        assert last_linear.y == pytest.approx(0.0, abs=1e-6)
        assert last_linear.kommentar and "Mitte" in last_linear.kommentar


class TestAussengewinde:
    def test_aussen_bahn_radius_korrekt(self):
        # M10 Aussengewinde, 3mm Fraeser kreist drumherum
        tp = erzeuge_thread_milling_toolpath(
            _werkzeug(3),
            ThreadMillingParameter(
                werkzeug_id="t_thread", spindel_rpm=10000, vorschub=400,
                eintauch_vorschub=100,
                nenn_durchmesser=10.0, gewinde_steigung=1.5, gewinde_tiefe=12.0,
                art=GewindeArt.AUSSEN,
            ),
        )
        # Bahn = (nenn + werkzeug)/2 = (10+3)/2 = 6.5
        assert tp.metadaten["bahn_radius_mm"] == pytest.approx(6.5)


class TestRichtung:
    def test_rechts_vs_links_drehrichtung_unterschied(self):
        rechts = erzeuge_thread_milling_toolpath(_werkzeug(3), ThreadMillingParameter(
            werkzeug_id="t_thread", spindel_rpm=10000, vorschub=400, eintauch_vorschub=100,
            nenn_durchmesser=6, gewinde_steigung=1.0, gewinde_tiefe=6,
            art=GewindeArt.INNEN, richtung=GewindeRichtung.RECHTS,
            segmente_pro_umdrehung=12,
        ))
        links = erzeuge_thread_milling_toolpath(_werkzeug(3), ThreadMillingParameter(
            werkzeug_id="t_thread", spindel_rpm=10000, vorschub=400, eintauch_vorschub=100,
            nenn_durchmesser=6, gewinde_steigung=1.0, gewinde_tiefe=6,
            art=GewindeArt.INNEN, richtung=GewindeRichtung.LINKS,
            segmente_pro_umdrehung=12,
        ))
        # Zweiter Helix-Punkt: bei Rechts geht's CCW (+Y wachsend),
        # bei Links CW (-Y wachsend) — gucken wir auf das jeweils erste y-Vorzeichen
        helix_r = [b for b in rechts.bewegungen if b.typ == BewegungsTyp.LINEAR
                   and (b.kommentar is None or "Zurueck" not in b.kommentar)]
        helix_l = [b for b in links.bewegungen if b.typ == BewegungsTyp.LINEAR
                   and (b.kommentar is None or "Zurueck" not in b.kommentar)]
        assert helix_r[0].y > 0  # CCW
        assert helix_l[0].y < 0  # CW
