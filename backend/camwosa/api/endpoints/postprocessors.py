"""API-Endpoint zum Auflisten verfuegbarer Postprozessoren."""

from __future__ import annotations

from flask import Blueprint, jsonify

from camwosa.postprocessor import registry

bp = Blueprint("postprocessors", __name__, url_prefix="/api/postprocessors")


@bp.get("/")
def liste():
    ids = registry().list_ids()
    out = []
    for pid in ids:
        klasse = registry().get(pid)
        out.append({
            "id": pid,
            "name": klasse.name,
            "beschreibung": klasse.beschreibung,
            "file_extension": klasse.file_extension,
        })
    return jsonify(out)
