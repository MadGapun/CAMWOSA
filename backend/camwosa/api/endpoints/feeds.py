"""API-Endpoint fuer Feeds & Speeds Rechner."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from camwosa.db.loader import lade_maschinen, lade_materialien, lade_werkzeuge
from camwosa.feeds import berechne_feeds_speeds

bp = Blueprint("feeds", __name__, url_prefix="/api/feeds")


@bp.post("/berechnen")
def berechnen():
    data = request.get_json()
    maschine_id = data["maschine_id"]
    werkzeug_id = data["werkzeug_id"]
    material_id = data["material_id"]
    rpm_wunsch = data.get("rpm_wunsch")

    maschinen = {m.id: m for m in lade_maschinen()}
    werkzeuge = {t.id: t for t in lade_werkzeuge()}
    materialien = {m.id: m for m in lade_materialien()}

    fehler = []
    for typ, key, lookup in (
        ("Maschine", maschine_id, maschinen),
        ("Werkzeug", werkzeug_id, werkzeuge),
        ("Material", material_id, materialien),
    ):
        if key not in lookup:
            fehler.append(f"{typ} '{key}' nicht gefunden")
    if fehler:
        return jsonify({"fehler": "; ".join(fehler)}), 404

    erg = berechne_feeds_speeds(
        maschinen[maschine_id],
        werkzeuge[werkzeug_id],
        materialien[material_id],
        rpm_wunsch=rpm_wunsch,
    )
    return jsonify({
        "rpm": erg.rpm,
        "vorschub": erg.vorschub,
        "eintauch_vorschub": erg.eintauch_vorschub,
        "stepdown": erg.stepdown,
        "stepover_prozent": erg.stepover_prozent,
        "schnittgeschwindigkeit_vc": erg.schnittgeschwindigkeit_vc,
        "spanvolumen_q": erg.spanvolumen_q,
        "quelle": erg.quelle,
        "warnungen": [
            {"stufe": w.stufe.value, "text": w.text} for w in erg.warnungen
        ],
    })
