"""Tests fuer Circular + Radial Pocketing."""

from __future__ import annotations

import math

import pytest

from camwosa.cam.circular_radial import (
    CircularPocketParameter,
    RadialPocketParameter,
    circular_pocket_pfade,
    radial_pocket_pfade,
)


class TestCircularPocket:
    def test_minimum_pfade_fuer_einfachen_kreis(self):
        pfade = circular_pocket_pfade(CircularPocketParameter(
            aussen_radius=20.0, werkzeug_durchmesser=3.0,
            stepover_prozent=50,  # 1.5 mm pro Step
        ))
        # 20 - 1.5 (werkzeug-radius) = 18.5 max-Radius
        # 18.5 / 1.5 ≈ 12 Pfade plus Mittelpunkt = ~13
        assert len(pfade) >= 10
        # Mittelpunkt-"Pfad" hat nur einen Punkt
        assert len(pfade[-1]) == 1

    def test_radien_monoton_kleiner_von_aussen_nach_innen(self):
        pfade = circular_pocket_pfade(CircularPocketParameter(
            aussen_radius=20.0, werkzeug_durchmesser=3.0,
            stepover_prozent=40,
            von_aussen_nach_innen=True,
        ))
        # Erster Punkt jedes Pfads liegt auf Radius — der nimmt monoton ab
        radien = []
        for pfad in pfade:
            x, y = pfad[0]
            radien.append(math.hypot(x, y))
        for i in range(1, len(radien)):
            assert radien[i] <= radien[i - 1] + 1e-9

    def test_richtungsumkehr_funktioniert(self):
        aussen = circular_pocket_pfade(CircularPocketParameter(
            aussen_radius=20, werkzeug_durchmesser=3, von_aussen_nach_innen=True,
        ))
        innen = circular_pocket_pfade(CircularPocketParameter(
            aussen_radius=20, werkzeug_durchmesser=3, von_aussen_nach_innen=False,
        ))
        # Erstes Element bei "aussen-nach-innen" ist Aussenkreis,
        # bei "innen-nach-aussen" ist Mittelpunkt
        assert len(aussen[0]) > len(innen[0])
        assert len(innen[0]) == 1  # Mittelpunkt
        assert len(aussen[-1]) == 1  # Mittelpunkt am Ende

    def test_zu_kleiner_radius_liefert_leer(self):
        # Werkzeug groesser als Tasche
        pfade = circular_pocket_pfade(CircularPocketParameter(
            aussen_radius=1.0, werkzeug_durchmesser=10.0,
        ))
        assert pfade == []

    def test_mittelpunkt_offset_funktioniert(self):
        pfade = circular_pocket_pfade(CircularPocketParameter(
            mittelpunkt_x=100, mittelpunkt_y=50,
            aussen_radius=10, werkzeug_durchmesser=2, stepover_prozent=50,
        ))
        # Erster Punkt des ersten Pfads
        x, y = pfade[0][0]
        # Sollte auf Kreis um (100, 50) liegen
        r = math.hypot(x - 100, y - 50)
        assert r == pytest.approx(9.0, abs=0.01)  # aussen_radius - werkzeug_radius

    def test_aufmass_reduziert_aussen_radius(self):
        ohne = circular_pocket_pfade(CircularPocketParameter(
            aussen_radius=20, werkzeug_durchmesser=3, fertigungs_aufmass=0,
        ))
        mit = circular_pocket_pfade(CircularPocketParameter(
            aussen_radius=20, werkzeug_durchmesser=3, fertigungs_aufmass=0.5,
        ))
        # Mit Aufmass: erster Aussenradius kleiner
        r_ohne = math.hypot(*ohne[0][0])
        r_mit = math.hypot(*mit[0][0])
        assert r_mit < r_ohne
        assert r_ohne - r_mit == pytest.approx(0.5, abs=0.01)


class TestRadialPocket:
    def test_anzahl_speichen_korrekt(self):
        pfade = radial_pocket_pfade(RadialPocketParameter(
            aussen_radius=20, werkzeug_durchmesser=3, anzahl_speichen=12,
        ))
        assert len(pfade) == 12

    def test_jede_speiche_hat_zwei_punkte(self):
        pfade = radial_pocket_pfade(RadialPocketParameter(
            aussen_radius=20, werkzeug_durchmesser=3, anzahl_speichen=8,
        ))
        for pfad in pfade:
            assert len(pfad) == 2

    def test_speichen_starten_am_mittelpunkt(self):
        pfade = radial_pocket_pfade(RadialPocketParameter(
            mittelpunkt_x=10, mittelpunkt_y=20,
            aussen_radius=15, werkzeug_durchmesser=2, anzahl_speichen=6,
        ))
        for pfad in pfade:
            assert pfad[0] == (10, 20)

    def test_speichen_winkelmaessig_gleich_verteilt(self):
        pfade = radial_pocket_pfade(RadialPocketParameter(
            aussen_radius=10, werkzeug_durchmesser=1, anzahl_speichen=4,
        ))
        # 4 Speichen = 0°, 90°, 180°, 270°
        winkel = []
        for pfad in pfade:
            (cx, cy), (ex, ey) = pfad
            winkel.append(math.degrees(math.atan2(ey - cy, ex - cx)) % 360)
        winkel.sort()
        for i, soll in enumerate([0, 90, 180, 270]):
            assert winkel[i] == pytest.approx(soll, abs=0.01)

    def test_alle_speichen_gleicher_radius(self):
        pfade = radial_pocket_pfade(RadialPocketParameter(
            aussen_radius=15, werkzeug_durchmesser=3, anzahl_speichen=16,
        ))
        erwartet = 15 - 1.5  # aussen - werkzeug_radius
        for pfad in pfade:
            (cx, cy), (ex, ey) = pfad
            r = math.hypot(ex - cx, ey - cy)
            assert r == pytest.approx(erwartet, abs=1e-6)

    def test_zu_kleiner_radius_liefert_leer(self):
        pfade = radial_pocket_pfade(RadialPocketParameter(
            aussen_radius=1.0, werkzeug_durchmesser=5.0, anzahl_speichen=12,
        ))
        assert pfade == []
