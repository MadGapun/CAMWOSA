"""Werkzeug-Standzeit-Tracking (Phase E2).

Speichert pro Werkzeug die gesammelten Schnitt-Minuten und Warnt wenn die
``standzeit_max_minuten`` aus dem Werkzeug-Profil ueberschritten wird.

Persistenz: JSON-Datei in ``data/standzeit.json`` (oder Override per Env).
Format: { "werkzeug_id": minuten, ... }
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from camwosa.db.loader import _data_root
from camwosa.db.models import Werkzeug


def _datei() -> Path:
    if env := os.environ.get("CAMWOSA_STANDZEIT_FILE"):
        return Path(env)
    return _data_root().parent / "standzeit.json"


def lade_standzeit() -> dict[str, float]:
    p = _datei()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def speichere_standzeit(daten: dict[str, float]) -> Path:
    p = _datei()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(daten, indent=2), encoding="utf-8")
    return p


def addiere_minuten(werkzeug_id: str, minuten: float) -> dict[str, float]:
    daten = lade_standzeit()
    daten[werkzeug_id] = daten.get(werkzeug_id, 0.0) + minuten
    speichere_standzeit(daten)
    return daten


def reset_werkzeug(werkzeug_id: str) -> dict[str, float]:
    daten = lade_standzeit()
    daten.pop(werkzeug_id, None)
    speichere_standzeit(daten)
    return daten


@dataclass
class StandzeitStatus:
    werkzeug_id: str
    genutzt_minuten: float
    max_minuten: float | None
    prozent: float | None
    warnung: bool  # > 80%
    kritisch: bool  # > 100%


def status_fuer(werkzeug: Werkzeug, daten: dict[str, float] | None = None) -> StandzeitStatus:
    if daten is None:
        daten = lade_standzeit()
    genutzt = daten.get(werkzeug.id, 0.0)
    if werkzeug.standzeit_max_minuten and werkzeug.standzeit_max_minuten > 0:
        prozent = (genutzt / werkzeug.standzeit_max_minuten) * 100
        return StandzeitStatus(
            werkzeug_id=werkzeug.id,
            genutzt_minuten=genutzt,
            max_minuten=werkzeug.standzeit_max_minuten,
            prozent=prozent,
            warnung=prozent >= 80,
            kritisch=prozent >= 100,
        )
    return StandzeitStatus(
        werkzeug_id=werkzeug.id, genutzt_minuten=genutzt,
        max_minuten=None, prozent=None, warnung=False, kritisch=False,
    )


__all__ = [
    "StandzeitStatus",
    "addiere_minuten",
    "lade_standzeit",
    "reset_werkzeug",
    "speichere_standzeit",
    "status_fuer",
]
