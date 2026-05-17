"""Generische CRUD-Helpers fuer Stammdaten (Werkzeug, Material, Spindel, ...).

Ablage-Konvention:
- ``data/<entitaet>/<id>.json`` — Einzel-Eintrag (User-Override oder Neu)
- ``data/<entitaet>/<sammel>.json`` — Liste mit mehreren Eintraegen (Defaults)

Beim Laden gewinnen Einzeldateien gegenueber Sammel-Files (Dedup ueber ID).
DELETE entfernt nur Einzeldateien. Eintraege aus Sammel-Files koennen
ueberschrieben werden, indem eine Einzeldatei mit gleicher ID angelegt wird.
"""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def dedup_by_id(eintraege: list[T], *, einzeldatei_ids: set[str]) -> list[T]:
    """Bei ID-Kollision gewinnt der Eintrag der aus einer Einzeldatei kommt.

    ``einzeldatei_ids`` ist die Menge der IDs fuer die ``<id>.json`` existiert.
    """
    gesehen: dict[str, T] = {}
    for e in eintraege:
        eid = getattr(e, "id", None)
        if eid is None:
            continue
        if eid in gesehen:
            # Wer ist Sieger?
            if eid in einzeldatei_ids:
                # Falls beide aus Einzeldatei kommen — zweiter gewinnt (alphabet.)
                gesehen[eid] = e
            # Sonst behalten wir den ersten (Sammel-Datei + Einzeldatei: Einzel hat
            # schon vorher gewonnen, weil dies-Funktion in der richtigen Reihenfolge
            # aufgerufen wird (Einzel zuerst).)
        else:
            gesehen[eid] = e
    return list(gesehen.values())


def einzeldatei_ids(directory: Path) -> set[str]:
    """Liefert die IDs fuer die eine ``<id>.json`` existiert.

    Sammel-Files werden uebersprungen — Heuristik: Datei enthaelt Top-Level-Liste.
    """
    import json

    if not directory.exists():
        return set()
    out: set[str] = set()
    for pfad in directory.glob("*.json"):
        try:
            inhalt = json.loads(pfad.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if isinstance(inhalt, dict) and "id" in inhalt and inhalt["id"] == pfad.stem:
            out.add(pfad.stem)
    return out


def schreibe_einzel(
    obj: BaseModel, directory: Path, *, dateiname: str | None = None
) -> Path:
    """Schreibt ``obj`` als JSON in ``<directory>/<id>.json``.

    ``dateiname`` ueberschreibt den Default (``obj.id``).
    """
    directory.mkdir(parents=True, exist_ok=True)
    name = dateiname or f"{getattr(obj, 'id', 'unbenannt')}.json"
    pfad = directory / name
    pfad.write_text(obj.model_dump_json(indent=2), encoding="utf-8")
    return pfad


def loesche_einzel(directory: Path, entity_id: str) -> bool:
    """Loescht ``<directory>/<entity_id>.json`` falls vorhanden.

    Returns True wenn geloescht, False wenn die Datei nicht existierte
    (z.B. weil der Eintrag nur in einer Sammel-Datei liegt).
    """
    pfad = directory / f"{entity_id}.json"
    if not pfad.exists():
        return False
    pfad.unlink()
    return True


__all__ = [
    "dedup_by_id",
    "einzeldatei_ids",
    "loesche_einzel",
    "schreibe_einzel",
]
