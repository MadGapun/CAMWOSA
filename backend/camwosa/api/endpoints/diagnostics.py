"""Diagnose-API: Z-Grid-Analyse."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from camwosa.diagnostics.z_grid import ZGridDaten, analyse

bp = Blueprint("diagnostics", __name__, url_prefix="/api/diagnostics")


@bp.post("/z-grid")
def z_grid():
    """Analysiert Z-Probing-Daten auf Werkstuecks-Ebenheit.

    Body:
        {
          "messpunkte": [{"x": 0, "y": 0, "z": 0.0}, ...],
          "werkzeug_typ": "schaftfraeser" | "kugelfraeser" | ...,
          "bezugs_z": 0.0  # optional
        }

    Response:
        {
          "befund": "eben_ok" | "leichte_neigung" | "starke_neigung" | "unebene_oberflaeche",
          "klartext": "...", "empfehlung": "...",
          "z_min": ..., "z_max": ..., "z_spreizung": ...,
          "neigung_grad": ..., "neigung_richtung_grad": ...,
          "abweichungen": [...]
        }
    """
    try:
        daten = ZGridDaten.model_validate(request.get_json() or {})
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    ergebnis = analyse(daten)
    return jsonify(ergebnis.model_dump(mode="json"))
