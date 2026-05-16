"""API-Endpoints fuer Materialien (mit Bundle-Sharing)."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from camwosa.db.loader import lade_materialien
from camwosa.db.models import Material

bp = Blueprint("materials", __name__, url_prefix="/api/materials")

_BUNDLE_TYP = "camwosa.material_bundle"


@bp.get("/")
def liste():
    return jsonify([m.model_dump(mode="json") for m in lade_materialien()])


@bp.get("/<material_id>")
def details(material_id: str):
    for m in lade_materialien():
        if m.id == material_id:
            return jsonify(m.model_dump(mode="json"))
    return jsonify({"fehler": "Material nicht gefunden"}), 404


@bp.get("/<material_id>/export")
def export_material(material_id: str):
    for m in lade_materialien():
        if m.id == material_id:
            return jsonify({
                "schema_version": 1,
                "typ": _BUNDLE_TYP,
                "material": m.model_dump(mode="json"),
            })
    return jsonify({"fehler": "Material nicht gefunden"}), 404


@bp.post("/import")
def import_material_bundle():
    data = request.get_json()
    if data.get("typ") != _BUNDLE_TYP:
        return jsonify({"fehler": "Kein gueltiges material_bundle"}), 422
    try:
        m = Material.model_validate(data["material"])
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    return jsonify({"gueltig": True, "material": m.model_dump(mode="json")})
