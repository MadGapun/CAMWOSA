"""API-Endpoints fuer Multi-Setup-Workflow.

Stellt Sicherheits-Pruefung der Workflow-Konfiguration und PDF-/MD-Generierung
fuer den Arbeitsplan bereit. Weitere Setup-Persistenz ist Sache des
Projekt-Endpoints (.cwp).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file

from camwosa.db.loader import lade_maschinen
from camwosa.project.schema import Variante
from camwosa.workflow import (
    erzeuge_arbeitsplan_markdown,
    erzeuge_arbeitsplan_pdf,
    pruefe_workflow,
)

bp = Blueprint("workflow", __name__, url_prefix="/api/workflow")


@bp.post("/pruefen")
def pruefen():
    data = request.get_json()
    variante = Variante.model_validate(data["variante"])
    bericht = pruefe_workflow(variante)
    return jsonify({
        "hat_blocker": bericht.hat_blocker,
        "probleme": [
            {"setup_id": p.setup_id, "stufe": p.stufe, "text": p.text}
            for p in bericht.probleme
        ],
    })


@bp.post("/arbeitsplan")
def arbeitsplan():
    """Liefert den Arbeitsplan als Markdown ODER als PDF (?format=pdf)."""
    data = request.get_json()
    variante = Variante.model_validate(data["variante"])
    projekt_name = data.get("projekt_name", "Unbenannt")
    maschine_id = data.get("maschine_id")
    maschinen = {m.id: m for m in lade_maschinen()}
    if maschine_id not in maschinen:
        return jsonify({"fehler": f"Maschine {maschine_id} unbekannt"}), 404
    maschine = maschinen[maschine_id]
    fmt = (data.get("format") or "markdown").lower()
    if fmt == "pdf":
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            pfad = Path(f.name)
        erzeuge_arbeitsplan_pdf(variante, projekt_name, maschine, ziel_pfad=pfad)
        return send_file(pfad, mimetype="application/pdf",
                         as_attachment=True,
                         download_name=f"arbeitsplan_{projekt_name}.pdf")
    md = erzeuge_arbeitsplan_markdown(variante, projekt_name, maschine)
    return jsonify({"markdown": md})
