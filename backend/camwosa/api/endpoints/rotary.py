"""API-Endpoints fuer Rotary-Profile + Rohmaterial-Setup."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from camwosa.db.crud import loesche_einzel, schreibe_einzel
from camwosa.db.loader import _data_root, lade_rotary_profile
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


# ---------------------------------------------------------------------------
# CRUD: Rotary-Profile als User-Override-Einzeldateien (data/rotary/<id>.json)
# ---------------------------------------------------------------------------


@bp.post("/profile")
def anlegen():
    try:
        p = RotaryProfil.model_validate(request.get_json() or {})
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    schreibe_einzel(p, _data_root() / "rotary")
    return jsonify({"gespeichert": True, "rotary_profil": p.model_dump(mode="json")}), 201


@bp.put("/profile/<profil_id>")
def aktualisieren(profil_id: str):
    daten = request.get_json() or {}
    daten["id"] = profil_id
    try:
        p = RotaryProfil.model_validate(daten)
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    schreibe_einzel(p, _data_root() / "rotary")
    return jsonify({"gespeichert": True, "rotary_profil": p.model_dump(mode="json")})


@bp.delete("/profile/<profil_id>")
def loeschen(profil_id: str):
    if loesche_einzel(_data_root() / "rotary", profil_id):
        return jsonify({"geloescht": True, "id": profil_id})
    return jsonify({
        "fehler": "Rotary-Profil kommt aus Sammel-Datei (Default) und kann nicht "
                  "geloescht werden. Lege stattdessen eine User-Override mit "
                  "gleicher ID an um die Defaults zu uebersteuern.",
    }), 409
