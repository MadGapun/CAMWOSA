"""API-Endpoints fuer CAD-Import (alle Formate via Registry)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from flask import Blueprint, jsonify, request

from camwosa.cad import CADImportFehler, lade_cad, registry
from camwosa.cad.bitmap_trace import (
    BitmapTraceFehler,
    BitmapTraceParameter,
    trace_bitmap,
)

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


@bp.post("/bitmap-trace")
def bitmap_trace():
    """Bitmap → Vektor-Schneid-Kontur (Cluster L1).

    Body: ``multipart/form-data`` mit:
    - ``datei``: das Bild (PNG, JPG, ...)
    - ``schwelle`` (optional, 0..1, Default 0.5)
    - ``invertieren`` (optional, "true"/"false", Default false)
    - ``pixel_pro_mm`` (optional, Default 4.0)
    - ``ziel_breite_mm`` (optional, Default null = aus Auflösung)
    - ``glaettung_toleranz_mm`` (optional, Default 0.2)
    - ``min_flaeche_mm2`` (optional, Default 1.0)

    Anders als ``/api/heightmap/aus-bild`` (3D-Relief) liefert dies 2D-Vektoren
    zum Ausschneiden/Aushöhlen/Gravieren.
    """
    if "datei" not in request.files:
        return jsonify({"fehler": "Keine Datei"}), 400
    bild_bytes = request.files["datei"].read()

    def _f(name, default):
        v = request.form.get(name)
        return float(v) if v not in (None, "", "null") else default

    def _b(name, default):
        v = request.form.get(name, "").lower()
        if v in ("true", "1", "yes", "ja"):
            return True
        if v in ("false", "0", "no", "nein"):
            return False
        return default

    parameter = BitmapTraceParameter(
        schwelle=_f("schwelle", 0.5),
        invertieren=_b("invertieren", False),
        pixel_pro_mm=_f("pixel_pro_mm", 4.0),
        ziel_breite_mm=_f("ziel_breite_mm", None),
        glaettung_toleranz_mm=_f("glaettung_toleranz_mm", 0.2),
        min_flaeche_mm2=_f("min_flaeche_mm2", 1.0),
    )
    try:
        geos = trace_bitmap(bild_bytes, parameter)
    except BitmapTraceFehler as e:
        return jsonify({"fehler": str(e)}), 422

    return jsonify({
        "anzahl": len(geos),
        "objekte": [
            {
                "typ": o.typ.value,
                "layer": o.layer,
                "geschlossen": o.geschlossen,
                "punkte": [(p.x, p.y) for p in o.punkte],
            }
            for o in geos
        ],
    })
