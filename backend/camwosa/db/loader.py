"""Loader fuer Default-Profile aus JSON-Dateien (data/-Verzeichnis).

Profile sind die mitgelieferten Maschinen-, Werkzeug- und Material-Definitionen.
Sie werden beim ersten Start in die SQLite-DB importiert oder direkt zur Laufzeit
geladen — je nach Aufrufer.

Siehe Wiki: docs/wiki/Datenmodell.md
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from camwosa.db.models import Maschine, Material, Spindel, Werkzeug

T = TypeVar("T", bound=BaseModel)


def _data_root() -> Path:
    """Liefert das data/-Verzeichnis im Repo (oder Override via Umgebungsvariable)."""
    import os

    if (env := os.environ.get("CAMWOSA_DATA_DIR")):
        return Path(env)
    # Repo-Layout: backend/camwosa/db/loader.py -> ../../../data
    return Path(__file__).resolve().parents[3] / "data"


def _load_json_files(directory: Path) -> list[dict]:
    """Sammelt alle *.json-Dateien aus einem Verzeichnis.

    Eine Datei kann ein einzelnes Objekt oder eine Liste enthalten.
    """
    if not directory.exists():
        return []
    eintraege: list[dict] = []
    for pfad in sorted(directory.glob("*.json")):
        with pfad.open("r", encoding="utf-8") as f:
            inhalt = json.load(f)
        if isinstance(inhalt, list):
            eintraege.extend(inhalt)
        elif isinstance(inhalt, dict):
            eintraege.append(inhalt)
        else:
            raise ValueError(f"Unerwartetes Format in {pfad}: {type(inhalt).__name__}")
    return eintraege


def _parse_alle(eintraege: list[dict], modell: type[T]) -> list[T]:
    return [modell.model_validate(e) for e in eintraege]


def lade_maschinen(data_dir: Path | None = None) -> list[Maschine]:
    """Laedt alle Maschinen-Profile aus data/machines/."""
    root = data_dir or _data_root()
    return _parse_alle(_load_json_files(root / "machines"), Maschine)


def lade_werkzeuge(data_dir: Path | None = None) -> list[Werkzeug]:
    """Laedt alle Werkzeuge aus data/tools/."""
    root = data_dir or _data_root()
    return _parse_alle(_load_json_files(root / "tools"), Werkzeug)


def lade_materialien(data_dir: Path | None = None) -> list[Material]:
    """Laedt alle Materialien aus data/materials/."""
    root = data_dir or _data_root()
    return _parse_alle(_load_json_files(root / "materials"), Material)


def lade_spindeln(data_dir: Path | None = None) -> list[Spindel]:
    """Laedt alle Spindeln aus data/spindles/."""
    root = data_dir or _data_root()
    return _parse_alle(_load_json_files(root / "spindles"), Spindel)


def spindel_index(data_dir: Path | None = None) -> dict[str, Spindel]:
    """Liefert {id: Spindel} fuer schnellen Lookup."""
    return {s.id: s for s in lade_spindeln(data_dir)}


def speichere_maschine(maschine: Maschine, data_dir: Path | None = None) -> Path:
    """Schreibt eine einzelne Maschine als JSON-Profil zurueck."""
    root = data_dir or _data_root()
    zielordner = root / "machines"
    zielordner.mkdir(parents=True, exist_ok=True)
    pfad = zielordner / f"{maschine.id}.json"
    pfad.write_text(maschine.model_dump_json(indent=2), encoding="utf-8")
    return pfad


__all__ = [
    "lade_maschinen",
    "lade_materialien",
    "lade_spindeln",
    "lade_werkzeuge",
    "spindel_index",
    "speichere_maschine",
]
