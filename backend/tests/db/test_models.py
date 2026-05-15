"""Tests fuer die pydantic-Datenmodelle."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from camwosa.db.models import (
    Arbeitsraum,
    ControllerTyp,
    Maschine,
    MaschinenModus,
    SpindelTyp,
    Werkzeug,
    WerkzeugTyp,
)


class TestMaschine:
    def test_proverxl_fixture_ist_valide(self, proverxl_maschine: Maschine) -> None:
        assert proverxl_maschine.controller == ControllerTyp.GRBL
        assert proverxl_maschine.arbeitsraum.x == 400.0
        assert proverxl_maschine.aktiver_modus == MaschinenModus.STANDARD_XYZ

    def test_sicherer_vorschub_darf_nicht_groesser_max_vorschub_sein(self) -> None:
        with pytest.raises(ValidationError, match="sicherer_vorschub"):
            Maschine(
                id="x",
                name="x",
                hersteller="x",
                modell="x",
                controller=ControllerTyp.GRBL,
                arbeitsraum=Arbeitsraum(x=100, y=100, z=100),
                max_vorschub=1000.0,
                sicherer_vorschub=2000.0,
                eilgang=3000.0,
                spindel_typ=SpindelTyp.MANUELL,
                spindel_rpm_min=10000,
                spindel_rpm_max=20000,
            )

    def test_rpm_max_kleiner_min_wird_abgelehnt(self) -> None:
        with pytest.raises(ValidationError, match="spindel_rpm_max"):
            Maschine(
                id="x",
                name="x",
                hersteller="x",
                modell="x",
                controller=ControllerTyp.GRBL,
                arbeitsraum=Arbeitsraum(x=100, y=100, z=100),
                max_vorschub=1000.0,
                sicherer_vorschub=500.0,
                eilgang=2000.0,
                spindel_typ=SpindelTyp.MANUELL,
                spindel_rpm_min=20000,
                spindel_rpm_max=10000,
            )

    def test_arbeitsraum_braucht_positive_werte(self) -> None:
        with pytest.raises(ValidationError):
            Arbeitsraum(x=-1, y=100, z=100)


class TestWerkzeug:
    def test_schaftfraeser_fixture_ist_valide(self, schaftfraeser_6mm: Werkzeug) -> None:
        assert schaftfraeser_6mm.typ == WerkzeugTyp.SCHAFTFRAESER
        assert schaftfraeser_6mm.durchmesser == 6.0

    def test_v_bit_braucht_spitzenwinkel(self) -> None:
        with pytest.raises(ValidationError, match="spitzenwinkel"):
            Werkzeug(
                id="x",
                name="V-Bit ohne Winkel",
                typ=WerkzeugTyp.V_BIT,
                durchmesser=10.0,
                schaft_durchmesser=6.35,
                schneidlaenge=10.0,
                gesamtlaenge=38.0,
                schneiden=2,
                # spitzenwinkel fehlt - muss validation error werfen
            )

    def test_v_bit_mit_winkel_ist_valide(self, vbit_60grad: Werkzeug) -> None:
        assert vbit_60grad.spitzenwinkel == 60.0

    def test_durchmesser_muss_positiv_sein(self) -> None:
        with pytest.raises(ValidationError):
            Werkzeug(
                id="x",
                name="x",
                typ=WerkzeugTyp.SCHAFTFRAESER,
                durchmesser=0,
                schaft_durchmesser=6,
                schneidlaenge=10,
                gesamtlaenge=20,
                schneiden=2,
            )

    def test_schneiden_max_12(self) -> None:
        with pytest.raises(ValidationError):
            Werkzeug(
                id="x",
                name="x",
                typ=WerkzeugTyp.SCHAFTFRAESER,
                durchmesser=6,
                schaft_durchmesser=6,
                schneidlaenge=10,
                gesamtlaenge=20,
                schneiden=15,
            )


class TestMaterial:
    def test_material_buche_fixture(self, material_buche) -> None:
        assert material_buche.janka_haerte == 1300
        assert len(material_buche.presets) == 1
        assert material_buche.presets[0].rpm == 18000


class TestRohmaterial:
    def test_platte_fixture(self, rohmaterial_buche_platte) -> None:
        assert rohmaterial_buche_platte.laenge == 300.0
        assert rohmaterial_buche_platte.hoehe == 18.0


class TestSerialisierung:
    def test_maschine_json_roundtrip(self, proverxl_maschine: Maschine) -> None:
        as_json = proverxl_maschine.model_dump_json()
        wiederhergestellt = Maschine.model_validate_json(as_json)
        assert wiederhergestellt == proverxl_maschine

    def test_werkzeug_json_roundtrip(self, schaftfraeser_6mm: Werkzeug) -> None:
        as_json = schaftfraeser_6mm.model_dump_json()
        wiederhergestellt = Werkzeug.model_validate_json(as_json)
        assert wiederhergestellt == schaftfraeser_6mm

    def test_extra_felder_werden_ignoriert(self, proverxl_maschine: Maschine) -> None:
        """Forward-Compat: zusaetzliche Felder in JSON brechen nicht den Parser."""
        as_dict = proverxl_maschine.model_dump()
        as_dict["zukuenftiges_feld"] = "neuer_wert"
        wiederhergestellt = Maschine.model_validate(as_dict)
        assert wiederhergestellt.id == proverxl_maschine.id
