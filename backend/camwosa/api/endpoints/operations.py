"""API-Endpoints zum Erzeugen von Toolpaths fuer einzelne Operationen."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from camwosa.cam import (
    erzeuge_bohren_toolpath,
    erzeuge_gravur_toolpath,
    erzeuge_kontur_toolpath,
    erzeuge_tasche_toolpath,
)
from camwosa.cam.overrides import (
    BohrOverrides,
    GravurOverrides,
    KonturOverrides,
    ProjektDefaults,
    TaschenOverrides,
    aufloese_bohren,
    aufloese_gravur,
    aufloese_kontur,
    aufloese_tasche,
)
from camwosa.cam.parameter import (
    BohrParameter,
    GravurParameter,
    KonturParameter,
    TaschenParameter,
)
from camwosa.db.loader import lade_materialien, lade_werkzeuge
from camwosa.dxf.parser import GeometrieObjekt, GeometrieTyp, Punkt2D
from camwosa.postprocessor import PostKontext, registry

bp = Blueprint("operations", __name__, url_prefix="/api/operations")


def _parse_geometrie(daten: dict) -> GeometrieObjekt:
    return GeometrieObjekt(
        typ=GeometrieTyp(daten["typ"]),
        layer=daten.get("layer", "0"),
        punkte=[Punkt2D(p[0], p[1]) for p in daten["punkte"]],
        geschlossen=daten.get("geschlossen", False),
        attribute=daten.get("attribute", {}),
    )


@bp.post("/kontur")
def kontur():
    data = request.get_json()
    werkzeuge = {t.id: t for t in lade_werkzeuge()}
    werkzeug_id = data["werkzeug_id"]
    if werkzeug_id not in werkzeuge:
        return jsonify({"fehler": f"Werkzeug {werkzeug_id} unbekannt"}), 404
    geo = _parse_geometrie(data["geometrie"])
    param = KonturParameter.model_validate(data["parameter"])
    tp = erzeuge_kontur_toolpath(geo, werkzeuge[werkzeug_id], param)
    return jsonify(_serialize_toolpath(tp))


@bp.post("/tasche")
def tasche():
    data = request.get_json()
    werkzeuge = {t.id: t for t in lade_werkzeuge()}
    werkzeug = werkzeuge[data["werkzeug_id"]]
    geo = _parse_geometrie(data["geometrie"])
    param = TaschenParameter.model_validate(data["parameter"])
    tp = erzeuge_tasche_toolpath(geo, werkzeug, param)
    return jsonify(_serialize_toolpath(tp))


@bp.post("/bohren")
def bohren():
    data = request.get_json()
    werkzeuge = {t.id: t for t in lade_werkzeuge()}
    werkzeug = werkzeuge[data["werkzeug_id"]]
    punkte = [Punkt2D(p[0], p[1]) for p in data["punkte"]]
    param = BohrParameter.model_validate(data["parameter"])
    tp = erzeuge_bohren_toolpath(punkte, werkzeug, param)
    return jsonify(_serialize_toolpath(tp))


@bp.post("/gravur")
def gravur():
    data = request.get_json()
    werkzeuge = {t.id: t for t in lade_werkzeuge()}
    werkzeug = werkzeuge[data["werkzeug_id"]]
    geo = _parse_geometrie(data["geometrie"])
    param = GravurParameter.model_validate(data["parameter"])
    tp = erzeuge_gravur_toolpath(geo, werkzeug, param)
    return jsonify(_serialize_toolpath(tp))


@bp.post("/aufloesen")
def aufloesen():
    """Loest Operation-Overrides + Material-/Projekt-Defaults zu effektiven Parametern auf.

    Body:
        {
          "typ": "kontur" | "tasche" | "bohren" | "gravur",
          "overrides": { ... werkzeug_id + optionale Felder ... },
          "material_id": "buche_massiv",
          "projekt_defaults": {...} (optional)
        }
    Response:
        {
          "parameter": {...},   // vollstaendig aufgelost
          "quellen": {"vorschub": "material_preset", ...}
        }
    """
    data = request.get_json()
    typ = data["typ"]
    material_id = data["material_id"]
    materialien = {m.id: m for m in lade_materialien()}
    werkzeuge = {t.id: t for t in lade_werkzeuge()}
    if material_id not in materialien:
        return jsonify({"fehler": f"Material {material_id} unbekannt"}), 404
    material = materialien[material_id]
    overrides_dict = data["overrides"]
    werkzeug_id = overrides_dict["werkzeug_id"]
    if werkzeug_id not in werkzeuge:
        return jsonify({"fehler": f"Werkzeug {werkzeug_id} unbekannt"}), 404
    werkzeug = werkzeuge[werkzeug_id]
    defaults = (
        ProjektDefaults(**data["projekt_defaults"])
        if data.get("projekt_defaults") else None
    )
    if typ == "kontur":
        ov = KonturOverrides.model_validate(overrides_dict)
        erg = aufloese_kontur(ov, material, werkzeug, defaults=defaults)
    elif typ == "tasche":
        ov = TaschenOverrides.model_validate(overrides_dict)
        erg = aufloese_tasche(ov, material, werkzeug, defaults=defaults)
    elif typ == "bohren":
        ov = BohrOverrides.model_validate(overrides_dict)
        erg = aufloese_bohren(ov, material, werkzeug, defaults=defaults)
    elif typ == "gravur":
        ov = GravurOverrides.model_validate(overrides_dict)
        erg = aufloese_gravur(ov, material, werkzeug, defaults=defaults)
    else:
        return jsonify({"fehler": f"Unbekannter Operations-Typ: {typ}"}), 400
    return jsonify({
        "parameter": erg.parameter.model_dump(mode="json"),
        "quellen": erg.quellen,
    })


@bp.post("/postprocess")
def postprocess():
    """Wandelt einen Toolpath (oder mehrere) in G-Code mittels Postprozessor."""
    data = request.get_json()
    from camwosa.db.loader import lade_maschinen
    maschinen = {m.id: m for m in lade_maschinen()}
    werkzeuge = {t.id: t for t in lade_werkzeuge()}
    maschine = maschinen[data["maschine_id"]]
    werkzeug = werkzeuge[data["werkzeug_id"]]
    post_id = data.get("postprozessor_id", maschine.postprozessor)
    post = registry().get(post_id)()
    ctx = PostKontext(maschine=maschine, werkzeug=werkzeug)
    toolpaths = [_deserialize_toolpath(tp) for tp in data["toolpaths"]]
    zeilen = post.post_alle(ctx, toolpaths)
    return jsonify({"gcode": "\n".join(zeilen) + "\n", "zeilen": len(zeilen)})


def _serialize_toolpath(tp) -> dict:
    return {
        "operation_id": tp.operation_id,
        "operation_typ": tp.operation_typ.value,
        "werkzeug_id": tp.werkzeug_id,
        "spindel_rpm": tp.spindel_rpm,
        "sicherheitshoehe": tp.sicherheitshoehe,
        "kommentar": tp.kommentar,
        "metadaten": tp.metadaten,
        "bewegungen": [
            {
                "typ": b.typ.value,
                "x": b.x, "y": b.y, "z": b.z,
                "feed": b.feed, "i": b.i, "j": b.j,
                "kommentar": b.kommentar,
            }
            for b in tp.bewegungen
        ],
        "gesamtlaenge": tp.gesamtlaenge,
        "schnittlaenge": tp.schnittlaenge,
    }


def _deserialize_toolpath(daten: dict):
    from camwosa.gcode.toolpath import (
        Bewegung, BewegungsTyp, OperationsTyp, Toolpath,
    )
    return Toolpath(
        operation_id=daten["operation_id"],
        operation_typ=OperationsTyp(daten["operation_typ"]),
        werkzeug_id=daten["werkzeug_id"],
        spindel_rpm=daten["spindel_rpm"],
        sicherheitshoehe=daten["sicherheitshoehe"],
        kommentar=daten.get("kommentar", ""),
        metadaten=daten.get("metadaten", {}),
        bewegungen=[
            Bewegung(
                typ=BewegungsTyp(b["typ"]),
                x=b["x"], y=b["y"], z=b["z"],
                feed=b.get("feed"),
                i=b.get("i"), j=b.get("j"),
                kommentar=b.get("kommentar", ""),
            )
            for b in daten["bewegungen"]
        ],
    )
