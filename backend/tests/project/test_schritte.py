"""Tests fuer das ArbeitsSchritt-Konzept."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, Field

from camwosa.project.schritte import (
    AchsWechselSchritt,
    ArbeitsSchritt,
    ManualNCSchritt,
    OperationSchritt,
    PauseSchritt,
    SchrittTyp,
    UmspannSchritt,
    WerkzeugWechselSchritt,
    aus_setup_legacy,
    pruefe_schritt_liste,
)


class TestSchrittTypen:
    def test_operation_schritt(self):
        s = OperationSchritt(id="s1", operation_id="op_kontur_1")
        assert s.typ == SchrittTyp.OPERATION
        assert s.aktiviert is True

    def test_werkzeugwechsel(self):
        s = WerkzeugWechselSchritt(
            id="s2",
            werkzeug_neu_id="t02_2mm",
            werkzeug_alt_id="t01_6mm",
            anweisung="2mm-Fraeser einsetzen, Z-Null neu setzen",
        )
        assert s.typ == SchrittTyp.WERKZEUGWECHSEL
        assert s.mensch_pause

    def test_manual_nc(self):
        s = ManualNCSchritt(
            id="s3",
            gcode_zeilen=["M62 P0 ; Vakuum AN", "G4 P2 ; 2s warten"],
        )
        assert s.typ == SchrittTyp.MANUAL_NC
        assert len(s.gcode_zeilen) == 2

    def test_achs_wechsel(self):
        s = AchsWechselSchritt(
            id="s4", modus_alt="standard_xyz", modus_neu="rotary_y",
            anweisung="Rotary-Aufsatz montieren",
        )
        assert s.typ == SchrittTyp.ACHSWECHSEL

    def test_umspann(self):
        s = UmspannSchritt(id="s5", anweisung="Werkstueck drehen, Nullpunkt rechts")
        assert s.typ == SchrittTyp.UMSPANN

    def test_pause(self):
        s = PauseSchritt(id="s6", anweisung="Spaene absaugen, dann OK")
        assert s.typ == SchrittTyp.PAUSE


class TestDiscriminatedUnion:
    """Pydantic muss aus dem ``typ``-Feld den richtigen Subtyp ableiten."""

    class _Container(BaseModel):
        schritte: list[ArbeitsSchritt] = Field(default_factory=list)

    def test_serialisierung_roundtrip(self):
        c = self._Container(schritte=[
            OperationSchritt(id="s1", operation_id="op1"),
            ManualNCSchritt(id="s2", gcode_zeilen=["M0"]),
            WerkzeugWechselSchritt(id="s3", werkzeug_neu_id="t99"),
        ])
        roh = c.model_dump(mode="json")
        wieder = self._Container.model_validate(roh)
        assert isinstance(wieder.schritte[0], OperationSchritt)
        assert isinstance(wieder.schritte[1], ManualNCSchritt)
        assert isinstance(wieder.schritte[2], WerkzeugWechselSchritt)
        assert wieder.schritte[1].gcode_zeilen == ["M0"]


class TestPruefung:
    def test_manual_nc_ohne_zeilen_wird_gemeldet(self):
        probleme = pruefe_schritt_liste([
            ManualNCSchritt(id="s1", gcode_zeilen=[]),
        ])
        assert any("ManualNC" in p for p in probleme)

    def test_operation_direkt_nach_achswechsel_wird_gemeldet(self):
        probleme = pruefe_schritt_liste([
            AchsWechselSchritt(
                id="s1", modus_alt="standard_xyz", modus_neu="rotary_y",
            ),
            OperationSchritt(id="s2", operation_id="op1"),
        ])
        assert any("Achswechsel" in p for p in probleme)

    def test_achswechsel_mit_pause_dazwischen_ok(self):
        probleme = pruefe_schritt_liste([
            AchsWechselSchritt(
                id="s1", modus_alt="standard_xyz", modus_neu="rotary_y",
            ),
            PauseSchritt(id="s2", anweisung="Rotary anschalten"),
            OperationSchritt(id="s3", operation_id="op1"),
        ])
        assert not any("Achswechsel" in p for p in probleme)

    def test_doppelte_ids_werden_gemeldet(self):
        probleme = pruefe_schritt_liste([
            PauseSchritt(id="dup", anweisung="x"),
            PauseSchritt(id="dup", anweisung="y"),
        ])
        assert any("Doppelte" in p for p in probleme)

    def test_werkzeug_alt_id_wird_ausgefuellt(self):
        schritte = [
            WerkzeugWechselSchritt(id="s1", werkzeug_neu_id="t1"),
            OperationSchritt(id="s2", operation_id="op1"),
            WerkzeugWechselSchritt(id="s3", werkzeug_neu_id="t2"),
        ]
        pruefe_schritt_liste(schritte)
        # s3 sollte werkzeug_alt_id = "t1" bekommen haben
        assert schritte[2].werkzeug_alt_id == "t1"

    def test_leere_liste_ist_ok(self):
        assert pruefe_schritt_liste([]) == []


class TestLegacyKonvertierung:
    def test_aus_setup_mit_pause_und_ops(self):
        from camwosa.project.schema import OperationsKonfig, Setup, SetupPause, SetupPauseTyp

        setup = Setup(
            id="s1", name="Setup 1",
            werkzeug_id="t01",
            pause_vor=SetupPause(
                typ=SetupPauseTyp.WERKZEUGWECHSEL,
                titel="Werkzeug einsetzen",
                anweisung="6mm Fraeser",
                werkzeug_neu_id="t01",
            ),
            operationen=[
                OperationsKonfig(
                    id="op1", name="Kontur", typ="kontur", parameter={},
                ),
                OperationsKonfig(
                    id="op2", name="Tasche", typ="tasche", parameter={},
                ),
            ],
        )
        schritte = aus_setup_legacy(setup)
        assert len(schritte) == 3
        assert isinstance(schritte[0], WerkzeugWechselSchritt)
        assert isinstance(schritte[1], OperationSchritt)
        assert isinstance(schritte[2], OperationSchritt)
        assert schritte[1].operation_id == "op1"
        assert schritte[2].operation_id == "op2"

    def test_effektive_schritte_bevorzugt_neue_liste(self):
        from camwosa.project.schema import OperationsKonfig, Setup

        setup = Setup(
            id="s1", name="x",
            werkzeug_id="t01",
            operationen=[
                OperationsKonfig(id="op1", name="X", typ="kontur", parameter={}),
            ],
            schritte=[
                ManualNCSchritt(id="manual", gcode_zeilen=["M0"]),
            ],
        )
        eff = setup.effektive_schritte()
        assert len(eff) == 1
        assert isinstance(eff[0], ManualNCSchritt)

    def test_effektive_schritte_fallback_auf_legacy(self):
        from camwosa.project.schema import OperationsKonfig, Setup

        setup = Setup(
            id="s1", name="x",
            werkzeug_id="t01",
            operationen=[
                OperationsKonfig(id="op1", name="X", typ="kontur", parameter={}),
            ],
        )
        eff = setup.effektive_schritte()
        assert len(eff) == 1
        assert isinstance(eff[0], OperationSchritt)
