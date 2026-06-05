"""ArbeitsSchritt-Konzept: flexible, beliebig kombinierbare Workflow-Schritte.

Hintergrund: bisher war ein Setup ein starrer Block mit:
- werkzeug_id (eines pro Setup)
- pause_vor (genau eine vor dem Setup)
- operationen (Liste innerhalb des Setups)

Das ist zu starr fuer reale Workflows. Beispiele die das alte Modell nicht
sauber abbildet:

- Mitten in einem Setup ein **Werkzeugwechsel** (gleiches Spannmittel, gleicher
  Modus, aber anderes Werkzeug)
- Ein **Manual NC**-Block (z.B. ``M0``, Spindel auf Drehzahl warten, Wasser an)
- Ein **Achswechsel** mitten im Setup (von Rotary auf XYZ, Werkstueck bleibt)
- Pause vor *einer einzelnen Operation* (nicht vor dem ganzen Setup)
- Beliebig viele Pausen hintereinander (z.B. Spindel-Wechsel + Werkstueck-
  Drehung als zwei separate Schritte)

ArbeitsSchritt ist die Generalisierung: jeder Schritt ist eines von:
- ``OperationSchritt`` — fuehrt eine CAM-Operation aus
- ``WerkzeugWechselSchritt`` — wechselt Werkzeug (mit oder ohne Mensch-Pause)
- ``UmspannSchritt`` — Werkstueck wird neu eingespannt
- ``AchsWechselSchritt`` — Maschinen-Modus aendert sich (z.B. XYZ <-> Rotary)
- ``ManualNCSchritt`` — beliebige G-Code-Zeilen direkt rein
- ``PauseSchritt`` — generische Mensch-Pause mit Anweisung

Setups bekommen ein neues optionales Feld ``schritte``. Wenn leer, wird das
Setup wie bisher aus ``operationen`` + ``pause_vor`` zusammengebaut (Rueckwaerts-
Kompat). Wenn ``schritte`` gefuellt ist, wird DAS verwendet.

Siehe Wiki: docs/wiki/ArbeitsSchritt.md
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


class SchrittTyp(str, Enum):
    OPERATION = "operation"
    WERKZEUGWECHSEL = "werkzeugwechsel"
    UMSPANN = "umspann"
    ACHSWECHSEL = "achswechsel"
    MANUAL_NC = "manual_nc"
    PAUSE = "pause"


class _SchrittBasis(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    aktiviert: bool = True
    titel: str = ""
    notizen: str = ""


class OperationSchritt(_SchrittBasis):
    """Fuehrt eine CAM-Operation aus.

    Verweist auf eine Operation-Definition (uebliche ``OperationsKonfig``-Felder).
    Damit die Daten nicht doppelt liegen, wird hier nur ``operation_id`` referenziert
    und im Setup nachgeschlagen (``Setup.operationen``).
    """

    typ: Literal[SchrittTyp.OPERATION] = SchrittTyp.OPERATION
    operation_id: str


class WerkzeugWechselStrategie(str, Enum):
    """Wie der Werkzeugwechsel beim G-Code-Export ausgegeben wird.

    - ``separate_datei`` (Default): an dieser Stelle wird der bisherige G-Code-Job
      beendet und ein neuer fuer das neue Werkzeug gestartet. CNCjs / der User
      laedt die Folge-Datei. Sicher fuer Hobby-GRBL ohne ATC — typisch fuer
      Schruppen + Schlichten ohne Umspannen.
    - ``inline_m6``: alles bleibt ein G-Code, mit ``M6 T<n>`` + ``M0`` an der
      Stelle. User wechselt das Werkzeug, drueckt Resume.
    - ``inline_makro``: nutzt ein CNCjs-Makro (z.B. ``TOOLCHANGE_PROBE``)
      das nach dem Werkzeugwechsel automatisch die Z-Hoehe neu probiert.
    """

    SEPARATE_DATEI = "separate_datei"
    INLINE_M6 = "inline_m6"
    INLINE_MAKRO = "inline_makro"


class WerkzeugWechselSchritt(_SchrittBasis):
    """Werkzeugwechsel innerhalb eines Setups (typisch: Schruppen + Schlichten).

    Das Werkstueck bleibt eingespannt, nur das Werkzeug wechselt. Die
    G-Code-Strategie steuert, ob daraus eine zweite Datei wird oder ob
    der Wechsel inline mit ``M6/M0`` ausgegeben wird.
    """

    typ: Literal[SchrittTyp.WERKZEUGWECHSEL] = SchrittTyp.WERKZEUGWECHSEL
    werkzeug_neu_id: str
    werkzeug_alt_id: str | None = None
    mensch_pause: bool = True
    anweisung: str = ""
    foto_pfad: str | None = None
    strategie: WerkzeugWechselStrategie = WerkzeugWechselStrategie.SEPARATE_DATEI
    makro_name: str | None = Field(
        default=None,
        description="Bei strategie=INLINE_MAKRO: Name des CNCjs-Makros",
    )
    z_probe_nach_wechsel: bool = Field(
        default=False,
        description="Soll nach dem Wechsel die Z-Hoehe neu probiert werden?",
    )


class UmspannSchritt(_SchrittBasis):
    """Werkstueck wird neu eingespannt — neuer Nullpunkt noetig."""

    typ: Literal[SchrittTyp.UMSPANN] = SchrittTyp.UMSPANN
    anweisung: str
    foto_pfad: str | None = None
    nullpunkt_neu: tuple[float, float, float] | None = None
    getrennte_datei: bool = Field(
        default=False,
        description=(
            "G-Code an dieser Stelle in eine NEUE Datei trennen statt M0-Pause. "
            "Noetig wenn die Maschine zum Umbau ausgeschaltet werden muss "
            "(z.B. Umkabeln) — dann reisst die Streaming-Verbindung ab und eine "
            "Einzeldatei mit Pause funktioniert nicht."
        ),
    )


class AchsWechselSchritt(_SchrittBasis):
    """Maschinen-Modus aendert sich (z.B. von Standard-XYZ auf Rotary)."""

    typ: Literal[SchrittTyp.ACHSWECHSEL] = SchrittTyp.ACHSWECHSEL
    modus_alt: str
    modus_neu: str
    anweisung: str = ""
    foto_pfad: str | None = None
    getrennte_datei: bool = Field(
        default=True,
        description=(
            "Achswechsel (z.B. XYZ<->Rotary) bedeutet i.d.R. Umkabeln bei "
            "ausgeschalteter Maschine — daher Default an: eigene G-Code-Datei. "
            "Auf False setzen nur wenn der Moduswechsel ohne Strom-Aus geht."
        ),
    )


class ManualNCSchritt(_SchrittBasis):
    """Beliebige G-Code-Zeilen direkt in den Output schreiben.

    Macht Sinn fuer:
    - Spindel-Hochlauf-Wartezeit (``G4 P5`` = 5s warten)
    - Programm-Stop mit Mensch-Interaktion (``M0``)
    - Werkzeug-Vermessung (``G38.2 Z-10 F100``)
    - Vakuumpumpe an/aus (``M62 P0`` / ``M63 P0``)
    - Coolant Mist (``M7`` / ``M9``)

    WICHTIG: keine Validierung der Zeilen — der User ist verantwortlich.
    Der Postprozessor schreibt sie unveraendert hinein.
    """

    typ: Literal[SchrittTyp.MANUAL_NC] = SchrittTyp.MANUAL_NC
    gcode_zeilen: list[str] = Field(default_factory=list)
    sicher_anfahren: bool = Field(
        default=True,
        description="Vor dem Manual-Block auf Sicherheitshoehe fahren",
    )


class PauseSchritt(_SchrittBasis):
    """Generische Mensch-Pause."""

    typ: Literal[SchrittTyp.PAUSE] = SchrittTyp.PAUSE
    anweisung: str
    foto_pfad: str | None = None
    bestaetigung_text: str = "Verstanden"
    getrennte_datei: bool = Field(
        default=False,
        description=(
            "G-Code an dieser Stelle in eine NEUE Datei trennen statt M0-Pause "
            "(z.B. wenn die Maschine fuer den Eingriff ausgeschaltet wird und die "
            "Verbindung abreisst)."
        ),
    )


# Discriminated Union via 'typ'-Feld
ArbeitsSchritt = Annotated[
    Union[
        OperationSchritt,
        WerkzeugWechselSchritt,
        UmspannSchritt,
        AchsWechselSchritt,
        ManualNCSchritt,
        PauseSchritt,
    ],
    Field(discriminator="typ"),
]


# ---------------------------------------------------------------------------
# Pruefungen
# ---------------------------------------------------------------------------


def pruefe_schritt_liste(schritte: list[ArbeitsSchritt]) -> list[str]:
    """Validiert eine Schritt-Liste und liefert Probleme als Strings zurueck.

    Kein hartes Raise — die UI / der Workflow-Manager entscheidet was kritisch ist.
    """
    probleme: list[str] = []
    if not schritte:
        return probleme

    # ManualNC ohne Zeilen ist sinnlos
    for s in schritte:
        if isinstance(s, ManualNCSchritt) and not s.gcode_zeilen:
            probleme.append(f"ManualNC-Schritt '{s.id}' hat keine G-Code-Zeilen")

    # Werkzeugwechsel ohne Vorgaenger-Werkzeug-Info: nicht kritisch, aber Hinweis
    aktuelles_werkzeug: str | None = None
    for s in schritte:
        if isinstance(s, WerkzeugWechselSchritt):
            if s.werkzeug_alt_id is None:
                s.werkzeug_alt_id = aktuelles_werkzeug
            aktuelles_werkzeug = s.werkzeug_neu_id

    # Operation nach Achswechsel ohne Pause? Warnung.
    for prev, curr in zip(schritte, schritte[1:]):
        if isinstance(prev, AchsWechselSchritt) and isinstance(curr, OperationSchritt):
            # Direkt eine Operation nach Achswechsel — meist will man dazwischen pausieren
            probleme.append(
                f"Operation '{curr.operation_id}' folgt direkt auf Achswechsel "
                f"'{prev.id}' ohne Pause — bitte explizite Pause einbauen."
            )

    # Doppelte IDs
    ids = [s.id for s in schritte]
    duplikate = {i for i in ids if ids.count(i) > 1}
    for d in duplikate:
        probleme.append(f"Doppelte Schritt-ID: '{d}'")

    return probleme


# ---------------------------------------------------------------------------
# Legacy-Konvertierung
# ---------------------------------------------------------------------------


def aus_setup_legacy(setup) -> list[ArbeitsSchritt]:  # type: ignore[no-untyped-def]
    """Baut die Schritt-Liste aus dem alten Setup-Format zusammen.

    Reihenfolge:
    1. ``pause_vor`` (falls vorhanden) wird zu einem entsprechenden Schritt
    2. Jede Operation wird ein OperationSchritt
    """
    aus: list[ArbeitsSchritt] = []
    if setup.pause_vor is not None:
        p = setup.pause_vor
        typ = p.typ.value if hasattr(p.typ, "value") else str(p.typ)
        if typ == "werkzeugwechsel":
            aus.append(WerkzeugWechselSchritt(
                id=f"{setup.id}__wz_wechsel",
                titel=p.titel,
                werkzeug_neu_id=p.werkzeug_neu_id or setup.werkzeug_id,
                mensch_pause=True,
                anweisung=p.anweisung,
                foto_pfad=p.foto_pfad,
            ))
        elif typ == "umspann":
            aus.append(UmspannSchritt(
                id=f"{setup.id}__umspann",
                titel=p.titel,
                anweisung=p.anweisung,
                foto_pfad=p.foto_pfad,
                nullpunkt_neu=p.nullpunkt_neu,
                getrennte_datei=getattr(p, "getrennte_datei", False),
            ))
        else:
            aus.append(PauseSchritt(
                id=f"{setup.id}__pause",
                titel=p.titel,
                anweisung=p.anweisung,
                foto_pfad=p.foto_pfad,
                bestaetigung_text=p.bestaetigung_text,
                getrennte_datei=getattr(p, "getrennte_datei", False),
            ))

    for op in setup.operationen:
        aus.append(OperationSchritt(
            id=f"{setup.id}__op_{op.id}",
            titel=op.name,
            operation_id=op.id,
            aktiviert=op.aktiviert,
        ))
    return aus


__all__ = [
    "AchsWechselSchritt",
    "ArbeitsSchritt",
    "ManualNCSchritt",
    "OperationSchritt",
    "PauseSchritt",
    "SchrittTyp",
    "UmspannSchritt",
    "WerkzeugWechselSchritt",
    "WerkzeugWechselStrategie",
    "aus_setup_legacy",
    "pruefe_schritt_liste",
]
