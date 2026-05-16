"""API-Endpoints fuer Rotary-Profile + Rohmaterial-Setup."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from camwosa.db.loader import lade_rotary_profile
from camwosa.db.rotary import RotaryProfil, RotaryRohmaterial

bp = Blueprint("rotary", __name__, url_prefix="/api/rotary")


@bp.get("/profile")
def liste_profile():
    return jsonify([p.model_dump(mode="json") for p in lade_rotary_profile()])


@bp.get("/profile/<profil_id>")
def details(profil_id: str):
    for p in lade_rotary_profile():
        if p.id == profil_id:
            return jsonify(p.model_dump(mode="json"))
    return jsonify({"fehler": "Rotary-Profil nicht gefunden"}), 404


@bp.post("/profile/validate")
def validate_profil():
    try:
        p = RotaryProfil.model_validate(request.get_json())
        return jsonify({"gueltig": True, "id": p.id})
    except Exception as e:  # noqa: BLE001
        return jsonify({"gueltig": False, "fehler": str(e)}), 422


@bp.post("/rohmaterial/validate")
def validate_rohmaterial():
    try:
        rm = RotaryRohmaterial.model_validate(request.get_json())
        return jsonify({
            "gueltig": True,
            "effektiver_radius_mm": rm.effektiver_radius(),
        })
    except Exception as e:  # noqa: BLE001
        return jsonify({"gueltig": False, "fehler": str(e)}), 422


_BUNDLE_TYP = "camwosa.rotary_bundle"


@bp.get("/profile/<profil_id>/export")
def export_profil(profil_id: str):
    for p in lade_rotary_profile():
        if p.id == profil_id:
            return jsonify({
                "schema_version": 1,
                "typ": _BUNDLE_TYP,
                "rotary_profil": p.model_dump(mode="json"),
            })
    return jsonify({"fehler": "Rotary-Profil nicht gefunden"}), 404


@bp.post("/profile/import")
def import_profil():
    data = request.get_json()
    if data.get("typ") != _BUNDLE_TYP:
        return jsonify({"fehler": "Kein gueltiges rotary_bundle"}), 422
    try:
        p = RotaryProfil.model_validate(data["rotary_profil"])
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    return jsonify({"gueltig": True, "rotary_profil": p.model_dump(mode="json")})
