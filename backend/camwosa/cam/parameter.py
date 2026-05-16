"""Pydantic-Parameter fuer CAM-Operationen.

Jede Operation hat ein eigenes Parameter-Modell. So sind die Parameter
typsicher (auch ueber API/MCP) und valid-by-construction.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Enums fuer alle Operations-Parameter
# ---------------------------------------------------------------------------


class KonturSeite(str, Enum):
    INNEN = "innen"
    AUSSEN = "aussen"
    AUF_LINIE = "auf_linie"


class FraesRichtung(str, Enum):
    GLEICHLAUF = "gleichlauf"
    GEGENLAUF = "gegenlauf"


class Eintauchstrategie(str, Enum):
    SENKRECHT = "senkrecht"
    RAMPE = "rampe"
    HELIX = "helix"


class TaschenStrategie(str, Enum):
    PARALLEL = "parallel"
    SPIRAL_AUSSEN = "spiral_aussen"
    SPIRAL_INNEN = "spiral_innen"
    OFFSET_KONTUR = "offset_kontur"
    ADAPTIVE = "adaptive"


class BohrStrategie(str, Enum):
    STANDARD = "standard"
    PECK = "peck"
    TIEF_PECK = "tief_peck"
    HELIX = "helix"
    REIB = "reib"


class GravurStrategie(str, Enum):
    KONSTANTE_TIEFE = "konstante_tiefe"
    V_CARVING = "v_carving"


# ---------------------------------------------------------------------------
# Parameter-Basisklasse
# ---------------------------------------------------------------------------


class OperationParameter(BaseModel):
    """Gemeinsame Felder aller CAM-Operationen."""

    model_config = ConfigDict(extra="ignore")

    werkzeug_id: str
    spindel_rpm: float = Field(gt=0)
    vorschub: float = Field(gt=0, description="mm/min")
    eintauch_vorschub: float = Field(gt=0, description="mm/min")
    sicherheitshoehe: float = Field(default=5.0, gt=0)
    max_tiefe: float = Field(gt=0, description="Max. Bearbeitungstiefe in mm (positiv)")
    stepdown: float = Field(gt=0, description="Tiefe pro Z-Pass in mm")

    @model_validator(mode="after")
    def _stepdown_kleiner_max_tiefe(self) -> "OperationParameter":
        if self.stepdown > self.max_tiefe:
            # Erlaubt: wir clampen einfach. Aber Hinweis im Modell sinnvoller.
            object.__setattr__(self, "stepdown", self.max_tiefe)
        return self


# ---------------------------------------------------------------------------
# Konkrete Parameter
# ---------------------------------------------------------------------------


class KonturParameter(OperationParameter):
    seite: KonturSeite = KonturSeite.AUSSEN
    fraes_richtung: FraesRichtung = FraesRichtung.GLEICHLAUF
    eintauch_strategie: Eintauchstrategie = Eintauchstrategie.RAMPE
    rampe_winkel_grad: float = Field(default=15.0, gt=0, le=45)
    tabs_anzahl: int = Field(default=0, ge=0, le=20)
    tabs_hoehe: float = Field(default=1.5, ge=0)
    tabs_breite: float = Field(default=4.0, ge=0)
    aufmass: float = Field(default=0.0, ge=0, description="Material das stehen bleibt (mm)")
    schlichtgang: bool = False
    lead_in_laenge: float = Field(default=0.0, ge=0)
    lead_out_laenge: float = Field(default=0.0, ge=0)


class TaschenParameter(OperationParameter):
    strategie: TaschenStrategie = TaschenStrategie.PARALLEL
    stepover_prozent: float = Field(default=40.0, gt=0, le=95, description="% vom Werkzeug-Durchmesser")
    eintauch_strategie: Eintauchstrategie = Eintauchstrategie.HELIX
    rampe_winkel_grad: float = Field(default=15.0, gt=0, le=45)
    aufmass_wand: float = Field(default=0.0, ge=0)
    aufmass_boden: float = Field(default=0.0, ge=0)
    schlichtgang_wand: bool = False
    schlichtgang_boden: bool = False
    fraes_richtung: FraesRichtung = FraesRichtung.GLEICHLAUF


class BohrParameter(OperationParameter):
    strategie: BohrStrategie = BohrStrategie.PECK
    peck_tiefe: float = Field(default=2.0, gt=0)
    dwell_sekunden: float = Field(default=0.0, ge=0)
    rueckzugs_hoehe: float = Field(default=2.0, ge=0)
    # Fuer HELIX + REIB: Soll-Durchmesser des Loches (groesser als Werkzeug)
    loch_durchmesser: float | None = Field(
        default=None, gt=0,
        description="Bei HELIX/REIB: Loch-Soll-Durchmesser (muss >= Werkzeug-Durchmesser sein)",
    )
    helix_steigung: float = Field(
        default=0.5, gt=0,
        description="Steigung pro Helix-Umdrehung in mm (HELIX-Strategie)",
    )


class GravurParameter(OperationParameter):
    strategie: GravurStrategie = GravurStrategie.KONSTANTE_TIEFE
    spitzenwinkel_grad: float | None = Field(
        default=None, description="Pflicht bei V_CARVING (uebernimmt vom Werkzeug wenn None)"
    )
    max_zustellung: float = Field(default=0.5, gt=0, description="Max. Zustellung pro Pass in mm")


__all__ = [
    "BohrParameter",
    "BohrStrategie",
    "Eintauchstrategie",
    "FraesRichtung",
    "GravurParameter",
    "GravurStrategie",
    "KonturParameter",
    "KonturSeite",
    "OperationParameter",
    "TaschenParameter",
    "TaschenStrategie",
]
