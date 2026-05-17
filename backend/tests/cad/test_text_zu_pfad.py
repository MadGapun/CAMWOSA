"""Tests fuer Text-zu-Pfad-Konverter (Master-Plan A37)."""

from __future__ import annotations

from pathlib import Path

import pytest

from camwosa.cad.text_zu_pfad import (
    FONT_FALLBACK,
    FontFehler,
    TextPfadParameter,
    polygone_zu_punktlisten,
    text_bounding_box,
    text_zu_pfade,
)


def _verfuegbarer_font() -> str | None:
    """Sucht den ersten verfuegbaren Default-Font, sonst None."""
    for kandidat in FONT_FALLBACK:
        if Path(kandidat).is_file():
            return kandidat
    return None


HAT_FONT = _verfuegbarer_font() is not None


@pytest.mark.skipif(not HAT_FONT, reason="Kein TTF im System verfuegbar")
class TestBasis:
    def test_einfacher_text_gibt_polygone(self):
        polygone = text_zu_pfade("A")
        assert len(polygone) > 0
        # Polygon-Flaeche > 0
        assert all(p.area > 0 for p in polygone)

    def test_leerer_text_liefert_leere_liste(self):
        assert text_zu_pfade("") == []

    def test_hoehe_skaliert_korrekt(self):
        klein = text_zu_pfade("A", TextPfadParameter(hoehe_mm=5.0))
        gross = text_zu_pfade("A", TextPfadParameter(hoehe_mm=15.0))
        # Gross-Polygon soll 3x groessere Bounding-Box haben
        b_klein = klein[0].bounds  # (minx, miny, maxx, maxy)
        b_gross = gross[0].bounds
        verh = (b_gross[3] - b_gross[1]) / (b_klein[3] - b_klein[1])
        assert verh == pytest.approx(3.0, rel=0.1)

    def test_mehrere_buchstaben_horizontal_versetzt(self):
        # "AB" — B muss rechts von A liegen
        polygone = text_zu_pfade("AB")
        # Mindestens 2 Polygone (eines pro Buchstabe, B koennte mit Loechern dazukommen)
        assert len(polygone) >= 2
        # X-min des B muss > X-max des A sein
        # Wir nehmen das linkste vs. rechtste Polygon
        x_mins = sorted(p.bounds[0] for p in polygone)
        x_maxs = sorted(p.bounds[2] for p in polygone)
        assert x_mins[-1] > x_mins[0]  # Versatz vorhanden


@pytest.mark.skipif(not HAT_FONT, reason="Kein TTF im System verfuegbar")
class TestLoecher:
    def test_o_hat_loch(self):
        """Buchstabe O sollte als Polygon mit einem Loch dargestellt sein."""
        polygone = text_zu_pfade("O")
        # Mindestens ein Polygon mit Innenring
        hat_loch = any(len(list(p.interiors)) >= 1 for p in polygone)
        assert hat_loch, "Buchstabe O sollte mindestens 1 Loch haben"

    def test_p_hat_loch(self):
        polygone = text_zu_pfade("P")
        hat_loch = any(len(list(p.interiors)) >= 1 for p in polygone)
        assert hat_loch, "Buchstabe P sollte 1 Loch haben"

    def test_x_hat_kein_loch(self):
        polygone = text_zu_pfade("X")
        # X ist ein einfaches Polygon ohne Loecher
        loecher_total = sum(len(list(p.interiors)) for p in polygone)
        assert loecher_total == 0


@pytest.mark.skipif(not HAT_FONT, reason="Kein TTF im System verfuegbar")
class TestBoundingBox:
    def test_bounding_box_korrekt(self):
        bbox = text_bounding_box("CAM", TextPfadParameter(hoehe_mm=10.0))
        x_min, y_min, x_max, y_max = bbox
        # Hoehe sollte ungefaehr 10mm sein
        assert (y_max - y_min) == pytest.approx(10.0, rel=0.2)
        # Breite > Hoehe (CAM ist breiter als hoch)
        assert (x_max - x_min) > (y_max - y_min)
        # Start nahe x_min = 0 — LSB (Left Side Bearing) kann etwas Versatz geben
        assert x_min == pytest.approx(0.0, abs=2.0)
        assert x_min >= 0  # nie negativ

    def test_leerer_text_bbox_null(self):
        bbox = text_bounding_box("")
        assert bbox == (0.0, 0.0, 0.0, 0.0)


@pytest.mark.skipif(not HAT_FONT, reason="Kein TTF im System verfuegbar")
class TestKonvertierung:
    def test_polygone_zu_punktlisten(self):
        polygone = text_zu_pfade("O")
        punktlisten = polygone_zu_punktlisten(polygone)
        # Mindestens eine Liste (Aussenkontur) + eine Insel
        assert len(punktlisten) >= 2
        # Jede Punktliste ist nicht leer und besteht aus Tupeln (x, y)
        for liste in punktlisten:
            assert len(liste) >= 3
            assert len(liste[0]) == 2


class TestFontHandling:
    def test_falscher_font_pfad_raises(self):
        with pytest.raises(FontFehler):
            text_zu_pfade("X", TextPfadParameter(
                font_pfad="C:/Quatsch/nichts.ttf"))


@pytest.mark.skipif(not HAT_FONT, reason="Kein TTF im System verfuegbar")
class TestMehrzeilig:
    def test_zwei_zeilen_y_versatz(self):
        polygone = text_zu_pfade("A\nB",
                                  TextPfadParameter(hoehe_mm=10.0, zeilen_abstand_faktor=1.5))
        # Mindestens 2 Buchstaben → mindestens 2 Polygone
        assert len(polygone) >= 2
        # Mindestens eine Y-Bewegung zwischen den Zeilen
        y_mittelpunkte = [(p.bounds[1] + p.bounds[3]) / 2 for p in polygone]
        # Es gibt mindestens 2 unterschiedliche Y-Cluster
        spanne = max(y_mittelpunkte) - min(y_mittelpunkte)
        assert spanne > 5  # mindestens 5mm Versatz