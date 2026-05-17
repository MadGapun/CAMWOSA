"""API-Endpoints fuer Wrap-Mode: Pattern-Skalierung + Toolpath-Erzeugung.

Master-Plan A32 (Wrap-Basis) + A38 (Pattern-Skalierung + DXF-Integration).
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from camwosa.cam.wrap import (
    PatternSkalierungsModus,
    WrapParameter,
    erzeuge_wrap_toolpath,
    pruefe_design_fuer_radius,
    skaliere_pattern_fuer_werkstueck,
)
from camwosa.db.loader import lade_werkzeuge

bp = Blueprint("wrap", __name__, url_prefix="/api/wrap")


@bp.post("/pattern-skalieren")
def pattern_skalieren():
    """Skaliert ein 2D-Pattern fuer den Wrap-Mode.

    JSON-Body:
    ```
    {
      "polygone": [[[x, y], ...], ...],
      "modus": "auf_werkstueck_anpassen" | "feste_skalierung" | "wiederholen",
      "werkstueck_radius_mm": 20.0,
      "soll_breite_mm": null,   // X-Spanne (optional)
      "soll_hoehe_mm": null,    // Y-Spanne (optional, nur feste_skalierung)
      "aspekt_erhalten": true
    }
    ```

    Antwort: ``{"polygone": [...], "metadaten": {...}, "warnungen": [...]}``.
    """
    payload = request.get_json(silent=True) or {}
    polygone_roh = payload.get("polygone")
    if not isinstance(polygone_roh, list):
        return jsonify({"fehler": "polygone (Liste von Punktlisten) erforderlich"}), 400
    polygone: list[list[tuple[float, float]]] = []
    for poly in polygone_roh:
        if not isinstance(poly, list):
            continue
        pl = [(float(p[0]), float(p[1])) for p in poly if len(p) >= 2]
        if len(pl) >= 2:
            polygone.append(pl)

    modus_str = str(payload.get("modus", "auf_werkstueck_anpassen")).lower()
    try:
        modus = PatternSkalierungsModus(modus_str)
    except ValueError:
        return jsonify(
            {"fehler": f"modus muss feste_skalierung/auf_werkstueck_anpassen/"
                       f"wiederholen sein (war {modus_str})"}
        ), 400

    try:
        ergebnis, meta = skaliere_pattern_fuer_werkstueck(
            polygone, modus,
            werkstueck_radius_mm=float(payload.get("werkstueck_radius_mm", 20.0)),
            soll_breite_mm=(float(payload["soll_breite_mm"])
                            if payload.get("soll_breite_mm") not in (None, "")
                            else None),
            soll_hoehe_mm=(float(payload["soll_hoehe_mm"])
                           if payload.get("soll_hoehe_mm") not in (None, "")
                           else None),
            aspekt_erhalten=bool(payload.get("aspekt_erhalten", True)),
        )
    except ValueError as e:
        return jsonify({"fehler": str(e)}), 422

    # Warnungen: alle Pfade zusammen pruefen
    alle_punkte = [pkt for poly in ergebnis for pkt in poly]
    warnungen = pruefe_design_fuer_radius(
        alle_punkte, float(payload.get("werkstueck_radius_mm", 20.0)),
    )

    return jsonify({
        "polygone": [[list(p) for p in poly] for poly in ergebnis],
        "metadaten": meta,
        "warnungen": warnungen,
        "ist_ok": len(warnungen) == 0,
    })


@bp.post("/toolpath")
def toolpath():
    """Erzeugt einen Wrap-Toolpath aus skalierten Polygonen.

    Erlaubt mehrere Polygone (z.B. mehrere Buchstaben aus Text-zu-Pfad oder
    mehrere Kontur-Loops aus DXF). Toolpath wird **pro Polygon** sequenziell
    erzeugt — Werkzeug springt zwischen den Polygonen auf Sicherheitshoehe.

    JSON-Body:
    ```
    {
      "polygone": [[[x, y], ...], ...],
      "werkzeug_id": "vbit_60grad",
      "spindel_rpm": 18000, "vorschub": 600, "eintauch_vorschub": 200,
      "werkstueck_radius_mm": 20.0,
      "max_tiefe": 0.5, "stepdown": 0.5,
      "sicherheitshoehe": 5.0,
      "geschlossen": false
    }
    ```
    """
    payload = request.get_json(silent=True) or {}
    polygone_roh = payload.get("polygone")
    if not isinstance(polygone_roh, list) or not polygone_roh:
        return jsonify({"fehler": "polygone erforderlich"}), 400

    werkzeug_id = payload.get("werkzeug_id")
    werkzeuge = {w.id: w for w in lade_werkzeuge()}
    if werkzeug_id not in werkzeuge:
        return jsonify({"fehler": f"Werkzeug '{werkzeug_id}' nicht gefunden"}), 404

    parameter = WrapParameter(
        werkzeug_id=werkzeug_id,
        spindel_rpm=float(payload.get("spindel_rpm", 18000)),
        vorschub=float(payload.get("vorschub", 600)),
        eintauch_vorschub=float(payload.get("eintauch_vorschub", 200)),
        sicherheitshoehe=float(payload.get("sicherheitshoehe", 5.0)),
        werkstueck_radius_mm=float(payload.get("werkstueck_radius_mm", 20.0)),
        max_tiefe=float(payload.get("max_tiefe", 0.5)),
        stepdown=float(payload.get("stepdown", 0.5)),
        geschlossen=bool(payload.get("geschlossen", False)),
    )

    alle_bewegungen = []
    fehler = []
    for idx, poly_roh in enumerate(polygone_roh):
        punkte = [(float(p[0]), float(p[1])) for p in poly_roh if len(p) >= 2]
        if len(punkte) < 2:
            continue
        try:
            tp = erzeuge_wrap_toolpath(
                punkte, werkzeuge[werkzeug_id], parameter,
                operation_id=f"wrap_{idx}",
            )
            alle_bewegungen.extend(tp.bewegungen)
        except ValueError as e:
            fehler.append(f"Polygon {idx}: {e}")
    if not alle_bewegungen:
        return jsonify({"fehler": "Kein gueltiger Toolpath erzeugbar", "details": fehler}), 422

    return jsonify({
        "bewegungen": [
            {"typ": b.typ.value, "x": b.x, "y": b.y, "z": b.z,
             "feed": b.feed, "kommentar": b.kommentar}
            for b in alle_bewegungen
        ],
        "anzahl_polygone": len(polygone_roh),
        "fehler_pro_polygon": fehler,
        "metadaten": {
            "werkstueck_radius_mm": parameter.werkstueck_radius_mm,
            "umfang_mm": 2 * 3.14159265 * parameter.werkstueck_radius_mm,
        },
    })
