"""API-Endpoints fuer DXF-Import."""

from __future__ import annotations

import tempfile
from pathlib import Path

from flask import Blueprint, jsonify, request

from camwosa.dxf import DXFFehler, lade_dxf

bp = Blueprint("dxf", __name__, url_prefix="/api/dxf")


@bp.post("/import")
def importieren():
    if "datei" not in request.files:
        return jsonify({"fehler": "Keine DXF-Datei"}), 400
    f = request.files["datei"]
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
        f.save(tmp.name)
        pfad = Path(tmp.name)
    try:
        dok = lade_dxf(pfad)
    except DXFFehler as e:
        return jsonify({"fehler": str(e)}), 422

    return jsonify({
        "einheit": dok.einheit,
        "layer": dok.layer,
        "anzahl_objekte": len(dok.objekte),
        "bounding_box": (
            {"min": (dok.bounding_box[0].x, dok.bounding_box[0].y),
             "max": (dok.bounding_box[1].x, dok.bounding_box[1].y)}
            if dok.bounding_box else None
        ),
        "objekte": [
            {
                "typ": o.typ.value,
                "layer": o.layer,
                "geschlossen": o.geschlossen,
                "punkte": [(p.x, p.y) for p in o.punkte],
                "attribute": o.attribute,
            }
            for o in dok.objekte
        ],
    })
