"""API-Endpoint fuer Sicherheits-Checks."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from camwosa.api.endpoints.operations import _deserialize_toolpath
from camwosa.db.loader import lade_maschinen, lade_werkzeuge
from camwosa.safety import pruefe_toolpath

bp = Blueprint("safety", __name__, url_prefix="/api/safety")


@bp.post("/check")
def check():
    data = request.get_json()
    maschinen = {m.id: m for m in lade_maschinen()}
    werkzeuge = {t.id: t for t in lade_werkzeuge()}
    maschine = maschinen[data["maschine_id"]]
    werkzeug = werkzeuge[data["werkzeug_id"]]
    toolpath = _deserialize_toolpath(data["toolpath"])
    z_oben = data.get("z_oberkante_material", 0.0)
    bericht = pruefe_toolpath(toolpath, maschine, werkzeug,
                              z_oberkante_material=z_oben)
    return jsonify({
        "hat_blocker": bericht.hat_blocker,
        "anzahl_kritisch": bericht.anzahl_kritisch,
        "anzahl_warnung": bericht.anzahl_warnung,
        "ergebnisse": [
            {
                "check_id": e.check_id,
                "stufe": e.stufe.value,
                "titel": e.titel,
                "beschreibung": e.beschreibung,
                "bewegungs_index": e.bewegungs_index,
            }
            for e in bericht.ergebnisse
        ],
    })
