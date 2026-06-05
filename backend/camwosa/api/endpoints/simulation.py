"""API-Endpoint fuer Voxel-Material-Abtrag-Simulation."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from camwosa.cam.rest_material import rest_heightmap
from camwosa.cam.simulation import (
    WerkstueckQuader,
    simuliere_toolpaths,
)
from camwosa.db.loader import lade_werkzeuge
from camwosa.gcode.toolpath import Bewegung, BewegungsTyp, OperationsTyp, Toolpath

bp = Blueprint("simulation", __name__, url_prefix="/api/simulation")


def _toolpath_aus_dict(d: dict) -> Toolpath:
    """Rekonstruiert einen Toolpath aus JSON."""
    bewegungen = [
        Bewegung(
            typ=BewegungsTyp(b["typ"]),
            x=float(b["x"]), y=float(b["y"]), z=float(b["z"]),
            feed=b.get("feed"),
            i=b.get("i"), j=b.get("j"),
            kommentar=b.get("kommentar", ""),
        )
        for b in d.get("bewegungen", [])
    ]
    return Toolpath(
        operation_id=d.get("operation_id", "sim"),
        operation_typ=OperationsTyp(d.get("operation_typ", "kontur")),
        werkzeug_id=d.get("werkzeug_id", ""),
        bewegungen=bewegungen,
        spindel_rpm=float(d.get("spindel_rpm", 0)),
        sicherheitshoehe=float(d.get("sicherheitshoehe", 5)),
        metadaten=d.get("metadaten", {}),
    )


@bp.post("/voxel")
def voxel_sim():
    """Body: ``{ toolpaths: [Toolpath...], werkzeug_id, werkstueck, aufloesung_mm? }``.

    werkstueck-Dict: ``{ laenge_x, breite_y, hoehe_z, nullpunkt_x?, nullpunkt_y? }``

    Antwortet mit Boundary-Voxel-Liste (sichtbare Oberflaeche) + Volumen-Stats.
    Boundary-Voxel sind Tupel (ix, iy, iz) — Welt-Koordinaten = Index ×
    aufloesung_mm (+ nullpunkt-Versatz).
    """
    data = request.get_json() or {}
    try:
        werkzeug_id = data["werkzeug_id"]
        ws_data = data["werkstueck"]
        tp_data = data.get("toolpaths")
        if tp_data is None and data.get("toolpath"):
            tp_data = [data["toolpath"]]
        if not tp_data:
            return jsonify({"fehler": "Mindestens 1 toolpath noetig"}), 422
    except KeyError as e:
        return jsonify({"fehler": f"Pflichtfeld fehlt: {e}"}), 422

    aufloesung = float(data.get("aufloesung_mm", 2.0))
    if aufloesung < 0.5 or aufloesung > 10:
        return jsonify({"fehler": "aufloesung_mm muss zwischen 0.5 und 10 liegen"}), 422

    werkzeuge = {w.id: w for w in lade_werkzeuge()}
    if werkzeug_id not in werkzeuge:
        return jsonify({"fehler": f"Werkzeug '{werkzeug_id}' unbekannt"}), 404
    werkzeug = werkzeuge[werkzeug_id]

    werkstueck = WerkstueckQuader(
        laenge_x=float(ws_data["laenge_x"]),
        breite_y=float(ws_data["breite_y"]),
        hoehe_z=float(ws_data["hoehe_z"]),
        nullpunkt_x=float(ws_data.get("nullpunkt_x", 0)),
        nullpunkt_y=float(ws_data.get("nullpunkt_y", 0)),
    )
    z_oberkante = data.get("z_oberkante_material")

    try:
        toolpaths = [_toolpath_aus_dict(raw) for raw in tp_data]
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": f"Toolpath-Format ungueltig: {e}"}), 422

    try:
        erg = simuliere_toolpaths(
            toolpaths, werkzeug, werkstueck,
            aufloesung_mm=aufloesung,
            z_oberkante_material=z_oberkante,
        )
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 500

    return jsonify({
        "aufloesung_mm": erg.aufloesung_mm,
        "nx": erg.nx, "ny": erg.ny, "nz": erg.nz,
        "werkstueck": {
            "laenge_x": werkstueck.laenge_x,
            "breite_y": werkstueck.breite_y,
            "hoehe_z": werkstueck.hoehe_z,
            "nullpunkt_x": werkstueck.nullpunkt_x,
            "nullpunkt_y": werkstueck.nullpunkt_y,
        },
        "boundary_voxel": erg.boundary_voxel,
        "voxel_count": len(erg.boundary_voxel),
        "voxel_volumen_mm3": erg.voxel_volumen_mm3,
        "abgetragenes_volumen_mm3": erg.abgetragenes_volumen_mm3,
        "bewegungen_simuliert": erg.bewegungen_simuliert,
    })


@bp.post("/rest-heightmap")
def rest_heightmap_sim():
    """I6: Rest-Material-Höhe-Karte nach Abtrag (Schruppen→Schlichten / A49-Stock).

    Body wie ``/voxel``: ``{ toolpaths|toolpath, werkzeug_id, werkstueck,
    aufloesung_mm? , z_oberkante_material? }``.

    Antwortet mit ``hoehen_mm`` (2D-Array [ix][iy] = Rest-Z in mm) + Rest-/Abtrag-
    Statistik. Welt: ``x = nullpunkt_x + (ix+0.5)*aufloesung_mm``.
    """
    data = request.get_json() or {}
    try:
        werkzeug_id = data["werkzeug_id"]
        ws_data = data["werkstueck"]
        tp_data = data.get("toolpaths")
        if tp_data is None and data.get("toolpath"):
            tp_data = [data["toolpath"]]
        if not tp_data:
            return jsonify({"fehler": "Mindestens 1 toolpath noetig"}), 422
    except KeyError as e:
        return jsonify({"fehler": f"Pflichtfeld fehlt: {e}"}), 422

    aufloesung = float(data.get("aufloesung_mm", 2.0))
    if aufloesung < 0.5 or aufloesung > 10:
        return jsonify({"fehler": "aufloesung_mm muss zwischen 0.5 und 10 liegen"}), 422

    werkzeuge = {w.id: w for w in lade_werkzeuge()}
    if werkzeug_id not in werkzeuge:
        return jsonify({"fehler": f"Werkzeug '{werkzeug_id}' unbekannt"}), 404
    werkzeug = werkzeuge[werkzeug_id]

    werkstueck = WerkstueckQuader(
        laenge_x=float(ws_data["laenge_x"]),
        breite_y=float(ws_data["breite_y"]),
        hoehe_z=float(ws_data["hoehe_z"]),
        nullpunkt_x=float(ws_data.get("nullpunkt_x", 0)),
        nullpunkt_y=float(ws_data.get("nullpunkt_y", 0)),
    )
    z_oberkante = data.get("z_oberkante_material")

    try:
        toolpaths = [_toolpath_aus_dict(raw) for raw in tp_data]
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": f"Toolpath-Format ungueltig: {e}"}), 422

    try:
        erg = rest_heightmap(
            toolpaths, werkzeug, werkstueck,
            aufloesung_mm=aufloesung,
            z_oberkante_material=z_oberkante,
        )
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 500

    return jsonify({
        "aufloesung_mm": erg.aufloesung_mm,
        "nx": erg.nx, "ny": erg.ny,
        "werkstueck": {
            "laenge_x": werkstueck.laenge_x,
            "breite_y": werkstueck.breite_y,
            "hoehe_z": werkstueck.hoehe_z,
            "nullpunkt_x": werkstueck.nullpunkt_x,
            "nullpunkt_y": werkstueck.nullpunkt_y,
        },
        "hoehen_mm": erg.hoehen_mm,
        "max_rest_mm": erg.max_rest_mm,
        "rest_volumen_mm3": erg.rest_volumen_mm3,
        "abgetragenes_volumen_mm3": erg.abgetragenes_volumen_mm3,
        "bewegungen_simuliert": erg.bewegungen_simuliert,
    })
