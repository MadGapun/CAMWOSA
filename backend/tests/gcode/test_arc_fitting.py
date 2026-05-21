"""Tests fuer Arc-Fitting (Cluster J1)."""

from __future__ import annotations

import math

import pytest

from camwosa.gcode.arc_fitting import fitte_boegen, fitte_toolpath
from camwosa.gcode.toolpath import Bewegung, BewegungsTyp, OperationsTyp, Toolpath


def _kreis_punkte(cx, cy, r, n, start_grad=0.0, end_grad=360.0):
    """n LINEAR-Punkte auf einem Kreisbogen (ohne Startpunkt-Anfahrt)."""
    pts = []
    for k in range(n + 1):
        t = start_grad + (end_grad - start_grad) * k / n
        rad = math.radians(t)
        pts.append((cx + r * math.cos(rad), cy + r * math.sin(rad)))
    return pts


def _linear_bahn(punkte, z=-1.0, feed=500.0):
    """Baut Bewegungsliste: Eilgang zum 1. Punkt, dann LINEAR durch den Rest."""
    bew = [Bewegung(typ=BewegungsTyp.EILGANG, x=punkte[0][0], y=punkte[0][1], z=z)]
    for (x, y) in punkte[1:]:
        bew.append(Bewegung(typ=BewegungsTyp.LINEAR, x=x, y=y, z=z, feed=feed))
    return bew


class TestKreisFit:
    def test_voller_kreis_wird_zu_wenigen_boegen(self):
        # 64-Segment-Kreis (Halbkreis-Bogen max 340°) → deutlich weniger Bewegungen
        pts = _kreis_punkte(0, 0, 10, 64)
        bew = _linear_bahn(pts)
        gefittet = fitte_boegen(bew, toleranz_mm=0.05)
        # Vorher: 1 Eilgang + 64 LINEAR = 65. Nachher viel weniger.
        assert len(gefittet) < len(bew) / 3
        # mind. ein Bogen drin
        assert any(b.typ in (BewegungsTyp.BOGEN_CW, BewegungsTyp.BOGEN_CCW) for b in gefittet)

    def test_bogen_hat_ij_zentrum(self):
        pts = _kreis_punkte(5, 3, 8, 48, 0, 180)  # Halbkreis um (5,3)
        bew = _linear_bahn(pts)
        gefittet = fitte_boegen(bew, toleranz_mm=0.05)
        bogen = next(b for b in gefittet if b.typ in (BewegungsTyp.BOGEN_CW, BewegungsTyp.BOGEN_CCW))
        # i/j relativ zum Startpunkt → absolutes Zentrum
        startpunkt = pts[0]
        cx = startpunkt[0] + bogen.i
        cy = startpunkt[1] + bogen.j
        assert cx == pytest.approx(5, abs=0.2)
        assert cy == pytest.approx(3, abs=0.2)

    def test_ccw_richtung_erkannt(self):
        # Gegen-Uhrzeigersinn (Winkel steigend) → BOGEN_CCW (G3)
        pts = _kreis_punkte(0, 0, 10, 32, 0, 90)
        bew = _linear_bahn(pts)
        gefittet = fitte_boegen(bew, toleranz_mm=0.05)
        boegen = [b for b in gefittet if b.typ in (BewegungsTyp.BOGEN_CW, BewegungsTyp.BOGEN_CCW)]
        assert boegen
        assert boegen[0].typ == BewegungsTyp.BOGEN_CCW

    def test_cw_richtung_erkannt(self):
        # Im Uhrzeigersinn (Winkel fallend) → BOGEN_CW (G2)
        pts = _kreis_punkte(0, 0, 10, 32, 90, 0)
        bew = _linear_bahn(pts)
        gefittet = fitte_boegen(bew, toleranz_mm=0.05)
        boegen = [b for b in gefittet if b.typ in (BewegungsTyp.BOGEN_CW, BewegungsTyp.BOGEN_CCW)]
        assert boegen
        assert boegen[0].typ == BewegungsTyp.BOGEN_CW


class TestKeinFalscherFit:
    def test_gerade_linie_bleibt_linear(self):
        # Eine Gerade darf NICHT zu einem Bogen werden
        pts = [(0, 0), (10, 0), (20, 0), (30, 0), (40, 0), (50, 0)]
        bew = _linear_bahn(pts)
        gefittet = fitte_boegen(bew, toleranz_mm=0.05)
        assert not any(
            b.typ in (BewegungsTyp.BOGEN_CW, BewegungsTyp.BOGEN_CCW) for b in gefittet
        )

    def test_eilgang_und_plunge_unveraendert(self):
        bew = [
            Bewegung(typ=BewegungsTyp.EILGANG, x=0, y=0, z=5),
            Bewegung(typ=BewegungsTyp.PLUNGE, x=0, y=0, z=-1, feed=100),
            Bewegung(typ=BewegungsTyp.EILGANG, x=10, y=10, z=5),
        ]
        gefittet = fitte_boegen(bew)
        assert len(gefittet) == 3
        assert gefittet[1].typ == BewegungsTyp.PLUNGE

    def test_variables_z_wird_nicht_gefittet(self):
        # 3D-Bahn (Z variiert) → kein 2D-Bogen-Fit
        bew = [Bewegung(typ=BewegungsTyp.EILGANG, x=10, y=0, z=0)]
        pts = _kreis_punkte(0, 0, 10, 32)
        for k, (x, y) in enumerate(pts[1:]):
            bew.append(Bewegung(typ=BewegungsTyp.LINEAR, x=x, y=y, z=-k * 0.1, feed=500))
        gefittet = fitte_boegen(bew, toleranz_mm=0.05)
        # variables Z → keine Boegen
        assert not any(
            b.typ in (BewegungsTyp.BOGEN_CW, BewegungsTyp.BOGEN_CCW) for b in gefittet
        )

    def test_zu_kurze_folge_bleibt_linear(self):
        # nur 2 Segmente → unter min_segmente
        pts = _kreis_punkte(0, 0, 10, 2, 0, 30)
        bew = _linear_bahn(pts)
        gefittet = fitte_boegen(bew, min_segmente=4)
        assert not any(
            b.typ in (BewegungsTyp.BOGEN_CW, BewegungsTyp.BOGEN_CCW) for b in gefittet
        )


class TestEndpunktTreue:
    def test_endpunkt_bleibt_erhalten(self):
        # Der letzte Punkt der Bahn muss nach dem Fit identisch sein
        pts = _kreis_punkte(0, 0, 10, 48, 0, 270)
        bew = _linear_bahn(pts)
        gefittet = fitte_boegen(bew, toleranz_mm=0.05)
        assert gefittet[-1].x == pytest.approx(pts[-1][0], abs=1e-6)
        assert gefittet[-1].y == pytest.approx(pts[-1][1], abs=1e-6)


class TestToolpathConvenience:
    def test_fitte_toolpath_setzt_metadaten(self):
        pts = _kreis_punkte(0, 0, 10, 64)
        tp = Toolpath(
            operation_id="op", operation_typ=OperationsTyp.KONTUR,
            werkzeug_id="t", bewegungen=_linear_bahn(pts),
            spindel_rpm=12000, sicherheitshoehe=5,
        )
        neu = fitte_toolpath(tp, toleranz_mm=0.05)
        assert neu.metadaten["arc_fitted"] is True
        assert neu.metadaten["arc_fit_bewegungen_nachher"] < neu.metadaten["arc_fit_bewegungen_vorher"]
        # Original unveraendert
        assert "arc_fitted" not in tp.metadaten
