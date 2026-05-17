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
from camwosa.project.schema import CWPProjekt, Variante
from camwosa.workflow import (
    erzeuge_arbeitsplan_markdown,
    erzeuge_arbeitsplan_pdf,
    pruefe_workflow,
)
from camwosa.workflow.run_lock import darf_gcode_generieren, pruefe_projekt

bp = Blueprint("workflow", __name__, url_prefix="/api/workflow")


@bp.post("/run-lock")
def run_lock():
    """Pre-Check vor G-Code-Generation (Master-Plan A48 Run-Lock).

    Body: ``{\"projekt\": {...komplettes CWPProjekt...}, \"variante_id\": ..., \"setup_id\": ...}``

    Antwort: ``{\"ok\": bool, \"blocker\": [text, ...], \"status_pro_op\": {id: status}}``.
    Wenn ``ok=false``, ist G-Code-Generierung blockiert — Markus' Regel:
    „Im Zweifel laeuft das Programm nicht."
    """
    data = request.get_json() or {}
    if "projekt" not in data:
        return jsonify({"fehler": "projekt erforderlich"}), 400
    try:
        projekt = CWPProjekt.model_validate(data["projekt"])
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": f"projekt ungueltig: {e}"}), 422
    ok, blocker = darf_gcode_generieren(
        projekt,
        variante_id=data.get("variante_id"),
        setup_id=data.get("setup_id"),
    )
    status_map = pruefe_projekt(projekt)
    return jsonify({
        "ok": ok,
        "blocker": blocker,
        "status_pro_op": {
            op_id: {"status": s.value, "fehler": f}
            for op_id, (s, f) in status_map.items()
        },
    })


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
