"""Postprozessor-Basisklasse + Registry.

Ein Postprozessor wandelt einen Toolpath in maschinenspezifischen G-Code.
Die Basisklasse definiert die API; konkrete Postprozessoren implementieren sie.

Plugin-fähig: User-Postprozessoren werden aus
``data/postprocessors/`` (oder ``$CAMWOSA_USER_POSTPROCESSOR_DIR``) geladen.

Siehe Wiki: docs/wiki/Postprozessor-Plugins.md
"""

from __future__ import annotations

import importlib.util
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from camwosa.db.models import Maschine, Werkzeug
from camwosa.gcode.toolpath import Bewegung, BewegungsTyp, Toolpath


@dataclass
class PostKontext:
    """Kontext-Informationen die der Postprozessor braucht."""

    maschine: Maschine
    werkzeug: Werkzeug
    operation_kommentar: str = ""
    backplot_annotation: bool = True
    metadaten: dict = field(default_factory=dict)
    # P1 (Cluster P): Spindel-Hochlauf-Pause in Sekunden. Wird nach M3 als
    # ``G4 P<t>`` ausgegeben, damit die Spindel vor dem Erstschnitt auf Drehzahl
    # ist. 0 = aus (rueckwaertskompatibel). Quelle: Spindel.rampen_zeit_s.
    spindel_hochlauf_s: float = 0.0
    # Warmlauf (optional): laesst die Spindel am PROGRAMMSTART eine Weile bei
    # moderater Drehzahl laufen, bevor der Job beginnt — schont VFD/Lager.
    # Beide > 0 noetig, sonst aus. Quelle: Spindel.warmlauf_zeit_s / warmlauf_rpm.
    warmlauf_s: float = 0.0
    warmlauf_rpm: float = 0.0


class PostProcessor(ABC):
    """Basisklasse fuer Postprozessoren.

    Konkrete Postprozessoren ueberschreiben ``header``, ``footer`` und die
    Bewegungs-Methoden. Default-Implementierungen liefern GRBL-konformes G-Code.
    """

    name: str = "Unbenannt"
    file_extension: str = ".nc"
    beschreibung: str = ""

    # --- Lifecycle ---------------------------------------------------------

    def header(self, ctx: PostKontext) -> list[str]:
        """G-Code-Header (Initialisierung)."""
        return []

    def footer(self, ctx: PostKontext) -> list[str]:
        """G-Code-Footer (Spindel aus, Park)."""
        return []

    def tool_change(self, ctx: PostKontext, tool: Werkzeug) -> list[str]:
        """Werkzeug-Wechsel-Sequenz."""
        return []

    def spindle_on(self, ctx: PostKontext, rpm: float) -> list[str]:
        zeilen = [f"M3 S{int(round(rpm))}"]
        # P1: Hochlauf-Pause, damit die Spindel vor dem ersten Schnitt dreht.
        if ctx.spindel_hochlauf_s and ctx.spindel_hochlauf_s > 0:
            # P-Wert in Sekunden; :g vermeidet unnoetige Nullen (2.0 -> 2).
            zeilen.append(f"G4 P{ctx.spindel_hochlauf_s:g}")
        return zeilen

    def spindle_off(self, ctx: PostKontext) -> list[str]:
        return ["M5"]

    def warmlauf(self, ctx: PostKontext) -> list[str]:
        """Optionaler Spindel-Warmlauf am Programmstart.

        Laesst die Spindel ``warmlauf_s`` Sekunden bei ``warmlauf_rpm`` drehen
        (M3 + G4-Dwell) bevor der eigentliche Job startet. Die Spindel bleibt an
        — der erste Schnitt rampt per ``spindle_on`` auf Schnittdrehzahl.
        Beide Werte > 0 noetig, sonst leer (rueckwaertskompatibel).
        """
        if not (ctx.warmlauf_s and ctx.warmlauf_s > 0 and ctx.warmlauf_rpm and ctx.warmlauf_rpm > 0):
            return []
        rpm = int(round(ctx.warmlauf_rpm))
        return [
            self._kommentar(f"Spindel-Warmlauf {ctx.warmlauf_s:g}s @ {rpm} U/min (VFD/Lager schonen)"),
            f"M3 S{rpm}",
            f"G4 P{ctx.warmlauf_s:g}",
        ]

    # --- Bewegungen --------------------------------------------------------

    @abstractmethod
    def rapid_move(self, ctx: PostKontext, b: Bewegung) -> list[str]:
        ...

    @abstractmethod
    def linear_move(self, ctx: PostKontext, b: Bewegung) -> list[str]:
        ...

    @abstractmethod
    def arc_move(self, ctx: PostKontext, b: Bewegung) -> list[str]:
        ...

    # --- Hauptmethode ------------------------------------------------------

    def post(self, ctx: PostKontext, toolpath: Toolpath) -> list[str]:
        """Wandelt einen einzelnen Toolpath in G-Code-Zeilen."""
        zeilen: list[str] = []

        if ctx.backplot_annotation and toolpath.kommentar:
            zeilen.append(self._kommentar(f"Operation: {toolpath.kommentar}"))

        zeilen.extend(self.spindle_on(ctx, toolpath.spindel_rpm))

        for b in toolpath.bewegungen:
            if b.typ == BewegungsTyp.EILGANG:
                zeilen.extend(self.rapid_move(ctx, b))
            elif b.typ in (BewegungsTyp.LINEAR, BewegungsTyp.PLUNGE):
                zeilen.extend(self.linear_move(ctx, b))
            elif b.typ in (BewegungsTyp.BOGEN_CW, BewegungsTyp.BOGEN_CCW):
                zeilen.extend(self.arc_move(ctx, b))
            else:
                raise ValueError(f"Unbekannter BewegungsTyp: {b.typ}")

        return zeilen

    def post_alle(self, ctx: PostKontext, toolpaths: Iterable[Toolpath]) -> list[str]:
        """Wandelt mehrere Toolpaths zu einem kompletten G-Code-File.

        Zwischen Toolpaths fuer unterschiedliche Werkzeuge wird ``tool_change``
        eingefuegt. Header und Footer umrahmen das Ganze.
        """
        zeilen: list[str] = []
        zeilen.extend(self.header(ctx))
        zeilen.extend(self.warmlauf(ctx))
        aktuelles_werkzeug = ctx.werkzeug
        for tp in toolpaths:
            if tp.werkzeug_id != aktuelles_werkzeug.id:
                # In der Praxis muss das Repository das Werkzeug nachladen.
                # Hier nutzen wir eine Stub-Werkzeug-Definition mit nur der ID.
                zeilen.append(self._kommentar(f"Werkzeugwechsel auf {tp.werkzeug_id}"))
                zeilen.extend(self.tool_change(ctx, ctx.werkzeug))
            zeilen.extend(self.post(ctx, tp))
        zeilen.extend(self.spindle_off(ctx))
        zeilen.extend(self.footer(ctx))
        return zeilen

    # --- Helfer ------------------------------------------------------------

    def _kommentar(self, text: str) -> str:
        return f"; {text}"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class PostProcessorRegistry:
    """Registriert verfuegbare Postprozessoren nach ID."""

    def __init__(self) -> None:
        self._registry: dict[str, type[PostProcessor]] = {}

    def register(self, post_id: str, klasse: type[PostProcessor]) -> None:
        if not issubclass(klasse, PostProcessor):
            raise TypeError(f"{klasse} ist kein PostProcessor")
        self._registry[post_id] = klasse

    def get(self, post_id: str) -> type[PostProcessor]:
        if post_id not in self._registry:
            raise KeyError(
                f"Postprozessor '{post_id}' nicht registriert. "
                f"Verfuegbar: {sorted(self._registry.keys())}"
            )
        return self._registry[post_id]

    def list_ids(self) -> list[str]:
        return sorted(self._registry.keys())

    def lade_aus_verzeichnis(self, verzeichnis: Path) -> int:
        """Laedt User-Postprozessoren aus *.py-Dateien.

        Jede Datei muss eine Subklasse von PostProcessor enthalten und ein
        Modul-Attribut ``POSTPROCESSOR_ID`` (str) definieren.
        Gibt die Anzahl geladener Module zurueck.
        """
        if not verzeichnis.exists():
            return 0
        anzahl = 0
        for pfad in sorted(verzeichnis.glob("*.py")):
            if pfad.name.startswith("_"):
                continue
            spec = importlib.util.spec_from_file_location(
                f"camwosa_userpost_{pfad.stem}", pfad
            )
            if spec is None or spec.loader is None:
                continue
            modul = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = modul
            try:
                spec.loader.exec_module(modul)
            except Exception as e:  # noqa: BLE001
                raise RuntimeError(f"Fehler beim Laden von {pfad}: {e}") from e
            post_id = getattr(modul, "POSTPROCESSOR_ID", None)
            if post_id is None:
                raise ValueError(
                    f"{pfad}: POSTPROCESSOR_ID-Konstante fehlt im Modul"
                )
            klassen = [
                v for v in vars(modul).values()
                if isinstance(v, type) and issubclass(v, PostProcessor) and v is not PostProcessor
            ]
            if not klassen:
                raise ValueError(f"{pfad}: keine PostProcessor-Subklasse gefunden")
            self.register(post_id, klassen[0])
            anzahl += 1
        return anzahl


_REGISTRY = PostProcessorRegistry()


def registry() -> PostProcessorRegistry:
    return _REGISTRY


__all__ = [
    "PostKontext",
    "PostProcessor",
    "PostProcessorRegistry",
    "registry",
]
