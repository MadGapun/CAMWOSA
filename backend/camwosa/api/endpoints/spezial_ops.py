"""API-Endpoints fuer Spezial-Operationen aus Cluster E (Issue #39).

- POST /api/spezial-ops/drag-engraving
- POST /api/spezial-ops/auto-inlay
- POST /api/spezial-ops/thread-milling
- POST /api/spezial-ops/circular-pocket-pfade
- POST /api/spezial-ops/radial-pocket-pfade
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from camwosa.cam.auto_inlay import (
    AutoInlayFehler,
    AutoInlayParameter,
    berechne_auto_inlay,
    ergebnis_zu_geometrien,
)
from camwosa.cam.circular_radial import (
    CircularPocketParameter,
    RadialPocketParameter,
    circular_pocket_pfade,
    radial_pocket_pfade,
)
from camwosa.cam.drag_engraving import (
    DragEngravingFehler,
    DragEngravingParameter,
    erzeuge_drag_engraving_toolpath,
)
from camwosa.cam.thread_milling import (
    ThreadMillingFehler,
    ThreadMillingParameter,
    erzeuge_thread_milling_toolpath,
)
from camwosa.cam.planfraesen import (
    PlanfraesFehler,
    PlanfraesParameter,
    erzeuge_planfraes_toolpath,
)
from camwosa.cam.strategie_3d import (
    Strategie3DFehler,
    Strategie3DParameter,
    erzeuge_3d_parallel_toolpath,
)
from camwosa.api.endpoints.operations import _serialize_toolpath
from camwosa.db.loader import lade_werkzeuge
from camwosa.dxf.parser import GeometrieObjekt, GeometrieTyp, Punkt2D
from camwosa.stl.heightmap import Heightmap

bp = Blueprint("spezial_ops", __name__, url_prefix="/api/spezial-ops")


def _werkzeug_oder_404(werkzeug_id: str):
    werkzeuge = {w.id: w for w in lade_werkzeuge()}
    if werkzeug_id not in werkzeuge:
        return None, (jsonify({"fehler": f"Werkzeug {werkzeug_id} unbekannt"}), 404)
    return werkzeuge[werkzeug_id], None


def _parse_geometrie(daten: dict) -> GeometrieObjekt:
    return GeometrieObjekt(
        typ=GeometrieTyp(daten["typ"]),
        layer=daten.get("layer", "0"),
        punkte=[Punkt2D(p[0], p[1]) for p in daten["punkte"]],
        geschlossen=daten.get("geschlossen", False),
        attribute=daten.get("attribute", {}),
    )


@bp.post("/drag-engraving")
def drag_engraving():
    data = request.get_json() or {}
    try:
        parameter = DragEngravingParameter.model_validate(data["parameter"])
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    werkzeug, fehler = _werkzeug_oder_404(parameter.werkzeug_id)
    if fehler:
        return fehler

    geo_daten = data.get("geometrie")
    if isinstance(geo_daten, list):
        geos = [_parse_geometrie(g) for g in geo_daten]
    elif isinstance(geo_daten, dict):
        geos = _parse_geometrie(geo_daten)
    else:
        return jsonify({"fehler": "geometrie fehlt"}), 422

    try:
        tp = erzeuge_drag_engraving_toolpath(geos, werkzeug, parameter)
    except DragEngravingFehler as e:
        return jsonify({"fehler": str(e)}), 422
    return jsonify(_serialize_toolpath(tp))


@bp.post("/auto-inlay")
def auto_inlay():
    data = request.get_json() or {}
    try:
        parameter = AutoInlayParameter.model_validate(data["parameter"])
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    if "geometrie" not in data:
        return jsonify({"fehler": "geometrie fehlt"}), 422
    geo = _parse_geometrie(data["geometrie"])
    try:
        ergebnis = berechne_auto_inlay(geo, parameter)
    except AutoInlayFehler as e:
        return jsonify({"fehler": str(e)}), 422
    tasche_geo, plug_geo = ergebnis_zu_geometrien(ergebnis)
    return jsonify({
        "ergebnis": ergebnis.model_dump(mode="json"),
        "tasche_geometrie": {
            "typ": tasche_geo.typ.value,
            "layer": tasche_geo.layer,
            "punkte": [p.to_tuple() for p in tasche_geo.punkte],
            "geschlossen": tasche_geo.geschlossen,
        },
        "plug_geometrie": {
            "typ": plug_geo.typ.value,
            "layer": plug_geo.layer,
            "punkte": [p.to_tuple() for p in plug_geo.punkte],
            "geschlossen": plug_geo.geschlossen,
        },
    })


@bp.post("/thread-milling")
def thread_milling():
    data = request.get_json() or {}
    try:
        parameter = ThreadMillingParameter.model_validate(data["parameter"])
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    werkzeug, fehler = _werkzeug_oder_404(parameter.werkzeug_id)
    if fehler:
        return fehler
    try:
        tp = erzeuge_thread_milling_toolpath(werkzeug, parameter)
    except ThreadMillingFehler as e:
        return jsonify({"fehler": str(e)}), 422
    return jsonify(_serialize_toolpath(tp))


@bp.post("/circular-pocket-pfade")
def circular_pfade_endpoint():
    data = request.get_json() or {}
    try:
        parameter = CircularPocketParameter.model_validate(data)
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    pfade = circular_pocket_pfade(parameter)
    return jsonify({"pfade": pfade, "anzahl": len(pfade)})


@bp.post("/radial-pocket-pfade")
def radial_pfade_endpoint():
    data = request.get_json() or {}
    try:
        parameter = RadialPocketParameter.model_validate(data)
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    pfade = radial_pocket_pfade(parameter)
    return jsonify({"pfade": pfade, "anzahl": len(pfade)})


@bp.post("/planfraesen")
def planfraesen():
    """Planfraesen (Cluster I1) — Spoilboard/Stock-Top ebnen."""
    data = request.get_json() or {}
    try:
        parameter = PlanfraesParameter.model_validate(data["parameter"])
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    werkzeug, fehler = _werkzeug_oder_404(parameter.werkzeug_id)
    if fehler:
        return fehler
    try:
        tp = erzeuge_planfraes_toolpath(werkzeug, parameter)
    except PlanfraesFehler as e:
        return jsonify({"fehler": str(e)}), 422
    return jsonify(_serialize_toolpath(tp))


def _heightmap_aus_payload(daten: dict) -> Heightmap:
    """Dekodiert eine Heightmap aus dem base64-Payload-Format (siehe /api/heightmap)."""
    import base64

    import numpy as np

    shape = tuple(daten["shape"])
    dtype = daten.get("z_values_dtype", "float32")
    buf = base64.b64decode(daten["z_values_base64"])
    z = np.frombuffer(buf, dtype=dtype).reshape(shape).astype(float)
    return Heightmap(
        z_values=z,
        aufloesung=float(daten["aufloesung"]),
        x_min=float(daten.get("x_min", 0.0)),
        y_min=float(daten.get("y_min", 0.0)),
        z_max=float(daten.get("z_max", float(z.max()))),
    )


@bp.post("/3d-parallel")
def dreid_parallel():
    """3D-Parallel-Schlichten (Cluster I2) auf einer STL-Heightmap.

    Body:
    {
      "parameter": { Strategie3DParameter-Felder },
      "heightmap": { shape, aufloesung, x_min, y_min, z_max, z_values_base64, z_values_dtype }
    }
    """
    data = request.get_json() or {}
    try:
        parameter = Strategie3DParameter.model_validate(data["parameter"])
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    werkzeug, fehler = _werkzeug_oder_404(parameter.werkzeug_id)
    if fehler:
        return fehler
    if "heightmap" not in data:
        return jsonify({"fehler": "heightmap fehlt"}), 422
    try:
        hm = _heightmap_aus_payload(data["heightmap"])
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": f"Heightmap ungueltig: {e}"}), 422
    try:
        tp = erzeuge_3d_parallel_toolpath(hm, werkzeug, parameter)
    except Strategie3DFehler as e:
        return jsonify({"fehler": str(e)}), 422
    return jsonify(_serialize_toolpath(tp))
