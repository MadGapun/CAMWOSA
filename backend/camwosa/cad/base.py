"""Basisklassen + Registry fuer CAD-Importer.

CAMWOSA unterstuetzt mehrere CAD-Formate ueber ein Plugin-System.
Jeder Importer registriert sich beim Start und liefert eine einheitliche
Schnittstelle: Datei -> Liste von GeometrieObjekten + Metadaten.

Siehe Wiki: docs/wiki/CAD-Import.md
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from camwosa.dxf.parser import GeometrieObjekt, Punkt2D


@dataclass
class CADImportErgebnis:
    """Einheitliches Ergebnis eines CAD-Imports."""

    format_id: str
    einheit: str  # "mm" | "inch" | "unbekannt"
    objekte: list[GeometrieObjekt]
    layer: list[str] = field(default_factory=list)
    bounding_box: tuple[Punkt2D, Punkt2D] | None = None
    metadaten: dict = field(default_factory=dict)


class CADImporter(ABC):
    """Basisklasse fuer CAD-Importer."""

    format_id: str = "unbekannt"
    name: str = "Unbekannter Importer"
    extensions: tuple[str, ...] = ()  # z.B. (".dxf", ".dwg")
    beschreibung: str = ""

    @abstractmethod
    def kann_lesen(self, pfad: Path) -> bool:
        """Prueft ob dieser Importer die Datei lesen kann."""
        ...

    @abstractmethod
    def lade(self, pfad: Path) -> CADImportErgebnis:
        """Liest die Datei und gibt das Ergebnis zurueck."""
        ...


class CADImportFehler(Exception):
    pass


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class CADImporterRegistry:
    def __init__(self) -> None:
        self._registry: dict[str, type[CADImporter]] = {}

    def register(self, format_id: str, klasse: type[CADImporter]) -> None:
        if not issubclass(klasse, CADImporter):
            raise TypeError(f"{klasse} ist kein CADImporter")
        self._registry[format_id] = klasse

    def list_ids(self) -> list[str]:
        return sorted(self._registry.keys())

    def list_extensions(self) -> dict[str, str]:
        """Mapping ext -> format_id, z.B. {'.dxf': 'dxf', '.svg': 'svg'}."""
        out: dict[str, str] = {}
        for fid, klasse in self._registry.items():
            for ext in klasse.extensions:
                out[ext.lower()] = fid
        return out

    def fuer_datei(self, pfad: Path) -> CADImporter:
        """Findet den passenden Importer fuer eine Datei."""
        ext = pfad.suffix.lower()
        # Erst per Extension
        for fid, klasse in self._registry.items():
            if ext in (e.lower() for e in klasse.extensions):
                return klasse()
        # Fallback: jeden Importer fragen
        for fid, klasse in self._registry.items():
            instanz = klasse()
            try:
                if instanz.kann_lesen(pfad):
                    return instanz
            except Exception:  # noqa: BLE001
                continue
        raise CADImportFehler(
            f"Kein Importer fuer {pfad.name} verfuegbar. "
            f"Unterstuetzte Formate: {sorted({e for k in self._registry.values() for e in k.extensions})}"
        )

    def get(self, format_id: str) -> type[CADImporter]:
        if format_id not in self._registry:
            raise KeyError(f"Format '{format_id}' nicht registriert.")
        return self._registry[format_id]


_REGISTRY = CADImporterRegistry()


def registry() -> CADImporterRegistry:
    return _REGISTRY


def lade_cad(pfad: str | Path) -> CADImportErgebnis:
    """Convenience: Findet den passenden Importer und liest die Datei."""
    p = Path(pfad)
    if not p.exists():
        raise CADImportFehler(f"Datei nicht gefunden: {p}")
    importer = registry().fuer_datei(p)
    return importer.lade(p)


__all__ = [
    "CADImportErgebnis",
    "CADImportFehler",
    "CADImporter",
    "CADImporterRegistry",
    "lade_cad",
    "registry",
]
