"""API-Endpoints fuer Werkzeuge."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from camwosa.db.crud import loesche_einzel, schreibe_einzel
from camwosa.db.loader import _data_root, lade_werkzeuge
from camwosa.db.models import (
    Werkzeug,
    berechne_v_bit_spitzendurchmesser,
    berechne_v_bit_winkel,
)

_BUNDLE_TYP = "camwosa.tool_bundle"

bp = Blueprint("tools", __name__, url_prefix="/api/tools")


@bp.get("/")
def liste():
    from camwosa.db.werkzeug_name import werkzeug_anzeigename
    out = []
    for t in lade_werkzeuge():
        d = t.model_dump(mode="json")
        d["_anzeigename"] = werkzeug_anzeigename(t)  # D34a: Auto-Name + Zusatz
        out.append(d)
    return jsonify(out)


@bp.post("/anzeigename")
def anzeigename():
    """Live-Vorschau des Auto-Namens beim Anlegen/Editieren (D34a).

    Body: (Teil-)Werkzeug-dict. Liefert { auto_name, anzeigename }.
    """
    from camwosa.db.models import Werkzeug
    from camwosa.db.werkzeug_name import werkzeug_anzeigename, werkzeug_auto_name
    data = request.get_json() or {}
    data.setdefault("id", "_preview")
    data.setdefault("name", "")
    try:
        wz = Werkzeug.model_validate(data)
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    return jsonify({
        "auto_name": werkzeug_auto_name(wz),
        "anzeigename": werkzeug_anzeigename(wz),
    })


@bp.get("/<tool_id>")
def details(tool_id: str):
    for t in lade_werkzeuge():
        if t.id == tool_id:
            return jsonify(t.model_dump(mode="json"))
    return jsonify({"fehler": "Werkzeug nicht gefunden"}), 404


@bp.post("/validate")
def validate():
    try:
        t = Werkzeug.model_validate(request.get_json())
        return jsonify({"gueltig": True, "id": t.id})
    except Exception as e:  # noqa: BLE001
        return jsonify({"gueltig": False, "fehler": str(e)}), 422


@bp.get("/<tool_id>/export")
def export_tool(tool_id: str):
    """Exportiert ein einzelnes Werkzeug als JSON-Bundle."""
    for t in lade_werkzeuge():
        if t.id == tool_id:
            return jsonify({
                "schema_version": 1,
                "typ": _BUNDLE_TYP,
                "werkzeug": t.model_dump(mode="json"),
            })
    return jsonify({"fehler": "Werkzeug nicht gefunden"}), 404


@bp.post("/import")
def import_tool_bundle():
    data = request.get_json()
    if data.get("typ") != _BUNDLE_TYP:
        return jsonify({"fehler": "Kein gueltiges tool_bundle"}), 422
    try:
        t = Werkzeug.model_validate(data["werkzeug"])
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    return jsonify({"gueltig": True, "werkzeug": t.model_dump(mode="json")})


# ---------------------------------------------------------------------------
# CRUD: anlegen, aktualisieren, loeschen — User-Overrides als Einzeldateien
# ---------------------------------------------------------------------------


@bp.post("/")
def anlegen():
    try:
        t = Werkzeug.model_validate(request.get_json() or {})
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    schreibe_einzel(t, _data_root() / "tools")
    return jsonify({"gespeichert": True, "werkzeug": t.model_dump(mode="json")}), 201


@bp.put("/<tool_id>")
def aktualisieren(tool_id: str):
    daten = request.get_json() or {}
    daten["id"] = tool_id
    try:
        t = Werkzeug.model_validate(daten)
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    schreibe_einzel(t, _data_root() / "tools")
    return jsonify({"gespeichert": True, "werkzeug": t.model_dump(mode="json")})


@bp.delete("/<tool_id>")
def loeschen(tool_id: str):
    if loesche_einzel(_data_root() / "tools", tool_id):
        return jsonify({"geloescht": True, "id": tool_id})
    return jsonify({
        "fehler": "Werkzeug kommt aus Sammel-Datei (Default) und kann nicht "
                  "geloescht werden. Lege stattdessen eine User-Override mit "
                  "gleicher ID an um die Defaults zu uebersteuern.",
    }), 409


# ---------------------------------------------------------------------------
# Smart-Helpers fuer den UI-Werkzeug-Editor
# ---------------------------------------------------------------------------


@bp.post("/helper/v-bit-spitzendurchmesser")
def helper_spitzendurchmesser():
    """Body: ``{ spitzenwinkel_grad, schneidlaenge_mm, durchmesser_max_mm }``."""
    d = request.get_json() or {}
    try:
        result = berechne_v_bit_spitzendurchmesser(
            float(d["spitzenwinkel_grad"]),
            float(d["schneidlaenge_mm"]),
            float(d["durchmesser_max_mm"]),
        )
    except (KeyError, ValueError, TypeError) as e:
        return jsonify({"fehler": f"Eingaben ungueltig: {e}"}), 422
    return jsonify({"spitzendurchmesser_mm": result})


@bp.post("/helper/v-bit-winkel")
def helper_winkel():
    """Body: ``{ spitzendurchmesser_mm, durchmesser_max_mm, schneidlaenge_mm }``."""
    d = request.get_json() or {}
    try:
        result = berechne_v_bit_winkel(
            float(d["spitzendurchmesser_mm"]),
            float(d["durchmesser_max_mm"]),
            float(d["schneidlaenge_mm"]),
        )
    except (KeyError, ValueError, TypeError) as e:
        return jsonify({"fehler": f"Eingaben ungueltig: {e}"}), 422
    return jsonify({"spitzenwinkel_grad": result})
