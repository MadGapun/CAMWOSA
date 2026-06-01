"""Tests fuer 3D-Parallel-Strategie (Cluster I2)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from camwosa.cam.strategie_3d import (
    StepoverModus,
    Strategie3DFehler,
    Strategie3DParameter,
    _werkzeug_kernel_offsets,
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


class TestScallop3D:
    def _rampe(self, steigung_pro_mm: float, aufl=0.5, nx=80, ny=20):
        # feines Raster, damit der Scallop-Stepover groesser als aufl ist
        # und die cos-Skalierung sichtbar wird.
        z = np.zeros((nx, ny))
        for i in range(nx):
            z[i, :] = i * aufl * steigung_pro_mm
        return Heightmap(z_values=z, aufloesung=aufl, x_min=0.0, y_min=0.0, z_max=float(z.max()))

    def _flach_fein(self, aufl=0.5, n=80):
        return Heightmap(
            z_values=np.zeros((n, n)), aufloesung=aufl, x_min=0.0, y_min=0.0, z_max=0.0,
        )

    def test_scallop_3d_auf_flach_wie_scallop(self):
        # Auf flacher Flaeche: cos(0)=1 → SCALLOP_3D ~ SCALLOP (gleiche Bahn-Anzahl)
        hm = self._flach_fein()
        s2d = erzeuge_3d_parallel_toolpath(
            hm, _kugelfraeser(4),
            _param(stepover_modus=StepoverModus.SCALLOP, scallop_hoehe_mm=0.1, bahn_winkel_grad=0),
        )
        s3d = erzeuge_3d_parallel_toolpath(
            hm, _kugelfraeser(4),
            _param(stepover_modus=StepoverModus.SCALLOP_3D, scallop_hoehe_mm=0.1, bahn_winkel_grad=0),
        )
        n2d = len([b for b in s2d.bewegungen if b.typ == BewegungsTyp.PLUNGE])
        n3d = len([b for b in s3d.bewegungen if b.typ == BewegungsTyp.PLUNGE])
        assert abs(n2d - n3d) <= max(2, n2d // 10)

    def test_scallop_3d_auf_steil_mehr_bahnen(self):
        # Rampe steigt in X (bahn_winkel 90 = Bahnen entlang Y, Stepover in X).
        hm = self._rampe(steigung_pro_mm=2.0)  # arctan(2) ≈ 63° steil
        s2d = erzeuge_3d_parallel_toolpath(
            hm, _kugelfraeser(4),
            _param(stepover_modus=StepoverModus.SCALLOP, scallop_hoehe_mm=0.1, bahn_winkel_grad=90),
        )
        s3d = erzeuge_3d_parallel_toolpath(
            hm, _kugelfraeser(4),
            _param(stepover_modus=StepoverModus.SCALLOP_3D, scallop_hoehe_mm=0.1, bahn_winkel_grad=90),
        )
        # 3D-Scallop macht auf der steilen Rampe engere Bahnen → mehr Bahnen
        n2d = len([b for b in s2d.bewegungen if b.typ == BewegungsTyp.PLUNGE])
        n3d = len([b for b in s3d.bewegungen if b.typ == BewegungsTyp.PLUNGE])
        assert n3d > n2d

    def test_scallop_3d_metadaten(self):
        hm = self._flach_fein()
        tp = erzeuge_3d_parallel_toolpath(
            hm, _kugelfraeser(4),
            _param(stepover_modus=StepoverModus.SCALLOP_3D, scallop_hoehe_mm=0.1),
        )
        assert tp.metadaten["strategie"] == "3d_parallel"

    def test_scallop_3d_terminiert_bei_steiler_flaeche(self):
        # Sicherheits-Limit: auch bei sehr steiler Flaeche darf die Schleife
        # nicht unendlich laufen (cos→0 wird auf 0.15 geklemmt).
        hm = self._rampe(steigung_pro_mm=10.0)  # ~84° fast senkrecht
        tp = erzeuge_3d_parallel_toolpath(
            hm, _kugelfraeser(4),
            _param(stepover_modus=StepoverModus.SCALLOP_3D, scallop_hoehe_mm=0.1, bahn_winkel_grad=90),
        )
        assert 0 < len(tp.bewegungen) < 100000


class TestWerkzeugKompensation:
    def test_kugelfraeser_auf_rampe_folgt_oberflaeche(self):
        # Auf einer Rampe sollte der Z-Wert der Bahn entlang X ansteigen
        hm = _rampe_heightmap(30, 30)
        tp = erzeuge_3d_parallel_toolpath(hm, _kugelfraeser(2), _param(bahn_winkel_grad=0))
        schnitt = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
        zs = [b.z for b in schnitt]
        # Z-Werte variieren (Oberflaeche wird gefolgt), nicht konstant
        assert max(zs) - min(zs) > 1.0


class TestVBitKegelprofil:
    """M1: V-Bit/Gravierstichel als Kegel statt Flachboden (V-Carve aus Tiefenbild)."""

    def _vbit(self, durchmesser=6.0, winkel=90.0, spitzen_d=0.0):
        return Werkzeug(
            id="t_vbit", name=f"V-Bit {winkel}°",
            typ=WerkzeugTyp.V_BIT,
            durchmesser=durchmesser, schaft_durchmesser=durchmesser,
            schneidlaenge=10, gesamtlaenge=40, schneiden=2,
            spitzenwinkel=winkel,
            spitzendurchmesser=spitzen_d or None,
        )

    def test_90grad_vbit_dz_negativ_gleich_distanz(self):
        # 90° V-Bit: tan(45°)=1 → profil = d, TIP-Referenz → dz = -d.
        # Bei aufl=0.5 ist der Offset bei d=2.0 → dz≈-2.0 (Spitze unter Kontakt).
        offsets = _werkzeug_kernel_offsets(self._vbit(winkel=90), aufloesung=0.5)
        treffer = [dz for (di, dj, dz) in offsets if di == 4 and dj == 0]
        assert treffer and treffer[0] == pytest.approx(-2.0, abs=0.01)

    def test_60grad_taucht_tiefer_als_90grad(self):
        # 60° V-Bit (half=30°) ist spitzer → groesseres profil → tieferes (negativeres) dz
        o90 = _werkzeug_kernel_offsets(self._vbit(winkel=90), aufloesung=0.5)
        o60 = _werkzeug_kernel_offsets(self._vbit(winkel=60), aufloesung=0.5)
        dz90 = min(dz for (di, dj, dz) in o90 if di == 4 and dj == 0)
        dz60 = min(dz for (di, dj, dz) in o60 if di == 4 and dj == 0)
        assert dz60 < dz90  # spitzer → negativer

    def test_nicht_flach_wie_schaftfraeser(self):
        # Der entscheidende M1-Punkt: V-Bit ist NICHT flach (anders als vorher).
        offsets = _werkzeug_kernel_offsets(self._vbit(winkel=90), aufloesung=0.5)
        dz_werte = [dz for (_, _, dz) in offsets]
        assert min(dz_werte) < -0.5  # echtes Kegelprofil, kein flacher Boden

    def test_spitzendurchmesser_flachflaeche(self):
        # V-Bit mit 1mm Flachspitze: innerhalb d<=0.5 ist dz=0
        offsets = _werkzeug_kernel_offsets(
            self._vbit(winkel=90, spitzen_d=1.0), aufloesung=0.25,
        )
        # d=0.25 (innerhalb spitzen_r=0.5) → dz=0
        zentrum = [dz for (di, dj, dz) in offsets if abs(di) <= 1 and dj == 0]
        assert max(zentrum) == 0.0

    def test_vbit_carvt_v_nut_tiefer_als_flach(self):
        # V-Carve aus Tiefenbild: V-Bit folgt einer V-foermigen Heightmap-Rille
        # und taucht in die Spitze ein. Eine flache Ebene mit V-Nut.
        nx, ny = 40, 20
        z = np.zeros((nx, ny))
        for i in range(nx):
            # V-Nut in der Mitte: tief bei i=20, hoch an den Raendern
            z[i, :] = -max(0.0, 5.0 - abs(i - 20) * 0.5)
        hm = Heightmap(z_values=z, aufloesung=1.0, x_min=0, y_min=0, z_max=0.0)
        tp = erzeuge_3d_parallel_toolpath(
            hm, self._vbit(winkel=60, durchmesser=8),
            _param(bahn_winkel_grad=0, stepover_modus=StepoverModus.DISTANZ,
                   stepover_distanz_mm=1.0),
        )
        zs = [b.z for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
        # Der V-Bit taucht in die Nut → deutlich negative Z erreichbar
        assert min(zs) < -1.0

    def test_ballnose_v_bit_hybrid(self):
        # Ball-Nose-V-Bit: Kugelspitze + Kegel. Profil muss monoton steigen
        # und am Zentrum gerundet (nicht spitz) sein.
        wz = Werkzeug(
            id="t_bnv", name="Ballnose-V", typ=WerkzeugTyp.BALLNOSE_V_BIT,
            durchmesser=6.0, schaft_durchmesser=6.0,
            schneidlaenge=10, gesamtlaenge=40, schneiden=2,
            spitzenwinkel=30.0, spitzendurchmesser=1.0, spitzenradius=0.5,
        )
        offsets = _werkzeug_kernel_offsets(wz, aufloesung=0.25)
        # am Zentrum dz≈0, nach aussen tiefer (negativer, TIP-Referenz)
        zentrum = max(dz for (di, dj, dz) in offsets if di == 0 and dj == 0)
        aussen = min(dz for (di, dj, dz) in offsets if di == 8 and dj == 0)
        assert zentrum == pytest.approx(0.0, abs=0.01)
        assert aussen < zentrum


class TestVCarveVorschlag:
    """M2: Tiefenbild→V-Carve-Pipeline Convenience-Builder."""

    def _vbit(self):
        return Werkzeug(
            id="t_v", name="V-Bit 60", typ=WerkzeugTyp.V_BIT,
            durchmesser=6, schaft_durchmesser=6, schneidlaenge=8,
            gesamtlaenge=40, schneiden=2, spitzenwinkel=60.0,
        )

    def test_vorschlag_nutzt_scallop_3d(self):
        from camwosa.cam.strategie_3d import v_carve_parameter_vorschlag
        p = v_carve_parameter_vorschlag(
            self._vbit(), spindel_rpm=18000, vorschub=1200, eintauch_vorschub=300,
        )
        assert p.stepover_modus == StepoverModus.SCALLOP_3D
        assert p.werkzeug_id == "t_v"

    def test_vorschlag_erzeugt_lauffaehigen_toolpath(self):
        from camwosa.cam.strategie_3d import v_carve_parameter_vorschlag
        nx, ny = 40, 20
        z = np.zeros((nx, ny))
        for i in range(nx):
            z[i, :] = -max(0.0, 4.0 - abs(i - 20) * 0.4)
        hm = Heightmap(z_values=z, aufloesung=1.0, x_min=0, y_min=0, z_max=0.0)
        p = v_carve_parameter_vorschlag(
            self._vbit(), spindel_rpm=18000, vorschub=1200, eintauch_vorschub=300,
        )
        tp = erzeuge_3d_parallel_toolpath(hm, self._vbit(), p)
        assert len(tp.bewegungen) > 2
        zs = [b.z for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
        assert min(zs) < 0
