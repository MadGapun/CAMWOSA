"""API-Endpoints fuer Maschinen-Profile."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from camwosa.db.loader import lade_maschinen
from camwosa.db.models import Maschine

bp = Blueprint("machines", __name__, url_prefix="/api/machines")


@bp.get("/")
def liste():
    maschinen = lade_maschinen()
    return jsonify([m.model_dump(mode="json") for m in maschinen])


@bp.get("/<machine_id>")
def details(machine_id: str):
    maschinen = lade_maschinen()
    for m in maschinen:
        if m.id == machine_id:
            return jsonify(m.model_dump(mode="json"))
    return jsonify({"fehler": "Maschine nicht gefunden"}), 404


@bp.post("/validate")
def validate():
    """Pruef-Endpoint fuer ein Maschinen-Profil."""
    data = request.get_json()
    try:
        maschine = Maschine.model_validate(data)
        return jsonify({"gueltig": True, "id": maschine.id})
    except Exception as e:  # noqa: BLE001
        return jsonify({"gueltig": False, "fehler": str(e)}), 422
