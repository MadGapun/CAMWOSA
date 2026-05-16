"""Per-Feature-Override-System fuer CAM-Operationen.

Idee:
- Jede Operation hat **Overrides**: ein Modell wo jedes Feld optional ist.
- Ein Feld == None heisst: nutze Default aus Material/Werkzeug/Projekt.
- Ein Feld != None heisst: dieser Wert ueberschreibt den Default.

Beim Toolpath-Berechnen wird mit ``aufloese_*`` der effektive Parameter
berechnet. Der Frontend kann pro Feld einen ``Reset"-Button anbieten, der
das Override auf ``None`` setzt.

Siehe Wiki: docs/wiki/Per-Feature-Override.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from camwosa.cam.parameter import (
    BohrParameter,
    BohrStrategie,
    Eintauchstrategie,
    FraesRichtung,
    GravurParameter,
    GravurStrategie,
    KonturParameter,
    KonturSeite,
    TaschenParameter,
    TaschenStrategie,
)
from camwosa.db.models import Maschine, Material, Werkzeug


# ---------------------------------------------------------------------------
# Override-Modelle (alle Felder optional)
# ---------------------------------------------------------------------------


class OverrideBasis(BaseModel):
    """Gemeinsame Felder. None = Default verwenden."""

    model_config = ConfigDict(extra="ignore")

    werkzeug_id: str  # Pflicht — bestimmt die Defaults
    spindel_rpm: float | None = None
    vorschub: float | None = None
    eintauch_vorschub: float | None = None
    sicherheitshoehe: float | None = None
    max_tiefe: float | None = None
    stepdown: float | None = None


class KonturOverrides(OverrideBasis):
    seite: KonturSeite | None = None
    fraes_richtung: FraesRichtung | None = None
    eintauch_strategie: Eintauchstrategie | None = None
    rampe_winkel_grad: float | None = None
    tabs_anzahl: int | None = None
    tabs_hoehe: float | None = None
    tabs_breite: float | None = None
    aufmass: float | None = None
    schlichtgang: bool | None = None
    lead_in_laenge: float | None = None
    lead_out_laenge: float | None = None


class TaschenOverrides(OverrideBasis):
    strategie: TaschenStrategie | None = None
    stepover_prozent: float | None = None
    eintauch_strategie: Eintauchstrategie | None = None
    rampe_winkel_grad: float | None = None
    aufmass_wand: float | None = None
    aufmass_boden: float | None = None
    schlichtgang_wand: bool | None = None
    schlichtgang_boden: bool | None = None
    fraes_richtung: FraesRichtung | None = None


class BohrOverrides(OverrideBasis):
    strategie: BohrStrategie | None = None
    peck_tiefe: float | None = None
    dwell_sekunden: float | None = None
    rueckzugs_hoehe: float | None = None


class GravurOverrides(OverrideBasis):
    strategie: GravurStrategie | None = None
    spitzenwinkel_grad: float | None = None
    max_zustellung: float | None = None


# ---------------------------------------------------------------------------
# Defaults (projektweit / werkstoffweit) und Resolver
# ---------------------------------------------------------------------------


@dataclass
class ProjektDefaults:
    """Standardwerte auf Projekt-Ebene (gelten fuer alle Operationen).

    Diese Defaults stehen ueber den Werkzeug-/Material-Presets, aber unter
    den Operation-spezifischen Overrides.
    """

    sicherheitshoehe: float = 5.0
    max_tiefe: float = 6.0
    stepdown: float = 2.0
    # Operations-Typ-spezifische Defaults
    kontur_seite: KonturSeite = KonturSeite.AUSSEN
    kontur_eintauchstrategie: Eintauchstrategie = Eintauchstrategie.RAMPE
    kontur_rampe_winkel_grad: float = 15.0
    kontur_fraes_richtung: FraesRichtung = FraesRichtung.GLEICHLAUF
    tasche_strategie: TaschenStrategie = TaschenStrategie.PARALLEL
    tasche_stepover_prozent: float = 40.0
    tasche_eintauchstrategie: Eintauchstrategie = Eintauchstrategie.HELIX
    bohren_strategie: BohrStrategie = BohrStrategie.PECK
    bohren_peck_tiefe: float = 2.0
    bohren_rueckzugshoehe: float = 2.0
    gravur_strategie: GravurStrategie = GravurStrategie.KONSTANTE_TIEFE
    gravur_max_zustellung: float = 0.5


@dataclass
class AufloesungsErgebnis:
    """Effektive Parameter + Aufschluesselung pro Feld woher der Wert kommt."""

    parameter: Any  # konkret: KonturParameter | TaschenParameter | ...
    quellen: dict[str, str] = field(default_factory=dict)
    # quellen[feldname] in {"override", "material_preset", "projekt_default", "fallback"}


def _preset_fuer(material: Material, werkzeug: Werkzeug):
    return next((p for p in material.presets if p.werkzeug_id == werkzeug.id), None)


def _waehle(
    override_val,
    *,
    preset_val=None,
    projekt_val=None,
    fallback,
    feld: str,
    quellen: dict[str, str],
):
    """Auswahl-Hierarchie: override > material_preset > projekt_default > fallback."""
    if override_val is not None:
        quellen[feld] = "override"
        return override_val
    if preset_val is not None:
        quellen[feld] = "material_preset"
        return preset_val
    if projekt_val is not None:
        quellen[feld] = "projekt_default"
        return projekt_val
    quellen[feld] = "fallback"
    return fallback


def aufloese_kontur(
    overrides: KonturOverrides,
    material: Material,
    werkzeug: Werkzeug,
    defaults: ProjektDefaults | None = None,
) -> AufloesungsErgebnis:
    d = defaults or ProjektDefaults()
    p = _preset_fuer(material, werkzeug)
    q: dict[str, str] = {}

    rpm = _waehle(overrides.spindel_rpm, preset_val=p.rpm if p else None,
                  fallback=12000, feld="spindel_rpm", quellen=q)
    vf = _waehle(overrides.vorschub, preset_val=p.vorschub if p else None,
                 fallback=1500, feld="vorschub", quellen=q)
    plunge = _waehle(overrides.eintauch_vorschub, preset_val=p.plunge if p else None,
                     fallback=vf * 0.2, feld="eintauch_vorschub", quellen=q)
    sh = _waehle(overrides.sicherheitshoehe, projekt_val=d.sicherheitshoehe,
                 fallback=5.0, feld="sicherheitshoehe", quellen=q)
    mt = _waehle(overrides.max_tiefe, projekt_val=d.max_tiefe,
                 fallback=6.0, feld="max_tiefe", quellen=q)
    sd = _waehle(overrides.stepdown, preset_val=p.stepdown if p else None,
                 projekt_val=d.stepdown, fallback=2.0, feld="stepdown", quellen=q)

    param = KonturParameter(
        werkzeug_id=overrides.werkzeug_id,
        spindel_rpm=rpm, vorschub=vf, eintauch_vorschub=plunge,
        sicherheitshoehe=sh, max_tiefe=mt, stepdown=sd,
        seite=_waehle(overrides.seite, projekt_val=d.kontur_seite,
                      fallback=KonturSeite.AUSSEN, feld="seite", quellen=q),
        fraes_richtung=_waehle(overrides.fraes_richtung,
                               projekt_val=d.kontur_fraes_richtung,
                               fallback=FraesRichtung.GLEICHLAUF,
                               feld="fraes_richtung", quellen=q),
        eintauch_strategie=_waehle(overrides.eintauch_strategie,
                                   projekt_val=d.kontur_eintauchstrategie,
                                   fallback=Eintauchstrategie.RAMPE,
                                   feld="eintauch_strategie", quellen=q),
        rampe_winkel_grad=_waehle(overrides.rampe_winkel_grad,
                                  projekt_val=d.kontur_rampe_winkel_grad,
                                  fallback=15.0, feld="rampe_winkel_grad", quellen=q),
        tabs_anzahl=_waehle(overrides.tabs_anzahl, fallback=0,
                            feld="tabs_anzahl", quellen=q),
        tabs_hoehe=_waehle(overrides.tabs_hoehe, fallback=1.5,
                           feld="tabs_hoehe", quellen=q),
        tabs_breite=_waehle(overrides.tabs_breite, fallback=4.0,
                            feld="tabs_breite", quellen=q),
        aufmass=_waehle(overrides.aufmass, fallback=0.0,
                        feld="aufmass", quellen=q),
        schlichtgang=_waehle(overrides.schlichtgang, fallback=False,
                             feld="schlichtgang", quellen=q),
        lead_in_laenge=_waehle(overrides.lead_in_laenge, fallback=0.0,
                               feld="lead_in_laenge", quellen=q),
        lead_out_laenge=_waehle(overrides.lead_out_laenge, fallback=0.0,
                                feld="lead_out_laenge", quellen=q),
    )
    return AufloesungsErgebnis(parameter=param, quellen=q)


def aufloese_tasche(
    overrides: TaschenOverrides,
    material: Material,
    werkzeug: Werkzeug,
    defaults: ProjektDefaults | None = None,
) -> AufloesungsErgebnis:
    d = defaults or ProjektDefaults()
    p = _preset_fuer(material, werkzeug)
    q: dict[str, str] = {}

    rpm = _waehle(overrides.spindel_rpm, preset_val=p.rpm if p else None,
                  fallback=12000, feld="spindel_rpm", quellen=q)
    vf = _waehle(overrides.vorschub, preset_val=p.vorschub if p else None,
                 fallback=1500, feld="vorschub", quellen=q)
    plunge = _waehle(overrides.eintauch_vorschub, preset_val=p.plunge if p else None,
                     fallback=vf * 0.2, feld="eintauch_vorschub", quellen=q)
    sh = _waehle(overrides.sicherheitshoehe, projekt_val=d.sicherheitshoehe,
                 fallback=5.0, feld="sicherheitshoehe", quellen=q)
    mt = _waehle(overrides.max_tiefe, projekt_val=d.max_tiefe,
                 fallback=4.0, feld="max_tiefe", quellen=q)
    sd = _waehle(overrides.stepdown, preset_val=p.stepdown if p else None,
                 projekt_val=d.stepdown, fallback=2.0, feld="stepdown", quellen=q)
    stepover = _waehle(overrides.stepover_prozent,
                       preset_val=p.stepover_prozent if p else None,
                       projekt_val=d.tasche_stepover_prozent,
                       fallback=40.0, feld="stepover_prozent", quellen=q)

    param = TaschenParameter(
        werkzeug_id=overrides.werkzeug_id,
        spindel_rpm=rpm, vorschub=vf, eintauch_vorschub=plunge,
        sicherheitshoehe=sh, max_tiefe=mt, stepdown=sd,
        strategie=_waehle(overrides.strategie, projekt_val=d.tasche_strategie,
                          fallback=TaschenStrategie.PARALLEL,
                          feld="strategie", quellen=q),
        stepover_prozent=stepover,
        eintauch_strategie=_waehle(overrides.eintauch_strategie,
                                   projekt_val=d.tasche_eintauchstrategie,
                                   fallback=Eintauchstrategie.HELIX,
                                   feld="eintauch_strategie", quellen=q),
        rampe_winkel_grad=_waehle(overrides.rampe_winkel_grad,
                                  projekt_val=15.0, fallback=15.0,
                                  feld="rampe_winkel_grad", quellen=q),
        aufmass_wand=_waehle(overrides.aufmass_wand, fallback=0.0,
                             feld="aufmass_wand", quellen=q),
        aufmass_boden=_waehle(overrides.aufmass_boden, fallback=0.0,
                              feld="aufmass_boden", quellen=q),
        schlichtgang_wand=_waehle(overrides.schlichtgang_wand, fallback=False,
                                  feld="schlichtgang_wand", quellen=q),
        schlichtgang_boden=_waehle(overrides.schlichtgang_boden, fallback=False,
                                   feld="schlichtgang_boden", quellen=q),
        fraes_richtung=_waehle(overrides.fraes_richtung,
                               projekt_val=d.kontur_fraes_richtung,
                               fallback=FraesRichtung.GLEICHLAUF,
                               feld="fraes_richtung", quellen=q),
    )
    return AufloesungsErgebnis(parameter=param, quellen=q)


def aufloese_bohren(
    overrides: BohrOverrides,
    material: Material,
    werkzeug: Werkzeug,
    defaults: ProjektDefaults | None = None,
) -> AufloesungsErgebnis:
    d = defaults or ProjektDefaults()
    p = _preset_fuer(material, werkzeug)
    q: dict[str, str] = {}

    rpm = _waehle(overrides.spindel_rpm, preset_val=p.rpm if p else None,
                  fallback=12000, feld="spindel_rpm", quellen=q)
    plunge = _waehle(overrides.eintauch_vorschub, preset_val=p.plunge if p else None,
                     fallback=300, feld="eintauch_vorschub", quellen=q)
    vf = _waehle(overrides.vorschub, preset_val=p.vorschub if p else None,
                 fallback=500, feld="vorschub", quellen=q)
    sh = _waehle(overrides.sicherheitshoehe, projekt_val=d.sicherheitshoehe,
                 fallback=5.0, feld="sicherheitshoehe", quellen=q)
    mt = _waehle(overrides.max_tiefe, projekt_val=10.0,
                 fallback=10.0, feld="max_tiefe", quellen=q)
    sd = _waehle(overrides.stepdown, fallback=mt,
                 feld="stepdown", quellen=q)

    param = BohrParameter(
        werkzeug_id=overrides.werkzeug_id,
        spindel_rpm=rpm, vorschub=vf, eintauch_vorschub=plunge,
        sicherheitshoehe=sh, max_tiefe=mt, stepdown=sd,
        strategie=_waehle(overrides.strategie, projekt_val=d.bohren_strategie,
                          fallback=BohrStrategie.PECK,
                          feld="strategie", quellen=q),
        peck_tiefe=_waehle(overrides.peck_tiefe, projekt_val=d.bohren_peck_tiefe,
                           fallback=2.0, feld="peck_tiefe", quellen=q),
        dwell_sekunden=_waehle(overrides.dwell_sekunden, fallback=0.0,
                               feld="dwell_sekunden", quellen=q),
        rueckzugs_hoehe=_waehle(overrides.rueckzugs_hoehe,
                                projekt_val=d.bohren_rueckzugshoehe,
                                fallback=2.0, feld="rueckzugs_hoehe", quellen=q),
    )
    return AufloesungsErgebnis(parameter=param, quellen=q)


def aufloese_gravur(
    overrides: GravurOverrides,
    material: Material,
    werkzeug: Werkzeug,
    defaults: ProjektDefaults | None = None,
) -> AufloesungsErgebnis:
    d = defaults or ProjektDefaults()
    p = _preset_fuer(material, werkzeug)
    q: dict[str, str] = {}

    rpm = _waehle(overrides.spindel_rpm, preset_val=p.rpm if p else None,
                  fallback=18000, feld="spindel_rpm", quellen=q)
    vf = _waehle(overrides.vorschub, preset_val=p.vorschub if p else None,
                 fallback=1500, feld="vorschub", quellen=q)
    plunge = _waehle(overrides.eintauch_vorschub, preset_val=p.plunge if p else None,
                     fallback=vf * 0.2, feld="eintauch_vorschub", quellen=q)
    sh = _waehle(overrides.sicherheitshoehe, projekt_val=d.sicherheitshoehe,
                 fallback=5.0, feld="sicherheitshoehe", quellen=q)
    mt = _waehle(overrides.max_tiefe, projekt_val=1.0,
                 fallback=1.0, feld="max_tiefe", quellen=q)
    sd = _waehle(overrides.stepdown, fallback=0.5,
                 feld="stepdown", quellen=q)
    spitze = overrides.spitzenwinkel_grad
    if spitze is None and werkzeug.spitzenwinkel is not None:
        spitze = werkzeug.spitzenwinkel
        q["spitzenwinkel_grad"] = "werkzeug"
    else:
        q["spitzenwinkel_grad"] = "override" if overrides.spitzenwinkel_grad else "fallback"

    param = GravurParameter(
        werkzeug_id=overrides.werkzeug_id,
        spindel_rpm=rpm, vorschub=vf, eintauch_vorschub=plunge,
        sicherheitshoehe=sh, max_tiefe=mt, stepdown=sd,
        strategie=_waehle(overrides.strategie, projekt_val=d.gravur_strategie,
                          fallback=GravurStrategie.KONSTANTE_TIEFE,
                          feld="strategie", quellen=q),
        spitzenwinkel_grad=spitze,
        max_zustellung=_waehle(overrides.max_zustellung,
                               projekt_val=d.gravur_max_zustellung,
                               fallback=0.5, feld="max_zustellung", quellen=q),
    )
    return AufloesungsErgebnis(parameter=param, quellen=q)


__all__ = [
    "AufloesungsErgebnis",
    "BohrOverrides",
    "GravurOverrides",
    "KonturOverrides",
    "OverrideBasis",
    "ProjektDefaults",
    "TaschenOverrides",
    "aufloese_bohren",
    "aufloese_gravur",
    "aufloese_kontur",
    "aufloese_tasche",
]
