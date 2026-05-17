"""Auto-CAM: aus High-Level-Beschreibung eine komplette Bearbeitung erzeugen.

Konkrete Use-Cases (Markus' Worte „sag Claude was du willst"):

1. „Mach mir eine 50×30mm Tasche, 5mm tief, mit Schruppen+Schlichten in Buche"
2. „Beschrifte einen Ø40mm Stab mit dem Wort CAMWOSA"
3. „Mach 4 Anschlagbohrungen in den Ecken eines 200×200mm Brettes"

Diese Funktion nimmt:
- Eine **Aufgaben-Beschreibung** (was?)
- Werkzeug + Material + Maschine
- Ggf. Geometrie-Hinweise (DXF-Pfad, Punkt-Liste, ...)

…und liefert:
- Komplettes ``CWPProjekt`` mit Variante, Setup, allen Operationen
- Optional: Multi-Werkzeug-ArbeitsSchritt-Liste (Schruppen → WW → Schlichten)
- Ist bereits „lauffaehig" — Toolpath-Erzeugung + G-Code-Export folgen wie ueblich

Das ist KEINE generative-AI-Anbindung — die Strategie-Auswahl ist regelbasiert
(„wenn Tasche tiefer als X mm: Schruppen+Schlichten, sonst nur Schruppen").
Wer KI will, kann den MCP-Tool aufrufen und Claude waehlen lassen.

Siehe Wiki: docs/wiki/MCP-AutoCAM.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from camwosa.db.models import (
    Maschine,
    Material,
    ProjektMetadaten,
    Rohmaterial,
    RohmaterialForm,
    Werkzeug,
    WerkzeugTyp,
)
from camwosa.project.schema import (
    CWP_SCHEMA_VERSION,
    CWPProjekt,
    OperationsKonfig,
    Setup,
    Variante,
)
from camwosa.project.schritte import (
    ArbeitsSchritt,
    OperationSchritt,
    WerkzeugWechselSchritt,
    WerkzeugWechselStrategie,
)


class AufgabenTyp(str, Enum):
    """Welche Art von Bearbeitung soll erzeugt werden?"""
    TASCHE = "tasche"
    BESCHRIFTUNG_WRAP = "beschriftung_wrap"
    ANSCHLAGBOHRUNGEN = "anschlagbohrungen"
    KONTUR_AUSSCHNEIDEN = "kontur_ausschneiden"
    DRECHSELN_PROFIL = "drechseln_profil"


@dataclass
class AutoCamErgebnis:
    """Was die Auto-CAM-Funktion zurueckliefert."""
    projekt: CWPProjekt
    hinweise: list[str] = field(default_factory=list)
    """Erklaerungen welche Entscheidungen getroffen wurden (z.B. „Tasche ist
    7 mm tief > 5 mm → Schruppen+Schlichten gewaehlt mit 6mm und 2mm Fraeser")."""


# ---------------------------------------------------------------------------
# Werkzeug-Auswahl-Heuristik (gemeinsam fuer alle Aufgaben)
# ---------------------------------------------------------------------------


def waehle_schrupp_werkzeug(
    werkzeuge: list[Werkzeug], gewuenschter_durchmesser_mm: float,
) -> Werkzeug | None:
    """Sucht einen Schaftfraeser mit Durchmesser nahe ``gewuenschter_durchmesser_mm``."""
    schaft = [w for w in werkzeuge if w.typ == WerkzeugTyp.SCHAFTFRAESER]
    if not schaft:
        return werkzeuge[0] if werkzeuge else None
    return min(schaft, key=lambda w: abs(w.durchmesser - gewuenschter_durchmesser_mm))


def waehle_schlicht_werkzeug(
    werkzeuge: list[Werkzeug], maximal_durchmesser_mm: float,
) -> Werkzeug | None:
    """Sucht einen Schlicht-Fraeser (Schaft oder Kugel, kleiner als Schruppen)."""
    kandidaten = [
        w for w in werkzeuge
        if w.typ in (WerkzeugTyp.SCHAFTFRAESER, WerkzeugTyp.KUGELFRAESER)
        and w.durchmesser <= maximal_durchmesser_mm
    ]
    if not kandidaten:
        return None
    return max(kandidaten, key=lambda w: w.durchmesser)


def waehle_bohrer(
    werkzeuge: list[Werkzeug], durchmesser_mm: float,
) -> Werkzeug | None:
    """Sucht einen Bohrer / Schaftfraeser nahe am gewuenschten Durchmesser."""
    bohrer = [w for w in werkzeuge if w.typ == WerkzeugTyp.BOHRER]
    if not bohrer:
        bohrer = [w for w in werkzeuge if w.typ == WerkzeugTyp.SCHAFTFRAESER]
    if not bohrer:
        return None
    return min(bohrer, key=lambda w: abs(w.durchmesser - durchmesser_mm))


def waehle_gravur_werkzeug(werkzeuge: list[Werkzeug]) -> Werkzeug | None:
    """V-Bit / Gravierstichel bevorzugt, sonst kleinster Schaftfraeser."""
    v_bits = [w for w in werkzeuge if w.typ in (WerkzeugTyp.V_BIT, WerkzeugTyp.GRAVIERSTICHEL)]
    if v_bits:
        return v_bits[0]
    schaft = [w for w in werkzeuge if w.typ == WerkzeugTyp.SCHAFTFRAESER]
    if schaft:
        return min(schaft, key=lambda w: w.durchmesser)
    return werkzeuge[0] if werkzeuge else None


# ---------------------------------------------------------------------------
# Strategie-Heuristik
# ---------------------------------------------------------------------------


def soll_schrupp_schlicht(
    tiefe_mm: float, material_haerte_hint: str = "weich",
) -> bool:
    """Ab welcher Tiefe lohnt sich Schruppen+Schlichten?

    Heuristik:
    - Tiefe > 5 mm: ja
    - Material gilt als „hart" (Buche, Eiche, Hartholz) → Schwelle 3 mm
    """
    schwelle = 3.0 if material_haerte_hint in ("hart", "metall") else 5.0
    return tiefe_mm >= schwelle


# ---------------------------------------------------------------------------
# Aufgaben-spezifische Builder
# ---------------------------------------------------------------------------


def _projekt_skelett(
    name: str, maschine: Maschine, rohmaterial: Rohmaterial, material: Material,
    werkzeuge: list[Werkzeug],
) -> CWPProjekt:
    jetzt = datetime.now(timezone.utc)
    return CWPProjekt(
        schema_version=CWP_SCHEMA_VERSION,
        metadaten=ProjektMetadaten(
            name=name, erstellt=jetzt, geaendert=jetzt,
            aktive_variante="default",
            notizen="Erzeugt von auto_cam_erstellen()",
        ),
        maschine=maschine,
        werkzeuge=werkzeuge,
        materialien=[material],
        varianten=[Variante(
            id="default", name="Default", rohmaterial=rohmaterial,
        )],
    )


def _erzeuge_tasche(
    *,
    name: str,
    maschine: Maschine, material: Material, werkzeuge: list[Werkzeug],
    rohmaterial: Rohmaterial,
    breite_mm: float, hoehe_mm: float, tiefe_mm: float,
    werkzeug_durchmesser_wunsch_mm: float = 6.0,
    material_haerte: str = "weich",
) -> AutoCamErgebnis:
    hinweise: list[str] = []
    schrupp_wz = waehle_schrupp_werkzeug(werkzeuge, werkzeug_durchmesser_wunsch_mm)
    if schrupp_wz is None:
        raise ValueError("Keine Werkzeuge verfuegbar")

    operationen: list[OperationsKonfig] = []
    schritte: list[ArbeitsSchritt] = []

    if soll_schrupp_schlicht(tiefe_mm, material_haerte):
        schlicht_wz = waehle_schlicht_werkzeug(werkzeuge, schrupp_wz.durchmesser - 0.5)
        if schlicht_wz is None or schlicht_wz.id == schrupp_wz.id:
            hinweise.append(
                "Tiefe wuerde Schruppen+Schlichten rechtfertigen, aber kein "
                "kleineres Schlicht-Werkzeug verfuegbar — nur Schruppen."
            )
        else:
            hinweise.append(
                f"Tiefe {tiefe_mm:.1f}mm ≥ Schwelle ({material_haerte}) → "
                f"Schruppen+Schlichten mit {schrupp_wz.name} + {schlicht_wz.name}"
            )
            # Schruppen-Operation mit Aufmass
            operationen.append(OperationsKonfig(
                id="op_schruppen", name="Tasche Schruppen", typ="tasche",
                parameter=_tasche_param(schrupp_wz.id, breite_mm, hoehe_mm, tiefe_mm,
                                          aufmass=0.3, strategie="schruppen"),
            ))
            operationen.append(OperationsKonfig(
                id="op_schlichten", name="Tasche Schlichten", typ="tasche",
                parameter=_tasche_param(schlicht_wz.id, breite_mm, hoehe_mm, tiefe_mm,
                                          aufmass=0.0, strategie="schlichten"),
            ))
            schritte = [
                OperationSchritt(id="s_schrupp", operation_id="op_schruppen"),
                WerkzeugWechselSchritt(
                    id="s_ww", werkzeug_neu_id=schlicht_wz.id,
                    werkzeug_alt_id=schrupp_wz.id,
                    strategie=WerkzeugWechselStrategie.SEPARATE_DATEI,
                    anweisung=f"{schlicht_wz.name} einsetzen, Z-Null neu setzen",
                ),
                OperationSchritt(id="s_schlicht", operation_id="op_schlichten"),
            ]

    if not operationen:
        hinweise.append(f"Tiefe {tiefe_mm:.1f}mm < Schwelle → nur Schruppen mit {schrupp_wz.name}")
        operationen.append(OperationsKonfig(
            id="op_tasche", name="Tasche", typ="tasche",
            parameter=_tasche_param(schrupp_wz.id, breite_mm, hoehe_mm, tiefe_mm,
                                      aufmass=0.0, strategie="schruppen"),
        ))
        schritte = [OperationSchritt(id="s_op", operation_id="op_tasche")]

    setup = Setup(
        id="setup_01", name=name,
        werkzeug_id=schrupp_wz.id,
        operationen=operationen,
        schritte=schritte,
    )

    projekt = _projekt_skelett(name, maschine, rohmaterial, material, werkzeuge)
    projekt.varianten[0].setups = [setup]

    return AutoCamErgebnis(projekt=projekt, hinweise=hinweise)


def _tasche_param(
    werkzeug_id: str, breite: float, hoehe: float, tiefe: float,
    *, aufmass: float, strategie: str,
) -> dict[str, Any]:
    return {
        "werkzeug_id": werkzeug_id,
        "max_tiefe": tiefe,
        "stepdown": min(tiefe, 2.0) if strategie == "schruppen" else min(tiefe, 0.5),
        "stepover_prozent": 50 if strategie == "schruppen" else 15,
        "aufmass_wand": aufmass,
        "aufmass_boden": aufmass,
        "strategie": "offset_kontur",
        "__quelle": "auto_cam",
        "__geometrie": {
            "typ": "polylinie",
            "punkte": [[0, 0], [breite, 0], [breite, hoehe], [0, hoehe], [0, 0]],
            "geschlossen": True,
        },
    }


def _erzeuge_anschlagbohrungen(
    *,
    name: str,
    maschine: Maschine, material: Material, werkzeuge: list[Werkzeug],
    rohmaterial: Rohmaterial,
    werkstueck_breite_mm: float, werkstueck_hoehe_mm: float,
    randabstand_mm: float = 10.0,
    durchmesser_mm: float = 3.0, tiefe_mm: float = 8.0,
) -> AutoCamErgebnis:
    bohrer = waehle_bohrer(werkzeuge, durchmesser_mm)
    if bohrer is None:
        raise ValueError("Kein Bohrer/Fraeser verfuegbar")

    hinweise = [
        f"4 Anschlagbohrungen Ø{durchmesser_mm}mm × {tiefe_mm}mm × {randabstand_mm}mm vom Rand. "
        f"Werkzeug: {bohrer.name} (Ø {bohrer.durchmesser}mm)."
    ]
    if abs(bohrer.durchmesser - durchmesser_mm) > 0.5:
        hinweise.append(
            f"Achtung: Werkzeug-Durchmesser {bohrer.durchmesser}mm weicht von Wunsch "
            f"{durchmesser_mm}mm ab — Loch wird entsprechend groesser."
        )

    punkte = [
        [randabstand_mm, randabstand_mm],
        [werkstueck_breite_mm - randabstand_mm, randabstand_mm],
        [werkstueck_breite_mm - randabstand_mm, werkstueck_hoehe_mm - randabstand_mm],
        [randabstand_mm, werkstueck_hoehe_mm - randabstand_mm],
    ]
    op = OperationsKonfig(
        id="op_anschlag", name="Anschlagbohrungen", typ="bohren",
        parameter={
            "werkzeug_id": bohrer.id,
            "max_tiefe": tiefe_mm,
            "stepdown": min(tiefe_mm, 2.0),
            "strategie": "peck",
            "__punkte": punkte,
            "__quelle": "auto_cam",
        },
    )
    setup = Setup(
        id="setup_01", name=name,
        werkzeug_id=bohrer.id,
        operationen=[op],
        schritte=[OperationSchritt(id="s_op", operation_id="op_anschlag")],
    )
    projekt = _projekt_skelett(name, maschine, rohmaterial, material, werkzeuge)
    projekt.varianten[0].setups = [setup]
    return AutoCamErgebnis(projekt=projekt, hinweise=hinweise)


def _erzeuge_beschriftung_wrap(
    *,
    name: str,
    maschine: Maschine, material: Material, werkzeuge: list[Werkzeug],
    rohmaterial: Rohmaterial,
    text: str, werkstueck_radius_mm: float,
    gravur_tiefe_mm: float = 0.5,
    text_hoehe_mm: float = 8.0,
) -> AutoCamErgebnis:
    werkzeug = waehle_gravur_werkzeug(werkzeuge)
    if werkzeug is None:
        raise ValueError("Kein Gravur-Werkzeug verfuegbar")
    hinweise = [
        (f"Wrap-Beschriftung '{text}' auf Ø{werkstueck_radius_mm * 2:.0f}mm Stab "
         f"mit {werkzeug.name}, Tiefe {gravur_tiefe_mm}mm, Hoehe {text_hoehe_mm}mm."),
    ]

    # Text → Pfad (Master-Plan A37) — erzeugt eine Liste von Polygonen
    text_punkte: list[list[tuple[float, float]]] = []
    try:
        from camwosa.cad.text_zu_pfad import (
            FontFehler,
            TextPfadParameter,
            polygone_zu_punktlisten,
            text_zu_pfade,
        )
        polygone = text_zu_pfade(text, TextPfadParameter(hoehe_mm=text_hoehe_mm))
        text_punkte = polygone_zu_punktlisten(polygone)
        if text_punkte:
            hinweise.append(
                f"Text-zu-Pfad: '{text}' in {len(text_punkte)} Polygone konvertiert "
                f"(Standard-System-Font, Hoehe {text_hoehe_mm}mm)."
            )
        else:
            hinweise.append(
                "Text-zu-Pfad lieferte keine Polygone — Font-Datei eventuell "
                "leer fuer diese Zeichen."
            )
    except FontFehler as e:
        hinweise.append(
            f"Text-zu-Pfad nicht moeglich (Font fehlt): {e}. "
            f"Operation wird mit Platzhalter erzeugt — User muss Pfad nachpflegen."
        )

    op = OperationsKonfig(
        id="op_wrap_text", name=f"Wrap: {text}", typ="gravur",
        parameter={
            "werkzeug_id": werkzeug.id,
            "max_tiefe": gravur_tiefe_mm,
            "stepdown": gravur_tiefe_mm,
            "__wrap_text": text,
            "__werkstueck_radius_mm": werkstueck_radius_mm,
            "__text_punkte": text_punkte,
            "__quelle": "auto_cam",
        },
    )
    setup = Setup(
        id="setup_01", name=name, werkzeug_id=werkzeug.id,
        operationen=[op],
        schritte=[OperationSchritt(id="s_op", operation_id="op_wrap_text")],
        maschinen_modus="rotary_y",
    )
    projekt = _projekt_skelett(name, maschine, rohmaterial, material, werkzeuge)
    projekt.varianten[0].setups = [setup]
    return AutoCamErgebnis(projekt=projekt, hinweise=hinweise)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


def auto_cam_erstellen(
    aufgabe: AufgabenTyp,
    *,
    name: str,
    maschine: Maschine,
    material: Material,
    werkzeuge: list[Werkzeug],
    rohmaterial: Rohmaterial | None = None,
    parameter: dict[str, Any] | None = None,
) -> AutoCamErgebnis:
    """Erzeugt aus einer High-Level-Aufgabe ein lauffaehiges Projekt.

    Args:
        aufgabe: Welche Art von Bearbeitung
        name: Projektname
        maschine, material, werkzeuge, rohmaterial: aus den Stammdaten
        parameter: aufgaben-spezifische Parameter — siehe einzelne Aufgaben-Builder

    Returns:
        ``AutoCamErgebnis`` mit fertigem Projekt + Liste der getroffenen
        Heuristik-Entscheidungen (= „warum hab ich's so gemacht").
    """
    parameter = parameter or {}
    if rohmaterial is None:
        rohmaterial = Rohmaterial(
            form=RohmaterialForm.PLATTE,
            laenge=200.0, breite=200.0, hoehe=12.0,
            material_id=material.id,
        )

    if aufgabe == AufgabenTyp.TASCHE:
        return _erzeuge_tasche(
            name=name, maschine=maschine, material=material,
            werkzeuge=werkzeuge, rohmaterial=rohmaterial,
            breite_mm=float(parameter.get("breite_mm", 50)),
            hoehe_mm=float(parameter.get("hoehe_mm", 30)),
            tiefe_mm=float(parameter.get("tiefe_mm", 5)),
            werkzeug_durchmesser_wunsch_mm=float(parameter.get("werkzeug_durchmesser_mm", 6)),
            material_haerte=parameter.get("material_haerte", "weich"),
        )

    if aufgabe == AufgabenTyp.ANSCHLAGBOHRUNGEN:
        return _erzeuge_anschlagbohrungen(
            name=name, maschine=maschine, material=material,
            werkzeuge=werkzeuge, rohmaterial=rohmaterial,
            werkstueck_breite_mm=float(parameter.get("werkstueck_breite_mm", 200)),
            werkstueck_hoehe_mm=float(parameter.get("werkstueck_hoehe_mm", 200)),
            randabstand_mm=float(parameter.get("randabstand_mm", 10)),
            durchmesser_mm=float(parameter.get("durchmesser_mm", 3)),
            tiefe_mm=float(parameter.get("tiefe_mm", 8)),
        )

    if aufgabe == AufgabenTyp.BESCHRIFTUNG_WRAP:
        return _erzeuge_beschriftung_wrap(
            name=name, maschine=maschine, material=material,
            werkzeuge=werkzeuge, rohmaterial=rohmaterial,
            text=str(parameter.get("text", "TEXT")),
            werkstueck_radius_mm=float(parameter.get("werkstueck_radius_mm", 20)),
            gravur_tiefe_mm=float(parameter.get("gravur_tiefe_mm", 0.5)),
            text_hoehe_mm=float(parameter.get("text_hoehe_mm", 8.0)),
        )

    raise NotImplementedError(f"Aufgaben-Typ '{aufgabe.value}' noch nicht unterstuetzt")


__all__ = [
    "AufgabenTyp",
    "AutoCamErgebnis",
    "auto_cam_erstellen",
    "soll_schrupp_schlicht",
    "waehle_bohrer",
    "waehle_gravur_werkzeug",
    "waehle_schlicht_werkzeug",
    "waehle_schrupp_werkzeug",
]
