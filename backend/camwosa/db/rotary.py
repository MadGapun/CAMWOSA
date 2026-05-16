"""Rotary-Setup-Modell (Phase 3 Erweiterung).

Beschreibt die konkrete Rotary-Hardware + das aktuell eingespannte
Rohmaterial-Profil. Ein Maschinenprofil kann mehrere Rotary-Konfigurationen
haben (z.B. „Mit Reitstock" vs. „Fliegend").

Geometrie- und Nullpunkt-Optionen sind die der Praxis: rund (Rundling),
rechteckig (Vierkant), oder freies 3D-Modell (z.B. unregelmaessiges
Restholz als STL).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RotaryRohmaterialForm(str, Enum):
    RUND = "rund"
    RECHTECKIG = "rechteckig"
    MODELL_3D = "modell_3d"  # eigenes STL-Modell


class RotaryNullpunktReferenz(str, Enum):
    """Wo der Nullpunkt der Rotary-Achse sitzt."""

    MITTE_DREHACHSE = "mitte_drehachse"      # Z=0 auf der Drehachse-Mitte
    OBERKANTE_ROHMATERIAL = "oberkante_rohmaterial"  # Z=0 auf hoechstem Punkt
    SPANNFUTTER_BACKE = "spannfutter_backe"  # X=0 an der Backen-Vorderseite
    REITSTOCK = "reitstock"                  # X=0 am Reitstock


class RotaryProfil(BaseModel):
    """Eine konkrete Rotary-Konfiguration.

    Ein Maschinenprofil kann mehrere dieser Konfigurationen haben — z.B.
    "Mit Reitstock" und "Fliegend" je nach Werkstuecklaenge.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str = Field(description="Anzeigename, z.B. 'Mit Reitstock'")
    hersteller: str = "Generisch"
    modell: str = ""
    quelle_url: str | None = Field(
        default=None, description="Link zum Hersteller/Bestellung (Community-Sharing)"
    )

    # Hardware
    spannfutter_backen_anzahl: int = Field(default=3, ge=2, le=8)
    spannfutter_max_durchmesser_mm: float = Field(gt=0, description="Max. spannbarer Durchmesser")
    spannfutter_min_durchmesser_mm: float = Field(default=0, ge=0)
    hat_reitstock: bool = False
    reitstock_verstellbar_mm: float | None = Field(
        default=None, ge=0,
        description="Pinole-Hub, wenn Reitstock vorhanden",
    )
    max_werkstueck_laenge_mm: float = Field(
        gt=0,
        description="Maximale Werkstuecklaenge zwischen Spannfutter und Reitstock (oder fliegend).",
    )
    durchschiebbar: bool = Field(
        default=False,
        description="Kann das Werkstueck durch das Spannfutter geschoben werden? "
                     "(Wichtig fuer lange Werkstuecke die in mehreren Setups bearbeitet werden)",
    )

    # GRBL-Setup-Hinweise
    grbl_y_steps_pro_grad: float | None = Field(
        default=None, gt=0,
        description="$101-Wert bei Y-Achs-Replacement, z.B. 88.889 fuer 1:36 Schneckengetriebe",
    )
    grbl_y_limit_aufheben: bool = Field(
        default=False,
        description="Erfordert $131=9999 zum Aufheben des Y-Soft-Limits.",
    )
    cncjs_macro_ein: str | None = Field(
        default=None, description="Name des CNCjs-Macros zum Aktivieren der Rotary-Settings",
    )
    cncjs_macro_aus: str | None = Field(default=None)

    notizen: str = ""


class RotaryRohmaterial(BaseModel):
    """Konkretes eingespanntes Rohmaterial in einer Rotary-Konfiguration."""

    model_config = ConfigDict(extra="ignore")

    form: RotaryRohmaterialForm
    durchmesser_mm: float | None = Field(
        default=None, gt=0,
        description="Bei RUND: Werkstueck-Durchmesser",
    )
    laenge_mm: float = Field(gt=0, description="Werkstueck-Laenge in mm")
    breite_mm: float | None = Field(
        default=None, gt=0,
        description="Bei RECHTECKIG: Werkstueck-Breite (Y-Richtung)",
    )
    hoehe_mm: float | None = Field(
        default=None, gt=0,
        description="Bei RECHTECKIG: Werkstueck-Hoehe (Z-Richtung)",
    )
    stl_pfad: str | None = Field(
        default=None,
        description="Bei MODELL_3D: Pfad zur STL-Datei",
    )
    material_id: str = Field(description="Verweis auf Material")

    # Nullpunkt-Konfiguration
    nullpunkt_referenz: RotaryNullpunktReferenz = RotaryNullpunktReferenz.MITTE_DREHACHSE
    nullpunkt_x_versatz_mm: float = Field(
        default=0.0,
        description="Versatz der Werkstueck-Vorderkante vom Spannfutter (positive Richtung X)",
    )

    @model_validator(mode="after")
    def _form_konsistenz(self) -> "RotaryRohmaterial":
        if self.form == RotaryRohmaterialForm.RUND:
            if self.durchmesser_mm is None:
                raise ValueError("RUND braucht durchmesser_mm")
        elif self.form == RotaryRohmaterialForm.RECHTECKIG:
            if self.breite_mm is None or self.hoehe_mm is None:
                raise ValueError("RECHTECKIG braucht breite_mm + hoehe_mm")
        elif self.form == RotaryRohmaterialForm.MODELL_3D:
            if self.stl_pfad is None:
                raise ValueError("MODELL_3D braucht stl_pfad")
        return self

    def effektiver_radius(self) -> float:
        """Liefert den Radius fuer Wrapping/Vorschub-Berechnung."""
        if self.form == RotaryRohmaterialForm.RUND:
            return (self.durchmesser_mm or 0) / 2.0
        if self.form == RotaryRohmaterialForm.RECHTECKIG:
            # Halbdiagonale ist der max. Drehradius
            import math
            b = self.breite_mm or 0
            h = self.hoehe_mm or 0
            return math.hypot(b, h) / 2.0
        # MODELL_3D: Aus STL-Bounding-Box ableiten — Aufrufer regelt das
        return 0.0


__all__ = [
    "RotaryNullpunktReferenz",
    "RotaryProfil",
    "RotaryRohmaterial",
    "RotaryRohmaterialForm",
]
