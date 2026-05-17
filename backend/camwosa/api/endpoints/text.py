"""API-Endpoint fuer Text-zu-Pfad (Master-Plan A37)."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from camwosa.cad.text_zu_pfad import (
    FontFehler,
    TextPfadParameter,
    polygone_zu_punktlisten,
    text_bounding_box,
    text_zu_pfade,
)

bp = Blueprint("text", __name__, url_prefix="/api/text")


@bp.post("/zu-pfad")
def zu_pfad():
    """Konvertiert Text in 2D-Polygone (mit Loechern als Inseln).

    JSON-Body:
    ```
    {
      "text": "MADGAPUN",
      "hoehe_mm": 10.0,
      "font_pfad": null,            // None -> System-Default-Font
      "zeichen_abstand_extra_mm": 0,
      "zeilen_abstand_faktor": 1.2,
      "kurven_aufloesung": 12
    }
    ```

    Antwort:
    ```
    {
      "polygone": [
        {
          "exterior": [[x, y], ...],
          "loecher": [[[x, y], ...], ...]
        }, ...
      ],
      "bounding_box": [x_min, y_min, x_max, y_max],
      "anzahl_polygone": N
    }
    ```
    """
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", ""))
    if not text:
        return jsonify({"fehler": "text erforderlich"}), 400

    parameter = TextPfadParameter(
        hoehe_mm=float(payload.get("hoehe_mm", 10.0)),
        font_pfad=payload.get("font_pfad"),
        zeichen_abstand_extra_mm=float(
            payload.get("zeichen_abstand_extra_mm", 0.0)),
        zeilen_abstand_faktor=float(payload.get("zeilen_abstand_faktor", 1.2)),
        kurven_aufloesung=int(payload.get("kurven_aufloesung", 12)),
    )

    try:
        polygone = text_zu_pfade(text, parameter)
    except FontFehler as e:
        return jsonify({"fehler": str(e)}), 422
    except ValueError as e:
        return jsonify({"fehler": str(e)}), 422

    poly_json = [
        {
            "exterior": [list(coord) for coord in p.exterior.coords],
            "loecher": [
                [list(coord) for coord in innen.coords]
                for innen in p.interiors
            ],
        }
        for p in polygone
    ]
    bbox = text_bounding_box(text, parameter)
    return jsonify({
        "polygone": poly_json,
        "bounding_box": list(bbox),
        "anzahl_polygone": len(polygone),
    })


@bp.post("/zu-pfad/punktlisten")
def zu_pfad_punktlisten():
    """Wie /zu-pfad, gibt aber eine flache Punktlisten-Liste zurueck.

    Aussenkonturen + Loecher werden als getrennte Listen geliefert — direkt
    nutzbar fuer cam.kontur und cam.wrap.
    """
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", ""))
    if not text:
        return jsonify({"fehler": "text erforderlich"}), 400

    parameter = TextPfadParameter(
        hoehe_mm=float(payload.get("hoehe_mm", 10.0)),
        font_pfad=payload.get("font_pfad"),
        zeichen_abstand_extra_mm=float(
            payload.get("zeichen_abstand_extra_mm", 0.0)),
        zeilen_abstand_faktor=float(payload.get("zeilen_abstand_faktor", 1.2)),
        kurven_aufloesung=int(payload.get("kurven_aufloesung", 12)),
    )
    try:
        polygone = text_zu_pfade(text, parameter)
    except FontFehler as e:
        return jsonify({"fehler": str(e)}), 422
    punktlisten = polygone_zu_punktlisten(polygone)
    bbox = text_bounding_box(text, parameter)
    return jsonify({
        "punktlisten": [[list(p) for p in liste] for liste in punktlisten],
        "bounding_box": list(bbox),
    })
