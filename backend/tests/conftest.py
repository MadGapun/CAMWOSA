"""Gemeinsame pytest-Fixtures fuer alle Backend-Tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from camwosa.db.models import (
    Arbeitsraum,
    ControllerTyp,
    Maschine,
    MaschinenModus,
    Material,
    MaterialKategorie,
    NullpunktReferenz,
    Rohmaterial,
    RohmaterialForm,
    SchnittParameterPreset,
    SpindelTyp,
    Werkzeug,
    WerkzeugTyp,
)


@pytest.fixture
def proverxl_maschine() -> Maschine:
    """Genmitsu ProVerXL 4030 V2 als Test-Maschine."""
    return Maschine(
        id="genmitsu_proverxl_4030_v2",
        name="Genmitsu ProVerXL 4030 V2",
        hersteller="Genmitsu",
        modell="ProVerXL 4030 V2",
        controller=ControllerTyp.GRBL,
        arbeitsraum=Arbeitsraum(x=400.0, y=400.0, z=110.0),
        max_vorschub=3000.0,
        sicherer_vorschub=2000.0,
        eilgang=5000.0,
        spindel_typ=SpindelTyp.MANUELL,
        spindel_rpm_min=10000.0,
        spindel_rpm_max=30000.0,
        sicherheitshoehe=5.0,
        werkzeugwechsel_position=(0.0, 0.0, 100.0),
        postprozessor="grbl_genmitsu",
        modi=[MaschinenModus.STANDARD_XYZ, MaschinenModus.ROTARY_Y],
    )


@pytest.fixture
def schaftfraeser_6mm() -> Werkzeug:
    """Standard 6mm Schaftfraeser, 2-Schneider Hartmetall."""
    return Werkzeug(
        id="t01_schaft_6mm",
        name="6mm Schaftfraeser 2-Schneider Hartmetall",
        typ=WerkzeugTyp.SCHAFTFRAESER,
        durchmesser=6.0,
        schaft_durchmesser=6.0,
        schneidlaenge=22.0,
        gesamtlaenge=76.0,
        schneiden=2,
    )


@pytest.fixture
def vbit_60grad() -> Werkzeug:
    """V-Bit 60 Grad fuer Gravuren."""
    return Werkzeug(
        id="t02_vbit_60",
        name="V-Bit 60 Grad",
        typ=WerkzeugTyp.V_BIT,
        durchmesser=12.7,
        schaft_durchmesser=6.35,
        schneidlaenge=10.0,
        gesamtlaenge=38.0,
        schneiden=2,
        spitzenwinkel=60.0,
    )


@pytest.fixture
def material_buche() -> Material:
    return Material(
        id="buche_massiv",
        name="Buche massiv",
        kategorie=MaterialKategorie.HOLZ,
        unter_kategorie="Hartholz",
        janka_haerte=1300.0,
        dichte=0.72,
        schnittgeschwindigkeit_min=300.0,
        schnittgeschwindigkeit_max=600.0,
        presets=[
            SchnittParameterPreset(
                werkzeug_id="t01_schaft_6mm",
                rpm=18000.0,
                vorschub=2000.0,
                plunge=400.0,
                stepdown=2.0,
                stepover_prozent=40.0,
            )
        ],
    )


@pytest.fixture
def rohmaterial_buche_platte(material_buche: Material) -> Rohmaterial:
    return Rohmaterial(
        form=RohmaterialForm.PLATTE,
        laenge=300.0,
        breite=200.0,
        hoehe=18.0,
        material_id=material_buche.id,
        nullpunkt=(0.0, 0.0, 0.0),
        z_referenz=NullpunktReferenz.MATERIAL_TOP,
    )


@pytest.fixture
def jetzt() -> datetime:
    return datetime.now(timezone.utc)
