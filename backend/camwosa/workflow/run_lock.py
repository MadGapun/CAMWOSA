"""Run-Lock + Dependency-Graph (Master-Plan A48).

Markus' Regel: „Im Zweifel laeuft das Programm nicht."

Bevor G-Code generiert wird, pruefen:
1. Alle Operations haben status OK (nicht DIRTY/BROKEN/NEU)
2. Alle referenzierten Geometrien existieren
3. Alle referenzierten Werkzeuge existieren
4. Reihenfolge ist plausibel (Heuristiken)

Bei Problemen: ``darf_gcode_generieren()`` liefert ``(False, [grund1, grund2])``
und der API-Endpoint wirft 422 mit der Begruendungs-Liste.

Plus: ``markiere_abhaengige_dirty()`` propagiert Aenderungen — wenn eine
Geometrie/Werkzeug/Material aendert, werden alle abhaengigen Operations
auf DIRTY gesetzt.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from camwosa.project.schema import (
    CWPProjekt,
    OperationsKonfig,
    OperationStatus,
    Setup,
    Variante,
)


def operation_input_hash(
    op: OperationsKonfig,
    geometrien_inhalt: dict[str, Any] | None = None,
    werkzeug_inhalt: dict[str, Any] | None = None,
    material_inhalt: dict[str, Any] | None = None,
) -> str:
    """Berechnet einen SHA1-Hash der Operation-Inputs.

    Aenderung an einem Input -> Hash aendert sich -> Status muss auf DIRTY.

    Args:
        op: die Operation
        geometrien_inhalt: dict ``geometrie_id -> serialisierte Daten``
            fuer alle referenzierten Geometrien
        werkzeug_inhalt: serialisiertes Werkzeug-Modell
        material_inhalt: serialisiertes Material-Modell

    Returns:
        SHA1-Hex-String der konkatenierten JSON-Repraesentation.
    """
    payload = {
        "typ": op.typ,
        "geometrie_ids": sorted(op.geometrie_ids),
        "parameter": op.parameter,
        "geometrien": geometrien_inhalt or {},
        "werkzeug": werkzeug_inhalt or {},
        "material": material_inhalt or {},
    }
    blob = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha1(blob).hexdigest()


def pruefe_operation(
    op: OperationsKonfig,
    geometrie_ids_vorhanden: set[str],
    werkzeug_ids_vorhanden: set[str],
    material_ids_vorhanden: set[str],
) -> tuple[OperationStatus, str]:
    """Pruefe Operation-Konsistenz.

    Returns:
        (neuer_status, fehler_text). Fehler-Text leer wenn Status OK/NEU/DIRTY.
    """
    if not op.aktiviert:
        return op.status, ""

    # 1. Geometrie-Referenzen existieren?
    fehlende_geometrien = [
        gid for gid in op.geometrie_ids if gid not in geometrie_ids_vorhanden
    ]
    if fehlende_geometrien and op.typ in ("kontur", "tasche", "bohren", "gravur", "relief", "wrap"):
        return (
            OperationStatus.BROKEN,
            f"Geometrie(n) {fehlende_geometrien} existieren nicht mehr",
        )

    # 2. Werkzeug-Ref existiert?
    werkzeug_id = op.parameter.get("werkzeug_id")
    if werkzeug_id and werkzeug_id not in werkzeug_ids_vorhanden:
        return (
            OperationStatus.BROKEN,
            f"Werkzeug '{werkzeug_id}' existiert nicht mehr",
        )

    # 3. Material-Ref (optional je nach Operation)
    material_id = op.parameter.get("material_id")
    if material_id and material_id not in material_ids_vorhanden:
        return (
            OperationStatus.BROKEN,
            f"Material '{material_id}' existiert nicht mehr",
        )

    # Alles ok — Status bleibt was er war (NEU/OK/DIRTY)
    return op.status, ""


def pruefe_projekt(projekt: CWPProjekt) -> dict[str, tuple[OperationStatus, str]]:
    """Pruefe alle Operations im Projekt + setze Status entsprechend.

    Returns:
        dict ``op_id -> (status, fehler_text)`` fuer alle Operations.
        Mutiert die Operations NICHT — Caller entscheidet ob er die
        Ergebnisse uebernimmt.
    """
    geometrie_ids = {g.id for g in projekt.geometrien}
    werkzeug_ids = {w.id for w in projekt.werkzeuge}
    material_ids = {m.id for m in projekt.materialien}

    result: dict[str, tuple[OperationStatus, str]] = {}
    for variante in projekt.varianten:
        for setup in variante.setups:
            for op in setup.operationen:
                result[op.id] = pruefe_operation(
                    op, geometrie_ids, werkzeug_ids, material_ids,
                )
    return result


def darf_gcode_generieren(
    projekt: CWPProjekt,
    variante_id: str | None = None,
    setup_id: str | None = None,
) -> tuple[bool, list[str]]:
    """Run-Lock-Check: darf G-Code generiert werden?

    Args:
        projekt: das Projekt
        variante_id: Wenn None, alle Varianten pruefen, sonst nur diese
        setup_id: Wenn None, alle Setups, sonst nur dieses

    Returns:
        ``(True, [])`` wenn alles ok.
        ``(False, ['Grund 1', 'Grund 2', ...])`` wenn blockiert.
    """
    blocker: list[str] = []
    status_map = pruefe_projekt(projekt)

    for variante in projekt.varianten:
        if variante_id and variante.id != variante_id:
            continue
        for setup in variante.setups:
            if setup_id and setup.id != setup_id:
                continue

            if not setup.operationen:
                blocker.append(f"Setup '{setup.name}': keine Operationen")
                continue

            for op in setup.operationen:
                if not op.aktiviert:
                    continue
                status, fehler = status_map.get(op.id, (op.status, op.fehler_text))
                if status == OperationStatus.BROKEN:
                    blocker.append(
                        f"Setup '{setup.name}' / Op '{op.name}': {fehler or 'BROKEN'}"
                    )
                if status == OperationStatus.DIRTY:
                    blocker.append(
                        f"Setup '{setup.name}' / Op '{op.name}': Toolpath veraltet — "
                        f"neu berechnen erforderlich"
                    )
                if status == OperationStatus.NEU:
                    blocker.append(
                        f"Setup '{setup.name}' / Op '{op.name}': noch nie berechnet"
                    )

    # Heuristik: Letzter Setup ist Boden-Setup? (A49)
    # — nur Warnung, kein Blocker
    # TODO: in spaeterer Iteration

    return len(blocker) == 0, blocker


def markiere_abhaengige_dirty(
    projekt: CWPProjekt,
    *,
    geometrie_ids: set[str] | None = None,
    werkzeug_ids: set[str] | None = None,
    material_ids: set[str] | None = None,
) -> int:
    """Propagiere Change-Markierung: setze abhaengige Operations auf DIRTY.

    Args:
        projekt: das Projekt
        geometrie_ids: Set von Geometrie-IDs die sich geaendert haben
        werkzeug_ids: Set von Werkzeug-IDs die sich geaendert haben
        material_ids: Set von Material-IDs die sich geaendert haben

    Returns:
        Anzahl der markierten Operations.

    Mutiert die Operations direkt (setzt status = DIRTY wo zutreffend).
    """
    geo_set = geometrie_ids or set()
    wz_set = werkzeug_ids or set()
    mat_set = material_ids or set()

    count = 0
    for variante in projekt.varianten:
        for setup in variante.setups:
            for op in setup.operationen:
                if not op.aktiviert:
                    continue
                if op.status == OperationStatus.BROKEN:
                    continue  # Broken bleibt Broken bis es gefixt wird

                if geo_set & set(op.geometrie_ids):
                    op.status = OperationStatus.DIRTY
                    count += 1
                    continue
                werkzeug_id = op.parameter.get("werkzeug_id")
                if werkzeug_id and werkzeug_id in wz_set:
                    op.status = OperationStatus.DIRTY
                    count += 1
                    continue
                material_id = op.parameter.get("material_id")
                if material_id and material_id in mat_set:
                    op.status = OperationStatus.DIRTY
                    count += 1
                    continue
    return count


__all__ = [
    "darf_gcode_generieren",
    "markiere_abhaengige_dirty",
    "operation_input_hash",
    "pruefe_operation",
    "pruefe_projekt",
]
