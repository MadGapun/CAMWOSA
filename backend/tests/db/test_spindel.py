"""Tests fuer das Spindel-System."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from camwosa.db.models import (
    Arbeitsraum,
    ControllerTyp,
    Maschine,
    Spindel,
    SpindelHerkunft,
    SpindelTyp,
)


@pytest.fixture
def makita_rt0700() -> Spindel:
    return Spindel(
        id="makita_rt0700",
        name="Makita RT0700",
        hersteller="Makita",
        modell="RT0700C",
        typ=SpindelTyp.MANUELL,
        rpm_min=10000,
        rpm_max=30000,
        leistung_watt=710,
        gewicht_g=1300,
        schaft_durchmesser_mm=6.0,
        kuehlung="luft",
        rampen_zeit_s=2.0,
        herkunft=SpindelHerkunft.UPGRADE,
        notizen="Klassisches Upgrade fuer ProVerXL — manuell geregelt",
    )


@pytest.fixture
def genmitsu_router() -> Spindel:
    return Spindel(
        id="genmitsu_router_710w",
        name="Genmitsu 710W Router",
        hersteller="Genmitsu",
        modell="Router 710W",
        typ=SpindelTyp.MANUELL,
        rpm_min=10000,
        rpm_max=30000,
        leistung_watt=710,
        schaft_durchmesser_mm=6.35,
        herkunft=SpindelHerkunft.OEM,
    )


class TestSpindel:
    def test_makita_fixture_valide(self, makita_rt0700: Spindel) -> None:
        assert makita_rt0700.id == "makita_rt0700"
        assert makita_rt0700.typ == SpindelTyp.MANUELL
        assert makita_rt0700.herkunft == SpindelHerkunft.UPGRADE

    def test_rpm_max_kleiner_min_wird_abgelehnt(self) -> None:
        with pytest.raises(ValidationError, match="rpm_max"):
            Spindel(
                id="x", name="X", hersteller="X", modell="X",
                typ=SpindelTyp.PWM, rpm_min=20000, rpm_max=10000,
            )

    def test_pwm_promille_range(self) -> None:
        sp = Spindel(
            id="pwm", name="PWM", hersteller="X", modell="X",
            typ=SpindelTyp.PWM, rpm_min=0, rpm_max=24000,
            pwm_min_promille=0, pwm_max_promille=1000,
        )
        assert sp.pwm_max_promille == 1000

    def test_pwm_promille_zu_hoch(self) -> None:
        with pytest.raises(ValidationError):
            Spindel(
                id="x", name="X", hersteller="X", modell="X",
                typ=SpindelTyp.PWM, rpm_min=0, rpm_max=24000,
                pwm_max_promille=1500,
            )

    def test_json_roundtrip(self, makita_rt0700: Spindel) -> None:
        as_json = makita_rt0700.model_dump_json()
        wieder = Spindel.model_validate_json(as_json)
        assert wieder == makita_rt0700


class TestMaschineMitSpindel:
    def test_maschine_mit_zwei_spindeln(
        self, makita_rt0700, genmitsu_router
    ) -> None:
        m = Maschine(
            id="m1", name="ProVerXL", hersteller="Genmitsu", modell="4030 V2",
            controller=ControllerTyp.GRBL,
            arbeitsraum=Arbeitsraum(x=400, y=400, z=110),
            max_vorschub=3000, sicherer_vorschub=2000, eilgang=5000,
            spindel_ids=[genmitsu_router.id, makita_rt0700.id],
            aktive_spindel_id=makita_rt0700.id,
        )
        index = {makita_rt0700.id: makita_rt0700, genmitsu_router.id: genmitsu_router}
        aktive = m.aktive_spindel(index)
        assert aktive == makita_rt0700
        assert m.effektive_rpm_range(index) == (10000, 30000)
        assert m.effektiver_spindel_typ(index) == SpindelTyp.MANUELL

    def test_aktive_spindel_id_muss_in_liste_sein(self) -> None:
        with pytest.raises(ValidationError, match="aktive_spindel_id"):
            Maschine(
                id="m1", name="X", hersteller="X", modell="X",
                controller=ControllerTyp.GRBL,
                arbeitsraum=Arbeitsraum(x=100, y=100, z=100),
                max_vorschub=1000, sicherer_vorschub=500, eilgang=2000,
                spindel_ids=["spindel_a"],
                aktive_spindel_id="spindel_b",  # nicht in spindel_ids!
            )

    def test_inline_fallback_ohne_spindel_ids(self) -> None:
        """Schema-v1-Profile (ohne spindel_ids) funktionieren weiter."""
        m = Maschine(
            id="m1", name="X", hersteller="X", modell="X",
            controller=ControllerTyp.GRBL,
            arbeitsraum=Arbeitsraum(x=100, y=100, z=100),
            max_vorschub=1000, sicherer_vorschub=500, eilgang=2000,
            spindel_typ=SpindelTyp.PWM, spindel_rpm_min=8000, spindel_rpm_max=24000,
        )
        # Ohne Spindel-Index: Inline-Werte
        assert m.effektive_rpm_range() == (8000, 24000)
        assert m.effektiver_spindel_typ() == SpindelTyp.PWM
