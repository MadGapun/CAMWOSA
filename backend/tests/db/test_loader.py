"""Tests fuer den Default-Profil-Loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from camwosa.db.loader import (
    lade_maschinen, lade_materialien, lade_spindeln, lade_werkzeuge,
    spindel_index,
)
from camwosa.db.models import ControllerTyp, MaterialKategorie, SpindelHerkunft, WerkzeugTyp


@pytest.fixture
def default_data_dir() -> Path:
    """Pfad auf das Repo-data/-Verzeichnis."""
    return Path(__file__).resolve().parents[3] / "data"


class TestMaschinen:
    def test_proverxl_ist_geladen(self, default_data_dir: Path) -> None:
        maschinen = lade_maschinen(default_data_dir)
        ids = {m.id for m in maschinen}
        assert "genmitsu_proverxl_4030_v2" in ids

    def test_alle_maschinen_haben_grbl_oder_andere_controller(self, default_data_dir: Path) -> None:
        maschinen = lade_maschinen(default_data_dir)
        assert len(maschinen) >= 2
        for m in maschinen:
            assert isinstance(m.controller, ControllerTyp)

    def test_proverxl_hat_rotary_modus(self, default_data_dir: Path) -> None:
        maschinen = lade_maschinen(default_data_dir)
        proverxl = next(m for m in maschinen if m.id == "genmitsu_proverxl_4030_v2")
        assert "rotary_y" in [m.value for m in proverxl.modi]


class TestWerkzeuge:
    def test_standard_werkzeuge_geladen(self, default_data_dir: Path) -> None:
        werkzeuge = lade_werkzeuge(default_data_dir)
        ids = {w.id for w in werkzeuge}
        assert "schaft_6mm_2s_hm" in ids
        assert "vbit_60grad" in ids
        assert "bohrer_3mm" in ids

    def test_v_bit_hat_spitzenwinkel(self, default_data_dir: Path) -> None:
        werkzeuge = lade_werkzeuge(default_data_dir)
        v_bits = [w for w in werkzeuge if w.typ == WerkzeugTyp.V_BIT]
        assert len(v_bits) >= 2
        for v in v_bits:
            assert v.spitzenwinkel is not None


class TestMaterialien:
    def test_buche_geladen(self, default_data_dir: Path) -> None:
        materialien = lade_materialien(default_data_dir)
        ids = {m.id for m in materialien}
        assert "buche_massiv" in ids

    def test_alle_kategorien_vorhanden(self, default_data_dir: Path) -> None:
        materialien = lade_materialien(default_data_dir)
        kats = {m.kategorie for m in materialien}
        assert MaterialKategorie.HOLZ in kats
        assert MaterialKategorie.HOLZWERKSTOFF in kats
        assert MaterialKategorie.KUNSTSTOFF in kats
        assert MaterialKategorie.NE_METALL in kats

    def test_buche_hat_presets(self, default_data_dir: Path) -> None:
        materialien = lade_materialien(default_data_dir)
        buche = next(m for m in materialien if m.id == "buche_massiv")
        assert len(buche.presets) >= 3


class TestSpindeln:
    def test_default_spindeln_geladen(self, default_data_dir: Path) -> None:
        spindeln = lade_spindeln(default_data_dir)
        ids = {s.id for s in spindeln}
        assert "makita_rt0700" in ids
        assert "genmitsu_router_710w" in ids
        assert "generic_pwm_24k" in ids

    def test_spindel_index(self, default_data_dir: Path) -> None:
        idx = spindel_index(default_data_dir)
        assert idx["makita_rt0700"].rpm_max == 30000
        assert idx["makita_rt0700"].herkunft == SpindelHerkunft.UPGRADE
        assert idx["genmitsu_router_710w"].herkunft == SpindelHerkunft.OEM

    def test_proverxl_referenziert_spindeln(self, default_data_dir: Path) -> None:
        maschinen = lade_maschinen(default_data_dir)
        idx = spindel_index(default_data_dir)
        proverxl = next(m for m in maschinen if m.id == "genmitsu_proverxl_4030_v2")
        assert "makita_rt0700" in proverxl.spindel_ids
        assert "genmitsu_router_710w" in proverxl.spindel_ids
        sp = proverxl.aktive_spindel(idx)
        assert sp is not None
        assert sp.id == "makita_rt0700"
        # Effektive RPM-Range sollte aus aktiver Spindel kommen
        assert proverxl.effektive_rpm_range(idx) == (10000, 30000)


class TestLeeresVerzeichnis:
    def test_nicht_existierendes_verzeichnis(self, tmp_path: Path) -> None:
        assert lade_maschinen(tmp_path) == []
        assert lade_werkzeuge(tmp_path) == []
        assert lade_materialien(tmp_path) == []
