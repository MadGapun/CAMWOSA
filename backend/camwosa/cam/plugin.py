"""Plugin-API fuer eigene CAM-Operationen.

Erlaubt User-Code eigene Operations-Typen zu registrieren — analog zum
Postprozessor-Plugin-System.

Beispiel:

    from camwosa.cam.plugin import OperationPlugin, registry

    OPERATION_ID = "meine_operation"

    class MeineOperation(OperationPlugin):
        name = "Meine Operation"
        beschreibung = "Tut etwas Spezielles"

        def erzeuge_toolpath(self, geometrie, werkzeug, parameter):
            ...

    registry().register("meine_operation", MeineOperation)
"""

from __future__ import annotations

import importlib.util
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from camwosa.db.models import Werkzeug
from camwosa.gcode.toolpath import Toolpath


class OperationPlugin(ABC):
    """Basisklasse fuer User-CAM-Operationen."""

    name: str = "Unbenannte Operation"
    beschreibung: str = ""
    benoetigt_geschlossene_kontur: bool = False
    benoetigt_punkte: bool = False
    benoetigt_offene_kontur: bool = False

    @abstractmethod
    def erzeuge_toolpath(
        self,
        geometrie: Any,
        werkzeug: Werkzeug,
        parameter: dict[str, Any],
    ) -> Toolpath:
        ...


class OperationPluginRegistry:
    def __init__(self) -> None:
        self._registry: dict[str, type[OperationPlugin]] = {}

    def register(self, op_id: str, klasse: type[OperationPlugin]) -> None:
        if not issubclass(klasse, OperationPlugin):
            raise TypeError(f"{klasse} ist kein OperationPlugin")
        self._registry[op_id] = klasse

    def get(self, op_id: str) -> type[OperationPlugin]:
        if op_id not in self._registry:
            raise KeyError(
                f"Operation-Plugin '{op_id}' nicht registriert. "
                f"Verfuegbar: {sorted(self._registry.keys())}"
            )
        return self._registry[op_id]

    def list_ids(self) -> list[str]:
        return sorted(self._registry.keys())

    def lade_aus_verzeichnis(self, verzeichnis: Path) -> int:
        if not verzeichnis.exists():
            return 0
        anzahl = 0
        for pfad in sorted(verzeichnis.glob("*.py")):
            if pfad.name.startswith("_"):
                continue
            spec = importlib.util.spec_from_file_location(
                f"camwosa_op_{pfad.stem}", pfad
            )
            if spec is None or spec.loader is None:
                continue
            modul = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = modul
            try:
                spec.loader.exec_module(modul)
            except Exception as e:  # noqa: BLE001
                raise RuntimeError(f"Fehler beim Laden von {pfad}: {e}") from e
            op_id = getattr(modul, "OPERATION_ID", None)
            if op_id is None:
                raise ValueError(f"{pfad}: OPERATION_ID-Konstante fehlt")
            klassen = [
                v for v in vars(modul).values()
                if isinstance(v, type)
                and issubclass(v, OperationPlugin)
                and v is not OperationPlugin
            ]
            if not klassen:
                raise ValueError(f"{pfad}: keine OperationPlugin-Subklasse gefunden")
            self.register(op_id, klassen[0])
            anzahl += 1
        return anzahl


_REGISTRY = OperationPluginRegistry()


def registry() -> OperationPluginRegistry:
    return _REGISTRY


__all__ = ["OperationPlugin", "OperationPluginRegistry", "registry"]
