"""Tests fuer das Override-System (Auswahl-Hierarchie + Quellen-Tracking)."""

from __future__ import annotations

import pytest

from camwosa.cam.overrides import (
    BohrOverrides,
    GravurOverrides,
    KonturOverrides,
    ProjektDefaults,
    TaschenOverrides,
    aufloese_bohren,
    aufloese_gravur,
    aufloese_kontur,
    aufloese_tasche,
)
from camwosa.cam.parameter import (
    BohrStrategie,
    Eintauchstrategie,
    KonturSeite,
    TaschenStrategie,
)


class TestKonturAufloesung:
    def test_alles_default_nimmt_preset(self, material_buche, schaftfraeser_6mm) -> None:
        ov = KonturOverrides(werkzeug_id=schaftfraeser_6mm.id)
        erg = aufloese_kontur(ov, material_buche, schaftfraeser_6mm)
        # material_buche hat preset fuer schaftfraeser_6mm in fixture
        # (rpm=18000, vorschub=2000, plunge=400, stepdown=2)
        assert erg.parameter.spindel_rpm == 18000
        assert erg.parameter.vorschub == 2000
        assert erg.quellen["spindel_rpm"] == "material_preset"
        assert erg.quellen["vorschub"] == "material_preset"

    def test_override_schlaegt_preset(self, material_buche, schaftfraeser_6mm) -> None:
        ov = KonturOverrides(werkzeug_id=schaftfraeser_6mm.id, vorschub=1234)
        erg = aufloese_kontur(ov, material_buche, schaftfraeser_6mm)
        assert erg.parameter.vorschub == 1234
        assert erg.quellen["vorschub"] == "override"

    def test_projekt_default_bei_fehlendem_preset(
        self, material_buche, schaftfraeser_6mm
    ) -> None:
        defaults = ProjektDefaults(sicherheitshoehe=8.0, max_tiefe=10.0)
        ov = KonturOverrides(werkzeug_id=schaftfraeser_6mm.id)
        erg = aufloese_kontur(ov, material_buche, schaftfraeser_6mm, defaults=defaults)
        assert erg.parameter.sicherheitshoehe == 8.0
        assert erg.parameter.max_tiefe == 10.0
        assert erg.quellen["sicherheitshoehe"] == "projekt_default"
        assert erg.quellen["max_tiefe"] == "projekt_default"

    def test_override_seite(self, material_buche, schaftfraeser_6mm) -> None:
        ov = KonturOverrides(werkzeug_id=schaftfraeser_6mm.id,
                              seite=KonturSeite.INNEN)
        erg = aufloese_kontur(ov, material_buche, schaftfraeser_6mm)
        assert erg.parameter.seite == KonturSeite.INNEN
        assert erg.quellen["seite"] == "override"


class TestTascheAufloesung:
    def test_stepover_aus_preset(self, material_buche, schaftfraeser_6mm) -> None:
        ov = TaschenOverrides(werkzeug_id=schaftfraeser_6mm.id)
        erg = aufloese_tasche(ov, material_buche, schaftfraeser_6mm)
        # Preset hat stepover_prozent=40
        assert erg.parameter.stepover_prozent == 40.0
        assert erg.quellen["stepover_prozent"] == "material_preset"

    def test_override_strategie(self, material_buche, schaftfraeser_6mm) -> None:
        ov = TaschenOverrides(werkzeug_id=schaftfraeser_6mm.id,
                              strategie=TaschenStrategie.OFFSET_KONTUR)
        erg = aufloese_tasche(ov, material_buche, schaftfraeser_6mm)
        assert erg.parameter.strategie == TaschenStrategie.OFFSET_KONTUR


class TestBohrenAufloesung:
    def test_peck_default(self, material_buche, schaftfraeser_6mm) -> None:
        ov = BohrOverrides(werkzeug_id=schaftfraeser_6mm.id)
        erg = aufloese_bohren(ov, material_buche, schaftfraeser_6mm)
        assert erg.parameter.strategie == BohrStrategie.PECK
        assert erg.parameter.peck_tiefe == 2.0

    def test_override_peck_tiefe(self, material_buche, schaftfraeser_6mm) -> None:
        ov = BohrOverrides(werkzeug_id=schaftfraeser_6mm.id, peck_tiefe=0.5)
        erg = aufloese_bohren(ov, material_buche, schaftfraeser_6mm)
        assert erg.parameter.peck_tiefe == 0.5
        assert erg.quellen["peck_tiefe"] == "override"


class TestGravurAufloesung:
    def test_spitzenwinkel_aus_werkzeug(
        self, material_buche, vbit_60grad
    ) -> None:
        ov = GravurOverrides(werkzeug_id=vbit_60grad.id)
        erg = aufloese_gravur(ov, material_buche, vbit_60grad)
        # V-Bit hat spitzenwinkel=60, sollte uebernommen werden
        assert erg.parameter.spitzenwinkel_grad == 60.0
        assert erg.quellen["spitzenwinkel_grad"] == "werkzeug"

    def test_override_spitzenwinkel(
        self, material_buche, vbit_60grad
    ) -> None:
        ov = GravurOverrides(werkzeug_id=vbit_60grad.id, spitzenwinkel_grad=90)
        erg = aufloese_gravur(ov, material_buche, vbit_60grad)
        assert erg.parameter.spitzenwinkel_grad == 90.0


class TestHierarchie:
    def test_hierarchie_komplett(self, material_buche, schaftfraeser_6mm) -> None:
        """override > preset > projekt > fallback."""
        defaults = ProjektDefaults(max_tiefe=99.0, sicherheitshoehe=20.0)
        ov = KonturOverrides(
            werkzeug_id=schaftfraeser_6mm.id,
            sicherheitshoehe=42.0,  # override -> 42 (gewinnt)
            # max_tiefe nicht gesetzt -> projekt_default 99
            # vorschub nicht gesetzt -> preset 2000
            # tabs_anzahl nicht gesetzt -> fallback 0
        )
        erg = aufloese_kontur(ov, material_buche, schaftfraeser_6mm, defaults=defaults)
        assert erg.parameter.sicherheitshoehe == 42.0
        assert erg.quellen["sicherheitshoehe"] == "override"
        assert erg.parameter.max_tiefe == 99.0
        assert erg.quellen["max_tiefe"] == "projekt_default"
        assert erg.parameter.vorschub == 2000
        assert erg.quellen["vorschub"] == "material_preset"
        assert erg.parameter.tabs_anzahl == 0
        assert erg.quellen["tabs_anzahl"] == "fallback"
