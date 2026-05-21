"""Tests fuer Planfraesen (Cluster I1)."""

from __future__ import annotations

import pytest

from camwosa.cam.planfraesen import (
    PlanfraesFehler,
    PlanfraesParameter,
    PlanfraesRichtung,
    aus_z_grid_befund,
    erzeuge_planfraes_toolpath,
)
from camwosa.db.models import Werkzeug, WerkzeugTyp
from camwosa.gcode.toolpath import BewegungsTyp


def _planfraeser(d: float = 6.0) -> Werkzeug:
    return Werkzeug(
        id="t_plan", name=f"Planfraeser {d}",
        typ=WerkzeugTyp.SCHAFTFRAESER,
        durchmesser=d, schaft_durchmesser=d,
        schneidlaenge=15, gesamtlaenge=40, schneiden=2,
    )


def _param(**kw) -> PlanfraesParameter:
    defaults = dict(
        werkzeug_id="t_plan", spindel_rpm=18000, vorschub=2000, eintauch_vorschub=600,
        x_min=0, y_min=0, x_max=100, y_max=80,
        z_start=0.0, abtrag=1.0, maximaler_stepdown=0.5,
        stepover_prozent=70, ueberstand_mm=2.0,
    )
    defaults.update(kw)
    return PlanfraesParameter(**defaults)


class TestGrundfunktion:
    def test_erzeugt_bewegungen(self):
        tp = erzeuge_planfraes_toolpath(_planfraeser(), _param())
        assert len(tp.bewegungen) > 4
        assert tp.metadaten["strategie"] == "planfraesen"

    def test_z_paesse_aus_abtrag(self):
        # 2 mm Abtrag, 0.5 mm Stepdown → 4 Pässe
        tp = erzeuge_planfraes_toolpath(_planfraeser(), _param(abtrag=2.0, maximaler_stepdown=0.5))
        assert tp.metadaten["z_paesse"] == 4

    def test_ein_zpass_bei_kleinem_abtrag(self):
        tp = erzeuge_planfraes_toolpath(_planfraeser(), _param(abtrag=0.3, maximaler_stepdown=1.0))
        assert tp.metadaten["z_paesse"] == 1

    def test_tiefste_z_erreicht_abtrag(self):
        tp = erzeuge_planfraes_toolpath(_planfraeser(), _param(abtrag=1.0, maximaler_stepdown=0.5))
        min_z = min(b.z for b in tp.bewegungen)
        assert min_z == pytest.approx(-1.0)

    def test_stepover_aus_durchmesser(self):
        tp = erzeuge_planfraes_toolpath(_planfraeser(6.0), _param(stepover_prozent=70))
        # 6 * 0.7 = 4.2 mm
        assert tp.metadaten["stepover_mm"] == pytest.approx(4.2)


class TestRichtung:
    def test_x_richtung_bahnen_variieren_y(self):
        tp = erzeuge_planfraes_toolpath(_planfraeser(), _param(richtung=PlanfraesRichtung.X))
        # In X-Richtung: aufeinanderfolgende Schnittbahnen haben unterschiedliche Y
        linear = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
        ys = {round(b.y, 1) for b in linear}
        assert len(ys) > 1

    def test_y_richtung(self):
        tp = erzeuge_planfraes_toolpath(_planfraeser(), _param(richtung=PlanfraesRichtung.Y))
        assert tp.metadaten["strategie"] == "planfraesen"


class TestUeberstand:
    def test_ueberstand_erweitert_bahn_ueber_kante(self):
        tp = erzeuge_planfraes_toolpath(_planfraeser(), _param(
            x_min=0, x_max=100, ueberstand_mm=3.0, richtung=PlanfraesRichtung.X,
        ))
        xs = [b.x for b in tp.bewegungen]
        assert min(xs) <= -3.0 + 1e-9  # faehrt links ueber die Kante
        assert max(xs) >= 103.0 - 1e-9  # und rechts


class TestFehler:
    def test_ungueltiges_rechteck_wirft(self):
        with pytest.raises(PlanfraesFehler):
            erzeuge_planfraes_toolpath(_planfraeser(), _param(x_min=100, x_max=50))


class TestZGridSynergie:
    def test_aus_z_grid_befund_setzt_abtrag(self):
        p = aus_z_grid_befund(
            "t_plan", 0, 0, 200, 200, z_spreizung_mm=0.8,
        )
        # Abtrag etwas groesser als Spreizung
        assert p.abtrag == pytest.approx(1.0)
        assert p.x_max == 200

    def test_aus_z_grid_minimaler_abtrag(self):
        p = aus_z_grid_befund("t_plan", 0, 0, 100, 100, z_spreizung_mm=0.0)
        assert p.abtrag >= 0.2

    def test_aus_z_grid_param_ist_gueltig(self):
        p = aus_z_grid_befund("t_plan", 0, 0, 100, 100, z_spreizung_mm=1.5)
        # muss eine lauffaehige Operation erzeugen
        tp = erzeuge_planfraes_toolpath(_planfraeser(), p)
        assert len(tp.bewegungen) > 0
