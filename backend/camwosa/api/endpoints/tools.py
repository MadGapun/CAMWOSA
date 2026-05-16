"""API-Endpoints fuer Werkzeuge."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from camwosa.db.loader import lade_werkzeuge
from camwosa.db.models import Werkzeug

_BUNDLE_TYP = "camwosa.tool_bundle"

bp = Blueprint("tools", __name__, url_prefix="/api/tools")


@bp.get("/")
def liste():
    return jsonify([t.model_dump(mode="json") for t in lade_werkzeuge()])


@bp.get("/<tool_id>")
def details(tool_id: str):
    for t in lade_werkzeuge():
        if t.id == tool_id:
            return jsonify(t.model_dump(mode="json"))
    return jsonify({"fehler": "Werkzeug nicht gefunden"}), 404


@bp.post("/validate")
def validate():
    try:
        t = Werkzeug.model_validate(request.get_json())
        return jsonify({"gueltig": True, "id": t.id})
    except Exception as e:  # noqa: BLE001
        return jsonify({"gueltig": False, "fehler": str(e)}), 422


@bp.get("/<tool_id>/export")
def export_tool(tool_id: str):
    """Exportiert ein einzelnes Werkzeug als JSON-Bundle."""
    for t in lade_werkzeuge():
        if t.id == tool_id:
            return jsonify({
                "schema_version": 1,
                "typ": _BUNDLE_TYP,
                "werkzeug": t.model_dump(mode="json"),
            })
    return jsonify({"fehler": "Werkzeug nicht gefunden"}), 404


@bp.post("/import")
def import_tool_bundle():
    data = request.get_json()
    if data.get("typ") != _BUNDLE_TYP:
        return jsonify({"fehler": "Kein gueltiges tool_bundle"}), 422
    try:
        t = Werkzeug.model_validate(data["werkzeug"])
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    return jsonify({"gueltig": True, "werkzeug": t.model_dump(mode="json")})
