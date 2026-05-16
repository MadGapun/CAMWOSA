"""API-Endpoints fuer CAD-Import (alle Formate via Registry)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from flask import Blueprint, jsonify, request

from camwosa.cad import CADImportFehler, lade_cad, registry

bp = Blueprint("cad", __name__, url_prefix="/api/cad")


@bp.get("/formate")
def formate():
    """Liste aller registrierten CAD-Importer + ihrer Extensions."""
    out = []
    for fid in registry().list_ids():
        klasse = registry().get(fid)
        out.append({
            "id": fid,
            "name": klasse.name,
            "extensions": list(klasse.extensions),
            "beschreibung": klasse.beschreibung,
        })
    return jsonify(out)


@bp.post("/import")
def importieren():
    """Importiert eine CAD-Datei beliebigen Formats."""
    if "datei" not in request.files:
        return jsonify({"fehler": "Keine Datei"}), 400
    f = request.files["datei"]
    suffix = Path(f.filename or "").suffix or ".bin"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        f.save(tmp.name)
        pfad = Path(tmp.name)
    try:
        erg = lade_cad(pfad)
    except CADImportFehler as e:
        return jsonify({"fehler": str(e)}), 422

    return jsonify({
        "format_id": erg.format_id,
        "einheit": erg.einheit,
        "layer": erg.layer,
        "anzahl_objekte": len(erg.objekte),
        "bounding_box": (
            {"min": (erg.bounding_box[0].x, erg.bounding_box[0].y),
             "max": (erg.bounding_box[1].x, erg.bounding_box[1].y)}
            if erg.bounding_box else None
        ),
        "objekte": [
            {
                "typ": o.typ.value,
                "layer": o.layer,
                "geschlossen": o.geschlossen,
                "punkte": [(p.x, p.y) for p in o.punkte],
                "attribute": o.attribute,
            }
            for o in erg.objekte
        ],
        "metadaten": erg.metadaten,
    })
