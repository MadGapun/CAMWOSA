"""API-Endpoints fuer Heightmap-Operationen (Bild → Heightmap, Stats, Wrap-Relief)."""

from __future__ import annotations

import base64

import numpy as np
from flask import Blueprint, jsonify, request

from camwosa.cam.wrap import (
    WrapReliefParameter,
    WrapReliefStrategie,
    erzeuge_wrap_relief_toolpath,
    pruefe_heightmap_fuer_radius,
)
from camwosa.db.loader import lade_werkzeuge
from camwosa.stl.ai_tiefenkarte import (
    AIExtraFehlt,
    AITiefenparameter,
    heightmap_aus_bild_ai,
    modell_info,
)
from camwosa.stl.bild_heightmap import (
    BildHeightmapParameter,
    heightmap_aus_bild,
    heightmap_statistik,
)
from camwosa.stl.heightmap import Heightmap
from camwosa.stl.heightmap_bearbeitung import (
    detail_slider,
    edge_boost,
    gamma_korrektur,
    histogramm_stretch,
    selective_smoothing,
    zero_plane,
)

bp = Blueprint("heightmap", __name__, url_prefix="/api/heightmap")


def _heightmap_payload(hm: Heightmap) -> dict:
    """Serialisiert die Heightmap zu JSON.

    Z-Werte werden als komprimiertes Base64 + Shape uebertragen — fuer
    grosse Heightmaps deutlich kleiner als JSON-Listen.
    """
    z = hm.z_values.astype("float32")
    buf = z.tobytes()
    return {
        "aufloesung_mm": float(hm.aufloesung),
        "x_min_mm": float(hm.x_min),
        "y_min_mm": float(hm.y_min),
        "z_max_mm": float(hm.z_max),
        "shape": list(z.shape),
        "z_values_base64": base64.b64encode(buf).decode("ascii"),
        "z_values_dtype": "float32",
        "statistik": heightmap_statistik(hm),
    }


@bp.post("/aus-bild")
def aus_bild():
    """Bild → Heightmap.

    Body: ``multipart/form-data`` mit:
    - ``datei``: das Bild (PNG, JPG, ...)
    - ``max_tiefe_mm`` (optional, Default 3.0)
    - ``pixel_pro_mm`` (optional, Default 5.0)
    - ``invertieren`` (optional, "true"/"false", Default false)
    - ``glaetten_radius`` (optional, Default 0)
    - ``zero_plane_schwelle`` (optional, 0..1, Default 0)
    - ``max_dimension_px`` (optional, Default null)
    """
    if "datei" not in request.files:
        return jsonify({"fehler": "Keine Datei"}), 400
    f = request.files["datei"]
    bild_bytes = f.read()

    def _f(name: str, default: float) -> float:
        v = request.form.get(name)
        return float(v) if v else default

    def _i(name: str, default: int | None) -> int | None:
        v = request.form.get(name)
        if v in (None, "", "null"):
            return default
        return int(v)

    def _b(name: str, default: bool) -> bool:
        v = request.form.get(name, "").lower()
        if v in ("true", "1", "yes", "ja"):
            return True
        if v in ("false", "0", "no", "nein"):
            return False
        return default

    parameter = BildHeightmapParameter(
        max_tiefe_mm=_f("max_tiefe_mm", 3.0),
        pixel_pro_mm=_f("pixel_pro_mm", 5.0),
        invertieren=_b("invertieren", False),
        glaetten_radius=_i("glaetten_radius", 0) or 0,
        zero_plane_schwelle=_f("zero_plane_schwelle", 0.0),
        max_dimension_px=_i("max_dimension_px", None),
    )

    try:
        hm = heightmap_aus_bild(bild_bytes, parameter)
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": f"Bild nicht verarbeitbar: {e}"}), 422

    return jsonify(_heightmap_payload(hm))


@bp.post("/aus-bild/statistik")
def aus_bild_nur_stats():
    """Wie /aus-bild, gibt aber nur die Statistik zurueck (kein Z-Array).

    Praktisch fuer schnelle Live-Vorschau ohne grosse Payloads.
    """
    if "datei" not in request.files:
        return jsonify({"fehler": "Keine Datei"}), 400
    f = request.files["datei"]
    bild_bytes = f.read()

    def _f(name: str, default: float) -> float:
        v = request.form.get(name)
        return float(v) if v else default

    parameter = BildHeightmapParameter(
        max_tiefe_mm=_f("max_tiefe_mm", 3.0),
        pixel_pro_mm=_f("pixel_pro_mm", 5.0),
    )

    try:
        hm = heightmap_aus_bild(bild_bytes, parameter)
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": str(e)}), 422

    return jsonify(heightmap_statistik(hm))


# ---------------------------------------------------------------------------
# Wrap-Relief — Master-Plan A34 (Bild-zu-Relief Phase C)
# ---------------------------------------------------------------------------


def _heightmap_aus_payload(payload: dict) -> Heightmap:
    """Rekonstruiert eine Heightmap aus dem JSON-Payload."""
    z_b64 = payload.get("z_values_base64")
    shape = payload.get("shape")
    if not z_b64 or not shape or len(shape) != 2:
        raise ValueError("Heightmap-Payload braucht z_values_base64 + shape [nx, ny]")
    z = np.frombuffer(base64.b64decode(z_b64), dtype=np.float32).reshape(shape)
    return Heightmap(
        z_values=z.copy(),
        aufloesung=float(payload.get("aufloesung_mm", 1.0)),
        x_min=float(payload.get("x_min_mm", 0.0)),
        y_min=float(payload.get("y_min_mm", 0.0)),
        z_max=float(payload.get("z_max_mm", 0.0)),
    )


def _bewegung_zu_json(b) -> dict:
    """Bewegung → JSON-Eintrag."""
    return {
        "typ": b.typ.value,
        "x": b.x, "y": b.y, "z": b.z,
        "feed": b.feed,
        "kommentar": b.kommentar,
    }


@bp.post("/wrap-relief")
def wrap_relief():
    """Wrap-Relief — Heightmap auf Zylinder gewickelt.

    JSON-Body:
    ```
    {
      "heightmap": { ...Payload aus /aus-bild oder /aus-stl... },
      "werkzeug_id": "kugel_2mm",
      "spindel_rpm": 18000,
      "vorschub": 600,
      "eintauch_vorschub": 200,
      "werkstueck_radius_mm": 20.0,
      "sicherheitshoehe_mm": 5.0,
      "strategie": "raster_x" | "raster_a",
      "serpentinen": true
    }
    ```

    Antwort: Toolpath (Bewegungen + metadaten + Warnungen).
    """
    payload = request.get_json(silent=True) or {}
    hm_payload = payload.get("heightmap")
    if not isinstance(hm_payload, dict):
        return jsonify({"fehler": "heightmap (objekt) erforderlich"}), 400

    try:
        hm = _heightmap_aus_payload(hm_payload)
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": f"Heightmap-Payload ungueltig: {e}"}), 422

    werkzeug_id = payload.get("werkzeug_id")
    werkzeuge = {w.id: w for w in lade_werkzeuge()}
    if werkzeug_id not in werkzeuge:
        return jsonify({"fehler": f"Werkzeug '{werkzeug_id}' nicht gefunden"}), 404

    strategie_str = str(payload.get("strategie", "raster_x")).lower()
    try:
        strategie = WrapReliefStrategie(strategie_str)
    except ValueError:
        return jsonify(
            {"fehler": f"strategie muss raster_x oder raster_a sein (war {strategie_str})"}
        ), 400

    parameter = WrapReliefParameter(
        werkzeug_id=werkzeug_id,
        spindel_rpm=float(payload.get("spindel_rpm", 18000)),
        vorschub=float(payload.get("vorschub", 600)),
        eintauch_vorschub=float(payload.get("eintauch_vorschub", 200)),
        sicherheitshoehe_mm=float(payload.get("sicherheitshoehe_mm", 5.0)),
        werkstueck_radius_mm=float(payload.get("werkstueck_radius_mm", 20.0)),
        strategie=strategie,
        serpentinen=bool(payload.get("serpentinen", True)),
    )

    try:
        tp = erzeuge_wrap_relief_toolpath(hm, werkzeuge[werkzeug_id], parameter)
    except ValueError as e:
        return jsonify({"fehler": str(e)}), 422

    return jsonify({
        "operation_id": tp.operation_id,
        "operation_typ": tp.operation_typ.value,
        "werkzeug_id": tp.werkzeug_id,
        "spindel_rpm": tp.spindel_rpm,
        "sicherheitshoehe": tp.sicherheitshoehe,
        "kommentar": tp.kommentar,
        "bewegungen": [_bewegung_zu_json(b) for b in tp.bewegungen],
        "metadaten": tp.metadaten,
        "gesamtlaenge_mm": tp.gesamtlaenge,
    })


# ---------------------------------------------------------------------------
# AI-Tiefenkarte — Master-Plan A36 (Phase E, optional [ai]-Extra)
# ---------------------------------------------------------------------------


@bp.get("/ai/modelle")
def ai_modelle():
    """Liefert Liste der bekannten AI-Modelle + Installations-Status."""
    return jsonify(modell_info())


@bp.post("/aus-bild-ai")
def aus_bild_ai():
    """Bild → Heightmap via AI-Tiefenschaetzung (Phase E).

    Erfordert das ``[ai]``-Extra. Wenn nicht installiert: 422 mit Hinweis.

    Body: ``multipart/form-data`` mit:
    - ``datei``: das Bild
    - ``max_tiefe_mm`` (Default 3.0)
    - ``pixel_pro_mm`` (Default 5.0)
    - ``modell`` (Default depth-anything-v2-small)
    - ``invertieren`` (Default false)
    - ``max_dimension_px`` (Default 1024)
    """
    if "datei" not in request.files:
        return jsonify({"fehler": "Keine Datei"}), 400
    f = request.files["datei"]
    bild_bytes = f.read()

    def _f(name: str, default: float) -> float:
        v = request.form.get(name)
        return float(v) if v else default

    def _b(name: str, default: bool) -> bool:
        v = request.form.get(name, "").lower()
        return v in ("true", "1", "yes", "ja") if v else default

    def _i(name: str, default: int | None) -> int | None:
        v = request.form.get(name)
        if v in (None, "", "null"):
            return default
        return int(v)

    parameter = AITiefenparameter(
        max_tiefe_mm=_f("max_tiefe_mm", 3.0),
        pixel_pro_mm=_f("pixel_pro_mm", 5.0),
        modell=request.form.get("modell") or "depth-anything-v2-small",
        invertieren=_b("invertieren", False),
        max_dimension_px=_i("max_dimension_px", 1024),
    )

    try:
        hm = heightmap_aus_bild_ai(bild_bytes, parameter)
    except AIExtraFehlt as e:
        return jsonify({
            "fehler": str(e),
            "extra_fehlt": e.fehlender_import,
            "installation": "pip install 'camwosa[ai]'",
        }), 422
    except ValueError as e:
        return jsonify({"fehler": str(e)}), 422

    return jsonify(_heightmap_payload(hm))


# ---------------------------------------------------------------------------
# Bearbeitungs-Tools — Master-Plan A35 (Phase D)
# ---------------------------------------------------------------------------


def _heightmap_zu_payload_response(hm: Heightmap):
    """Liefert einen Heightmap-Payload + Status — wiederverwendbar fuer Filter-Endpoints."""
    return jsonify(_heightmap_payload(hm))


@bp.post("/bearbeitung/gamma")
def bearbeitung_gamma():
    """Gamma-Korrektur. JSON: ``{"heightmap": {...}, "gamma": 1.5}``."""
    payload = request.get_json(silent=True) or {}
    if "heightmap" not in payload:
        return jsonify({"fehler": "heightmap erforderlich"}), 400
    try:
        hm = _heightmap_aus_payload(payload["heightmap"])
        hm_neu = gamma_korrektur(hm, gamma=float(payload.get("gamma", 1.0)))
    except (ValueError, KeyError) as e:
        return jsonify({"fehler": str(e)}), 422
    return _heightmap_zu_payload_response(hm_neu)


@bp.post("/bearbeitung/histogramm-stretch")
def bearbeitung_histogramm():
    """Histogramm-Stretching. JSON: ``{"heightmap": {...}, "low_perzentil": 2, "high_perzentil": 98}``."""
    payload = request.get_json(silent=True) or {}
    if "heightmap" not in payload:
        return jsonify({"fehler": "heightmap erforderlich"}), 400
    try:
        hm = _heightmap_aus_payload(payload["heightmap"])
        hm_neu = histogramm_stretch(
            hm,
            low_perzentil=float(payload.get("low_perzentil", 2.0)),
            high_perzentil=float(payload.get("high_perzentil", 98.0)),
        )
    except (ValueError, KeyError) as e:
        return jsonify({"fehler": str(e)}), 422
    return _heightmap_zu_payload_response(hm_neu)


@bp.post("/bearbeitung/zero-plane")
def bearbeitung_zero_plane():
    """Zero-Plane. JSON: ``{"heightmap": {...}, "schwelle": 0.5}``."""
    payload = request.get_json(silent=True) or {}
    if "heightmap" not in payload:
        return jsonify({"fehler": "heightmap erforderlich"}), 400
    try:
        hm = _heightmap_aus_payload(payload["heightmap"])
        hm_neu = zero_plane(hm, schwelle=float(payload.get("schwelle", 0.5)))
    except (ValueError, KeyError) as e:
        return jsonify({"fehler": str(e)}), 422
    return _heightmap_zu_payload_response(hm_neu)


@bp.post("/bearbeitung/edge-boost")
def bearbeitung_edge_boost():
    """Edge-Boost. JSON: ``{"heightmap": {...}, "faktor": 1.0}``."""
    payload = request.get_json(silent=True) or {}
    if "heightmap" not in payload:
        return jsonify({"fehler": "heightmap erforderlich"}), 400
    try:
        hm = _heightmap_aus_payload(payload["heightmap"])
        hm_neu = edge_boost(hm, faktor=float(payload.get("faktor", 1.0)))
    except (ValueError, KeyError) as e:
        return jsonify({"fehler": str(e)}), 422
    return _heightmap_zu_payload_response(hm_neu)


@bp.post("/bearbeitung/selective-smoothing")
def bearbeitung_smoothing():
    """Selective Smoothing. JSON: ``{"heightmap": {...}, "radius": 1, "bereich": "alles", "schwelle": 0.5}``."""
    payload = request.get_json(silent=True) or {}
    if "heightmap" not in payload:
        return jsonify({"fehler": "heightmap erforderlich"}), 400
    try:
        hm = _heightmap_aus_payload(payload["heightmap"])
        hm_neu = selective_smoothing(
            hm,
            radius=int(payload.get("radius", 1)),
            bereich=str(payload.get("bereich", "alles")),  # type: ignore[arg-type]
            schwelle=float(payload.get("schwelle", 0.5)),
        )
    except (ValueError, KeyError) as e:
        return jsonify({"fehler": str(e)}), 422
    return _heightmap_zu_payload_response(hm_neu)


@bp.post("/bearbeitung/detail-slider")
def bearbeitung_detail():
    """Detail-Slider (-1..+1). JSON: ``{"heightmap": {...}, "detail": 0.5}``."""
    payload = request.get_json(silent=True) or {}
    if "heightmap" not in payload:
        return jsonify({"fehler": "heightmap erforderlich"}), 400
    try:
        hm = _heightmap_aus_payload(payload["heightmap"])
        hm_neu = detail_slider(hm, detail=float(payload.get("detail", 0.0)))
    except (ValueError, KeyError) as e:
        return jsonify({"fehler": str(e)}), 422
    return _heightmap_zu_payload_response(hm_neu)


@bp.post("/wrap-relief/pruefen")
def wrap_relief_pruefen():
    """Schnelle Vorab-Pruefung ohne Toolpath-Generierung.

    JSON-Body: ``{"heightmap": {...}, "werkstueck_radius_mm": 20.0}``
    Antwort: ``{"warnungen": ["..."], "ist_ok": bool}``
    """
    payload = request.get_json(silent=True) or {}
    hm_payload = payload.get("heightmap")
    if not isinstance(hm_payload, dict):
        return jsonify({"fehler": "heightmap (objekt) erforderlich"}), 400
    try:
        hm = _heightmap_aus_payload(hm_payload)
    except Exception as e:  # noqa: BLE001
        return jsonify({"fehler": f"Heightmap-Payload ungueltig: {e}"}), 422
    radius = float(payload.get("werkstueck_radius_mm", 20.0))
    warnungen = pruefe_heightmap_fuer_radius(hm, radius)
    return jsonify({
        "warnungen": warnungen,
        "ist_ok": len(warnungen) == 0,
        "werkstueck_umfang_mm": 2 * 3.14159265 * radius,
    })
