"""API-Tests fuer Zeitschaetzung (K5) + Bitmap-Trace (L1)."""

from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw


def _toolpath_dict():
    return {
        "operation_id": "op", "operation_typ": "kontur", "werkzeug_id": "t1",
        "spindel_rpm": 12000, "sicherheitshoehe": 5, "kommentar": "", "metadaten": {},
        "bewegungen": [
            {"typ": "linear", "x": 0, "y": 0, "z": -1, "feed": 600},
            {"typ": "linear", "x": 600, "y": 0, "z": -1, "feed": 600},
        ],
    }


class TestZeitschaetzungAPI:
    def test_mit_eilgang(self, client):
        rv = client.post("/api/operations/zeitschaetzung", json={
            "toolpaths": [_toolpath_dict()],
            "eilgang_mm_min": 3000,
            "overhead_faktor": 1.0,
        })
        assert rv.status_code == 200, rv.get_json()
        data = rv.get_json()
        # 600mm @ 600 = 60s
        assert abs(data["schnitt_sekunden"] - 60.0) < 0.5
        assert "Min" in data["klartext"]

    def test_ohne_eilgang_und_maschine_422(self, client):
        rv = client.post("/api/operations/zeitschaetzung", json={
            "toolpaths": [_toolpath_dict()],
        })
        assert rv.status_code == 422

    def test_mit_maschine_id(self, client):
        # erste Default-Maschine nutzen
        maschinen = client.get("/api/machines/").get_json()
        assert maschinen
        rv = client.post("/api/operations/zeitschaetzung", json={
            "toolpaths": [_toolpath_dict()],
            "maschine_id": maschinen[0]["id"],
        })
        assert rv.status_code == 200
        assert rv.get_json()["gesamt_sekunden"] > 0


def _png_quadrat() -> bytes:
    img = Image.new("L", (100, 100), color=255)
    ImageDraw.Draw(img).rectangle([20, 20, 80, 80], fill=0)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestBitmapTraceAPI:
    def test_trace_quadrat(self, client):
        rv = client.post(
            "/api/cad/bitmap-trace",
            data={
                "datei": (BytesIO(_png_quadrat()), "logo.png"),
                "pixel_pro_mm": "4",
                "ziel_breite_mm": "50",
            },
            content_type="multipart/form-data",
        )
        assert rv.status_code == 200, rv.get_json()
        data = rv.get_json()
        assert data["anzahl"] == 1
        assert data["objekte"][0]["geschlossen"] is True
        assert data["objekte"][0]["typ"] == "polylinie"

    def test_leeres_bild_422(self, client):
        img = Image.new("L", (50, 50), color=255)
        buf = BytesIO()
        img.save(buf, format="PNG")
        rv = client.post(
            "/api/cad/bitmap-trace",
            data={"datei": (BytesIO(buf.getvalue()), "weiss.png")},
            content_type="multipart/form-data",
        )
        assert rv.status_code == 422

    def test_keine_datei_400(self, client):
        rv = client.post("/api/cad/bitmap-trace", data={},
                         content_type="multipart/form-data")
        assert rv.status_code == 400


class TestWerkzeugAutoNameAPI:
    def test_anzeigename_endpoint(self, client):
        rv = client.post("/api/tools/anzeigename", json={
            "typ": "schaftfraeser", "durchmesser": 6, "schaft_durchmesser": 6,
            "schneidlaenge": 12, "gesamtlaenge": 40, "schneiden": 2,
            "name_zusatz": "Test",
        })
        assert rv.status_code == 200, rv.get_json()
        data = rv.get_json()
        assert "Schaftfräser" in data["auto_name"]
        assert data["anzeigename"].endswith("(Test)")

    def test_tools_liste_hat_anzeigename(self, client):
        rv = client.get("/api/tools/")
        assert rv.status_code == 200
        tools = rv.get_json()
        assert tools and "_anzeigename" in tools[0]


class TestFahrwegPostprocess:
    def _tp_dict(self, werkzeug_id):
        # drei Bohrungen in schlechter Reihenfolge (0 → 100 → 10)
        def bohr(x):
            return [
                {"typ": "eilgang", "x": x, "y": 0, "z": 5},
                {"typ": "plunge", "x": x, "y": 0, "z": -3, "feed": 200},
                {"typ": "eilgang", "x": x, "y": 0, "z": 5},
            ]
        return {
            "operation_id": "op", "operation_typ": "bohren", "werkzeug_id": werkzeug_id,
            "spindel_rpm": 12000, "sicherheitshoehe": 5, "kommentar": "", "metadaten": {},
            "bewegungen": bohr(0) + bohr(100) + bohr(10),
        }

    def test_postprocess_mit_fahrweg_optimierung(self, client):
        maschinen = client.get("/api/machines/").get_json()
        tools = client.get("/api/tools/").get_json()
        rv = client.post("/api/operations/postprocess", json={
            "maschine_id": maschinen[0]["id"],
            "werkzeug_id": tools[0]["id"],
            "toolpaths": [self._tp_dict(tools[0]["id"])],
            "fahrweg_optimierung": True,
            "freifahrt_hoehe": 1.0,
        })
        assert rv.status_code == 200, rv.get_json()
        assert "gcode" in rv.get_json()
