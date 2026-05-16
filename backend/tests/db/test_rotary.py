"""Tests fuer Rotary-Profil-Modell + Rohmaterial."""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from camwosa.db.loader import lade_rotary_profile, rotary_index
from camwosa.db.rotary import (
    RotaryNullpunktReferenz,
    RotaryProfil,
    RotaryRohmaterial,
    RotaryRohmaterialForm,
)


class TestRotaryProfil:
    def test_default_profile_geladen(self) -> None:
        profile = lade_rotary_profile()
        ids = {p.id for p in profile}
        assert "generic_4achs_3backen_50mm" in ids

    def test_proverxl_referenziert_rotary(self) -> None:
        from camwosa.db.loader import lade_maschinen
        ms = lade_maschinen()
        proverxl = next(m for m in ms if m.id == "genmitsu_proverxl_4030_v2")
        assert "generic_4achs_3backen_50mm" in proverxl.rotary_profile_ids
        # Default: nicht aktiv (rotary muss manuell montiert werden)
        assert proverxl.aktive_rotary_profil_id is None

    def test_y_replacement_settings(self) -> None:
        idx = rotary_index()
        r = idx["generic_4achs_3backen_50mm"]
        assert r.grbl_y_steps_pro_grad == 88.889
        assert r.grbl_y_limit_aufheben is True


class TestRohmaterial:
    def test_rund(self) -> None:
        rm = RotaryRohmaterial(
            form=RotaryRohmaterialForm.RUND,
            durchmesser_mm=40,
            laenge_mm=120,
            material_id="buche_massiv",
        )
        assert rm.effektiver_radius() == 20

    def test_rund_braucht_durchmesser(self) -> None:
        with pytest.raises(ValidationError, match="durchmesser_mm"):
            RotaryRohmaterial(
                form=RotaryRohmaterialForm.RUND,
                laenge_mm=120,
                material_id="x",
            )

    def test_rechteckig(self) -> None:
        rm = RotaryRohmaterial(
            form=RotaryRohmaterialForm.RECHTECKIG,
            laenge_mm=200,
            breite_mm=30,
            hoehe_mm=40,
            material_id="buche_massiv",
        )
        # Halbdiagonale = sqrt(30² + 40²) / 2 = 50/2 = 25
        assert rm.effektiver_radius() == pytest.approx(25, abs=0.01)

    def test_rechteckig_braucht_breite_hoehe(self) -> None:
        with pytest.raises(ValidationError, match="breite_mm"):
            RotaryRohmaterial(
                form=RotaryRohmaterialForm.RECHTECKIG,
                laenge_mm=200,
                material_id="x",
            )

    def test_modell_3d_braucht_stl_pfad(self) -> None:
        with pytest.raises(ValidationError, match="stl_pfad"):
            RotaryRohmaterial(
                form=RotaryRohmaterialForm.MODELL_3D,
                laenge_mm=200,
                material_id="x",
            )

    def test_nullpunkt_referenz_optionen(self) -> None:
        for ref in RotaryNullpunktReferenz:
            rm = RotaryRohmaterial(
                form=RotaryRohmaterialForm.RUND,
                durchmesser_mm=40, laenge_mm=120,
                material_id="x", nullpunkt_referenz=ref,
            )
            assert rm.nullpunkt_referenz == ref


class TestMaschineMitRotary:
    def test_aktive_rotary_id_muss_in_liste_sein(self) -> None:
        from camwosa.db.models import (
            Arbeitsraum, ControllerTyp, Maschine,
        )
        with pytest.raises(ValidationError, match="aktive_rotary_profil_id"):
            Maschine(
                id="m", name="m", hersteller="x", modell="x",
                controller=ControllerTyp.GRBL,
                arbeitsraum=Arbeitsraum(x=100, y=100, z=100),
                max_vorschub=1000, sicherer_vorschub=500, eilgang=2000,
                rotary_profile_ids=["a"],
                aktive_rotary_profil_id="b",  # b nicht in Liste
            )
