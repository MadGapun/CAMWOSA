"""Tests fuer Rampen-Eintauchen (Cluster J5, Issue #46)."""

from __future__ import annotations

import math

from camwosa.gcode.eintauchen import rampe_eintauchen
from camwosa.gcode.toolpath import Bewegung, BewegungsTyp, OperationsTyp, Toolpath


def _tp(bew):
    return Toolpath(
        operation_id="op", operation_typ=OperationsTyp.KONTUR, werkzeug_id="t",
        bewegungen=bew, spindel_rpm=12000, sicherheitshoehe=5.0,
    )


def _kontur_mit_plunge(z_cut=-2.0, q=(100.0, 0.0)):
    """Anfahrt → senkrechter Plunge → Schnitt → Rueckzug."""
    return [
        Bewegung(BewegungsTyp.EILGANG, 0, 0, 5),
        Bewegung(BewegungsTyp.PLUNGE, 0, 0, z_cut, feed=300),
        Bewegung(BewegungsTyp.LINEAR, q[0], q[1], z_cut, feed=800),
        Bewegung(BewegungsTyp.EILGANG, q[0], q[1], 5),
    ]


class TestRampe:
    def test_senkrechter_plunge_wird_rampe(self):
        out = rampe_eintauchen(_tp(_kontur_mit_plunge())).bewegungen
        # kein PLUNGE mehr unter Material-Oberkante (nur evtl. Luft-Plunge bis 0)
        material_plunges = [b for b in out
                            if b.typ == BewegungsTyp.PLUNGE and b.z < -1e-6]
        assert material_plunges == []
        # Rampen-Schnitte vorhanden
        assert any(b.kommentar == "Rampen-Eintauchen" for b in out)

    def test_endpunkt_treue(self):
        out = rampe_eintauchen(_tp(_kontur_mit_plunge())).bewegungen
        # Vor dem eigentlichen Schnitt nach (100,0) muss die Rampe exakt bei
        # (0,0,-2) enden.
        idx = next(i for i, b in enumerate(out)
                   if b.typ == BewegungsTyp.LINEAR and abs(b.x - 100) < 1e-6)
        davor = out[idx - 1]
        assert (round(davor.x, 6), round(davor.y, 6), round(davor.z, 6)) == (0, 0, -2)

    def test_rampen_winkel_eingehalten(self):
        out = rampe_eintauchen(_tp(_kontur_mit_plunge()), winkel_grad=5.0).bewegungen
        tan5 = math.tan(math.radians(5.0))
        prev = out[0]
        for b in out:
            if b.kommentar == "Rampen-Eintauchen":
                dxy = math.hypot(b.x - prev.x, b.y - prev.y)
                dz = abs(b.z - prev.z)
                if dxy > 1e-9:
                    assert dz / dxy <= tan5 + 1e-6
            prev = b

    def test_luft_bleibt_plunge(self):
        # Plunge 5 -> -2: der Teil 5..0 bleibt Plunge (Anfahrt bis Material)
        out = rampe_eintauchen(_tp(_kontur_mit_plunge())).bewegungen
        assert any(b.typ == BewegungsTyp.PLUNGE and abs(b.z) < 1e-6 for b in out)

    def test_rampe_bleibt_im_segment(self):
        # alle Rampen-XY liegen zwischen P=(0,0) und Q-Richtung (x>=0, y==0)
        out = rampe_eintauchen(_tp(_kontur_mit_plunge(q=(100, 0)))).bewegungen
        for b in out:
            if b.kommentar in ("Rampen-Eintauchen", "Rampen-Ende"):
                assert -1e-6 <= b.x <= 100 + 1e-6
                assert abs(b.y) < 1e-6


class TestFallback:
    def test_bohren_ohne_folgeschnitt_unveraendert(self):
        # Plunge dann Eilgang (Bohren) → keine Rampe moeglich
        bew = [
            Bewegung(BewegungsTyp.EILGANG, 0, 0, 5),
            Bewegung(BewegungsTyp.PLUNGE, 0, 0, -3, feed=200),
            Bewegung(BewegungsTyp.EILGANG, 0, 0, 5),
        ]
        tp = _tp(bew)
        assert rampe_eintauchen(tp) is tp

    def test_zu_kurzes_segment_fallback(self):
        # winkel sehr flach + sehr kurzer Folgeschnitt → zu viele Passes → Plunge
        out = rampe_eintauchen(
            _tp(_kontur_mit_plunge(z_cut=-6.0, q=(0.3, 0.0))),
            winkel_grad=2.0, max_passes=10,
        ).bewegungen
        assert any(b.typ == BewegungsTyp.PLUNGE and b.z < -1e-6 for b in out)

    def test_leerer_toolpath(self):
        tp = _tp([])
        assert rampe_eintauchen(tp) is tp


class TestMehrfach:
    def test_zwei_stepdowns_beide_gerampt(self):
        bew = [
            Bewegung(BewegungsTyp.EILGANG, 0, 0, 5),
            Bewegung(BewegungsTyp.PLUNGE, 0, 0, -2, feed=300),
            Bewegung(BewegungsTyp.LINEAR, 50, 0, -2, feed=800),
            Bewegung(BewegungsTyp.LINEAR, 0, 0, -2, feed=800),
            Bewegung(BewegungsTyp.PLUNGE, 0, 0, -4, feed=300),  # 2. Stepdown
            Bewegung(BewegungsTyp.LINEAR, 50, 0, -4, feed=800),
            Bewegung(BewegungsTyp.LINEAR, 0, 0, -4, feed=800),
            Bewegung(BewegungsTyp.EILGANG, 0, 0, 5),
        ]
        out = rampe_eintauchen(_tp(bew)).bewegungen
        # beide Material-Plunges ersetzt
        material_plunges = [b for b in out
                            if b.typ == BewegungsTyp.PLUNGE and b.z < -1e-6]
        assert material_plunges == []
        assert sum(1 for b in out if b.kommentar == "Rampen-Eintauchen") >= 2

    def test_material_oberkante_parameter(self):
        # Materialoberkante bei z=2 → ab z=2 wird gerampt
        out = rampe_eintauchen(
            _tp(_kontur_mit_plunge(z_cut=-2.0)), material_oberkante=2.0,
        ).bewegungen
        # Luft-Plunge endet bei z=2 (Materialoberkante)
        assert any(b.typ == BewegungsTyp.PLUNGE and abs(b.z - 2.0) < 1e-6 for b in out)
