"""CuttingPreset — Schnittparameter als separate Top-Level-Entitaet.

Hintergrund: bisher waren Schnittparameter in ``Material.presets[]`` eingebettet
(siehe ``SchnittParameterPreset`` in models.py). Das ist unflexibel:

- Ein Preset gilt immer fuer eine Werkzeug-Material-Kombination
- Operation-spezifische Varianten (z.B. Schruppen vs. Schlichten, Konturieren vs.
  Taschen) lassen sich nicht abbilden
- User koennen Presets nicht teilen oder global pflegen
- CRUD-API muss durch das Material durch — kein direktes Editieren

Diese Datei macht CuttingPreset zu einer separaten Entitaet mit eigener ID.
Lookup geht ueber ``(material_id, werkzeug_id [, operation_type])``.

Backwards-Kompat: ``lade_cutting_presets()`` migriert automatisch die alten
``Material.presets[]`` zu CuttingPreset-Objekten. Die alten Felder bleiben
weiterhin in Material lesbar, koennen aber nicht mehr neu geschrieben werden,
sobald migriert wurde.

Siehe Wiki: docs/wiki/CuttingPreset.md
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from camwosa.db.models import Material, SchnittParameterPreset


class OperationsTyp(str, Enum):
    """Operations-Typ fuer feinere Preset-Zuordnung.

    ``GENERIC`` ist der Fallback wenn keine operations-spezifische Optimierung
    noetig ist (entspricht dem alten Material.presets[]-Verhalten).
    """

    GENERIC = "generic"
    KONTUR = "kontur"
    TASCHE = "tasche"
    GRAVUR = "gravur"
    BOHREN = "bohren"
    RELIEF = "relief"
    SCHRUPPEN = "schruppen"
    SCHLICHTEN = "schlichten"


class CuttingPreset(BaseModel):
    """Schnittparameter fuer (Material, Werkzeug, [Operation])-Kombination.

    Beispiele:
    - ``buche__schaft6mm__generic`` — Standard-Werte fuer Buche + 6mm-Fraeser
    - ``buche__schaft6mm__schruppen`` — Schruppen-Variante (mehr Vorschub, weniger sauber)
    - ``buche__schaft6mm__schlichten`` — Schlichten-Variante (weniger Vorschub, sauber)
    """

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="z.B. 'buche__schaft6mm__generic'")
    name: str = Field(default="", description="Anzeigename, frei waehlbar")
    material_id: str
    werkzeug_id: str
    operation_typ: OperationsTyp = OperationsTyp.GENERIC

    rpm: float = Field(gt=0)
    vorschub: float = Field(gt=0, description="mm/min")
    plunge: float = Field(gt=0, description="mm/min")
    stepdown: float = Field(gt=0, description="mm pro Z-Pass")
    stepover_prozent: float = Field(
        gt=0, le=100, description="Seitlicher Versatz in % vom Werkzeug-Durchmesser"
    )

    # Optionale Detailparameter
    kuehlung: str = Field(default="luft", description="luft / nebel / spray / keine")
    rampen_winkel_grad: float | None = Field(
        default=None, ge=0, le=90,
        description="Falls Rampen-Eintauchen statt senkrecht — Winkel in Grad",
    )
    quelle: str = Field(
        default="user",
        description="user / hersteller / community — fuer UI-Hinweise",
    )
    notizen: str = ""

    @model_validator(mode="after")
    def _gen_default_name(self) -> "CuttingPreset":
        if not self.name:
            object.__setattr__(
                self, "name",
                f"{self.material_id} + {self.werkzeug_id} ({self.operation_typ.value})",
            )
        return self


# ---------------------------------------------------------------------------
# Loader + Migration
# ---------------------------------------------------------------------------


def _lade_aus_dateien(directory: Path) -> list[CuttingPreset]:
    """Liest data/cutting_presets/*.json."""
    if not directory.exists():
        return []
    ergebnisse: list[CuttingPreset] = []
    for pfad in sorted(directory.glob("*.json")):
        with pfad.open("r", encoding="utf-8") as f:
            inhalt = json.load(f)
        roh = inhalt if isinstance(inhalt, list) else [inhalt]
        for e in roh:
            ergebnisse.append(CuttingPreset.model_validate(e))
    return ergebnisse


def migriere_material_presets(materialien: list[Material]) -> list[CuttingPreset]:
    """Migriert die alten ``Material.presets[]``-Eintraege zu CuttingPreset.

    ID wird deterministisch generiert: ``{material_id}__{werkzeug_id}__generic``.
    """
    ergebnisse: list[CuttingPreset] = []
    for mat in materialien:
        for p in mat.presets:
            ergebnisse.append(_aus_legacy_preset(mat.id, p))
    return ergebnisse


def _aus_legacy_preset(material_id: str, alt: SchnittParameterPreset) -> CuttingPreset:
    return CuttingPreset(
        id=f"{material_id}__{alt.werkzeug_id}__generic",
        material_id=material_id,
        werkzeug_id=alt.werkzeug_id,
        operation_typ=OperationsTyp.GENERIC,
        rpm=alt.rpm,
        vorschub=alt.vorschub,
        plunge=alt.plunge,
        stepdown=alt.stepdown,
        stepover_prozent=alt.stepover_prozent,
        quelle="legacy-migration",
    )


def lade_cutting_presets(
    data_dir: Path | None = None,
    *,
    materialien: list[Material] | None = None,
    include_legacy: bool = True,
) -> list[CuttingPreset]:
    """Laedt alle CuttingPresets aus data/cutting_presets/ + Migration.

    Mit ``include_legacy=True`` werden alte Material.presets[] mit aufgenommen,
    sofern sie nicht bereits durch eine eigene CuttingPreset-Datei ersetzt sind
    (Dedup ueber ID).
    """
    from camwosa.db.loader import _data_root, lade_materialien

    root = data_dir or _data_root()
    aus_dateien = _lade_aus_dateien(root / "cutting_presets")
    bekannte_ids = {p.id for p in aus_dateien}
    ergebnisse = list(aus_dateien)

    if include_legacy:
        mats = materialien if materialien is not None else lade_materialien(data_dir)
        for migr in migriere_material_presets(mats):
            if migr.id not in bekannte_ids:
                ergebnisse.append(migr)
                bekannte_ids.add(migr.id)
    return ergebnisse


# ---------------------------------------------------------------------------
# Lookup-Helpers
# ---------------------------------------------------------------------------


def finde_preset(
    presets: list[CuttingPreset],
    *,
    material_id: str,
    werkzeug_id: str,
    operation_typ: OperationsTyp | str = OperationsTyp.GENERIC,
) -> CuttingPreset | None:
    """Sucht das beste Preset.

    Reihenfolge:
    1. Exakter Match (material + werkzeug + operation_typ)
    2. Fallback auf GENERIC fuer dieselbe (material, werkzeug)
    3. None
    """
    op = OperationsTyp(operation_typ) if isinstance(operation_typ, str) else operation_typ
    exakt = next(
        (p for p in presets
         if p.material_id == material_id
         and p.werkzeug_id == werkzeug_id
         and p.operation_typ == op),
        None,
    )
    if exakt:
        return exakt
    if op != OperationsTyp.GENERIC:
        return finde_preset(
            presets,
            material_id=material_id,
            werkzeug_id=werkzeug_id,
            operation_typ=OperationsTyp.GENERIC,
        )
    return None


def speichere_cutting_preset(
    preset: CuttingPreset, data_dir: Path | None = None
) -> Path:
    """Schreibt ein einzelnes CuttingPreset als JSON in data/cutting_presets/."""
    from camwosa.db.loader import _data_root

    root = data_dir or _data_root()
    zielordner = root / "cutting_presets"
    zielordner.mkdir(parents=True, exist_ok=True)
    pfad = zielordner / f"{preset.id}.json"
    pfad.write_text(preset.model_dump_json(indent=2), encoding="utf-8")
    return pfad


__all__ = [
    "CuttingPreset",
    "OperationsTyp",
    "finde_preset",
    "lade_cutting_presets",
    "migriere_material_presets",
    "speichere_cutting_preset",
]
