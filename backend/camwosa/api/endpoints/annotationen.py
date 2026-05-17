"""API-Endpoints fuer Geometrie-Annotationen (Anschlagbohrungen, Refpunkte).

Annotationen leben pro GeometrieSnapshot. Der Endpoint validiert nur die
einzelnen Annotation-Eintraege — Persistierung erfolgt im Projekt-IO
(CWP-Container).
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from camwosa.db.loader import lade_werkzeuge
from camwosa.db.models import Werkzeug
from camwosa.project.schema import (
    GeometrieAnnotation,
    GeometrieAnnotationTyp,
)
from camwosa.workflow.annotationen_zu_operationen import annotationen_zu_operationen

bp = Blueprint("annotationen", __name__, url_prefix="/api/annotationen")


@bp.get("/typen")
def typen():
    return jsonify([t.value for t in GeometrieAnnotationTyp])


@bp.post("/validate")
def validiere():
    """Validiert eine einzelne Annotation."""
    try:
        a = GeometrieAnnotation.model_validate(request.get_json() or {})
    except Exception as e:  # noqa: BLE001
        return jsonify({"gueltig": False, "fehler": str(e)}), 422
    return jsonify({"gueltig": True, "annotation": a.model_dump(mode="json")})


@bp.post("/validate-liste")
def validiere_liste():
    """Validiert eine ganze Annotation-Liste auf einmal."""
    daten = request.get_json() or {}
    eintraege = daten.get("annotationen", [])
    if not isinstance(eintraege, list):
        return jsonify({"fehler": "Erwarte Feld 'annotationen' als Liste"}), 422
    ok: list[GeometrieAnnotation] = []
    fehler: list[dict] = []
    ids: set[str] = set()
    for idx, e in enumerate(eintraege):
        try:
            a = GeometrieAnnotation.model_validate(e)
        except Exception as exc:  # noqa: BLE001
            fehler.append({"index": idx, "fehler": str(exc)})
            continue
        if a.id in ids:
            fehler.append({"index": idx, "fehler": f"Doppelte ID '{a.id}'"})
            continue
        ids.add(a.id)
        ok.append(a)
    return jsonify({
        "gueltig": not fehler,
        "annotationen": [a.model_dump(mode="json") for a in ok],
        "fehler": fehler,
    })


@bp.post("/zu-operationen")
def zu_operationen():
    """Wandelt eine Annotation-Liste in CAM-Operationen um.

    Body: ``{ "annotationen": [...], "werkzeug_ids"?: [...] }``

    Wenn ``werkzeug_ids`` weggelassen wird, werden alle verfuegbaren Werkzeuge
    zur Auswahl genommen. Ergebnis enthaelt ``operationen`` + ``hinweise``.
    """
    data = request.get_json() or {}
    eintraege = data.get("annotationen", [])
    werkzeug_ids = data.get("werkzeug_ids")

    annotationen: list[GeometrieAnnotation] = []
    for e in eintraege:
        try:
            annotationen.append(GeometrieAnnotation.model_validate(e))
        except Exception as exc:  # noqa: BLE001
            return jsonify({"fehler": f"Annotation ungueltig: {exc}"}), 422

    werkzeuge: list[Werkzeug] = lade_werkzeuge()
    if werkzeug_ids:
        werkzeuge = [w for w in werkzeuge if w.id in set(werkzeug_ids)]

    erg = annotationen_zu_operationen(annotationen, werkzeuge)
    return jsonify({
        "operationen": [op.model_dump(mode="json") for op in erg.operationen],
        "hinweise": erg.hinweise,
    })
