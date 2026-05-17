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
    # Adaptive-Clearing-spezifisch (Master-Plan E4) — nur bei strategie=ADAPTIVE genutzt
    adaptive_amplitude_faktor: float | None = Field(
        default=None, ge=0, le=0.5,
        description="Trochoidal-Modulationsamplitude als Faktor des Werkzeug-Durchmessers. None -> Default 0.05.",
    )
    adaptive_wellen_pro_mm: float = Field(
        default=0.5, gt=0,
        description="Wellen pro mm fuer die Trochoidal-Modulation (nur ADAPTIVE).",
    )


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


# ---------------------------------------------------------------------------
# Drechseln (Rotary-Achse: kontinuierliche A-Drehung waehrend X+Z-Bewegung)
# ---------------------------------------------------------------------------


class DrechselStrategie(str, Enum):
    """Wie das Profil abgetragen wird.

    - ``laengs_schruppen``: konzentrische, parallele Zylinder-Schalen entlang X.
      Schnelle Material-Abnahme, danach Schlichten noetig.
    - ``profil_schlichten``: Werkzeug folgt dem Profil in einem Pass.
      Saubere Oberflaeche, geringe Material-Abnahme pro Pass.
    - ``schrupp_und_schlicht``: erst Schruppen, dann Schlichten — ein
      Drechsel-Operations-Aufruf erzeugt beide Toolpath-Bloecke.
    - ``helix``: Helikale Nut/Schraube — Werkzeug faehrt mit synchronisiertem
      X-Vorschub entlang Werkstueck, waehrend die A-Achse mit fester Drehzahl
      rotiert. Steigung ``helix_steigung_mm_pro_umdrehung`` bestimmt die
      Verschiebung pro Werkstueck-Umdrehung. Mehrere Passes erlauben tiefere
      Nuten durch stufenweises Eintauchen.
    """

    LAENGS_SCHRUPPEN = "laengs_schruppen"
    PROFIL_SCHLICHTEN = "profil_schlichten"
    SCHRUPP_UND_SCHLICHT = "schrupp_und_schlicht"
    HELIX = "helix"


class DrechselParameter(OperationParameter):
    """Parameter fuer Drechsel-Operationen auf der Rotary-Achse.

    Hardware-Realitaet: das Fraeswerkzeug rotiert vertikal von oben, das
    Werkstueck dreht sich langsam darunter durch (Wrap-Carving — kein
    klassisches Drechseln). Siehe Modul-Docstring in ``cam/drechseln.py``.

    Das Profil ist eine Liste von ``(laenge_x_mm, radius_mm)``-Punkten —
    Halbschnitt eines rotationssymmetrischen Werkstuecks (linkes Ende
    laenge_x_mm=0). Beschreibt die AUSSENKONTUR — Innen-Hohlraeume sind
    auf dieser Hardware nicht moeglich.
    """

    strategie: DrechselStrategie = DrechselStrategie.SCHRUPP_UND_SCHLICHT
    rohmaterial_radius_mm: float = Field(
        gt=0,
        description="Werkstueck-Radius vor der Bearbeitung — vom Rotary-Rohmaterial",
    )
    aufmass_schlichten_mm: float = Field(
        default=0.3, ge=0,
        description="Restmaterial das nach dem Schruppen stehen bleibt (Schlicht-Reserve)",
    )
    schlicht_zustellung_mm: float = Field(
        default=0.5, gt=0,
        description="Wie viel Material der Schlichtgang pro Pass abnimmt",
    )
    drehzahl_werkstueck_upm: float = Field(
        default=200, gt=0,
        description="Werkstueck-Drehzahl in U/min (A-Achse). Achtung: NICHT die Spindel.",
    )
    profil: list[tuple[float, float]] = Field(
        default_factory=list,
        description="Halbschnitt: (laenge_x_mm, radius_mm)-Tupel, X aufsteigend",
    )

    # --- Helix-spezifisch (nur bei strategie=HELIX relevant) ---
    helix_steigung_mm_pro_umdrehung: float = Field(
        default=2.0, gt=0,
        description="Wie weit das Werkzeug pro Werkstueck-Umdrehung in X "
                     "vorrueckt — definiert die Helix-Steigung",
    )
    helix_tiefe_mm: float = Field(
        default=2.0, gt=0,
        description="Wie tief unter die Werkstueck-Oberflaeche das Werkzeug "
                     "eintaucht (= Radius-Reduktion gegenueber Profil)",
    )
    helix_anzahl_passes: int = Field(
        default=1, ge=1, le=20,
        description="Anzahl Passes — tieferes Nut wird in mehreren Schichten erzeugt",
    )
    helix_x_start_mm: float | None = Field(
        default=None,
        description="X-Anfang der Helix (None = profil[0].x)",
    )
    helix_x_ende_mm: float | None = Field(
        default=None,
        description="X-Ende der Helix (None = profil[-1].x)",
    )

    @model_validator(mode="after")
    def _check_profil(self) -> "DrechselParameter":
        if not self.profil:
            return self
        prev_x = -float("inf")
        for x, r in self.profil:
            if x < prev_x:
                raise ValueError(
                    "Profil-X-Werte muessen aufsteigend sortiert sein (laenge_x_mm)",
                )
            if r < 0:
                raise ValueError("Profil-Radien duerfen nicht negativ sein")
            if r > self.rohmaterial_radius_mm:
                raise ValueError(
                    f"Profil-Radius {r}mm an x={x}mm groesser als "
                    f"Rohmaterial-Radius {self.rohmaterial_radius_mm}mm — "
                    f"da ist kein Material zum Abtragen."
                )
            prev_x = x
        return self


__all__ = [
    "BohrParameter",
    "BohrStrategie",
    "DrechselParameter",
    "DrechselStrategie",
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
