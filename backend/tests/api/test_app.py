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
        # Liste sollte Spindel-Anreicherung haben
        proverxl = next(m for m in items if m["id"] == "genmitsu_proverxl_4030_v2")
        assert proverxl["_aktive_spindel"] is not None

    def test_details(self, client) -> None:
        rv = client.get("/api/machines/genmitsu_proverxl_4030_v2")
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["controller"] == "GRBL"
        assert data["_aktive_spindel"]["id"] == "spindle_1500w_aircooled_vfd"
        assert len(data["_verfuegbare_spindeln"]) == 4

    def test_unbekannt_404(self, client) -> None:
        rv = client.get("/api/machines/xxx")
        assert rv.status_code == 404

    def test_export_bundle(self, client) -> None:
        rv = client.get("/api/machines/genmitsu_proverxl_4030_v2/export")
        assert rv.status_code == 200
        bundle = rv.get_json()
        assert bundle["typ"] == "camwosa.machine_bundle"
        assert bundle["maschine"]["id"] == "genmitsu_proverxl_4030_v2"
        ids = {s["id"] for s in bundle["spindeln"]}
        assert "makita_rt0700" in ids
        assert "genmitsu_router_710w" in ids

    def test_import_bundle_roundtrip(self, client) -> None:
        rv = client.get("/api/machines/genmitsu_proverxl_4030_v2/export")
        bundle = rv.get_json()
        rv2 = client.post("/api/machines/import", json=bundle)
        assert rv2.status_code == 200
        data = rv2.get_json()
        assert data["gueltig"] is True
        assert data["maschine"]["id"] == "genmitsu_proverxl_4030_v2"

    def test_import_bundle_inkonsistent(self, client) -> None:
        bundle = {
            "schema_version": 1,
            "typ": "camwosa.machine_bundle",
            "maschine": {
                "id": "x", "name": "X", "hersteller": "X", "modell": "X",
                "controller": "GRBL",
                "arbeitsraum": {"x": 100, "y": 100, "z": 100},
                "max_vorschub": 1000, "sicherer_vorschub": 500, "eilgang": 2000,
                "spindel_ids": ["fehlende_spindel"],
            },
            "spindeln": [],
        }
        rv = client.post("/api/machines/import", json=bundle)
        assert rv.status_code == 422
        assert "inkonsistent" in rv.get_json()["fehler"]


class TestSpindeln:
    def test_liste(self, client) -> None:
        rv = client.get("/api/spindles/")
        assert rv.status_code == 200
        items = rv.get_json()
        ids = {s["id"] for s in items}
        assert "makita_rt0700" in ids
        assert "watercool_2_2kw_24k" in ids

    def test_details(self, client) -> None:
        rv = client.get("/api/spindles/makita_rt0700")
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["hersteller"] == "Makita"
        assert data["rpm_max"] == 30000


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


class TestAufloesen:
    def test_kontur_preset_quelle(self, client) -> None:
        rv = client.post("/api/operations/aufloesen", json={
            "typ": "kontur",
            "material_id": "buche_massiv",
            "overrides": {"werkzeug_id": "schaft_6mm_2s_hm"},
        })
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["quellen"]["vorschub"] == "material_preset"

    def test_kontur_override(self, client) -> None:
        rv = client.post("/api/operations/aufloesen", json={
            "typ": "kontur",
            "material_id": "buche_massiv",
            "overrides": {
                "werkzeug_id": "schaft_6mm_2s_hm",
                "vorschub": 999,
            },
        })
        data = rv.get_json()
        assert data["parameter"]["vorschub"] == 999
        assert data["quellen"]["vorschub"] == "override"

    def test_unbekanntes_material(self, client) -> None:
        rv = client.post("/api/operations/aufloesen", json={
            "typ": "kontur",
            "material_id": "exotisches_unobtainium",
            "overrides": {"werkzeug_id": "schaft_6mm_2s_hm"},
        })
        assert rv.status_code == 404


class TestWorkflow:
    def test_pruefen_blocker_bei_modus_wechsel(self, client) -> None:
        variante = {
            "id": "v1",
            "name": "Default",
            "rohmaterial": {
                "form": "platte",
                "laenge": 300, "breite": 200, "hoehe": 18,
                "material_id": "buche_massiv",
            },
            "setups": [
                {"id": "s1", "name": "A", "werkzeug_id": "schaft_6mm_2s_hm"},
                {"id": "s2", "name": "B", "werkzeug_id": "schaft_6mm_2s_hm",
                 "maschinen_modus": "rotary_y"},
            ],
        }
        rv = client.post("/api/workflow/pruefen", json={"variante": variante})
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["hat_blocker"] is True

    def test_arbeitsplan_markdown(self, client) -> None:
        variante = {
            "id": "v1",
            "name": "Default",
            "rohmaterial": {
                "form": "platte",
                "laenge": 300, "breite": 200, "hoehe": 18,
                "material_id": "buche_massiv",
            },
            "setups": [
                {"id": "s1", "name": "Rohling", "werkzeug_id": "schaft_6mm_2s_hm"},
            ],
        }
        rv = client.post("/api/workflow/arbeitsplan", json={
            "variante": variante,
            "projekt_name": "Test",
            "maschine_id": "genmitsu_proverxl_4030_v2",
            "format": "markdown",
        })
        assert rv.status_code == 200
        data = rv.get_json()
        assert "Test" in data["markdown"]
        assert "Rohling" in data["markdown"]
