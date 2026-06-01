"""Tests fuer Bearbeitungszeit-Schaetzung (Cluster K5)."""

from __future__ import annotations

import pytest

from camwosa.gcode.toolpath import Bewegung, BewegungsTyp, OperationsTyp, Toolpath
from camwosa.gcode.zeit_schaetzung import (
    formatiere_dauer,
    schaetze_job_zeit,
    schaetze_toolpath_zeit,
)


def _tp(bewegungen, werkzeug_id="t1"):
    return Toolpath(
        operation_id="op", operation_typ=OperationsTyp.KONTUR,
        werkzeug_id=werkzeug_id, bewegungen=bewegungen,
        spindel_rpm=12000, sicherheitshoehe=5,
    )


class TestFormatiereDauer:
    def test_sekunden(self):
        assert formatiere_dauer(45) == "45 Sek"

    def test_minuten_sekunden(self):
        assert formatiere_dauer(125) == "2 Min 5 Sek"

    def test_stunde(self):
        assert formatiere_dauer(3661) == "1 Std 1 Min"

    def test_grosse_minuten_ohne_sekunden(self):
        # >10 Min → Sekunden weggelassen (Groessenordnung)
        assert formatiere_dauer(20 * 60 + 30) == "20 Min"

    def test_unter_einer_sekunde(self):
        assert formatiere_dauer(0.3) == "unter 1 Sek"


class TestToolpathZeit:
    def test_reine_schnittbahn(self):
        # 100 mm bei 1000 mm/min = 0.1 min = 6 s, * overhead 1.0
        bew = [
            Bewegung(BewegungsTyp.LINEAR, 0, 0, -1, feed=1000),
            Bewegung(BewegungsTyp.LINEAR, 100, 0, -1, feed=1000),
        ]
        z = schaetze_toolpath_zeit(_tp(bew), eilgang_mm_min=3000, overhead_faktor=1.0)
        assert z.schnitt_sekunden == pytest.approx(6.0, abs=0.01)
        assert z.eilgang_sekunden == 0.0

    def test_eilgang_getrennt(self):
        bew = [
            Bewegung(BewegungsTyp.EILGANG, 0, 0, 5),
            Bewegung(BewegungsTyp.EILGANG, 300, 0, 5),  # 300mm @ 3000 = 6s
        ]
        z = schaetze_toolpath_zeit(_tp(bew), eilgang_mm_min=3000, overhead_faktor=1.0)
        assert z.eilgang_sekunden == pytest.approx(6.0, abs=0.01)
        assert z.schnitt_sekunden == 0.0

    def test_overhead_faktor_verlaengert(self):
        bew = [
            Bewegung(BewegungsTyp.LINEAR, 0, 0, -1, feed=1000),
            Bewegung(BewegungsTyp.LINEAR, 100, 0, -1, feed=1000),
        ]
        ohne = schaetze_toolpath_zeit(_tp(bew), eilgang_mm_min=3000, overhead_faktor=1.0)
        mit = schaetze_toolpath_zeit(_tp(bew), eilgang_mm_min=3000, overhead_faktor=1.2)
        assert mit.schnitt_sekunden == pytest.approx(ohne.schnitt_sekunden * 1.2)

    def test_fallback_vorschub_bei_fehlendem_feed(self):
        bew = [
            Bewegung(BewegungsTyp.LINEAR, 0, 0, -1, feed=None),
            Bewegung(BewegungsTyp.LINEAR, 100, 0, -1, feed=None),
        ]
        z = schaetze_toolpath_zeit(
            _tp(bew), eilgang_mm_min=3000, overhead_faktor=1.0,
            fallback_vorschub_mm_min=600,
        )
        # 100mm @ 600 = 10s
        assert z.schnitt_sekunden == pytest.approx(10.0, abs=0.01)

    def test_gesamt_und_klartext(self):
        bew = [
            Bewegung(BewegungsTyp.LINEAR, 0, 0, -1, feed=600),
            Bewegung(BewegungsTyp.LINEAR, 600, 0, -1, feed=600),  # 60s
        ]
        z = schaetze_toolpath_zeit(_tp(bew), eilgang_mm_min=3000, overhead_faktor=1.0)
        assert z.gesamt_sekunden == pytest.approx(60.0, abs=0.1)
        assert "Min" in z.klartext

    def test_leerer_toolpath(self):
        z = schaetze_toolpath_zeit(_tp([]), eilgang_mm_min=3000)
        assert z.gesamt_sekunden == 0.0

    def test_ungueltiger_eilgang_wirft(self):
        with pytest.raises(ValueError):
            schaetze_toolpath_zeit(_tp([]), eilgang_mm_min=0)


class TestJobZeit:
    def test_aggregiert_mehrere_ops(self):
        bew = [
            Bewegung(BewegungsTyp.LINEAR, 0, 0, -1, feed=600),
            Bewegung(BewegungsTyp.LINEAR, 600, 0, -1, feed=600),  # 60s je Op
        ]
        z = schaetze_job_zeit(
            [_tp(bew, "t1"), _tp(bew, "t1")],
            eilgang_mm_min=3000, overhead_faktor=1.0,
        )
        # 2x 60s, kein Werkzeugwechsel (gleiches Werkzeug)
        assert z.schnitt_sekunden == pytest.approx(120.0, abs=0.1)
        assert z.pausen_sekunden == 0.0

    def test_werkzeugwechsel_pause(self):
        bew = [
            Bewegung(BewegungsTyp.LINEAR, 0, 0, -1, feed=600),
            Bewegung(BewegungsTyp.LINEAR, 600, 0, -1, feed=600),
        ]
        z = schaetze_job_zeit(
            [_tp(bew, "t1"), _tp(bew, "t2")],  # Werkzeugwechsel zwischen t1 und t2
            eilgang_mm_min=3000, overhead_faktor=1.0,
            werkzeugwechsel_sekunden=45,
        )
        assert z.pausen_sekunden == pytest.approx(45.0)

    def test_leerer_job(self):
        z = schaetze_job_zeit([], eilgang_mm_min=3000)
        assert z.gesamt_sekunden == 0.0
