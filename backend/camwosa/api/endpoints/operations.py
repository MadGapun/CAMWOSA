"""API-Endpoints zum Erzeugen von Toolpaths fuer einzelne Operationen."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from camwosa.cam import (
    erzeuge_bohren_toolpath,
    erzeuge_gravur_toolpath,
    erzeuge_kontur_toolpath,
    erzeuge_tasche_toolpath,
)
from camwosa.cam.drechseln import erzeuge_drechsel_toolpath
from camwosa.cam.parameter import DrechselParameter
from camwosa.cam.wrap import (
    WrapParameter,
    erzeuge_wrap_toolpath,
    pruefe_design_fuer_radius,
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


@bp.post("/drechseln")
def drechseln():
    """Drechsel-Operation auf der Rotary-Achse.

    Body: ``{ werkzeug_id, parameter }`` — Parameter enthaelt das Profil
    (Liste von [laenge_x_mm, radius_mm]), Strategie, Rohmaterial-Radius etc.
    """
    data = request.get_json() or {}
    werkzeuge = {t.id: t for t in lade_werkzeuge()}
    werkzeug_id = data.get("werkzeug_id")
    if werkzeug_id not in werkzeuge:
        return jsonify({"fehler": f"Werkzeug {werkzeug_id} unbekannt"}), 404
    try:
        param = DrechselParameter.model_validate(data["parameter"])
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    try:
        tp = erzeuge_drechsel_toolpath(
            werkzeug_id, param, werkzeug=werkzeuge[werkzeug_id],
        )
    except ValueError as e:
        return jsonify({"fehler": str(e)}), 422
    return jsonify(_serialize_toolpath(tp))


@bp.post("/wrap")
def wrap():
    """Wrap-Operation: 2D-Pfad auf einen rotierenden Zylinder wickeln.

    Body: ``{ werkzeug_id, punkte_xy: [[x, y], ...], parameter }``.
    Y wird per Postprozessor zu Y-in-Grad = A-Achsen-Winkel.
    """
    data = request.get_json() or {}
    werkzeuge = {t.id: t for t in lade_werkzeuge()}
    werkzeug_id = data.get("werkzeug_id")
    if werkzeug_id not in werkzeuge:
        return jsonify({"fehler": f"Werkzeug {werkzeug_id} unbekannt"}), 404
    try:
        param = WrapParameter(**(data.get("parameter") or {}))
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    punkte_xy = [(float(p[0]), float(p[1])) for p in data.get("punkte_xy", [])]
    # Sicherheits-Pruefung
    warnungen = pruefe_design_fuer_radius(punkte_xy, param.werkstueck_radius_mm)
    try:
        tp = erzeuge_wrap_toolpath(punkte_xy, werkzeuge[werkzeug_id], param)
    except ValueError as e:
        return jsonify({"fehler": str(e), "warnungen": warnungen}), 422
    out = _serialize_toolpath(tp)
    out["warnungen"] = warnungen
    return jsonify(out)


@bp.post("/wrap/pruefe")
def wrap_pruefe():
    """Nur Design-Pruefung ohne Toolpath-Generierung."""
    data = request.get_json() or {}
    punkte_xy = [(float(p[0]), float(p[1])) for p in data.get("punkte_xy", [])]
    radius = float(data.get("werkstueck_radius_mm", 20.0))
    warnungen = pruefe_design_fuer_radius(punkte_xy, radius)
    return jsonify({"gueltig": not warnungen, "warnungen": warnungen})


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
    # P1: Spindel-Hochlauf-Dwell aus aktiver Spindel (rampen_zeit_s), per Body uebersteuerbar.
    hochlauf = data.get("spindel_hochlauf_s")
    if hochlauf is None:
        try:
            from camwosa.db.loader import lade_spindeln
            sp_index = {s.id: s for s in lade_spindeln()}
            sp = maschine.aktive_spindel(sp_index)
            if sp and sp.rampen_zeit_s:
                hochlauf = sp.rampen_zeit_s
        except Exception:  # noqa: BLE001 — Spindel-Aufloesung optional
            hochlauf = None
    ctx = PostKontext(
        maschine=maschine, werkzeug=werkzeug,
        spindel_hochlauf_s=float(hochlauf) if hochlauf else 0.0,
    )
    toolpaths = [_deserialize_toolpath(tp) for tp in data["toolpaths"]]
    # J5: Rampen-Eintauchen statt senkrechtem Plunge (vor allen weiteren Schritten)
    if data.get("rampe_eintauchen"):
        from camwosa.gcode.eintauchen import rampe_eintauchen
        winkel = float(data.get("rampen_winkel_grad", 5.0))
        mat_ok = float(data.get("material_oberkante", 0.0))
        # Q2: variable Eintauchgeschwindigkeit (Rampe darf schneller sein als Plunge)
        r_feed = data.get("rampen_vorschub")
        r_feed = float(r_feed) if r_feed is not None else None
        r_faktor = float(data.get("rampen_vorschub_faktor", 1.0))
        toolpaths = [
            rampe_eintauchen(tp, winkel_grad=winkel, material_oberkante=mat_ok,
                             rampe_feed=r_feed, rampe_faktor=r_faktor)
            for tp in toolpaths
        ]
    # J9/J10: intelligente Fahrwege (Reihenfolge optimieren + Freifahrten senken)
    if data.get("fahrweg_optimierung") or data.get("freifahrt_hoehe") is not None:
        from camwosa.gcode.fahrweg import optimiere_fahrwege
        reihenfolge = bool(data.get("fahrweg_optimierung", True))
        freifahrt = data.get("freifahrt_hoehe")
        toolpaths = [
            optimiere_fahrwege(
                tp, reihenfolge=reihenfolge,
                freifahrt_hoehe=float(freifahrt) if freifahrt is not None else None,
            )
            for tp in toolpaths
        ]
    # P3: Rapid-Safety — diagonale Eilgaenge in sichere Reihenfolge splitten
    if data.get("rapid_safety"):
        from camwosa.gcode.fahrweg import entschaerfe_eilgaenge
        toolpaths = [entschaerfe_eilgaenge(tp) for tp in toolpaths]
    # J1: optionales Arc-Fitting (G1-Folgen → G2/G3) vor dem Postprozessor
    if data.get("arc_fitting"):
        from camwosa.gcode.arc_fitting import fitte_toolpath
        tol = float(data.get("arc_toleranz_mm", 0.05))
        toolpaths = [fitte_toolpath(tp, toleranz_mm=tol) for tp in toolpaths]
    zeilen = post.post_alle(ctx, toolpaths)
    # P2: modale Kompression (redundante Achsworte/Feed/Bewegungs-Wort entfernen)
    if data.get("modal"):
        from camwosa.gcode.modal import komprimiere_modal
        zeilen = komprimiere_modal(zeilen)
    return jsonify({"gcode": "\n".join(zeilen) + "\n", "zeilen": len(zeilen)})


@bp.post("/zeitschaetzung")
def zeitschaetzung():
    """Schätzt die Bearbeitungszeit einer Operation oder eines ganzen Jobs (K5).

    Body:
    {
      "toolpaths": [ ...serialisierte Toolpaths... ],
      "maschine_id": "..."  ODER  "eilgang_mm_min": 3000,
      "overhead_faktor": 1.15 (optional),
      "werkzeugwechsel_sekunden": 45 (optional)
    }
    Response: { schnitt_sekunden, eilgang_sekunden, pausen_sekunden,
                gesamt_sekunden, gesamt_minuten, klartext }
    """
    from camwosa.gcode.zeit_schaetzung import schaetze_job_zeit

    data = request.get_json() or {}
    eilgang = data.get("eilgang_mm_min")
    if eilgang is None and data.get("maschine_id"):
        from camwosa.db.loader import lade_maschinen
        maschinen = {m.id: m for m in lade_maschinen()}
        m = maschinen.get(data["maschine_id"])
        if m is None:
            return jsonify({"fehler": "Maschine nicht gefunden"}), 404
        eilgang = m.eilgang
    if not eilgang or eilgang <= 0:
        return jsonify({"fehler": "eilgang_mm_min oder gueltige maschine_id noetig"}), 422

    try:
        toolpaths = [_deserialize_toolpath(tp) for tp in data.get("toolpaths", [])]
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": f"Toolpath ungueltig: {e}"}), 422

    erg = schaetze_job_zeit(
        toolpaths,
        eilgang_mm_min=float(eilgang),
        werkzeugwechsel_sekunden=float(data.get("werkzeugwechsel_sekunden", 45.0)),
        overhead_faktor=float(data.get("overhead_faktor", 1.15)),
    )
    return jsonify({
        "schnitt_sekunden": erg.schnitt_sekunden,
        "eilgang_sekunden": erg.eilgang_sekunden,
        "pausen_sekunden": erg.pausen_sekunden,
        "gesamt_sekunden": erg.gesamt_sekunden,
        "gesamt_minuten": erg.gesamt_minuten,
        "klartext": erg.klartext,
    })


@bp.post("/transformiere")
def transformiere():
    """A49: wendet eine Umspann-Transformation auf einen Toolpath an.

    Body: ``{ toolpath: {...}, transformation: { spiegeln, drehung_grad,
    invertiere_z, offset, werkstueck_breite_mm, werkstueck_tiefe_mm } }``.
    Liefert den transformierten Toolpath (serialisiert).
    """
    from camwosa.cam.umspannung import (
        WerkstueckTransformation, transformiere_toolpath,
    )
    data = request.get_json() or {}
    try:
        tp = _deserialize_toolpath(data["toolpath"])
        t = WerkstueckTransformation.model_validate(data.get("transformation", {}))
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422
    return jsonify(_serialize_toolpath(transformiere_toolpath(tp, t)))


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
                "rampe_feed": b.rampe_feed,  # Q2: Rampen-Feed ueber Roundtrip erhalten
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
                rampe_feed=b.get("rampe_feed"),  # Q2
            )
            for b in daten["bewegungen"]
        ],
    )
