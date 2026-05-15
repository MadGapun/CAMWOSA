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


CWP_SCHEMA_VERSION = 1
"""Schema-Version. Aenderungen erfordern Migration."""


# ---------------------------------------------------------------------------
# Operation
# ---------------------------------------------------------------------------


class OperationsKonfig(BaseModel):
    """Eine Operation in einem Setup.

    ``parameter`` ist je nach ``typ`` ein KonturParameter, TaschenParameter,
    BohrParameter oder GravurParameter.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    typ: str  # "kontur" | "tasche" | "bohren" | "gravur" | "relief"
    geometrie_ids: list[str] = Field(default_factory=list)
    parameter: dict[str, Any]
    aktiviert: bool = True


# ---------------------------------------------------------------------------
# Setup + Pause
# ---------------------------------------------------------------------------


class SetupPauseTyp(str, Enum):
    WERKZEUGWECHSEL = "werkzeugwechsel"
    UMSPANN = "umspann"
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
    operationen: list[OperationsKonfig] = Field(default_factory=list)
    pause_vor: SetupPause | None = None
    foto_pfad: str | None = None
    geschaetzte_zeit_minuten: float = 0.0
    notizen: str = ""


# ---------------------------------------------------------------------------
# Geometrie-Snapshot (im Projekt eingebettet)
# ---------------------------------------------------------------------------


class GeometrieSnapshot(BaseModel):
    """Eine Geometrie wie sie im Projekt liegt.

    Das kann eine importierte DXF-Datei oder ein Zeichnungs-Objekt aus dem
    integrierten Zeichnen-Modul sein.
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
    "GeometrieSnapshot",
    "OperationsKonfig",
    "Setup",
    "SetupPause",
    "SetupPauseTyp",
    "Variante",
    "neues_projekt",
]
