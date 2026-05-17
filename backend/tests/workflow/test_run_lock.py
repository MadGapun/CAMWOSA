"""Tests fuer Run-Lock + Dependency-Graph (A48)."""

from __future__ import annotations

import pytest

from camwosa.db.models import (
    Arbeitsraum,
    ControllerTyp,
    Maschine,
    MaschinenModus,
    Material,
    MaterialKategorie,
    ProjektMetadaten,
    Rohmaterial,
    RohmaterialForm,
    SpindelTyp,
    Werkzeug,
    WerkzeugTyp,
)
from camwosa.project.schema import (
    CWPProjekt,
    GeometrieSnapshot,
    OperationsKonfig,
    OperationStatus,
    Setup,
    Variante,
)
from camwosa.workflow.run_lock import (
    darf_gcode_generieren,
    markiere_abhaengige_dirty,
    operation_input_hash,
    pruefe_operation,
    pruefe_projekt,
)


def _maschine() -> Maschine:
    return Maschine(
        id="m1", name="Test", hersteller="x", modell="y",
        controller=ControllerTyp.GRBL,
        arbeitsraum=Arbeitsraum(x=400, y=400, z=110),
        max_vorschub=3000, sicherer_vorschub=2000, eilgang=5000,
        spindel_typ=SpindelTyp.MANUELL,
        spindel_rpm_min=10000, spindel_rpm_max=30000,
        modi=[MaschinenModus.STANDARD_XYZ],
    )


def _werkzeug() -> Werkzeug:
    return Werkzeug(
        id="wz_test", name="Test 6mm",
        typ=WerkzeugTyp.SCHAFTFRAESER,
        durchmesser=6, schaft_durchmesser=6,
        schneidlaenge=20, gesamtlaenge=50, schneiden=2,
    )


def _material() -> Material:
    return Material(
        id="buche", name="Buche",
        kategorie=MaterialKategorie.HOLZ,
        janka_haerte=1300,
    )


def _rohmat() -> Rohmaterial:
    return Rohmaterial(
        form=RohmaterialForm.PLATTE,
        laenge=200, breite=200, hoehe=18,
        material_id="buche",
    )


def _geometrie(gid: str = "g1") -> GeometrieSnapshot:
    return GeometrieSnapshot(
        id=gid, name="Kreis", quelle="zeichnung",
    )


def _operation(op_id: str = "op1", geo_ids: list[str] | None = None,
               werkzeug_id: str = "wz_test", typ: str = "tasche") -> OperationsKonfig:
    return OperationsKonfig(
        id=op_id, name=f"Op {op_id}", typ=typ,
        geometrie_ids=geo_ids if geo_ids is not None else ["g1"],
        parameter={"werkzeug_id": werkzeug_id, "material_id": "buche",
                   "spindel_rpm": 18000, "vorschub": 600,
                   "eintauch_vorschub": 200, "max_tiefe": 5, "stepdown": 2},
    )


def _projekt(setups: list[Setup] | None = None,
             geometrien: list[GeometrieSnapshot] | None = None) -> CWPProjekt:
    from datetime import datetime, timezone
    jetzt = datetime.now(timezone.utc)
    return CWPProjekt(
        metadaten=ProjektMetadaten(name="Test", erstellt=jetzt, geaendert=jetzt),
        maschine=_maschine(),
        werkzeuge=[_werkzeug()],
        materialien=[_material()],
        geometrien=geometrien if geometrien is not None else [_geometrie()],
        varianten=[
            Variante(id="default", name="Default", rohmaterial=_rohmat(),
                     setups=setups or [
                         Setup(id="s1", name="Setup 1", werkzeug_id="wz_test",
                               operationen=[_operation()]),
                     ]),
        ],
    )


class TestInputHash:
    def test_hash_deterministisch(self):
        op = _operation()
        h1 = operation_input_hash(op)
        h2 = operation_input_hash(op)
        assert h1 == h2

    def test_hash_aendert_sich_bei_parameter_change(self):
        op = _operation()
        h1 = operation_input_hash(op)
        op.parameter["max_tiefe"] = 10  # vorher 5
        h2 = operation_input_hash(op)
        assert h1 != h2

    def test_hash_aendert_sich_bei_geometrie_change(self):
        op = _operation()
        h1 = operation_input_hash(op, geometrien_inhalt={"g1": {"r": 20}})
        h2 = operation_input_hash(op, geometrien_inhalt={"g1": {"r": 25}})
        assert h1 != h2


class TestPruefeOperation:
    def test_alle_ok(self):
        op = _operation()
        status, fehler = pruefe_operation(op, {"g1"}, {"wz_test"}, {"buche"})
        assert status == OperationStatus.NEU  # initial
        assert fehler == ""

    def test_geometrie_fehlt(self):
        op = _operation()
        status, fehler = pruefe_operation(op, set(), {"wz_test"}, {"buche"})
        assert status == OperationStatus.BROKEN
        assert "g1" in fehler

    def test_werkzeug_fehlt(self):
        op = _operation()
        status, fehler = pruefe_operation(op, {"g1"}, set(), {"buche"})
        assert status == OperationStatus.BROKEN
        assert "wz_test" in fehler

    def test_material_fehlt(self):
        op = _operation()
        status, fehler = pruefe_operation(op, {"g1"}, {"wz_test"}, set())
        assert status == OperationStatus.BROKEN
        assert "buche" in fehler

    def test_deaktivierte_op_bleibt_ok(self):
        op = _operation()
        op.aktiviert = False
        status, fehler = pruefe_operation(op, set(), set(), set())
        assert status == op.status  # unveraendert
        assert fehler == ""


class TestRunLock:
    def test_neu_status_blockiert(self):
        projekt = _projekt()
        # status ist Default NEU
        ok, blocker = darf_gcode_generieren(projekt)
        assert not ok
        assert any("noch nie berechnet" in b for b in blocker)

    def test_alle_ok_geht_durch(self):
        projekt = _projekt()
        # Manuell status auf OK setzen
        for v in projekt.varianten:
            for s in v.setups:
                for op in s.operationen:
                    op.status = OperationStatus.OK
        ok, blocker = darf_gcode_generieren(projekt)
        assert ok, f"Erwartet OK, blocker={blocker}"
        assert blocker == []

    def test_dirty_blockiert(self):
        projekt = _projekt()
        for v in projekt.varianten:
            for s in v.setups:
                for op in s.operationen:
                    op.status = OperationStatus.DIRTY
        ok, blocker = darf_gcode_generieren(projekt)
        assert not ok
        assert any("veraltet" in b for b in blocker)

    def test_broken_blockiert(self):
        # Geometrie geloescht
        projekt = _projekt(geometrien=[])
        for v in projekt.varianten:
            for s in v.setups:
                for op in s.operationen:
                    op.status = OperationStatus.OK
        ok, blocker = darf_gcode_generieren(projekt)
        # pruefe_projekt sollte BROKEN feststellen
        status_map = pruefe_projekt(projekt)
        assert status_map["op1"][0] == OperationStatus.BROKEN
        assert not ok

    def test_leerer_setup_blockiert(self):
        projekt = _projekt(setups=[
            Setup(id="s1", name="Leer", werkzeug_id="wz_test", operationen=[]),
        ])
        ok, blocker = darf_gcode_generieren(projekt)
        assert not ok
        assert any("keine Operationen" in b for b in blocker)


class TestMarkiereDirty:
    def test_geometrie_change_setzt_dirty(self):
        projekt = _projekt()
        for v in projekt.varianten:
            for s in v.setups:
                for op in s.operationen:
                    op.status = OperationStatus.OK
        count = markiere_abhaengige_dirty(projekt, geometrie_ids={"g1"})
        assert count == 1
        assert projekt.varianten[0].setups[0].operationen[0].status == OperationStatus.DIRTY

    def test_werkzeug_change_setzt_dirty(self):
        projekt = _projekt()
        for v in projekt.varianten:
            for s in v.setups:
                for op in s.operationen:
                    op.status = OperationStatus.OK
        count = markiere_abhaengige_dirty(projekt, werkzeug_ids={"wz_test"})
        assert count == 1

    def test_unbeteiligte_geo_keine_aenderung(self):
        projekt = _projekt()
        for v in projekt.varianten:
            for s in v.setups:
                for op in s.operationen:
                    op.status = OperationStatus.OK
        count = markiere_abhaengige_dirty(projekt, geometrie_ids={"andere_geo"})
        assert count == 0
        assert projekt.varianten[0].setups[0].operationen[0].status == OperationStatus.OK

    def test_broken_bleibt_broken(self):
        projekt = _projekt()
        for v in projekt.varianten:
            for s in v.setups:
                for op in s.operationen:
                    op.status = OperationStatus.BROKEN
                    op.fehler_text = "test"
        count = markiere_abhaengige_dirty(projekt, geometrie_ids={"g1"})
        assert count == 0  # BROKEN bleibt BROKEN

    def test_deaktivierte_op_uebersprungen(self):
        projekt = _projekt()
        for v in projekt.varianten:
            for s in v.setups:
                for op in s.operationen:
                    op.status = OperationStatus.OK
                    op.aktiviert = False
        count = markiere_abhaengige_dirty(projekt, geometrie_ids={"g1"})
        assert count == 0


class TestWerkzeugErweiterungen:
    """Tests fuer A39 (BALLNOSE_V_BIT, V-Bit-Range) + A46 (free_length, auto_speeds)."""

    def test_v_bit_range_4_grad_ok(self):
        # War vorher ge=10 — jetzt ge=1
        wz = Werkzeug(
            id="vbit_4", name="V-Bit 4 Grad", typ=WerkzeugTyp.V_BIT,
            durchmesser=3.175, schaft_durchmesser=3.175,
            schneidlaenge=15, gesamtlaenge=40, schneiden=1,
            spitzenwinkel=4,
        )
        assert wz.spitzenwinkel == 4

    def test_v_bit_range_179_grad_ok(self):
        wz = Werkzeug(
            id="vbit_flat", name="V-Bit 179", typ=WerkzeugTyp.V_BIT,
            durchmesser=10, schaft_durchmesser=6,
            schneidlaenge=5, gesamtlaenge=40, schneiden=2,
            spitzenwinkel=179,
        )
        assert wz.spitzenwinkel == 179

    def test_v_bit_winkel_0_raises(self):
        with pytest.raises(Exception):
            Werkzeug(
                id="x", name="X", typ=WerkzeugTyp.V_BIT,
                durchmesser=6, schaft_durchmesser=6,
                schneidlaenge=10, gesamtlaenge=40, schneiden=2,
                spitzenwinkel=0,
            )

    def test_ballnose_v_bit_braucht_spitzenwinkel(self):
        with pytest.raises(ValueError, match="spitzenwinkel"):
            Werkzeug(
                id="x", name="Ballnose V", typ=WerkzeugTyp.BALLNOSE_V_BIT,
                durchmesser=6, schaft_durchmesser=6,
                schneidlaenge=10, gesamtlaenge=40, schneiden=2,
                spitzendurchmesser=0.5,
                # spitzenwinkel fehlt
            )

    def test_ballnose_v_bit_braucht_spitzendurchmesser(self):
        with pytest.raises(ValueError, match="spitzendurchmesser"):
            Werkzeug(
                id="x", name="Ballnose V", typ=WerkzeugTyp.BALLNOSE_V_BIT,
                durchmesser=6, schaft_durchmesser=6,
                schneidlaenge=10, gesamtlaenge=40, schneiden=2,
                spitzenwinkel=30,
                # spitzendurchmesser fehlt
            )

    def test_ballnose_v_bit_voll_definiert_ok(self):
        wz = Werkzeug(
            id="bnv_30", name="Ballnose V 30 Grad 0.25mm Tip",
            typ=WerkzeugTyp.BALLNOSE_V_BIT,
            durchmesser=6, schaft_durchmesser=6,
            schneidlaenge=15, gesamtlaenge=40, schneiden=2,
            spitzenwinkel=30,
            spitzendurchmesser=0.25,
        )
        assert wz.spitzenwinkel == 30
        assert wz.spitzendurchmesser == 0.25

    def test_free_length_default_gesamtlaenge(self):
        wz = _werkzeug()  # ohne free_length
        assert wz.free_length_mm == wz.gesamtlaenge

    def test_free_length_explizit(self):
        wz = Werkzeug(
            id="wz", name="X", typ=WerkzeugTyp.SCHAFTFRAESER,
            durchmesser=6, schaft_durchmesser=6,
            schneidlaenge=20, gesamtlaenge=50, schneiden=2,
            free_length_mm=30,  # weniger als gesamtlaenge — User hat tief eingespannt
        )
        assert wz.free_length_mm == 30

    def test_auto_set_speeds_default_off(self):
        wz = _werkzeug()
        assert wz.auto_set_speeds is False
        assert wz.auto_feedrate is None
        assert wz.auto_spindel_rpm is None

    def test_auto_set_speeds_komplett(self):
        wz = Werkzeug(
            id="wz", name="X", typ=WerkzeugTyp.V_BIT,
            durchmesser=6, schaft_durchmesser=6,
            schneidlaenge=15, gesamtlaenge=40, schneiden=2,
            spitzenwinkel=60,
            auto_set_speeds=True,
            auto_feedrate=400,
            auto_spindel_rpm=22000,
        )
        assert wz.auto_set_speeds is True
        assert wz.auto_feedrate == 400
        assert wz.auto_spindel_rpm == 22000

    def test_drag_gravierer_typ_existiert(self):
        wz = Werkzeug(
            id="dg", name="Drag Diamant", typ=WerkzeugTyp.DRAG_GRAVIERER,
            durchmesser=0.5, schaft_durchmesser=3.175,
            schneidlaenge=2, gesamtlaenge=40, schneiden=1,
        )
        assert wz.typ == WerkzeugTyp.DRAG_GRAVIERER
