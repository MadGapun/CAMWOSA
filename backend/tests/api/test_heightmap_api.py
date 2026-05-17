"""API-Tests fuer Heightmap-Endpoints."""

from __future__ import annotations

import base64
from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from camwosa.api import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _png_bytes(arr: np.ndarray) -> bytes:
    img = Image.fromarray(arr.astype(np.uint8), mode="L")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


class TestAusBild:
    def test_einfacher_upload(self, client):
        arr = np.array([[0, 128, 255]], dtype=np.uint8)
        png = _png_bytes(arr)
        rv = client.post("/api/heightmap/aus-bild",
            data={
                "datei": (BytesIO(png), "test.png"),
                "max_tiefe_mm": "2.5",
                "pixel_pro_mm": "2.0",
            },
            content_type="multipart/form-data",
        )
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["aufloesung_mm"] == 0.5
        assert body["shape"] == [3, 1]
        assert body["statistik"]["max_tiefe_mm"] == pytest.approx(2.5, abs=0.01)
        # Z-Werte: decode aus base64
        z_bytes = base64.b64decode(body["z_values_base64"])
        z = np.frombuffer(z_bytes, dtype=np.float32).reshape(body["shape"])
        # Linker Pixel (schwarz) → tiefste Stelle
        assert z[0, 0] == pytest.approx(-2.5, abs=0.01)
        # Rechter Pixel (weiss) → 0
        assert z[2, 0] == pytest.approx(0.0, abs=0.01)

    def test_invertieren_param(self, client):
        arr = np.array([[0, 255]], dtype=np.uint8)
        png = _png_bytes(arr)
        rv = client.post("/api/heightmap/aus-bild",
            data={
                "datei": (BytesIO(png), "x.png"),
                "max_tiefe_mm": "1.0",
                "invertieren": "true",
            },
            content_type="multipart/form-data",
        )
        body = rv.get_json()
        z_bytes = base64.b64decode(body["z_values_base64"])
        z = np.frombuffer(z_bytes, dtype=np.float32).reshape(body["shape"])
        # Mit invertieren: schwarz wird hoch (0), weiss tief (-1)
        assert z[0, 0] == pytest.approx(0.0, abs=0.01)
        assert z[1, 0] == pytest.approx(-1.0, abs=0.01)

    def test_keine_datei(self, client):
        rv = client.post("/api/heightmap/aus-bild", data={})
        assert rv.status_code == 400

    def test_kaputt_bild(self, client):
        rv = client.post("/api/heightmap/aus-bild",
            data={"datei": (BytesIO(b"nicht-ein-bild"), "x.png")},
            content_type="multipart/form-data",
        )
        assert rv.status_code == 422


class TestNurStatistik:
    def test_stats_endpoint(self, client):
        arr = np.full((20, 30), 128, dtype=np.uint8)
        png = _png_bytes(arr)
        rv = client.post("/api/heightmap/aus-bild/statistik",
            data={"datei": (BytesIO(png), "x.png"),
                  "max_tiefe_mm": "5", "pixel_pro_mm": "2"},
            content_type="multipart/form-data",
        )
        assert rv.status_code == 200
        s = rv.get_json()
        # Pillow ist (zeilen=hoehe, spalten=breite) → transponiert (breite, hoehe)
        # 30 spalten breit, 20 zeilen hoch → shape_x=30, shape_y=20
        assert s["shape_x"] == 30
        assert s["shape_y"] == 20
        assert s["breite_mm"] == 15.0
        assert s["hoehe_mm"] == 10.0
        # Uniform 128 → z_mittel ≈ -(1-128/255)*5
        assert s["z_mittel"] == pytest.approx(-(1 - 128/255) * 5.0, abs=0.05)


# ---------------------------------------------------------------------------
# Wrap-Relief-Endpoints (Master-Plan A34)
# ---------------------------------------------------------------------------


def _heightmap_payload_aus_bild(client, arr: np.ndarray,
                                 max_tiefe: float = 1.0,
                                 pixel_pro_mm: float = 1.0) -> dict:
    """Hilfs-Helper: laed Bild hoch, gibt Heightmap-Payload zurueck."""
    png = _png_bytes(arr)
    rv = client.post("/api/heightmap/aus-bild",
        data={
            "datei": (BytesIO(png), "x.png"),
            "max_tiefe_mm": str(max_tiefe),
            "pixel_pro_mm": str(pixel_pro_mm),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    return rv.get_json()


class TestAITiefenkarte:
    def test_modelle_endpoint(self, client):
        rv = client.get("/api/heightmap/ai/modelle")
        assert rv.status_code == 200
        body = rv.get_json()
        assert "modelle" in body
        assert "default" in body
        assert "ist_installiert" in body

    def test_inferenz_ohne_extra_gibt_422(self, client):
        from camwosa.stl.ai_tiefenkarte import ist_verfuegbar
        if ist_verfuegbar():
            pytest.skip("[ai]-Extra ist installiert")
        arr = np.array([[0, 128, 255]], dtype=np.uint8)
        png = _png_bytes(arr)
        rv = client.post("/api/heightmap/aus-bild-ai",
            data={"datei": (BytesIO(png), "x.png"),
                  "max_tiefe_mm": "1.0", "pixel_pro_mm": "2.0"},
            content_type="multipart/form-data",
        )
        assert rv.status_code == 422
        body = rv.get_json()
        assert "camwosa[ai]" in body.get("installation", "")

    def test_inferenz_ohne_datei(self, client):
        rv = client.post("/api/heightmap/aus-bild-ai", data={})
        assert rv.status_code == 400


class TestWrapReliefPruefen:
    def test_ok_heightmap(self, client):
        hm_payload = _heightmap_payload_aus_bild(
            client, np.zeros((5, 5), dtype=np.uint8), max_tiefe=0.5)
        rv = client.post("/api/heightmap/wrap-relief/pruefen",
            json={"heightmap": hm_payload, "werkstueck_radius_mm": 20})
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["ist_ok"] is True
        assert body["warnungen"] == []
        assert body["werkstueck_umfang_mm"] == pytest.approx(125.66, abs=0.1)

    def test_warnung_wenn_design_umlauft(self, client):
        # 80 Pixel á 1mm Y-Spanne, R=5 → Umfang 31mm → Warnung
        arr = np.zeros((80, 5), dtype=np.uint8)  # (zeilen=80, spalten=5)
        # Bei Pillow: zeilen=hoehe, transponiert wird shape_x=5, shape_y=80
        hm_payload = _heightmap_payload_aus_bild(client, arr, pixel_pro_mm=1.0)
        rv = client.post("/api/heightmap/wrap-relief/pruefen",
            json={"heightmap": hm_payload, "werkstueck_radius_mm": 5})
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["ist_ok"] is False
        assert any("mehrfach um" in w for w in body["warnungen"])

    def test_fehlende_heightmap(self, client):
        rv = client.post("/api/heightmap/wrap-relief/pruefen", json={"werkstueck_radius_mm": 10})
        assert rv.status_code == 400


class TestWrapReliefGenerieren:
    def test_basis_aufruf(self, client):
        hm_payload = _heightmap_payload_aus_bild(
            client, np.array([[0, 128, 255]], dtype=np.uint8), max_tiefe=1.0)
        rv = client.post("/api/heightmap/wrap-relief",
            json={
                "heightmap": hm_payload,
                "werkzeug_id": "kugel_3mm_2s_hm",
                "spindel_rpm": 18000, "vorschub": 600, "eintauch_vorschub": 200,
                "werkstueck_radius_mm": 20.0,
                "strategie": "raster_x",
            })
        # Wenn Werkzeug nicht in der DB, gibts 404
        if rv.status_code == 404:
            pytest.skip("kugel_3mm_2s_hm nicht in Default-Werkzeug-Bibliothek")
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["operation_typ"] == "relief"
        assert body["metadaten"]["ist_wrap"] is True
        assert body["metadaten"]["werkstueck_radius_mm"] == 20.0
        assert len(body["bewegungen"]) > 0
        # Erste Bewegung sollte auf Sicherheitshoehe (R + 5)
        assert body["bewegungen"][0]["z"] == pytest.approx(25.0)

    def test_radius_null_blockiert(self, client):
        hm_payload = _heightmap_payload_aus_bild(
            client, np.array([[128]], dtype=np.uint8))
        rv = client.post("/api/heightmap/wrap-relief",
            json={
                "heightmap": hm_payload,
                "werkzeug_id": "kugel_3mm_2s_hm",
                "spindel_rpm": 18000, "vorschub": 600, "eintauch_vorschub": 200,
                "werkstueck_radius_mm": 0,
            })
        # 404 wenn Werkzeug fehlt, sonst 422 wegen Radius
        if rv.status_code == 404:
            pytest.skip("kugel_3mm_2s_hm nicht in Default-Werkzeug-Bibliothek")
        assert rv.status_code == 422

    def test_unbekanntes_werkzeug(self, client):
        hm_payload = _heightmap_payload_aus_bild(
            client, np.array([[128]], dtype=np.uint8))
        rv = client.post("/api/heightmap/wrap-relief",
            json={
                "heightmap": hm_payload,
                "werkzeug_id": "gibts_nicht",
                "spindel_rpm": 18000, "vorschub": 600, "eintauch_vorschub": 200,
                "werkstueck_radius_mm": 20,
            })
        assert rv.status_code == 404

    def test_bearbeitung_gamma(self, client):
        hm_payload = _heightmap_payload_aus_bild(
            client, np.array([[0, 128, 255]], dtype=np.uint8), max_tiefe=1.0)
        rv = client.post("/api/heightmap/bearbeitung/gamma",
            json={"heightmap": hm_payload, "gamma": 2.0})
        assert rv.status_code == 200
        body = rv.get_json()
        # Antwort ist eine neue Heightmap
        assert "z_values_base64" in body
        assert "shape" in body

    def test_bearbeitung_zero_plane(self, client):
        hm_payload = _heightmap_payload_aus_bild(
            client, np.array([[0, 128, 255]], dtype=np.uint8), max_tiefe=1.0)
        rv = client.post("/api/heightmap/bearbeitung/zero-plane",
            json={"heightmap": hm_payload, "schwelle": 0.5})
        assert rv.status_code == 200
        # Helle Pixel muessen Z=0 sein → max Z = 0
        body = rv.get_json()
        z_max = body["statistik"]["z_max"]
        assert z_max == pytest.approx(0.0, abs=0.01)

    def test_bearbeitung_histogramm(self, client):
        hm_payload = _heightmap_payload_aus_bild(
            client, np.array([[100, 128, 150]], dtype=np.uint8), max_tiefe=1.0)
        rv = client.post("/api/heightmap/bearbeitung/histogramm-stretch",
            json={"heightmap": hm_payload})
        assert rv.status_code == 200

    def test_bearbeitung_edge_boost(self, client):
        hm_payload = _heightmap_payload_aus_bild(
            client, np.array(
                [[0, 0, 255, 255], [0, 0, 255, 255], [0, 0, 255, 255]],
                dtype=np.uint8), max_tiefe=1.0)
        rv = client.post("/api/heightmap/bearbeitung/edge-boost",
            json={"heightmap": hm_payload, "faktor": 0.5})
        assert rv.status_code == 200

    def test_bearbeitung_selective_smoothing(self, client):
        hm_payload = _heightmap_payload_aus_bild(
            client, np.full((5, 5), 128, dtype=np.uint8), max_tiefe=1.0)
        rv = client.post("/api/heightmap/bearbeitung/selective-smoothing",
            json={"heightmap": hm_payload, "radius": 1, "bereich": "alles"})
        assert rv.status_code == 200

    def test_bearbeitung_detail_slider(self, client):
        hm_payload = _heightmap_payload_aus_bild(
            client, np.array([[0, 128, 255]], dtype=np.uint8), max_tiefe=1.0)
        rv = client.post("/api/heightmap/bearbeitung/detail-slider",
            json={"heightmap": hm_payload, "detail": -0.5})
        assert rv.status_code == 200

    def test_bearbeitung_fehlerhafter_parameter(self, client):
        hm_payload = _heightmap_payload_aus_bild(
            client, np.array([[128]], dtype=np.uint8))
        rv = client.post("/api/heightmap/bearbeitung/gamma",
            json={"heightmap": hm_payload, "gamma": -1.0})
        assert rv.status_code == 422

    def test_bearbeitung_ohne_heightmap(self, client):
        rv = client.post("/api/heightmap/bearbeitung/gamma",
            json={"gamma": 1.5})
        assert rv.status_code == 400

    def test_ungueltige_strategie(self, client):
        hm_payload = _heightmap_payload_aus_bild(
            client, np.array([[128]], dtype=np.uint8))
        rv = client.post("/api/heightmap/wrap-relief",
            json={
                "heightmap": hm_payload,
                "werkzeug_id": "kugel_3mm_2s_hm",
                "spindel_rpm": 18000, "vorschub": 600, "eintauch_vorschub": 200,
                "werkstueck_radius_mm": 20,
                "strategie": "kompletter_unsinn",
            })
        assert rv.status_code == 400
