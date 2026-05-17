"""Tests fuer Spannmittel-Modell (A47 / Cluster H)."""

from __future__ import annotations

import pytest

from camwosa.db.spannmittel import (
    Spannmittel,
    SpannmittelTyp,
    pruefe_toolpath_gegen_spannmittel,
    punkt_in_sperrzone,
)


class TestSpannmittelBasics:
    def test_create_schraubzwinge(self):
        sp = Spannmittel(
            id="zw1", typ=SpannmittelTyp.SCHRAUBZWINGE,
            position_x=50, position_y=10,
            sicherheits_radius_mm=15,
            hoehe_mm=80,
        )
        assert sp.typ == SpannmittelTyp.SCHRAUBZWINGE
        assert sp.position_x == 50

    def test_vakuum_ohne_sperrbereich(self):
        sp = Spannmittel(
            id="vak", typ=SpannmittelTyp.VAKUUM_TISCH,
            position_x=0, position_y=0,
            sicherheits_radius_mm=0,
        )
        # Vakuum hat keinen Sperrbereich
        assert not punkt_in_sperrzone(sp, 100, 100)


class TestSperrzone:
    def test_punkt_in_radius(self):
        sp = Spannmittel(
            id="zw", typ=SpannmittelTyp.SCHRAUBZWINGE,
            position_x=50, position_y=50,
            sicherheits_radius_mm=10,
        )
        assert punkt_in_sperrzone(sp, 50, 50)
        assert punkt_in_sperrzone(sp, 55, 55)  # innerhalb
        assert not punkt_in_sperrzone(sp, 70, 70)  # ausserhalb

    def test_punkt_in_box(self):
        sp = Spannmittel(
            id="ts", typ=SpannmittelTyp.T_NUT,
            position_x=100, position_y=100,
            sicherheits_box_x_mm=40, sicherheits_box_y_mm=20,
        )
        assert punkt_in_sperrzone(sp, 100, 100)
        assert punkt_in_sperrzone(sp, 119, 109)  # Innen Box
        assert not punkt_in_sperrzone(sp, 121, 100)  # Aussen Box X

    def test_z_ueber_spannmittel_kein_problem(self):
        sp = Spannmittel(
            id="zw", typ=SpannmittelTyp.SCHRAUBZWINGE,
            position_x=50, position_y=50,
            sicherheits_radius_mm=10,
            position_z=0, hoehe_mm=50,
        )
        # Z=60 ist UEBER der Zwinge (hoehe 50) — Cutter sicher
        assert not punkt_in_sperrzone(sp, 50, 50, z=60)
        # Z=30 ist INNERHALB der Zwinge — Sperre
        assert punkt_in_sperrzone(sp, 50, 50, z=30)

    def test_cutter_radius_macht_zone_groesser(self):
        sp = Spannmittel(
            id="zw", typ=SpannmittelTyp.SCHRAUBZWINGE,
            position_x=50, position_y=50,
            sicherheits_radius_mm=10,
        )
        # Punkt bei 12mm Distanz — radius 10, also OK
        assert not punkt_in_sperrzone(sp, 50, 62)
        # Mit Cutter-Radius 3 wird die Zone 13mm — Punkt jetzt in Zone
        assert punkt_in_sperrzone(sp, 50, 62, cutter_radius=3)


class TestPruefeToolpath:
    def test_keine_kollision(self):
        from camwosa.gcode.toolpath import Bewegung, BewegungsTyp
        bewegungen = [
            Bewegung(BewegungsTyp.LINEAR, x=10, y=10, z=-2, feed=600),
            Bewegung(BewegungsTyp.LINEAR, x=20, y=20, z=-2, feed=600),
        ]
        spannmittel = [
            Spannmittel(id="zw", typ=SpannmittelTyp.SCHRAUBZWINGE,
                        position_x=80, position_y=80, sicherheits_radius_mm=10),
        ]
        fehler = pruefe_toolpath_gegen_spannmittel(bewegungen, spannmittel, 3.0)
        assert fehler == []

    def test_kollision_erkannt(self):
        from camwosa.gcode.toolpath import Bewegung, BewegungsTyp
        bewegungen = [
            Bewegung(BewegungsTyp.LINEAR, x=80, y=80, z=-2, feed=600),
        ]
        spannmittel = [
            Spannmittel(id="zw", typ=SpannmittelTyp.SCHRAUBZWINGE,
                        position_x=80, position_y=80, sicherheits_radius_mm=10,
                        hoehe_mm=50),
        ]
        fehler = pruefe_toolpath_gegen_spannmittel(bewegungen, spannmittel, 3.0)
        assert len(fehler) == 1
        assert "Sperrzone" in fehler[0][1]
