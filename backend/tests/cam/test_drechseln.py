"""Tests fuer Drechsel-Operationen."""

from __future__ import annotations

import pytest

from camwosa.cam.drechseln import (
    berechne_helix_vorschub,
    erzeuge_drechsel_toolpath,
    radius_an_x,
    werkzeug_z_offset,
)
from camwosa.cam.parameter import DrechselParameter, DrechselStrategie
from camwosa.db.models import Werkzeug, WerkzeugTyp
from camwosa.gcode.toolpath import BewegungsTyp


def _params(**overrides) -> DrechselParameter:
    defaults = dict(
        werkzeug_id="dreh_meissel",
        spindel_rpm=10000, vorschub=300, eintauch_vorschub=150,
        sicherheitshoehe=5, max_tiefe=15, stepdown=1.5,
        rohmaterial_radius_mm=20,
        aufmass_schlichten_mm=0.3,
        schlicht_zustellung_mm=0.5,
        drehzahl_werkstueck_upm=300,
        profil=[(0, 18), (100, 18)],  # Zylinder Ø36
        strategie=DrechselStrategie.SCHRUPP_UND_SCHLICHT,
    )
    defaults.update(overrides)
    return DrechselParameter(**defaults)


class TestRadiusInterpolation:
    def test_innerhalb_punkte_linear(self):
        profil = [(0, 10), (100, 20)]
        assert radius_an_x(50, profil) == pytest.approx(15)

    def test_ausserhalb_links_clamp(self):
        profil = [(10, 5), (50, 10)]
        assert radius_an_x(0, profil) == 5

    def test_ausserhalb_rechts_clamp(self):
        profil = [(0, 5), (50, 10)]
        assert radius_an_x(99, profil) == 10

    def test_leeres_profil(self):
        assert radius_an_x(50, []) == 0.0


class TestProfilValidierung:
    def test_unsortiert_raises(self):
        with pytest.raises(ValueError, match="aufsteigend"):
            _params(profil=[(0, 10), (50, 10), (40, 10)])

    def test_radius_groesser_rohmaterial_raises(self):
        with pytest.raises(ValueError, match="groesser als"):
            _params(rohmaterial_radius_mm=15, profil=[(0, 20)])

    def test_negativer_radius_raises(self):
        with pytest.raises(ValueError, match="nicht negativ"):
            _params(profil=[(0, -1)])


class TestSchruppStrategie:
    def test_schruppen_macht_mehrere_passes(self):
        # Tiefes Profil — Material 20mm, Profil 8mm, Aufmass 0.3 → 11.7mm zu schaelen
        p = _params(
            strategie=DrechselStrategie.LAENGS_SCHRUPPEN,
            stepdown=2.0,
            profil=[(0, 8), (100, 8)],
        )
        tp = erzeuge_drechsel_toolpath("dreh", p)
        plunges = [b for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE]
        # 11.7mm / 2mm ≈ 6 passes
        assert len(plunges) >= 5
        # Erster Plunge liegt zwischen Roh-Radius und Ziel
        assert plunges[0].z < p.rohmaterial_radius_mm
        # Letzter Plunge liegt knapp ueberm Profil + Aufmass
        ziel = 8 + p.aufmass_schlichten_mm  # 8.3
        assert plunges[-1].z <= ziel + 0.01

    def test_passes_alternieren_richtung(self):
        p = _params(
            strategie=DrechselStrategie.LAENGS_SCHRUPPEN,
            stepdown=2.0,
            profil=[(0, 8), (100, 8)],
        )
        tp = erzeuge_drechsel_toolpath("dreh", p)
        plunges = [b for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE]
        # Erster Pass faehrt nach +X, zweiter nach -X
        assert plunges[0].x == 0.0
        assert plunges[1].x == 100.0


class TestSchlichtStrategie:
    def test_schlichten_folgt_profil(self):
        profil = [(0, 18), (50, 12), (100, 18)]  # Vase-aehnlich
        p = _params(strategie=DrechselStrategie.PROFIL_SCHLICHTEN, profil=profil)
        tp = erzeuge_drechsel_toolpath("dreh", p)
        linears = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
        # An x=50 sollte das Werkzeug bei z≈12 sein
        nahe_mitte = min(linears, key=lambda b: abs(b.x - 50))
        assert nahe_mitte.z == pytest.approx(12, abs=0.5)
        # An x=0 bei z≈18
        nahe_start = min(linears, key=lambda b: abs(b.x - 0))
        assert nahe_start.z == pytest.approx(18, abs=0.5)


class TestSchruppUndSchlicht:
    def test_kombiniert_enthaelt_beide_phasen(self):
        p = _params(strategie=DrechselStrategie.SCHRUPP_UND_SCHLICHT)
        tp = erzeuge_drechsel_toolpath("dreh", p)
        kommentare = [b.kommentar for b in tp.bewegungen if b.kommentar]
        assert any("Schrupp" in k for k in kommentare)
        assert any("Schlicht" in k for k in kommentare)


class TestHelixStrategie:
    def test_vorschub_synchron_zu_drehzahl(self):
        # 2 mm/U bei 250 U/min → 500 mm/min
        assert berechne_helix_vorschub(2.0, 250) == 500.0
        # 1.5 mm/U bei 200 U/min → 300 mm/min
        assert berechne_helix_vorschub(1.5, 200) == 300.0

    def test_helix_erzeugt_passes_mit_zunehmender_tiefe(self):
        p = _params(
            strategie=DrechselStrategie.HELIX,
            profil=[(0, 20), (200, 20)],   # zylindrisches Werkstueck
            rohmaterial_radius_mm=20,
            helix_steigung_mm_pro_umdrehung=2.0,
            helix_tiefe_mm=3.0,
            helix_anzahl_passes=3,
            drehzahl_werkstueck_upm=250,
        )
        tp = erzeuge_drechsel_toolpath("dreh", p)
        plunges = [b for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE]
        assert len(plunges) == 3
        # Z-Tiefen: 20 - 1, 20 - 2, 20 - 3
        plunge_zs = [b.z for b in plunges]
        assert plunge_zs == pytest.approx([19.0, 18.0, 17.0])

    def test_helix_linear_bewegungen_haben_sync_vorschub(self):
        p = _params(
            strategie=DrechselStrategie.HELIX,
            profil=[(0, 18), (100, 18)],
            helix_steigung_mm_pro_umdrehung=2.0,
            helix_tiefe_mm=1.5,
            helix_anzahl_passes=1,
            drehzahl_werkstueck_upm=300,
        )
        tp = erzeuge_drechsel_toolpath("dreh", p)
        linears = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
        erwarteter_vorschub = 2.0 * 300  # = 600 mm/min
        assert all(b.feed == erwarteter_vorschub for b in linears)

    def test_helix_metadaten_im_toolpath(self):
        p = _params(
            strategie=DrechselStrategie.HELIX,
            profil=[(0, 18), (50, 18)],
            helix_steigung_mm_pro_umdrehung=3.0,
            helix_tiefe_mm=2.0,
            helix_anzahl_passes=2,
            drehzahl_werkstueck_upm=200,
        )
        tp = erzeuge_drechsel_toolpath("dreh", p)
        assert tp.metadaten["strategie"] == "helix"
        assert tp.metadaten["helix_steigung_mm"] == 3.0
        assert tp.metadaten["helix_tiefe_mm"] == 2.0
        assert tp.metadaten["helix_anzahl_passes"] == 2
        assert tp.metadaten["helix_x_vorschub_mm_min"] == 600

    def test_helix_x_bereich_uebersteuert_profil(self):
        p = _params(
            strategie=DrechselStrategie.HELIX,
            profil=[(0, 18), (100, 18)],
            helix_x_start_mm=20,
            helix_x_ende_mm=80,
            helix_steigung_mm_pro_umdrehung=2.0,
            helix_tiefe_mm=1.0,
            helix_anzahl_passes=1,
        )
        tp = erzeuge_drechsel_toolpath("dreh", p)
        # Erster Plunge bei X=20 (nicht 0)
        plunges = [b for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE]
        assert plunges[0].x == 20.0
        # Linears enden bei X=80
        linears = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
        assert linears[-1].x == pytest.approx(80.0)

    def test_helix_folgt_profil_bei_nicht_zylindrischem_werkstueck(self):
        # Konisches Werkstueck: 20mm am Anfang, 10mm am Ende
        p = _params(
            strategie=DrechselStrategie.HELIX,
            profil=[(0, 20), (100, 10)],
            rohmaterial_radius_mm=20,
            helix_steigung_mm_pro_umdrehung=2.0,
            helix_tiefe_mm=1.0,
            helix_anzahl_passes=1,
        )
        tp = erzeuge_drechsel_toolpath("dreh", p)
        linears = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
        # An x=0: Z ~= 19 (20 - 1), an x=100: Z ~= 9 (10 - 1)
        z_start = next(b.z for b in linears if b.x == 0)
        z_ende = next(b.z for b in reversed(linears) if abs(b.x - 100) < 0.5)
        assert z_start == pytest.approx(19.0, abs=0.5)
        assert z_ende == pytest.approx(9.0, abs=0.5)


class TestWerkzeugZOffset:
    """Werkzeug-Geometrie-Kompensation im Drechsel-Mode."""

    def _wz(self, typ: WerkzeugTyp, durchmesser: float = 6.0, spitzenradius: float | None = None) -> Werkzeug:
        return Werkzeug(
            id=f"wz_{typ.value}",
            name=f"Test {typ.value}",
            typ=typ,
            durchmesser=durchmesser,
            schaft_durchmesser=6.0,
            schneidlaenge=22,
            gesamtlaenge=50,
            schneiden=2,
            spitzenradius=spitzenradius,
        )

    def test_schaftfraeser_kein_offset(self):
        assert werkzeug_z_offset(self._wz(WerkzeugTyp.SCHAFTFRAESER, 6.0)) == 0.0

    def test_kugelfraeser_offset_ist_radius(self):
        assert werkzeug_z_offset(self._wz(WerkzeugTyp.KUGELFRAESER, 6.0)) == 3.0

    def test_torusfraeser_offset_ist_spitzenradius(self):
        wz = self._wz(WerkzeugTyp.TORUSFRAESER, 8.0, spitzenradius=1.5)
        assert werkzeug_z_offset(wz) == 1.5

    def test_keine_werkzeug_kein_offset(self):
        assert werkzeug_z_offset(None) == 0.0

    def test_kugelfraeser_im_schlicht_pass(self):
        """Mit Kugelfraeser muss der Z-Wert um Radius hoeher sein als das Profil."""
        wz = self._wz(WerkzeugTyp.KUGELFRAESER, 4.0)  # Radius = 2.0
        p = _params(
            strategie=DrechselStrategie.PROFIL_SCHLICHTEN,
            profil=[(0, 18), (50, 12), (100, 18)],
        )
        tp = erzeuge_drechsel_toolpath("dreh", p, werkzeug=wz)
        linears = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
        # An x=50 liegt das Profil bei Z=12, mit Werkzeug-Offset +2 → Z=14
        nahe_mitte = min(linears, key=lambda b: abs(b.x - 50))
        assert nahe_mitte.z == pytest.approx(14.0, abs=0.5)

    def test_metadaten_speichern_werkzeug_offset(self):
        wz = self._wz(WerkzeugTyp.KUGELFRAESER, 6.0)
        p = _params()
        tp = erzeuge_drechsel_toolpath("dreh", p, werkzeug=wz)
        assert tp.metadaten["werkzeug_z_offset_mm"] == 3.0
        assert tp.metadaten["werkzeug_typ"] == "kugelfraeser"


class TestToolpathMetadaten:
    def test_metadaten_kennzeichnen_drechseln(self):
        p = _params(drehzahl_werkstueck_upm=250)
        tp = erzeuge_drechsel_toolpath("dreh", p)
        assert tp.metadaten["ist_drechseln"] is True
        assert tp.metadaten["drehzahl_werkstueck_upm"] == 250
        assert tp.metadaten["strategie"] == "schrupp_und_schlicht"
        assert tp.metadaten["rohmaterial_radius_mm"] == 20

    def test_sicheres_anfahren_und_zurueckziehen(self):
        p = _params()
        tp = erzeuge_drechsel_toolpath("dreh", p)
        eilgaenge = [b for b in tp.bewegungen if b.typ == BewegungsTyp.EILGANG]
        assert len(eilgaenge) >= 2
        # Erster + letzter Eilgang auf Sicherheitshoehe ueber Rohmaterial
        assert eilgaenge[0].z == p.rohmaterial_radius_mm + p.sicherheitshoehe
        assert eilgaenge[-1].z == p.rohmaterial_radius_mm + p.sicherheitshoehe
