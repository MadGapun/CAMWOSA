"""API-Endpoints fuer Werkzeug-Standzeit-Tracking."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from camwosa.db.loader import lade_werkzeuge
from camwosa.db.standzeit import (
    addiere_minuten,
    lade_standzeit,
    reset_werkzeug,
    status_fuer,
)

bp = Blueprint("standzeit", __name__, url_prefix="/api/standzeit")


@bp.get("/")
def liste():
    """Liefert pro Werkzeug aktuellen Status (genutzt, max, prozent, warnung)."""
    daten = lade_standzeit()
    werkzeuge = lade_werkzeuge()
    out = []
    for w in werkzeuge:
        s = status_fuer(w, daten)
        out.append({
            "werkzeug_id": s.werkzeug_id,
            "name": w.name,
            "genutzt_minuten": s.genutzt_minuten,
            "max_minuten": s.max_minuten,
            "prozent": s.prozent,
            "warnung": s.warnung,
            "kritisch": s.kritisch,
        })
    return jsonify(out)


@bp.post("/addiere")
def addiere():
    data = request.get_json()
    werkzeug_id = data["werkzeug_id"]
    minuten = float(data["minuten"])
    addiere_minuten(werkzeug_id, minuten)
    return jsonify({"ok": True})


@bp.post("/reset/<werkzeug_id>")
def reset(werkzeug_id: str):
    reset_werkzeug(werkzeug_id)
    return jsonify({"ok": True})
