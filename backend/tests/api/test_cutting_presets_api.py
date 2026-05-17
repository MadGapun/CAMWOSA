"""API-Tests fuer CuttingPresets-Endpoints."""

from __future__ import annotations

import pytest

from camwosa.api import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


class TestListeUndDetails:
    def test_liste(self, client):
        rv = client.get("/api/cutting-presets/")
        assert rv.status_code == 200
        items = rv.get_json()
        assert isinstance(items, list)
        # Mindestens die Schruppen/Schlichten-Defaults sind drin
        ids = {p["id"] for p in items}
        assert "buche__schaft_6mm_2s_hm__schruppen" in ids
        assert "buche__schaft_6mm_2s_hm__schlichten" in ids

    def test_filter_material(self, client):
        rv = client.get("/api/cutting-presets/?material_id=buche_massiv")
        assert rv.status_code == 200
        items = rv.get_json()
        assert all(p["material_id"] == "buche_massiv" for p in items)

    def test_filter_operation_typ(self, client):
        rv = client.get("/api/cutting-presets/?operation_typ=schlichten")
        assert rv.status_code == 200
        items = rv.get_json()
        assert all(p["operation_typ"] == "schlichten" for p in items)

    def test_filter_invalid_operation_typ(self, client):
        rv = client.get("/api/cutting-presets/?operation_typ=quatsch")
        assert rv.status_code == 422

    def test_details_existiert(self, client):
        rv = client.get("/api/cutting-presets/buche__schaft_6mm_2s_hm__schlichten")
        assert rv.status_code == 200
        assert rv.get_json()["rpm"] == 20000

    def test_details_404(self, client):
        rv = client.get("/api/cutting-presets/gibts-nicht")
        assert rv.status_code == 404


class TestLookup:
    def test_lookup_exakt(self, client):
        rv = client.post("/api/cutting-presets/lookup", json={
            "material_id": "buche_massiv",
            "werkzeug_id": "schaft_6mm_2s_hm",
            "operation_typ": "schlichten",
        })
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["gefunden"]
        assert body["preset"]["rpm"] == 20000

    def test_lookup_fallback_auf_generic(self, client):
        # Wir fragen "bohren" — gibt's nicht; soll auf GENERIC zurueckfallen
        rv = client.post("/api/cutting-presets/lookup", json={
            "material_id": "buche_massiv",
            "werkzeug_id": "schaft_6mm_2s_hm",
            "operation_typ": "bohren",
        })
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["gefunden"]
        # GENERIC entsteht aus Legacy-Migration mit rpm=18000
        assert body["preset"]["operation_typ"] == "generic"

    def test_lookup_pflichtfeld(self, client):
        rv = client.post("/api/cutting-presets/lookup", json={"material_id": "x"})
        assert rv.status_code == 422


class TestExportImport:
    def test_export(self, client):
        rv = client.get(
            "/api/cutting-presets/buche__schaft_6mm_2s_hm__schlichten/export"
        )
        assert rv.status_code == 200
        bundle = rv.get_json()
        assert bundle["typ"] == "camwosa.cutting_preset_bundle"
        assert bundle["preset"]["id"] == "buche__schaft_6mm_2s_hm__schlichten"

    def test_import_validiert(self, client):
        bundle = {
            "schema_version": 1,
            "typ": "camwosa.cutting_preset_bundle",
            "preset": {
                "id": "x__y__generic",
                "material_id": "x",
                "werkzeug_id": "y",
                "rpm": 1000, "vorschub": 100, "plunge": 50,
                "stepdown": 0.5, "stepover_prozent": 30,
            },
        }
        rv = client.post("/api/cutting-presets/import", json=bundle)
        assert rv.status_code == 200
        assert rv.get_json()["gueltig"]

    def test_import_falscher_typ(self, client):
        rv = client.post(
            "/api/cutting-presets/import",
            json={"typ": "anderer.bundle", "preset": {}},
        )
        assert rv.status_code == 422
