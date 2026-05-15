"""API-Endpoint fuer Nesting."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from camwosa.nesting import PlattenDefinition, TeilDefinition, neste

bp = Blueprint("nesting", __name__, url_prefix="/api/nesting")


@bp.post("/run")
def run():
    data = request.get_json()
    teile = [TeilDefinition(**t) for t in data["teile"]]
    platten = [PlattenDefinition(**p) for p in data["platten"]]
    abstand = data.get("abstand_zwischen_teilen", 5.0)
    erg = neste(teile, platten, abstand_zwischen_teilen=abstand)
    return jsonify({
        "platzierungen": [
            {
                "teil_id": p.teil_id,
                "instanz_index": p.instanz_index,
                "platte_id": p.platte_id,
                "x": p.x, "y": p.y,
                "breite": p.breite, "hoehe": p.hoehe,
                "rotation_grad": p.rotation_grad,
            }
            for p in erg.platzierungen
        ],
        "nicht_platziert": [{"teil_id": t, "instanz_index": i}
                            for (t, i) in erg.nicht_platziert],
        "platten_genutzt": erg.platten_genutzt,
        "verschnitt_prozent": erg.verschnitt_prozent,
        "genutzte_flaeche": erg.genutzte_flaeche,
        "gesamt_flaeche": erg.gesamt_flaeche,
    })
