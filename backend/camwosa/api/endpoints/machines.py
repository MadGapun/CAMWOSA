"""API-Endpoints fuer Maschinen-Profile (inkl. Spindeln + Sharing-Export/Import)."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from camwosa.db.crud import loesche_einzel, schreibe_einzel
from camwosa.db.loader import _data_root, lade_maschinen, spindel_index
from camwosa.db.models import Maschine, Spindel

bp = Blueprint("machines", __name__, url_prefix="/api/machines")


@bp.get("/")
def liste():
    maschinen = lade_maschinen()
    idx = spindel_index()
    out = []
    for m in maschinen:
        data = m.model_dump(mode="json")
        rpm_min, rpm_max = m.effektive_rpm_range(idx)
        data["_effektive_rpm_min"] = rpm_min
        data["_effektive_rpm_max"] = rpm_max
        aktive = m.aktive_spindel(idx)
        data["_aktive_spindel"] = aktive.model_dump(mode="json") if aktive else None
        out.append(data)
    return jsonify(out)


@bp.get("/<machine_id>")
def details(machine_id: str):
    maschinen = lade_maschinen()
    idx = spindel_index()
    for m in maschinen:
        if m.id == machine_id:
            data = m.model_dump(mode="json")
            aktive = m.aktive_spindel(idx)
            data["_aktive_spindel"] = aktive.model_dump(mode="json") if aktive else None
            data["_verfuegbare_spindeln"] = [
                idx[sid].model_dump(mode="json") for sid in m.spindel_ids if sid in idx
            ]
            return jsonify(data)
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


@bp.get("/<machine_id>/export")
def export_bundle(machine_id: str):
    """Exportiert ein Maschinenprofil als gebuendeltes JSON inkl. ihrer Spindeln.

    Format:
        {
          "schema_version": 1,
          "typ": "camwosa.machine_bundle",
          "maschine": {...},
          "spindeln": [{...}, {...}]
        }

    Dieses Bundle ist portabel — andere CAMWOSA-User koennen es importieren und
    bekommen die Maschine + ihre Spindeln in einem Schritt.
    """
    maschinen = lade_maschinen()
    idx = spindel_index()
    m = next((x for x in maschinen if x.id == machine_id), None)
    if m is None:
        return jsonify({"fehler": "Maschine nicht gefunden"}), 404
    spindeln = [idx[sid] for sid in m.spindel_ids if sid in idx]
    return jsonify({
        "schema_version": 1,
        "typ": "camwosa.machine_bundle",
        "maschine": m.model_dump(mode="json"),
        "spindeln": [s.model_dump(mode="json") for s in spindeln],
    })


@bp.post("/import")
def import_bundle():
    """Validiert ein Maschinen-Bundle.

    Body: das Bundle aus /export.
    Response: validierte Maschine + Spindeln oder Fehler.
    Die eigentliche Persistenz erfolgt durch die UI (Datei in
    `data/machines/community/` ablegen).
    """
    data = request.get_json()
    if data.get("typ") != "camwosa.machine_bundle":
        return jsonify({"fehler": "Kein gueltiges machine_bundle"}), 422
    try:
        m = Maschine.model_validate(data["maschine"])
        spindeln = [Spindel.model_validate(s) for s in data.get("spindeln", [])]
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422

    spindel_id_set = {s.id for s in spindeln}
    fehlend = [sid for sid in m.spindel_ids if sid not in spindel_id_set]
    if fehlend:
        return jsonify({
            "fehler": (
                f"Bundle inkonsistent — Maschine referenziert Spindeln die nicht "
                f"im Bundle sind: {fehlend}"
            )
        }), 422

    return jsonify({
        "gueltig": True,
        "maschine": m.model_dump(mode="json"),
        "spindeln": [s.model_dump(mode="json") for s in spindeln],
    })


@bp.post("/")
def anlegen():
    """Legt eine neue Maschine an (Issue #22: First-Run-Wizard inline-Anlegen)."""
    try:
        m = Maschine.model_validate(request.get_json() or {})
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    schreibe_einzel(m, _data_root() / "machines")
    return jsonify({"gespeichert": True, "maschine": m.model_dump(mode="json")}), 201


@bp.put("/<machine_id>")
def aktualisieren(machine_id: str):
    daten = request.get_json() or {}
    daten["id"] = machine_id
    try:
        m = Maschine.model_validate(daten)
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    schreibe_einzel(m, _data_root() / "machines")
    return jsonify({"gespeichert": True, "maschine": m.model_dump(mode="json")})


@bp.delete("/<machine_id>")
def loeschen(machine_id: str):
    if loesche_einzel(_data_root() / "machines", machine_id):
        return jsonify({"geloescht": True, "id": machine_id})
    return jsonify({
        "fehler": "Maschine kommt aus Sammel-Datei (Default). User-Override "
                  "mit gleicher ID anlegen um zu uebersteuern.",
    }), 409
