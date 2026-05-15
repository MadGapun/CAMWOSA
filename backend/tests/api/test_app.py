"""Tests fuer die Flask-API."""

from __future__ import annotations

import pytest

from camwosa.api import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


class TestHealth:
    def test_health(self, client) -> None:
        rv = client.get("/health")
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["status"] == "ok"
        assert "version" in data


class TestMaschinen:
    def test_liste(self, client) -> None:
        rv = client.get("/api/machines/")
        assert rv.status_code == 200
        items = rv.get_json()
        assert any(m["id"] == "genmitsu_proverxl_4030_v2" for m in items)

    def test_details(self, client) -> None:
        rv = client.get("/api/machines/genmitsu_proverxl_4030_v2")
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["controller"] == "GRBL"

    def test_unbekannt_404(self, client) -> None:
        rv = client.get("/api/machines/xxx")
        assert rv.status_code == 404


class TestWerkzeuge:
    def test_liste(self, client) -> None:
        rv = client.get("/api/tools/")
        items = rv.get_json()
        assert any(t["id"] == "schaft_6mm_2s_hm" for t in items)


class TestMaterialien:
    def test_liste(self, client) -> None:
        rv = client.get("/api/materials/")
        items = rv.get_json()
        assert any(m["id"] == "buche_massiv" for m in items)


class TestFeedsSpeeds:
    def test_berechnung_buche(self, client) -> None:
        rv = client.post("/api/feeds/berechnen", json={
            "maschine_id": "genmitsu_proverxl_4030_v2",
            "werkzeug_id": "schaft_6mm_2s_hm",
            "material_id": "buche_massiv",
        })
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["rpm"] == 18000
        assert data["vorschub"] == 2000
        assert data["quelle"] == "preset"


class TestPostprozessoren:
    def test_liste_enthaelt_grbl(self, client) -> None:
        rv = client.get("/api/postprocessors/")
        items = rv.get_json()
        ids = [p["id"] for p in items]
        assert "grbl_standard" in ids
        assert "grbl_genmitsu" in ids
        assert "grbl_genmitsu_rotary_y" in ids


class TestNesting:
    def test_lotus_schalen(self, client) -> None:
        rv = client.post("/api/nesting/run", json={
            "teile": [{"id": "rohling", "breite": 130, "hoehe": 130, "anzahl": 4}],
            "platten": [{"id": "buche", "breite": 600, "hoehe": 400}],
        })
        assert rv.status_code == 200
        data = rv.get_json()
        assert len(data["platzierungen"]) == 4
