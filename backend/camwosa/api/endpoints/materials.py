"""API-Endpoints fuer Materialien."""

from __future__ import annotations

from flask import Blueprint, jsonify

from camwosa.db.loader import lade_materialien

bp = Blueprint("materials", __name__, url_prefix="/api/materials")


@bp.get("/")
def liste():
    return jsonify([m.model_dump(mode="json") for m in lade_materialien()])


@bp.get("/<material_id>")
def details(material_id: str):
    for m in lade_materialien():
        if m.id == material_id:
            return jsonify(m.model_dump(mode="json"))
    return jsonify({"fehler": "Material nicht gefunden"}), 404
