"""Datenmodelle (pydantic 2) fuer Maschine, Werkzeug, Material, Rohmaterial.

Diese Modelle sind die zentrale Basis fuer alle CAM-Operationen.
Sie werden sowohl in der Bibliothek als auch in der API und im MCP genutzt.

Siehe Wiki: docs/wiki/Datenmodell.md
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Maschine
# ---------------------------------------------------------------------------


class ControllerTyp(str, Enum):
    """CNC-Controller-Typen, die CAMWOSA kennt."""

    GRBL = "GRBL"
    MARLIN = "Marlin"
    LINUXCNC = "LinuxCNC"
    MACH3 = "Mach3"
    DUET = "Duet"
    SONSTIGE = "Sonstige"


class SpindelTyp(str, Enum):
    """Spindel-Typ (Steuerungsart)."""

    MANUELL = "manuell"  # z.B. Makita RT0700, kein PWM
    PWM = "PWM"
    ANALOG = "analog"


class MaschinenModus(str, Enum):
    """Modi die ein Maschinenprofil unterstuetzen kann."""

    STANDARD_XYZ = "standard_xyz"
    ROTARY_Y = "rotary_y"
    ROTARY_X = "rotary_x"
    LASER = "laser"
    DRAG_KNIFE = "drag_knife"


class Arbeitsraum(BaseModel):
    """Maximaler Verfahrweg in mm."""

    x: float = Field(gt=0, description="Verfahrweg X in mm")
    y: float = Field(gt=0, description="Verfahrweg Y in mm")
    z: float = Field(gt=0, description="Verfahrweg Z in mm")


class Maschine(BaseModel):
    """Maschinen-Profil."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Eindeutige ID, z.B. 'genmitsu_proverxl_4030_v2'")
    name: str = Field(description="Anzeigename")
    hersteller: str
    modell: str
    controller: ControllerTyp
    arbeitsraum: Arbeitsraum
    max_vorschub: float = Field(gt=0, description="Max. Vorschub in mm/min")
    sicherer_vorschub: float = Field(gt=0, description="Empfohlener Max-Vorschub fuer sichere Operationen")
    eilgang: float = Field(gt=0, description="G0-Geschwindigkeit in mm/min")
    spindel_typ: SpindelTyp
    spindel_rpm_min: float = Field(ge=0)
    spindel_rpm_max: float = Field(gt=0)
    sicherheitshoehe: float = Field(default=5.0, description="Z-Hoehe ueber Werkstueck-OK in mm")
    werkzeugwechsel_position: tuple[float, float, float] | None = Field(
        default=None, description="X,Y,Z fuer Werkzeugwechsel-Park-Position"
    )
    postprozessor: str = Field(default="grbl_standard", description="ID des Default-Postprozessors")
    modi: list[MaschinenModus] = Field(default_factory=lambda: [MaschinenModus.STANDARD_XYZ])
    aktiver_modus: MaschinenModus = MaschinenModus.STANDARD_XYZ
    notizen: str = ""

    @field_validator("sicherer_vorschub")
    @classmethod
    def _check_sicherer_vorschub(cls, v: float, info) -> float:
        max_vf = info.data.get("max_vorschub")
        if max_vf is not None and v > max_vf:
            raise ValueError("sicherer_vorschub darf nicht groesser als max_vorschub sein")
        return v

    @field_validator("spindel_rpm_max")
    @classmethod
    def _check_rpm(cls, v: float, info) -> float:
        rpm_min = info.data.get("spindel_rpm_min", 0)
        if v < rpm_min:
            raise ValueError("spindel_rpm_max muss >= spindel_rpm_min sein")
        return v


# ---------------------------------------------------------------------------
# Werkzeug
# ---------------------------------------------------------------------------


class WerkzeugTyp(str, Enum):
    """Werkzeug-Typen mit fester Geometrie-Semantik."""

    SCHAFTFRAESER = "schaftfraeser"
    KUGELFRAESER = "kugelfraeser"
    TORUSFRAESER = "torusfraeser"
    V_BIT = "v_bit"
    GRAVIERSTICHEL = "gravierstichel"
    BOHRER = "bohrer"
    EINSCHNEIDER = "einschneider"
    FISCHSCHWANZ = "fischschwanz"
    SCHRUPPFRAESER = "schruppfraeser"
    DIAMANTGRAVIERER = "diamantgravierer"


class WerkzeugMaterial(str, Enum):
    HSS = "HSS"
    HARTMETALL = "Hartmetall"
    DIAMANT = "Diamant"
    KERAMIK = "Keramik"


class WerkzeugBeschichtung(str, Enum):
    KEINE = "keine"
    TIN = "TiN"
    TIALN = "TiAlN"
    DLC = "DLC"
    NACO = "nACo"


class WerkzeugSteigung(str, Enum):
    """Spiralrichtung."""

    UPCUT = "upcut"
    DOWNCUT = "downcut"
    COMPRESSION = "compression"
    NEUTRAL = "neutral"  # z.B. Bohrer ohne Spiraleinfluss


class WerkzeugDrehrichtung(str, Enum):
    CW = "cw"  # Rechtslauf (M3)
    CCW = "ccw"  # Linkslauf (M4)


class Werkzeug(BaseModel):
    """Werkzeug-Definition mit allen Geometrie- und Anwendungs-Daten."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    typ: WerkzeugTyp
    material: WerkzeugMaterial = WerkzeugMaterial.HARTMETALL
    beschichtung: WerkzeugBeschichtung = WerkzeugBeschichtung.KEINE
    durchmesser: float = Field(gt=0, description="Schneid-Durchmesser in mm")
    schaft_durchmesser: float = Field(gt=0, description="Schaft-Durchmesser in mm")
    schneidlaenge: float = Field(gt=0, description="Schneidlaenge in mm")
    gesamtlaenge: float = Field(gt=0, description="Gesamtlaenge in mm")
    schneiden: int = Field(ge=1, le=12, description="Anzahl Schneiden")
    spitzenwinkel: float | None = Field(
        default=None, ge=10, le=180, description="V-Bit/Bohrer-Spitzenwinkel in Grad"
    )
    spitzenradius: float | None = Field(
        default=None, ge=0, description="Eckenradius bei Bull-Nose oder Ball-End-Radius"
    )
    drehrichtung: WerkzeugDrehrichtung = WerkzeugDrehrichtung.CW
    steigung: WerkzeugSteigung = WerkzeugSteigung.UPCUT
    notizen: str = ""

    @model_validator(mode="after")
    def _werkzeug_geometrie_check(self) -> "Werkzeug":
        if self.typ == WerkzeugTyp.V_BIT and self.spitzenwinkel is None:
            raise ValueError("spitzenwinkel ist Pflicht fuer V_BIT")
        return self


# ---------------------------------------------------------------------------
# Material
# ---------------------------------------------------------------------------


class MaterialKategorie(str, Enum):
    HOLZ = "holz"
    HOLZWERKSTOFF = "holzwerkstoff"
    KUNSTSTOFF = "kunststoff"
    NE_METALL = "ne_metall"
    METALL = "metall"
    SONSTIGES = "sonstiges"


class SchnittParameterPreset(BaseModel):
    """Schnittparameter fuer Werkzeug-Material-Kombination."""

    werkzeug_id: str
    rpm: float = Field(gt=0)
    vorschub: float = Field(gt=0, description="mm/min")
    plunge: float = Field(gt=0, description="mm/min")
    stepdown: float = Field(gt=0, description="mm pro Z-Pass")
    stepover_prozent: float = Field(gt=0, le=100, description="seitlicher Versatz in % vom Werkzeug-Durchmesser")


class Material(BaseModel):
    """Material-Definition mit Schnittparametern."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    kategorie: MaterialKategorie
    unter_kategorie: str = ""
    janka_haerte: float | None = Field(default=None, ge=0, description="Janka-Haerte (nur Holz)")
    dichte: float | None = Field(default=None, ge=0, description="g/cm3")
    schnittgeschwindigkeit_min: float | None = Field(
        default=None, description="Vc min in m/min"
    )
    schnittgeschwindigkeit_max: float | None = Field(
        default=None, description="Vc max in m/min"
    )
    presets: list[SchnittParameterPreset] = Field(default_factory=list)
    spaeneabsaugung_empfohlen: bool = False
    risiken: str = ""
    notizen: str = ""


# ---------------------------------------------------------------------------
# Rohmaterial
# ---------------------------------------------------------------------------


class RohmaterialForm(str, Enum):
    QUADER = "quader"
    ZYLINDER = "zylinder"
    PLATTE = "platte"
    FREI = "frei"


class NullpunktReferenz(str, Enum):
    """Wo der Nullpunkt sitzt."""

    MATERIAL_TOP = "material_top"
    MATERIAL_BOTTOM = "material_bottom"
    TISCH_TOP = "tisch_top"


class Rohmaterial(BaseModel):
    """Rohmaterial-Definition fuer ein Projekt."""

    model_config = ConfigDict(extra="ignore")

    form: RohmaterialForm
    laenge: float = Field(gt=0, description="X in mm")
    breite: float = Field(gt=0, description="Y in mm; bei Zylinder = Durchmesser")
    hoehe: float = Field(gt=0, description="Z in mm")
    material_id: str = Field(description="Verweis auf Material")
    nullpunkt: tuple[float, float, float] = Field(
        default=(0.0, 0.0, 0.0), description="X,Y,Z des Nullpunkts in Material-Koordinaten"
    )
    z_referenz: NullpunktReferenz = NullpunktReferenz.MATERIAL_TOP
    rotation_grad: float = Field(default=0.0, ge=-360, le=360)


# ---------------------------------------------------------------------------
# Projekt-Metadaten (das volle Projekt-Schema steht in project/schema.py)
# ---------------------------------------------------------------------------


class ProjektMetadaten(BaseModel):
    """Metadaten eines CAMWOSA-Projekts."""

    model_config = ConfigDict(extra="ignore")

    name: str
    autor: str = ""
    erstellt: datetime
    geaendert: datetime
    schema_version: int = 1
    notizen: str = ""
    aktive_variante: str = "default"


__all__ = [
    "Arbeitsraum",
    "ControllerTyp",
    "Maschine",
    "MaschinenModus",
    "Material",
    "MaterialKategorie",
    "NullpunktReferenz",
    "ProjektMetadaten",
    "Rohmaterial",
    "RohmaterialForm",
    "SchnittParameterPreset",
    "SpindelTyp",
    "Werkzeug",
    "WerkzeugBeschichtung",
    "WerkzeugDrehrichtung",
    "WerkzeugMaterial",
    "WerkzeugSteigung",
    "WerkzeugTyp",
]
