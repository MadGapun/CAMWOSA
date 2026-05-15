"""API-Endpoints fuer .cwp-Projekte."""

from __future__ import annotations

import tempfile
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file

from camwosa.db.loader import lade_maschinen
from camwosa.db.models import Rohmaterial
from camwosa.project import (
    CWPFehler,
    lade_cwp,
    neues_projekt,
    speichere_cwp,
)

bp = Blueprint("projects", __name__, url_prefix="/api/projects")


@bp.post("/new")
def neu():
    """Erzeugt ein neues, leeres Projekt und gibt das JSON zurueck."""
    data = request.get_json()
    name = data.get("name", "Unbenanntes Projekt")
    maschine_id = data.get("maschine_id")
    maschinen = {m.id: m for m in lade_maschinen()}
    if maschine_id not in maschinen:
        return jsonify({"fehler": f"Maschine {maschine_id} nicht gefunden"}), 404
    rohmaterial = Rohmaterial.model_validate(data.get("rohmaterial", {}))
    projekt = neues_projekt(name, maschinen[maschine_id], rohmaterial,
                            autor=data.get("autor", ""))
    return jsonify(projekt.model_dump(mode="json"))


@bp.post("/save")
def speichern():
    """Speichert ein Projekt als .cwp und gibt die Datei zurueck."""
    daten = request.get_json()
    from camwosa.project.schema import CWPProjekt
    projekt = CWPProjekt.model_validate(daten)
    with tempfile.NamedTemporaryFile(suffix=".cwp", delete=False) as f:
        pfad = Path(f.name)
    speichere_cwp(projekt, pfad)
    return send_file(pfad, mimetype="application/zip", as_attachment=True,
                     download_name=f"{projekt.metadaten.name}.cwp")


@bp.post("/load")
def laden():
    """Laedt ein hochgeladenes .cwp-File."""
    if "datei" not in request.files:
        return jsonify({"fehler": "Keine Datei uebergeben"}), 400
    f = request.files["datei"]
    with tempfile.NamedTemporaryFile(suffix=".cwp", delete=False) as tmp:
        f.save(tmp.name)
        tmp_pfad = Path(tmp.name)
    try:
        projekt = lade_cwp(tmp_pfad)
        return jsonify(projekt.model_dump(mode="json"))
    except CWPFehler as e:
        return jsonify({"fehler": str(e)}), 422
