"""API-Endpoints fuer CuttingPresets (separate Top-Level-Entitaet)."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from camwosa.db.cutting_presets import (
    CuttingPreset,
    OperationsTyp,
    finde_preset,
    lade_cutting_presets,
    speichere_cutting_preset,
)

bp = Blueprint("cutting_presets", __name__, url_prefix="/api/cutting-presets")

_BUNDLE_TYP = "camwosa.cutting_preset_bundle"


@bp.get("/")
def liste():
    """Alle Presets (mit Filtern: material_id, werkzeug_id, operation_typ)."""
    material_id = request.args.get("material_id")
    werkzeug_id = request.args.get("werkzeug_id")
    op = request.args.get("operation_typ")
    presets = lade_cutting_presets()
    if material_id:
        presets = [p for p in presets if p.material_id == material_id]
    if werkzeug_id:
        presets = [p for p in presets if p.werkzeug_id == werkzeug_id]
    if op:
        try:
            op_enum = OperationsTyp(op)
        except ValueError:
            return jsonify({"fehler": f"Unbekannter operation_typ '{op}'"}), 422
        presets = [p for p in presets if p.operation_typ == op_enum]
    return jsonify([p.model_dump(mode="json") for p in presets])


@bp.get("/<preset_id>")
def details(preset_id: str):
    for p in lade_cutting_presets():
        if p.id == preset_id:
            return jsonify(p.model_dump(mode="json"))
    return jsonify({"fehler": "Preset nicht gefunden"}), 404


@bp.post("/lookup")
def lookup():
    """Sucht das beste Preset fuer eine (material, werkzeug, operation)-Kombi.

    Body: {"material_id": ..., "werkzeug_id": ..., "operation_typ": "schruppen"}
    """
    data = request.get_json() or {}
    material_id = data.get("material_id")
    werkzeug_id = data.get("werkzeug_id")
    op = data.get("operation_typ", "generic")
    if not material_id or not werkzeug_id:
        return jsonify({"fehler": "material_id und werkzeug_id sind Pflicht"}), 422
    try:
        op_enum = OperationsTyp(op)
    except ValueError:
        return jsonify({"fehler": f"Unbekannter operation_typ '{op}'"}), 422
    treffer = finde_preset(
        lade_cutting_presets(),
        material_id=material_id, werkzeug_id=werkzeug_id, operation_typ=op_enum,
    )
    if treffer is None:
        return jsonify({"gefunden": False}), 404
    return jsonify({"gefunden": True, "preset": treffer.model_dump(mode="json")})


@bp.post("/")
def anlegen():
    """Neues Preset anlegen (oder updaten via gleicher ID)."""
    try:
        p = CuttingPreset.model_validate(request.get_json() or {})
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    speichere_cutting_preset(p)
    return jsonify({"gespeichert": True, "preset": p.model_dump(mode="json")}), 201


@bp.put("/<preset_id>")
def aktualisieren(preset_id: str):
    daten = request.get_json() or {}
    daten["id"] = preset_id  # ID aus URL gewinnt
    try:
        p = CuttingPreset.model_validate(daten)
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    speichere_cutting_preset(p)
    return jsonify({"gespeichert": True, "preset": p.model_dump(mode="json")})


@bp.delete("/<preset_id>")
def loeschen(preset_id: str):
    from camwosa.db.loader import _data_root

    pfad = _data_root() / "cutting_presets" / f"{preset_id}.json"
    if not pfad.exists():
        return jsonify({"fehler": "Preset-Datei nicht gefunden (evtl. Legacy?)"}), 404
    pfad.unlink()
    return jsonify({"geloescht": True, "id": preset_id})


@bp.get("/<preset_id>/export")
def export_preset(preset_id: str):
    for p in lade_cutting_presets():
        if p.id == preset_id:
            return jsonify({
                "schema_version": 1,
                "typ": _BUNDLE_TYP,
                "preset": p.model_dump(mode="json"),
            })
    return jsonify({"fehler": "Preset nicht gefunden"}), 404


@bp.post("/import")
def import_preset_bundle():
    data = request.get_json() or {}
    if data.get("typ") != _BUNDLE_TYP:
        return jsonify({"fehler": "Kein gueltiges cutting_preset_bundle"}), 422
    try:
        p = CuttingPreset.model_validate(data["preset"])
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    return jsonify({"gueltig": True, "preset": p.model_dump(mode="json")})
