"""Tests fuer CuttingPreset als separate Top-Level-Entitaet."""

from __future__ import annotations

import json

import pytest

from camwosa.db.cutting_presets import (
    CuttingPreset,
    OperationsTyp,
    finde_preset,
    lade_cutting_presets,
    migriere_material_presets,
    speichere_cutting_preset,
)
from camwosa.db.models import Material, MaterialKategorie, SchnittParameterPreset


# ---------------------------------------------------------------------------
# Modell
# ---------------------------------------------------------------------------


class TestCuttingPresetModell:
    def test_pflichtfelder(self):
        p = CuttingPreset(
            id="x",
            material_id="m",
            werkzeug_id="w",
            rpm=18000,
            vorschub=1500,
            plunge=300,
            stepdown=1.0,
            stepover_prozent=40,
        )
        assert p.operation_typ == OperationsTyp.GENERIC
        assert p.name  # auto-generated
        assert "m" in p.name and "w" in p.name

    def test_explizit_operation_typ(self):
        p = CuttingPreset(
            id="x", material_id="m", werkzeug_id="w",
            operation_typ=OperationsTyp.SCHRUPPEN,
            rpm=18000, vorschub=1500, plunge=300, stepdown=1.0, stepover_prozent=40,
        )
        assert p.operation_typ == OperationsTyp.SCHRUPPEN

    def test_validierung_stepover_grenzen(self):
        with pytest.raises(ValueError):
            CuttingPreset(
                id="x", material_id="m", werkzeug_id="w",
                rpm=1, vorschub=1, plunge=1, stepdown=1, stepover_prozent=0,
            )
        with pytest.raises(ValueError):
            CuttingPreset(
                id="x", material_id="m", werkzeug_id="w",
                rpm=1, vorschub=1, plunge=1, stepdown=1, stepover_prozent=120,
            )


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------


class TestMigration:
    def test_migration_aus_material(self):
        mat = Material(
            id="buche_test",
            name="Buche",
            kategorie=MaterialKategorie.HOLZ,
            presets=[
                SchnittParameterPreset(
                    werkzeug_id="t1", rpm=18000, vorschub=2000,
                    plunge=400, stepdown=2.0, stepover_prozent=40,
                ),
            ],
        )
        migr = migriere_material_presets([mat])
        assert len(migr) == 1
        m = migr[0]
        assert m.id == "buche_test__t1__generic"
        assert m.material_id == "buche_test"
        assert m.werkzeug_id == "t1"
        assert m.operation_typ == OperationsTyp.GENERIC
        assert m.rpm == 18000
        assert m.quelle == "legacy-migration"

    def test_migration_mehrere_materialien(self):
        mats = [
            Material(
                id=f"m{i}", name=f"M{i}", kategorie=MaterialKategorie.HOLZ,
                presets=[
                    SchnittParameterPreset(
                        werkzeug_id="t1", rpm=18000, vorschub=2000,
                        plunge=400, stepdown=2.0, stepover_prozent=40,
                    ),
                ],
            )
            for i in range(3)
        ]
        migr = migriere_material_presets(mats)
        assert len(migr) == 3
        assert {m.material_id for m in migr} == {"m0", "m1", "m2"}


# ---------------------------------------------------------------------------
# Lookup
# ---------------------------------------------------------------------------


def _preset(material_id, werkzeug_id, op=OperationsTyp.GENERIC, rpm=18000):
    return CuttingPreset(
        id=f"{material_id}__{werkzeug_id}__{op.value}",
        material_id=material_id, werkzeug_id=werkzeug_id, operation_typ=op,
        rpm=rpm, vorschub=2000, plunge=400, stepdown=1.0, stepover_prozent=40,
    )


class TestFindePreset:
    def test_exakter_match(self):
        presets = [
            _preset("buche", "t1", OperationsTyp.GENERIC, rpm=18000),
            _preset("buche", "t1", OperationsTyp.SCHRUPPEN, rpm=20000),
        ]
        treffer = finde_preset(
            presets,
            material_id="buche", werkzeug_id="t1",
            operation_typ=OperationsTyp.SCHRUPPEN,
        )
        assert treffer is not None
        assert treffer.rpm == 20000

    def test_fallback_auf_generic(self):
        presets = [_preset("buche", "t1", OperationsTyp.GENERIC, rpm=18000)]
        treffer = finde_preset(
            presets,
            material_id="buche", werkzeug_id="t1",
            operation_typ=OperationsTyp.SCHRUPPEN,
        )
        assert treffer is not None
        assert treffer.rpm == 18000  # vom Generic-Fallback

    def test_keine_uebereinstimmung(self):
        presets = [_preset("buche", "t1")]
        treffer = finde_preset(
            presets,
            material_id="eiche", werkzeug_id="t1",
        )
        assert treffer is None

    def test_str_operation_typ_wird_geparst(self):
        presets = [_preset("buche", "t1", OperationsTyp.GRAVUR, rpm=22000)]
        treffer = finde_preset(
            presets,
            material_id="buche", werkzeug_id="t1",
            operation_typ="gravur",
        )
        assert treffer is not None
        assert treffer.rpm == 22000


# ---------------------------------------------------------------------------
# Laden + Speichern (Dedup gegen Legacy)
# ---------------------------------------------------------------------------


class TestLadenUndSpeichern:
    def test_speichern_und_laden(self, tmp_path):
        p = _preset("test_mat", "test_tool")
        speichere_cutting_preset(p, data_dir=tmp_path)
        gespeichert = tmp_path / "cutting_presets" / f"{p.id}.json"
        assert gespeichert.exists()
        inhalt = json.loads(gespeichert.read_text(encoding="utf-8"))
        assert inhalt["material_id"] == "test_mat"

    def test_laden_dedupliziert_legacy(self, tmp_path):
        # 1. Material mit Legacy-Preset, das die selbe ID erzeugt
        mat = Material(
            id="buche_x", name="Buche", kategorie=MaterialKategorie.HOLZ,
            presets=[
                SchnittParameterPreset(
                    werkzeug_id="t1", rpm=99999, vorschub=2000,  # Markiert mit 99999
                    plunge=400, stepdown=2.0, stepover_prozent=40,
                ),
            ],
        )
        # 2. Datei-basiertes Preset mit selber ID hat Vorrang
        datei_preset = CuttingPreset(
            id="buche_x__t1__generic", material_id="buche_x", werkzeug_id="t1",
            rpm=12345, vorschub=2000, plunge=400, stepdown=1.0, stepover_prozent=40,
        )
        speichere_cutting_preset(datei_preset, data_dir=tmp_path)

        ergebnis = lade_cutting_presets(
            data_dir=tmp_path, materialien=[mat], include_legacy=True
        )
        relevante = [p for p in ergebnis if p.id == "buche_x__t1__generic"]
        assert len(relevante) == 1
        assert relevante[0].rpm == 12345  # Datei-Preset hat gewonnen

    def test_laden_ohne_legacy(self, tmp_path):
        mat = Material(
            id="m", name="M", kategorie=MaterialKategorie.HOLZ,
            presets=[
                SchnittParameterPreset(
                    werkzeug_id="t1", rpm=18000, vorschub=2000,
                    plunge=400, stepdown=2.0, stepover_prozent=40,
                ),
            ],
        )
        ergebnis = lade_cutting_presets(
            data_dir=tmp_path, materialien=[mat], include_legacy=False
        )
        assert ergebnis == []
