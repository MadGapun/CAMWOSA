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


class SpindelHerkunft(str, Enum):
    """Standard / Upgrade / Eigenbau (fuer Community-Sharing)."""

    OEM = "oem"  # vom Maschinen-Hersteller mitgeliefert
    UPGRADE = "upgrade"  # vom User nachgeruestet
    EIGENBAU = "eigenbau"


class Spindel(BaseModel):
    """Spindel-Profil.

    Eine Maschine kann mehrere Spindeln haben (z.B. Original-Router + Makita-Upgrade).
    Die aktive Spindel wird im Projekt gewaehlt und ist Grundlage fuer
    RPM-Range, Drehzahl-Steuerung und Sicherheits-Checks.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="z.B. 'makita_rt0700' oder 'genmitsu_router_710w'")
    name: str
    hersteller: str
    modell: str
    typ: SpindelTyp = Field(description="manuell / PWM / analog")
    rpm_min: float = Field(ge=0)
    rpm_max: float = Field(gt=0)
    leistung_watt: float | None = Field(default=None, ge=0)
    drehmoment_ncm: float | None = Field(default=None, ge=0, description="Drehmoment in Ncm")
    gewicht_g: float | None = Field(default=None, ge=0)
    schaft_durchmesser_mm: float | None = Field(
        default=None, ge=0, description="Spannzangen-Standard, z.B. 6.0 / 6.35 / 8.0"
    )
    kuehlung: str = Field(default="luft", description="luft / wasser / sonstige")
    pwm_min_promille: float | None = Field(
        default=None, ge=0, le=1000,
        description="PWM-Wert (0-1000) der rpm_min entspricht (nur PWM-Spindeln)",
    )
    pwm_max_promille: float | None = Field(default=None, ge=0, le=1000)
    rampen_zeit_s: float | None = Field(
        default=None, ge=0, description="Zeit bis Spindel auf Solldrehzahl (Sicherheits-Pause)"
    )
    herkunft: SpindelHerkunft = SpindelHerkunft.OEM
    notizen: str = ""

    @model_validator(mode="after")
    def _check_rpm(self) -> "Spindel":
        if self.rpm_max < self.rpm_min:
            raise ValueError("rpm_max muss >= rpm_min sein")
        return self


class Arbeitsraum(BaseModel):
    """Maximaler Verfahrweg in mm."""

    x: float = Field(gt=0, description="Verfahrweg X in mm")
    y: float = Field(gt=0, description="Verfahrweg Y in mm")
    z: float = Field(gt=0, description="Verfahrweg Z in mm")


class Maschine(BaseModel):
    """Maschinen-Profil.

    Eine Maschine hat ein oder mehrere Spindeln (siehe Spindel-Klasse). Die
    bisherigen Inline-Felder ``spindel_typ`` + ``spindel_rpm_*`` sind weiterhin
    vorhanden — sie werden automatisch aus der aktiven Spindel abgeleitet
    falls eine ``aktive_spindel_id`` gesetzt ist (siehe ``aktive_spindel()``).

    So bleiben aeltere Maschinenprofile (Schema-Version 1) ohne Spindel-Refs
    weiterhin ladbar.
    """

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
    # --- Spindel-System ---
    spindel_ids: list[str] = Field(
        default_factory=list,
        description="IDs der Spindeln die fuer diese Maschine verfuegbar sind",
    )
    aktive_spindel_id: str | None = Field(
        default=None, description="Welche Spindel ist aktuell montiert"
    )
    # --- Rotary-Konfigurationen (Phase 3) ---
    rotary_profile_ids: list[str] = Field(
        default_factory=list,
        description="IDs der Rotary-Konfigurationen (aus data/rotary/) die fuer diese Maschine verfuegbar sind",
    )
    aktive_rotary_profil_id: str | None = Field(
        default=None,
        description="Aktuell montierte Rotary-Konfiguration (None wenn ohne Rotary)",
    )
    # --- Inline-Fallback (Schema v1, weiter unterstuetzt) ---
    spindel_typ: SpindelTyp = SpindelTyp.MANUELL
    spindel_rpm_min: float = Field(default=0, ge=0)
    spindel_rpm_max: float = Field(default=1, gt=0)
    # --- Sonstiges ---
    sicherheitshoehe: float = Field(default=5.0, description="Z-Hoehe ueber Werkstueck-OK in mm")
    werkzeugwechsel_position: tuple[float, float, float] | None = Field(
        default=None, description="X,Y,Z fuer Werkzeugwechsel-Park-Position"
    )
    postprozessor: str = Field(default="grbl_standard", description="ID des Default-Postprozessors")
    modi: list[MaschinenModus] = Field(default_factory=lambda: [MaschinenModus.STANDARD_XYZ])
    aktiver_modus: MaschinenModus = MaschinenModus.STANDARD_XYZ
    notizen: str = ""

    @model_validator(mode="after")
    def _check_konsistenz(self) -> "Maschine":
        if self.sicherer_vorschub > self.max_vorschub:
            raise ValueError("sicherer_vorschub darf nicht groesser als max_vorschub sein")
        if self.spindel_rpm_max < self.spindel_rpm_min:
            raise ValueError("spindel_rpm_max muss >= spindel_rpm_min sein")
        if self.aktive_spindel_id and self.aktive_spindel_id not in self.spindel_ids:
            raise ValueError(
                f"aktive_spindel_id '{self.aktive_spindel_id}' "
                f"nicht in spindel_ids {self.spindel_ids}"
            )
        if self.aktive_rotary_profil_id and self.aktive_rotary_profil_id not in self.rotary_profile_ids:
            raise ValueError(
                f"aktive_rotary_profil_id '{self.aktive_rotary_profil_id}' "
                f"nicht in rotary_profile_ids {self.rotary_profile_ids}"
            )
        return self

    def aktive_spindel(self, spindel_index: dict[str, "Spindel"]) -> "Spindel | None":
        """Liefert die aktive Spindel aus dem uebergebenen Spindel-Index, oder None."""
        if self.aktive_spindel_id and self.aktive_spindel_id in spindel_index:
            return spindel_index[self.aktive_spindel_id]
        return None

    def effektive_rpm_range(
        self, spindel_index: dict[str, "Spindel"] | None = None
    ) -> tuple[float, float]:
        """Liefert (rpm_min, rpm_max) der aktiven Spindel, sonst Inline-Werte."""
        if spindel_index:
            sp = self.aktive_spindel(spindel_index)
            if sp:
                return (sp.rpm_min, sp.rpm_max)
        return (self.spindel_rpm_min, self.spindel_rpm_max)

    def effektiver_spindel_typ(
        self, spindel_index: dict[str, "Spindel"] | None = None
    ) -> SpindelTyp:
        if spindel_index:
            sp = self.aktive_spindel(spindel_index)
            if sp:
                return sp.typ
        return self.spindel_typ


# ---------------------------------------------------------------------------
# Werkzeug
# ---------------------------------------------------------------------------


class WerkzeugTyp(str, Enum):
    """Werkzeug-Typen mit fester Geometrie-Semantik."""

    SCHAFTFRAESER = "schaftfraeser"
    KUGELFRAESER = "kugelfraeser"
    TORUSFRAESER = "torusfraeser"
    V_BIT = "v_bit"
    BALLNOSE_V_BIT = "ballnose_v_bit"  # A39: V-Bit mit Mini-Kugel-Spitze (robuster)
    GRAVIERSTICHEL = "gravierstichel"
    BOHRER = "bohrer"
    EINSCHNEIDER = "einschneider"
    FISCHSCHWANZ = "fischschwanz"
    SCHRUPPFRAESER = "schruppfraeser"
    DIAMANTGRAVIERER = "diamantgravierer"
    DRAG_GRAVIERER = "drag_gravierer"  # E6: Diamant ohne Spindel-Drehung (M5)


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


class WerkzeugSegment(BaseModel):
    """Ein konisches Segment des Werkzeugs entlang der Z-Achse.

    Erlaubt komplexe Geometrien wie Gravurstichel (Spitze 0.5 mm, dann
    konisch auf 3.175 mm Schaft) oder Schwalbenschwanz-Fraeser.

    Konvention: z_oben = 0 ist Werkzeug-Spitze, z waechst nach oben.
    """

    model_config = ConfigDict(extra="ignore")

    z_unten: float = Field(ge=0, description="Z-Position Segment-Unterkante (mm von Spitze)")
    z_oben: float = Field(gt=0, description="Z-Position Segment-Oberkante (mm von Spitze)")
    durchmesser_unten: float = Field(ge=0, description="Durchmesser an z_unten in mm")
    durchmesser_oben: float = Field(gt=0, description="Durchmesser an z_oben in mm")
    ist_schneide: bool = Field(
        default=False,
        description="Schneidet dieses Segment? (False = nur Schaft/Halter, kein Eingriff erlaubt)",
    )

    @model_validator(mode="after")
    def _check_z(self) -> "WerkzeugSegment":
        if self.z_oben <= self.z_unten:
            raise ValueError("z_oben muss > z_unten sein")
        return self


class Werkzeug(BaseModel):
    """Werkzeug-Definition mit allen Geometrie- und Anwendungs-Daten.

    Erweitertes Modell (ab v2):
    - Geometrie ist segmentiert (Cutter + Shaft + ggf. Halter) — fuer korrekte
      Kollisionserkennung bei konischen Werkzeugen wie Gravurstichel.
    - max_arbeitstiefe_mm pro Werkzeug — wird von Operations geprueft.
    - Smart-Helpers helfen den User beim Anlegen (auto-Berechnung von Winkel
      aus Schneidlaenge+Durchmesser, etc.).

    Rueckwaerts-kompatibel: die alten Felder (durchmesser, schneidlaenge,
    schaft_durchmesser, gesamtlaenge) sind weiter Pflicht — die Segmente
    sind ein Override fuer Praezision.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    typ: WerkzeugTyp
    material: WerkzeugMaterial = WerkzeugMaterial.HARTMETALL
    beschichtung: WerkzeugBeschichtung = WerkzeugBeschichtung.KEINE

    # --- Klassische Felder (Schema v1, weiter unterstuetzt) ---
    durchmesser: float = Field(gt=0, description="Schneid-Durchmesser in mm")
    schaft_durchmesser: float = Field(gt=0, description="Schaft-Durchmesser in mm")
    schneidlaenge: float = Field(gt=0, description="Schneidlaenge in mm")
    gesamtlaenge: float = Field(gt=0, description="Gesamtlaenge in mm")
    schneiden: int = Field(ge=1, le=12, description="Anzahl Schneiden")

    # --- Erweiterte Geometrie (Schema v2) ---
    segmente: list[WerkzeugSegment] = Field(
        default_factory=list,
        description="Segment-basierte Geometrie. Wenn leer: aus klassischen Feldern abgeleitet.",
    )
    halter_segmente: list[WerkzeugSegment] = Field(
        default_factory=list,
        description="Halter-Segmente (oberhalb gesamtlaenge). Fuer Kollisionserkennung.",
    )

    # --- Charakteristik ---
    spitzenwinkel: float | None = Field(
        default=None, ge=1, le=179,
        description="V-Bit/Bohrer-Spitzenwinkel in Grad. "
                    "Erweitert auf 1-179° fuer Relief-V-Bits (4°/8°/10°/15°/20°...)."
    )
    spitzenradius: float | None = Field(
        default=None, ge=0, description="Eckenradius bei Bull-Nose oder Ball-End-Radius"
    )
    spitzendurchmesser: float | None = Field(
        default=None, ge=0, description="Bei Gravurstichel/V-Bit: Durchmesser an der Spitze (kann 0 sein)"
    )

    # --- Limits ---
    max_arbeitstiefe_mm: float | None = Field(
        default=None, gt=0,
        description="Max. Bearbeitungstiefe pro Eintauchen (mm). "
                     "Wird in Operations geprueft, damit Schaft nicht ins Material taucht.",
    )

    drehrichtung: WerkzeugDrehrichtung = WerkzeugDrehrichtung.CW
    steigung: WerkzeugSteigung = WerkzeugSteigung.UPCUT

    # Standzeit-Tracking (Phase E2)
    standzeit_max_minuten: float | None = Field(
        default=None, ge=0,
        description="Erwartete Standzeit in Schnitt-Minuten (Erfahrungswert)",
    )

    # A46: Collet-Modell + Auto-Set-Speeds
    free_length_mm: float | None = Field(
        default=None, gt=0,
        description="Freie Werkzeug-Laenge vom Collet bis Spitze. "
                    "Genutzt fuer Collet-Collision-Check. Default = gesamtlaenge wenn None.",
    )
    auto_set_speeds: bool = Field(
        default=False,
        description="Wenn True: auto_feedrate + auto_spindel_rpm werden bei Werkzeug-Wahl "
                    "in Operationen uebernommen.",
    )
    auto_feedrate: float | None = Field(
        default=None, gt=0,
        description="Vorschlag-Vorschub mm/min wenn auto_set_speeds aktiv.",
    )
    auto_spindel_rpm: float | None = Field(
        default=None, gt=0,
        description="Vorschlag-Spindelspeed RPM wenn auto_set_speeds aktiv.",
    )

    notizen: str = ""

    @model_validator(mode="after")
    def _werkzeug_geometrie_check(self) -> "Werkzeug":
        if self.typ == WerkzeugTyp.V_BIT and self.spitzenwinkel is None:
            raise ValueError("spitzenwinkel ist Pflicht fuer V_BIT")
        if self.typ == WerkzeugTyp.BALLNOSE_V_BIT:
            if self.spitzenwinkel is None:
                raise ValueError("spitzenwinkel ist Pflicht fuer BALLNOSE_V_BIT")
            if self.spitzendurchmesser is None or self.spitzendurchmesser <= 0:
                raise ValueError(
                    "spitzendurchmesser (>0) ist Pflicht fuer BALLNOSE_V_BIT "
                    "(= Durchmesser der Mini-Kugel an der Spitze)"
                )
        # Auto-default: max_arbeitstiefe = schneidlaenge wenn nicht gesetzt
        if self.max_arbeitstiefe_mm is None:
            object.__setattr__(self, "max_arbeitstiefe_mm", self.schneidlaenge)
        # Auto-default: free_length = gesamtlaenge wenn nicht explizit gesetzt
        if self.free_length_mm is None:
            object.__setattr__(self, "free_length_mm", self.gesamtlaenge)
        return self

    # --- Smart-Helpers ---

    def effektive_segmente(self) -> list[WerkzeugSegment]:
        """Liefert die Segmente. Wenn keine explizit gesetzt, werden sie aus
        den klassischen Feldern abgeleitet (Cylinder Schneide + Cylinder Schaft).
        """
        if self.segmente:
            return self.segmente
        # Default: Schneidlaenge als Schneid-Segment, Rest bis gesamtlaenge als Schaft
        spitze_d = self.spitzendurchmesser
        if spitze_d is None and self.spitzenwinkel:
            # V-Bit: Spitze=0
            spitze_d = 0.0
        else:
            spitze_d = self.durchmesser
        return [
            WerkzeugSegment(
                z_unten=0.0,
                z_oben=self.schneidlaenge,
                durchmesser_unten=spitze_d,
                durchmesser_oben=self.durchmesser,
                ist_schneide=True,
            ),
            WerkzeugSegment(
                z_unten=self.schneidlaenge,
                z_oben=self.gesamtlaenge,
                durchmesser_unten=self.schaft_durchmesser,
                durchmesser_oben=self.schaft_durchmesser,
                ist_schneide=False,
            ),
        ]

    def durchmesser_bei_z(self, z_von_spitze: float) -> float:
        """Liefert den effektiven Werkzeug-Durchmesser bei einer Z-Position von der Spitze.

        Wichtig fuer Kollisionserkennung — z.B. ein Gravurstichel mit 0.5mm Spitze
        und 3.175mm Schaft bei z=5mm hat schon 3.175mm Durchmesser.
        """
        for seg in self.effektive_segmente():
            if seg.z_unten <= z_von_spitze <= seg.z_oben:
                # Lineare Interpolation
                if seg.z_oben == seg.z_unten:
                    return seg.durchmesser_unten
                t = (z_von_spitze - seg.z_unten) / (seg.z_oben - seg.z_unten)
                return seg.durchmesser_unten + t * (seg.durchmesser_oben - seg.durchmesser_unten)
        # Ausserhalb: max-Durchmesser
        return self.schaft_durchmesser

    def darf_in_tiefe(self, schnitttiefe_mm: float) -> bool:
        """Prueft ob die Bearbeitungstiefe vom Werkzeug noch zulaessig ist."""
        max_t = self.max_arbeitstiefe_mm or self.schneidlaenge
        return abs(schnitttiefe_mm) <= max_t


def berechne_v_bit_spitzendurchmesser(
    spitzenwinkel_grad: float, schneidlaenge_mm: float, durchmesser_max_mm: float,
) -> float:
    """Smart-Helper: Berechnet bei V-Bit den Durchmesser an der Spitze.

    Geometrie: bei einem konischen V-Bit ergibt sich der Spitzen-Durchmesser
    aus dem Winkel und der konischen Hoehe. Wenn der Konus auf voller
    Schneidlaenge bis zum Durchmesser_max laeuft, ist die Spitze 0.

    Eigentlich liefert diese Funktion einen Hinweis: Bei welchem Spitzenwinkel
    + Schneidlaenge wuerde der Konus den durchmesser_max ueberschreiten? Dann
    ist die Spitze nicht 0, sondern hat einen Rest-Durchmesser.
    """
    import math
    halb = math.radians(spitzenwinkel_grad / 2.0)
    # Bei 0er-Spitze laeuft d von 0 (unten) auf 2*tan(halb)*schneidlaenge (oben).
    d_an_oberkante = 2 * math.tan(halb) * schneidlaenge_mm
    if d_an_oberkante <= durchmesser_max_mm:
        return 0.0  # Spitze ist echt 0
    # Sonst: die Spitze ist abgestumpft auf einen Rest-Durchmesser
    # Wir loesen: 2*tan(halb)*z_unten + d_spitze = durchmesser_max
    # mit z_unten + schneidlaenge*tan(halb) = max-Hoehe ... eigentlich anders.
    # Vereinfacht: Spitze hat den Wert der noetig ist um auf durchmesser_max zu kommen
    return durchmesser_max_mm - 2 * math.tan(halb) * schneidlaenge_mm


def berechne_v_bit_winkel(
    spitzendurchmesser_mm: float, durchmesser_max_mm: float, schneidlaenge_mm: float,
) -> float:
    """Smart-Helper: Berechnet bei V-Bit den Spitzenwinkel aus Geometrie.

    z.B. Gravurstichel Spitze 0.3mm, Durchmesser oben 3.175mm, Schneidlaenge 6mm
    -> Halbwinkel = atan((d_oben - d_spitze)/2 / schneidlaenge)
    -> Spitzenwinkel = 2 * Halbwinkel
    """
    import math
    if schneidlaenge_mm <= 0:
        return 0.0
    halb_rad = math.atan((durchmesser_max_mm - spitzendurchmesser_mm) / 2.0 / schneidlaenge_mm)
    return 2 * math.degrees(halb_rad)


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
    "Spindel",
    "SpindelHerkunft",
    "SpindelTyp",
    "Werkzeug",
    "WerkzeugBeschichtung",
    "WerkzeugDrehrichtung",
    "WerkzeugMaterial",
    "WerkzeugSegment",
    "WerkzeugSteigung",
    "WerkzeugTyp",
    "berechne_v_bit_spitzendurchmesser",
    "berechne_v_bit_winkel",
]
