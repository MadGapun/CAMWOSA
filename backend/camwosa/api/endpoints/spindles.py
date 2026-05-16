"""API-Endpoints fuer Spindeln."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from camwosa.db.loader import lade_spindeln
from camwosa.db.models import Spindel

bp = Blueprint("spindles", __name__, url_prefix="/api/spindles")


@bp.get("/")
def liste():
    return jsonify([s.model_dump(mode="json") for s in lade_spindeln()])


@bp.get("/<spindel_id>")
def details(spindel_id: str):
    for s in lade_spindeln():
        if s.id == spindel_id:
            return jsonify(s.model_dump(mode="json"))
    return jsonify({"fehler": "Spindel nicht gefunden"}), 404


@bp.post("/validate")
def validate():
    try:
        s = Spindel.model_validate(request.get_json())
        return jsonify({"gueltig": True, "id": s.id})
    except Exception as e:  # noqa: BLE001
        return jsonify({"gueltig": False, "fehler": str(e)}), 422
