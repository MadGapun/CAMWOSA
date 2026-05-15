"""Workflow-Manager fuer Multi-Setup-Projekte.

Stellt API-Funktionen bereit:
- setup_erstellen
- setup_pause_einfuegen
- setups_anordnen / -loeschen
- multi_setup_sicherheits_pruefung
- gcode_dateien_pro_setup_generieren

Siehe Wiki: docs/wiki/Workflow-Modul.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from camwosa.db.models import Maschine, Werkzeug
from camwosa.gcode.toolpath import Toolpath
from camwosa.postprocessor import PostKontext, registry
from camwosa.project.schema import Setup, SetupPause, Variante


@dataclass
class WorkflowProblem:
    """Ein Hinweis aus der Multi-Setup-Pruefung."""

    setup_id: str | None
    stufe: str  # "info" | "warnung" | "kritisch"
    text: str


@dataclass
class WorkflowBericht:
    probleme: list[WorkflowProblem] = field(default_factory=list)

    @property
    def hat_blocker(self) -> bool:
        return any(p.stufe == "kritisch" for p in self.probleme)


def pruefe_workflow(variante: Variante) -> WorkflowBericht:
    """Multi-Setup-Sicherheits-Checks (siehe Issue #13 Akzeptanzkriterien)."""
    bericht = WorkflowBericht()

    setups = variante.setups

    # Modus-Wechsel ohne Pause
    for prev, curr in zip(setups, setups[1:]):
        if prev.maschinen_modus != curr.maschinen_modus and curr.pause_vor is None:
            bericht.probleme.append(WorkflowProblem(
                setup_id=curr.id,
                stufe="kritisch",
                text=(
                    f"Modus-Wechsel von '{prev.maschinen_modus}' auf "
                    f"'{curr.maschinen_modus}' ohne Setup-Pause. Pause hinzufuegen!"
                ),
            ))

    # Werkzeugwechsel ohne Pause
    for prev, curr in zip(setups, setups[1:]):
        if prev.werkzeug_id != curr.werkzeug_id and (
            curr.pause_vor is None
            or curr.pause_vor.typ.value != "werkzeugwechsel"
        ):
            bericht.probleme.append(WorkflowProblem(
                setup_id=curr.id,
                stufe="warnung",
                text=(
                    f"Werkzeugwechsel von '{prev.werkzeug_id}' auf "
                    f"'{curr.werkzeug_id}' ohne explizite Werkzeugwechsel-Pause."
                ),
            ))

    # Pause ohne Anweisung
    for s in setups:
        if s.pause_vor and not s.pause_vor.anweisung.strip():
            bericht.probleme.append(WorkflowProblem(
                setup_id=s.id,
                stufe="warnung",
                text=f"Pause vor Setup '{s.name}' hat keine Anweisungs-Text.",
            ))

    return bericht


def schreibe_gcode_pro_setup(
    variante: Variante,
    maschine: Maschine,
    werkzeug_index: dict[str, Werkzeug],
    toolpaths_pro_setup: dict[str, list[Toolpath]],
    ziel_verzeichnis: str | Path,
) -> dict[str, Path]:
    """Schreibt fuer jedes Setup eine eigene G-Code-Datei.

    ``toolpaths_pro_setup``: Mapping setup_id -> Liste von Toolpaths.
    """
    ziel = Path(ziel_verzeichnis)
    ziel.mkdir(parents=True, exist_ok=True)
    ergebnis: dict[str, Path] = {}

    for setup in variante.setups:
        toolpaths = toolpaths_pro_setup.get(setup.id, [])
        if not toolpaths:
            continue
        werkzeug = werkzeug_index[setup.werkzeug_id]
        post_id = maschine.postprozessor
        post_klasse = registry().get(post_id)
        post = post_klasse()
        ctx = PostKontext(maschine=maschine, werkzeug=werkzeug)
        zeilen = post.post_alle(ctx, toolpaths)
        ext = post.file_extension
        pfad = ziel / f"{setup.id}_{_safe_name(setup.name)}{ext}"
        pfad.write_text("\n".join(zeilen) + "\n", encoding="utf-8")
        ergebnis[setup.id] = pfad

    return ergebnis


def _safe_name(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)


__all__ = [
    "WorkflowBericht",
    "WorkflowProblem",
    "pruefe_workflow",
    "schreibe_gcode_pro_setup",
]
