"""Tests fuer erweiterte Werkzeug-Geometrie (Segmente, Smart-Helpers)."""

from __future__ import annotations

import math

import pytest

from camwosa.db.models import (
    Werkzeug,
    WerkzeugSegment,
    WerkzeugTyp,
    berechne_v_bit_spitzendurchmesser,
    berechne_v_bit_winkel,
)


class TestSegmente:
    def test_default_segmente_aus_klassischen_feldern(self, schaftfraeser_6mm) -> None:
        segmente = schaftfraeser_6mm.effektive_segmente()
        assert len(segmente) == 2
        # Schneide-Segment unten
        assert segmente[0].ist_schneide is True
        assert segmente[0].z_unten == 0
        assert segmente[0].z_oben == schaftfraeser_6mm.schneidlaenge
        # Schaft-Segment oben
        assert segmente[1].ist_schneide is False
        assert segmente[1].z_unten == schaftfraeser_6mm.schneidlaenge

    def test_durchmesser_bei_z(self, schaftfraeser_6mm) -> None:
        # In der Schneide: Schneid-Durchmesser
        assert schaftfraeser_6mm.durchmesser_bei_z(5) == 6.0
        # Im Schaft: Schaft-Durchmesser (gleich bei Schaftfraeser)
        assert schaftfraeser_6mm.durchmesser_bei_z(50) == 6.0

    def test_gravurstichel_segmente(self) -> None:
        """Gravurstichel: 0.3mm Spitze, 3.175mm Schaft, konische Schneide."""
        stichel = Werkzeug(
            id="gravur_03_30grad",
            name="Gravurstichel 0.3 / 30°",
            typ=WerkzeugTyp.GRAVIERSTICHEL,
            durchmesser=3.175,
            schaft_durchmesser=3.175,
            schneidlaenge=6.0,
            gesamtlaenge=38.0,
            schneiden=1,
            spitzenwinkel=30.0,
            spitzendurchmesser=0.3,
            segmente=[
                WerkzeugSegment(
                    z_unten=0, z_oben=6,
                    durchmesser_unten=0.3, durchmesser_oben=3.175,
                    ist_schneide=True,
                ),
                WerkzeugSegment(
                    z_unten=6, z_oben=38,
                    durchmesser_unten=3.175, durchmesser_oben=3.175,
                    ist_schneide=False,
                ),
            ],
        )
        # Bei z=3 (mitte Konus): linear interpoliert (0.3 + (3.175-0.3)*0.5) = 1.74
        assert abs(stichel.durchmesser_bei_z(3) - 1.7375) < 0.01
        # Bei z=10 (im Schaft): voller Schaft-Durchmesser
        assert stichel.durchmesser_bei_z(10) == 3.175


class TestMaxArbeitstiefe:
    def test_default_ist_schneidlaenge(self, schaftfraeser_6mm) -> None:
        # max_arbeitstiefe_mm wird default = schneidlaenge gesetzt
        assert schaftfraeser_6mm.max_arbeitstiefe_mm == schaftfraeser_6mm.schneidlaenge

    def test_darf_in_tiefe(self, schaftfraeser_6mm) -> None:
        # schneidlaenge=22 -> max_arbeitstiefe=22
        assert schaftfraeser_6mm.darf_in_tiefe(20) is True
        assert schaftfraeser_6mm.darf_in_tiefe(-20) is True
        assert schaftfraeser_6mm.darf_in_tiefe(25) is False

    def test_explizite_max_arbeitstiefe(self) -> None:
        w = Werkzeug(
            id="x", name="x", typ=WerkzeugTyp.SCHAFTFRAESER,
            durchmesser=6, schaft_durchmesser=6, schneidlaenge=22,
            gesamtlaenge=76, schneiden=2,
            max_arbeitstiefe_mm=10,  # nur 10mm darf eintauchen
        )
        assert w.darf_in_tiefe(10) is True
        assert w.darf_in_tiefe(11) is False


class TestSmartHelpers:
    def test_v_bit_winkel_aus_geometrie(self) -> None:
        # Spitze 0.3, Durchmesser oben 3.175, Schneidlaenge 6
        # -> Halbwinkel = atan(((3.175-0.3)/2) / 6) = atan(0.2396)
        # -> Halbwinkel ~ 13.47°, Spitzenwinkel ~ 26.95°
        w = berechne_v_bit_winkel(
            spitzendurchmesser_mm=0.3,
            durchmesser_max_mm=3.175,
            schneidlaenge_mm=6,
        )
        assert abs(w - 26.95) < 0.1

    def test_v_bit_winkel_klassisch_60grad(self) -> None:
        # V-Bit mit 60°: bei 5mm Schneidlaenge ist d_oben = 2*tan(30°)*5 = 5.77mm
        # Rueckwaerts: Winkel(0, 5.77, 5) = 60°
        import math
        d_oben = 2 * math.tan(math.radians(30)) * 5
        w = berechne_v_bit_winkel(0, d_oben, 5)
        assert abs(w - 60) < 0.1

    def test_v_bit_spitzendurchmesser_echt_null(self) -> None:
        # 60° Winkel, 5mm Schneide -> bei welchem durchmesser_max ist Spitze noch 0?
        # d_oben = 2*tan(30°)*5 = ~5.77mm. Wenn durchmesser_max >= 5.77 -> Spitze = 0
        s = berechne_v_bit_spitzendurchmesser(60, 5, 12.7)
        assert s == 0.0

    def test_v_bit_spitzendurchmesser_abgestumpft(self) -> None:
        # 30° Winkel, 6mm Schneide -> d_oben = 2*tan(15°)*6 = 3.215mm
        # Wenn durchmesser_max = 3.175mm (kleiner!) -> Spitze muss > 0 sein
        s = berechne_v_bit_spitzendurchmesser(30, 6, 3.175)
        assert s < 0.05  # praktisch 0 weil knapp unter d_oben


class TestRueckwaertskompatibilitaet:
    def test_altes_werkzeug_ohne_segmente_laedt(self) -> None:
        """Alte JSON-Daten ohne segmente-Feld muessen weiter laden."""
        daten = {
            "id": "alt", "name": "Alt", "typ": "schaftfraeser",
            "durchmesser": 6, "schaft_durchmesser": 6,
            "schneidlaenge": 22, "gesamtlaenge": 76, "schneiden": 2,
        }
        w = Werkzeug.model_validate(daten)
        assert w.segmente == []
        # Trotzdem: effektive_segmente liefert sinnvolle Defaults
        assert len(w.effektive_segmente()) == 2
