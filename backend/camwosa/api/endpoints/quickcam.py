"""API-Endpoints fuer Quick-CAM-Templates.

Schneller Weg vom Programmstart zum lauffaehigen G-Code: Template waehlen,
Maße eingeben, fertig.
"""

from __future__ import annotations

from dataclasses import asdict

from flask import Blueprint, jsonify, request

from camwosa.db.loader import lade_maschinen, lade_materialien, lade_werkzeuge
from camwosa.quickcam import erzeuge_aus_template, template_index, templates

bp = Blueprint("quickcam", __name__, url_prefix="/api/quickcam")


@bp.get("/templates")
def liste_templates():
    out = []
    for t in templates():
        out.append({
            "id": t.id,
            "name": t.name,
            "kurzbeschreibung": t.kurzbeschreibung,
            "icon": t.icon,
            "operation_typ": t.operation_typ,
            "parameter": [asdict(p) for p in t.parameter],
        })
    return jsonify(out)


@bp.get("/templates/<template_id>")
def template_details(template_id: str):
    t = template_index().get(template_id)
    if t is None:
        return jsonify({"fehler": "Template nicht gefunden"}), 404
    return jsonify({
        "id": t.id,
        "name": t.name,
        "kurzbeschreibung": t.kurzbeschreibung,
        "icon": t.icon,
        "operation_typ": t.operation_typ,
        "parameter": [asdict(p) for p in t.parameter],
    })


@bp.post("/erzeugen")
def erzeugen():
    """Body: ``{ template_id, eingaben, maschine_id, werkzeug_id, material_id, projekt_name? }``."""
    d = request.get_json() or {}
    try:
        template_id = d["template_id"]
        eingaben = d.get("eingaben", {})
        maschine_id = d["maschine_id"]
        werkzeug_id = d["werkzeug_id"]
        material_id = d["material_id"]
    except KeyError as k:
        return jsonify({"fehler": f"Pflichtfeld fehlt: {k}"}), 422

    maschinen = {m.id: m for m in lade_maschinen()}
    werkzeuge = {w.id: w for w in lade_werkzeuge()}
    materialien = {m.id: m for m in lade_materialien()}

    if maschine_id not in maschinen:
        return jsonify({"fehler": f"Maschine '{maschine_id}' unbekannt"}), 422
    if werkzeug_id not in werkzeuge:
        return jsonify({"fehler": f"Werkzeug '{werkzeug_id}' unbekannt"}), 422
    if material_id not in materialien:
        return jsonify({"fehler": f"Material '{material_id}' unbekannt"}), 422

    try:
        projekt = erzeuge_aus_template(
            template_id, eingaben,
            maschine=maschinen[maschine_id],
            werkzeug=werkzeuge[werkzeug_id],
            material=materialien[material_id],
            projekt_name=d.get("projekt_name", "QuickCAM-Projekt"),
        )
    except KeyError as e:
        return jsonify({"fehler": str(e)}), 404
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422

    return jsonify({"projekt": projekt.model_dump(mode="json")})
