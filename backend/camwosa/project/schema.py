"""Projekt-Schema fuer CAMWOSA-Projekte (.cwp).

Ein Projekt enthaelt:
- Metadaten (Name, Autor, Schema-Version)
- Maschinen-Snapshot
- Material- und Werkzeug-Snapshots (damit Projekte auch ohne globale DB ladbar sind)
- Rohmaterial-Definition
- Geometrie-Objekte (DXF-Inhalt + Eigene Zeichnungen)
- Mehrere Varianten (jeweils Setups + Operationen)
- Generierte G-Code-Dateien (optional, im ZIP eingebettet)

Siehe Wiki: docs/wiki/Projekt-Format.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from camwosa.cam.umspannung import WerkstueckTransformation
from camwosa.cam.parameter import (
    BohrParameter,
    GravurParameter,
    KonturParameter,
    TaschenParameter,
)
from camwosa.db.models import (
    Maschine,
    Material,
    ProjektMetadaten,
    Rohmaterial,
    Werkzeug,
)

from camwosa.project.schritte import ArbeitsSchritt


CWP_SCHEMA_VERSION = 2
"""Schema-Version. Aenderungen erfordern Migration.

v2 (A48): OperationStatus + input_hash fuer Dirty-Tracking + Run-Lock.
"""


# ---------------------------------------------------------------------------
# Operation
# ---------------------------------------------------------------------------


class OperationStatus(str, Enum):
    """Status einer Operation (A48 Dependency-Graph / Run-Lock).

    - NEU: noch nie berechnet
    - OK: Toolpath aktuell, alle Inputs gueltig
    - DIRTY: Quelle hat sich geaendert, Recalc noetig (orange Markierung)
    - BROKEN: Quelle fehlt oder ungueltig — G-Code-Export blockiert (rot)
    """

    NEU = "neu"
    OK = "ok"
    DIRTY = "dirty"
    BROKEN = "broken"


class OperationsKonfig(BaseModel):
    """Eine Operation in einem Setup.

    ``parameter`` ist je nach ``typ`` ein KonturParameter, TaschenParameter,
    BohrParameter oder GravurParameter.

    Ab v2: ``status`` + ``input_hash`` fuer Dirty-Tracking (A48).
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    typ: str  # "kontur" | "tasche" | "bohren" | "gravur" | "relief"
    geometrie_ids: list[str] = Field(default_factory=list)
    parameter: dict[str, Any]
    aktiviert: bool = True

    # A48: Status + Dirty-Tracking
    status: OperationStatus = OperationStatus.NEU
    input_hash: str = ""
    """SHA1-Hash der Inputs (geometrie + werkzeug + parameter + material).
    Aenderung -> Status -> DIRTY."""
    letzte_berechnung: datetime | None = None
    fehler_text: str = ""
    """Bei status=BROKEN: Erklaerung warum (z.B. 'Geometrie X gibt es nicht mehr')."""


# ---------------------------------------------------------------------------
# Setup + Pause
# ---------------------------------------------------------------------------


class SetupPauseTyp(str, Enum):
    WERKZEUGWECHSEL = "werkzeugwechsel"
    UMSPANN = "umspann"
    WERKSTUECK_VERSCHIEBEN = "werkstueck_verschieben"  # lange Werkstuecke
    SPINDEL_WECHSEL = "spindel_wechsel"  # z.B. OEM-Router -> Makita
    OPTIONALER_STOP = "optionaler_stop"


class SetupPause(BaseModel):
    model_config = ConfigDict(extra="ignore")

    typ: SetupPauseTyp
    titel: str
    anweisung: str
    foto_pfad: str | None = None
    werkzeug_neu_id: str | None = None  # nur fuer Werkzeugwechsel
    nullpunkt_neu: tuple[float, float, float] | None = None  # nur fuer Umspann
    bestaetigung_text: str = "Verstanden"


class Setup(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    maschinen_modus: str = "standard_xyz"
    spannmittel: str = ""
    werkzeug_id: str
    rohmaterial_uebernehmen: bool = True  # vom Vorgaenger-Setup
    nullpunkt: tuple[float, float, float] = (0.0, 0.0, 0.0)
    # A49: Werkstueck-Transformation gegenueber dem Design/Vorgaenger (Wenden/
    # Spiegeln/Drehen beim Umspannen). None = keine (nur Nullpunkt gilt).
    transformation: WerkstueckTransformation | None = None
    operationen: list[OperationsKonfig] = Field(default_factory=list)
    pause_vor: SetupPause | None = None
    # Schritt-Liste (ab v2): flexible Workflow-Reihenfolge mit ArbeitsSchritt.
    # Wenn leer, wird aus pause_vor + operationen abgeleitet (Backwards-Kompat).
    schritte: list[ArbeitsSchritt] = Field(default_factory=list)
    foto_pfad: str | None = None
    geschaetzte_zeit_minuten: float = 0.0
    notizen: str = ""

    def effektive_schritte(self) -> list[ArbeitsSchritt]:
        """Liefert die Schritt-Liste, wenn leer wird Legacy abgeleitet."""
        if self.schritte:
            return list(self.schritte)
        from camwosa.project.schritte import aus_setup_legacy

        return aus_setup_legacy(self)


# ---------------------------------------------------------------------------
# Geometrie-Snapshot (im Projekt eingebettet)
# ---------------------------------------------------------------------------


class GeometrieAnnotationTyp(str, Enum):
    """Typ einer manuellen Annotation, die User auf eine importierte Geometrie setzen.

    Annotationen sind reine Zusatz-Punkte — sie aendern die Original-Geometrie
    nicht. Beispiel: nachtraegliche Anschlagbohrung in einem importierten STL.
    """

    ANSCHLAGBOHRUNG = "anschlagbohrung"
    REFPUNKT = "refpunkt"
    KOMMENTAR = "kommentar"
    AUSSCHNITT = "ausschnitt"


class GeometrieAnnotation(BaseModel):
    """Eine User-Annotation auf einer Geometrie.

    Wird vom Frontend gepflegt — der Backend speichert sie nur und gibt sie
    an die jeweiligen Operations weiter (z.B. erzeugt eine ANSCHLAGBOHRUNG-
    Annotation eine zusaetzliche Bohren-Operation im Workflow).
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    typ: GeometrieAnnotationTyp
    x: float
    y: float
    z: float = 0.0
    durchmesser_mm: float | None = Field(
        default=None, ge=0,
        description="Bei ANSCHLAGBOHRUNG: Bohr-Durchmesser",
    )
    tiefe_mm: float | None = Field(
        default=None, gt=0,
        description="Bei ANSCHLAGBOHRUNG: Bohr-Tiefe",
    )
    text: str = ""


class GeometrieSnapshot(BaseModel):
    """Eine Geometrie wie sie im Projekt liegt.

    Das kann eine importierte DXF-Datei oder ein Zeichnungs-Objekt aus dem
    integrierten Zeichnen-Modul sein.

    Zusaetzlich koennen User nachtraeglich ``annotationen`` setzen — z.B.
    eine Anschlagbohrung in ein importiertes 3D-Modell legen, ohne die
    Original-Datei zu mutieren.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    quelle: str  # "dxf" | "stl" | "zeichnung"
    layer: str = "0"
    # Bei DXF/STL: Pfad zur eingebetteten Datei im ZIP-Container
    eingebettete_datei: str | None = None
    # Bei Zeichnung: serialisierte Geometrie
    daten: dict[str, Any] = Field(default_factory=dict)
    annotationen: list[GeometrieAnnotation] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Variante
# ---------------------------------------------------------------------------


class Variante(BaseModel):
    """Eine Auspraegung des Projekts.

    Verschiedene Varianten teilen die Grundgeometrie, koennen aber andere
    Materialien, Werkzeuge oder Operations-Parameter nutzen.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    rohmaterial: Rohmaterial
    setups: list[Setup] = Field(default_factory=list)
    # Globale Annotationen — auf Werkstueck-Ebene, nicht an eine Geometrie gebunden.
    # (Pro-Geometrie-Annotationen leben in GeometrieSnapshot.annotationen.)
    annotationen: list[GeometrieAnnotation] = Field(default_factory=list)
    notizen: str = ""


# ---------------------------------------------------------------------------
# Komplettes Projekt
# ---------------------------------------------------------------------------


class CWPProjekt(BaseModel):
    """Vollstaendiges CAMWOSA-Projekt.

    Wird beim Speichern als JSON-Manifest in den .cwp-ZIP-Container geschrieben.
    """

    model_config = ConfigDict(extra="ignore")

    schema_version: int = CWP_SCHEMA_VERSION
    metadaten: ProjektMetadaten
    maschine: Maschine
    werkzeuge: list[Werkzeug] = Field(default_factory=list)
    materialien: list[Material] = Field(default_factory=list)
    geometrien: list[GeometrieSnapshot] = Field(default_factory=list)
    varianten: list[Variante] = Field(default_factory=list)
    audit_log: list[str] = Field(default_factory=list)


def neues_projekt(
    name: str,
    maschine: Maschine,
    rohmaterial: Rohmaterial,
    *,
    autor: str = "",
) -> CWPProjekt:
    """Erzeugt ein neues, leeres Projekt mit Default-Variante."""
    jetzt = datetime.now(timezone.utc)
    return CWPProjekt(
        metadaten=ProjektMetadaten(
            name=name,
            autor=autor,
            erstellt=jetzt,
            geaendert=jetzt,
            aktive_variante="default",
        ),
        maschine=maschine,
        varianten=[
            Variante(
                id="default",
                name="Default",
                rohmaterial=rohmaterial,
            )
        ],
    )


__all__ = [
    "CWPProjekt",
    "CWP_SCHEMA_VERSION",
    "GeometrieAnnotation",
    "GeometrieAnnotationTyp",
    "GeometrieSnapshot",
    "OperationsKonfig",
    "Setup",
    "SetupPause",
    "SetupPauseTyp",
    "Variante",
    "neues_projekt",
]
