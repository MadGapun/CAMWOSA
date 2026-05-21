"""Tests fuer 3D-Parallel-Strategie (Cluster I2)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from camwosa.cam.strategie_3d import (
    StepoverModus,
    Strategie3DFehler,
    Strategie3DParameter,
    berechne_steigungswinkel,
    erzeuge_3d_parallel_toolpath,
    scallop_zu_stepover,
)
from camwosa.db.models import Werkzeug, WerkzeugTyp
from camwosa.gcode.toolpath import BewegungsTyp
from camwosa.stl.heightmap import Heightmap


def _kugelfraeser(d: float = 3.0) -> Werkzeug:
    return Werkzeug(
        id="t_kugel", name=f"Kugelfraeser {d}",
        typ=WerkzeugTyp.KUGELFRAESER,
        durchmesser=d, schaft_durchmesser=d,
        schneidlaenge=12, gesamtlaenge=40, schneiden=2,
    )


def _flache_heightmap(nx=20, ny=20, aufl=1.0, z=0.0) -> Heightmap:
    return Heightmap(
        z_values=np.full((nx, ny), z, dtype=float),
        aufloesung=aufl, x_min=0.0, y_min=0.0, z_max=max(z, 0.0),
    )


def _rampe_heightmap(nx=20, ny=20, aufl=1.0) -> Heightmap:
    # Z steigt linear entlang X von 0 auf 5
    z = np.zeros((nx, ny))
    for i in range(nx):
        z[i, :] = (i / (nx - 1)) * 5.0
    return Heightmap(z_values=z, aufloesung=aufl, x_min=0.0, y_min=0.0, z_max=5.0)


def _param(**kw) -> Strategie3DParameter:
    defaults = dict(
        werkzeug_id="t_kugel", spindel_rpm=18000, vorschub=1500, eintauch_vorschub=400,
        stepover_modus=StepoverModus.DISTANZ, stepover_distanz_mm=2.0,
        bahn_winkel_grad=0.0, aufmass_mm=0.0, toleranz_mm=0.01, zickzack=True,
    )
    defaults.update(kw)
    return Strategie3DParameter(**defaults)


class TestScallopFormel:
    def test_scallop_zu_stepover_grundfall(self):
        # r=1.5, h=0.01 → stepover = 2*sqrt(2*1.5*0.01 - 0.01²) ≈ 2*sqrt(0.0299) ≈ 0.346
        so = scallop_zu_stepover(0.01, 1.5)
        assert so == pytest.approx(2 * math.sqrt(2 * 1.5 * 0.01 - 0.0001), abs=1e-6)

    def test_groessere_scallop_groesserer_stepover(self):
        klein = scallop_zu_stepover(0.005, 1.5)
        gross = scallop_zu_stepover(0.05, 1.5)
        assert gross > klein

    def test_scallop_groesser_radius_geklemmt(self):
        # h kann nicht groesser als r sein
        so = scallop_zu_stepover(10.0, 1.5)
        assert so >= 0  # kein Crash, kein negatives Ergebnis


class TestGrundfunktion:
    def test_flache_flaeche_erzeugt_bewegungen(self):
        tp = erzeuge_3d_parallel_toolpath(_flache_heightmap(), _kugelfraeser(), _param())
        assert len(tp.bewegungen) > 2
        assert tp.metadaten["strategie"] == "3d_parallel"

    def test_werkzeug_durchmesser_null_vom_modell_abgelehnt(self):
        # Das Werkzeug-Modell selbst verhindert durchmesser<=0 (Pydantic).
        # Damit ist der r<=0-Pfad in der Strategie ein defensiver Guard.
        with pytest.raises(Exception):
            _kugelfraeser(0.0)

    def test_flache_flaeche_z_konstant_grobes_raster(self):
        # Auf flacher Ebene (z=0) liegt der Ball-Center bei z=r=1.5 (exakt).
        # Bei grobem Raster (aufl=1.0, r=1.5) trifft die Dilation den Rand d=r
        # nicht → diskretes Ergebnis liegt zwischen [1.0, 1.5].
        tp = erzeuge_3d_parallel_toolpath(
            _flache_heightmap(aufl=1.0, z=0.0), _kugelfraeser(3.0), _param(),
        )
        zs = [b.z for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
        assert 0.9 <= max(zs) <= 1.6
        # konstant (flache Ebene → keine Z-Variation)
        assert max(zs) - min(zs) < 1e-6

    def test_flache_flaeche_feines_raster_konvergiert_gegen_r(self):
        # Bei feinem Raster (aufl=0.25) trifft die Dilation den Rand d=r besser
        # → Ball-Center-Z konvergiert gegen r=1.5.
        tp = erzeuge_3d_parallel_toolpath(
            _flache_heightmap(nx=40, ny=40, aufl=0.25, z=0.0),
            _kugelfraeser(3.0), _param(stepover_distanz_mm=1.0),
        )
        zs = [b.z for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
        assert max(zs) == pytest.approx(1.5, abs=0.15)


class TestStepover:
    def test_scallop_modus_feiner_als_grob(self):
        grob = erzeuge_3d_parallel_toolpath(
            _flache_heightmap(40, 40), _kugelfraeser(3),
            _param(stepover_modus=StepoverModus.DISTANZ, stepover_distanz_mm=3.0),
        )
        fein = erzeuge_3d_parallel_toolpath(
            _flache_heightmap(40, 40), _kugelfraeser(3),
            _param(stepover_modus=StepoverModus.SCALLOP, scallop_hoehe_mm=0.005),
        )
        # Feiner Scallop → mehr Bahnen → mehr Bewegungen
        assert len(fein.bewegungen) > len(grob.bewegungen)

    def test_stepover_in_metadaten(self):
        tp = erzeuge_3d_parallel_toolpath(
            _flache_heightmap(), _kugelfraeser(),
            _param(stepover_modus=StepoverModus.DISTANZ, stepover_distanz_mm=1.5),
        )
        assert tp.metadaten["stepover_mm"] == pytest.approx(1.5)


class TestAufmass:
    def test_aufmass_hebt_z_an(self):
        ohne = erzeuge_3d_parallel_toolpath(
            _flache_heightmap(z=0), _kugelfraeser(3), _param(aufmass_mm=0.0),
        )
        mit = erzeuge_3d_parallel_toolpath(
            _flache_heightmap(z=0), _kugelfraeser(3), _param(aufmass_mm=0.5),
        )
        z_ohne = max(b.z for b in ohne.bewegungen if b.typ == BewegungsTyp.LINEAR)
        z_mit = max(b.z for b in mit.bewegungen if b.typ == BewegungsTyp.LINEAR)
        assert z_mit == pytest.approx(z_ohne + 0.5, abs=0.05)


class TestBahnwinkel:
    def test_winkel_0_und_90_unterscheiden_sich(self):
        hm = _rampe_heightmap(30, 30)
        w0 = erzeuge_3d_parallel_toolpath(hm, _kugelfraeser(2), _param(bahn_winkel_grad=0))
        w90 = erzeuge_3d_parallel_toolpath(hm, _kugelfraeser(2), _param(bahn_winkel_grad=90))
        assert w0.metadaten["bahn_winkel_grad"] == 0
        assert w90.metadaten["bahn_winkel_grad"] == 90
        # Beide muessen gueltige Bahnen erzeugen
        assert len(w0.bewegungen) > 2
        assert len(w90.bewegungen) > 2


class TestToleranz:
    def test_groebere_toleranz_weniger_punkte(self):
        hm = _rampe_heightmap(40, 40)
        fein = erzeuge_3d_parallel_toolpath(hm, _kugelfraeser(2), _param(toleranz_mm=0.001))
        grob = erzeuge_3d_parallel_toolpath(hm, _kugelfraeser(2), _param(toleranz_mm=0.5))
        # Gröbere Toleranz → kollineare Punkte entfernt → weniger Bewegungen
        assert len(grob.bewegungen) <= len(fein.bewegungen)


class TestSteigungswinkel:
    def test_flache_ebene_null_grad(self):
        z = np.zeros((10, 10))
        slope = berechne_steigungswinkel(z, 1.0)
        assert np.allclose(slope, 0.0)

    def test_45_grad_rampe(self):
        # Z steigt 1mm pro 1mm in X → 45°
        z = np.zeros((10, 10))
        for i in range(10):
            z[i, :] = i * 1.0
        slope = berechne_steigungswinkel(z, 1.0)
        # Innen (nicht am Rand) sollte ~45° sein
        assert slope[5, 5] == pytest.approx(45.0, abs=1.0)

    def test_steilere_rampe_groesserer_winkel(self):
        z = np.zeros((10, 10))
        for i in range(10):
            z[i, :] = i * 3.0  # 3mm pro 1mm → arctan(3) ≈ 71.6°
        slope = berechne_steigungswinkel(z, 1.0)
        assert slope[5, 5] == pytest.approx(math.degrees(math.atan(3.0)), abs=1.0)


class TestSteilheitsTrennung:
    def _stufenflaeche(self):
        # Linke Haelfte flach (z=0), rechte Haelfte steile Rampe
        nx, ny = 40, 20
        z = np.zeros((nx, ny))
        for i in range(nx):
            if i < nx // 2:
                z[i, :] = 0.0
            else:
                z[i, :] = (i - nx // 2) * 2.0  # steil
        return Heightmap(z_values=z, aufloesung=1.0, x_min=0.0, y_min=0.0, z_max=float(z.max()))

    def test_nur_flache_bereiche(self):
        hm = self._stufenflaeche()
        # slope 0-20: nur die flache linke Haelfte
        tp = erzeuge_3d_parallel_toolpath(
            hm, _kugelfraeser(2),
            _param(bahn_winkel_grad=0, slope_min_grad=0, slope_max_grad=20),
        )
        schnitt = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
        # Alle Schnittpunkte sollten in der flachen Haelfte liegen (x < ~20)
        assert all(b.x < 25 for b in schnitt)
        assert tp.metadaten["slope_max_grad"] == 20

    def test_nur_steile_bereiche(self):
        hm = self._stufenflaeche()
        tp = erzeuge_3d_parallel_toolpath(
            hm, _kugelfraeser(2),
            _param(bahn_winkel_grad=0, slope_min_grad=20, slope_max_grad=90),
        )
        schnitt = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
        # Schnittpunkte nur in der steilen Haelfte (x > ~18)
        assert len(schnitt) > 0
        assert all(b.x > 15 for b in schnitt)

    def test_volles_fenster_wie_ohne_maske(self):
        hm = self._stufenflaeche()
        ohne = erzeuge_3d_parallel_toolpath(hm, _kugelfraeser(2), _param())
        voll = erzeuge_3d_parallel_toolpath(
            hm, _kugelfraeser(2), _param(slope_min_grad=0, slope_max_grad=90),
        )
        # 0-90° = alles → gleiche Anzahl Schnittbewegungen
        s_ohne = len([b for b in ohne.bewegungen if b.typ == BewegungsTyp.LINEAR])
        s_voll = len([b for b in voll.bewegungen if b.typ == BewegungsTyp.LINEAR])
        assert s_ohne == s_voll


class TestWerkzeugKompensation:
    def test_kugelfraeser_auf_rampe_folgt_oberflaeche(self):
        # Auf einer Rampe sollte der Z-Wert der Bahn entlang X ansteigen
        hm = _rampe_heightmap(30, 30)
        tp = erzeuge_3d_parallel_toolpath(hm, _kugelfraeser(2), _param(bahn_winkel_grad=0))
        schnitt = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
        zs = [b.z for b in schnitt]
        # Z-Werte variieren (Oberflaeche wird gefolgt), nicht konstant
        assert max(zs) - min(zs) > 1.0
