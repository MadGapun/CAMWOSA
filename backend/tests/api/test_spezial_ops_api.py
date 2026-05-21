"""API-Tests fuer /api/spezial-ops."""

from __future__ import annotations

import pytest


@pytest.fixture
def drag_werkzeug_id(client, isolierte_daten):
    """Legt einen Drag-Gravierer im Werkzeug-Store an + gibt id zurueck."""
    rv = client.post("/api/tools/", json={
        "id": "user_drag_test", "name": "Diamantgravierer Test",
        "typ": "drag_gravierer",
        "durchmesser": 0.5, "schaft_durchmesser": 6.0,
        "schneidlaenge": 2.0, "gesamtlaenge": 40.0, "schneiden": 1,
    })
    assert rv.status_code == 201, rv.get_json()
    yield "user_drag_test"
    client.delete("/api/tools/user_drag_test")


@pytest.fixture
def fraeser_werkzeug_id(client, isolierte_daten):
    rv = client.post("/api/tools/", json={
        "id": "user_fraeser_test", "name": "Fraeser 3mm",
        "typ": "schaftfraeser",
        "durchmesser": 3.0, "schaft_durchmesser": 3.0,
        "schneidlaenge": 12.0, "gesamtlaenge": 30.0, "schneiden": 2,
    })
    assert rv.status_code == 201, rv.get_json()
    yield "user_fraeser_test"
    client.delete("/api/tools/user_fraeser_test")


class TestDragEngravingEndpoint:
    def test_einfache_linie(self, client, drag_werkzeug_id):
        rv = client.post("/api/spezial-ops/drag-engraving", json={
            "parameter": {
                "werkzeug_id": drag_werkzeug_id,
                "tiefe": 0.15,
            },
            "geometrie": {
                "typ": "linie", "layer": "0",
                "punkte": [[0, 0], [50, 0]],
                "geschlossen": False,
            },
        })
        assert rv.status_code == 200, rv.get_json()
        data = rv.get_json()
        assert data["spindel_rpm"] == 0.0
        assert data["metadaten"]["drag_engraving"] is True

    def test_falsches_werkzeug_422(self, client, fraeser_werkzeug_id):
        rv = client.post("/api/spezial-ops/drag-engraving", json={
            "parameter": {"werkzeug_id": fraeser_werkzeug_id},
            "geometrie": {
                "typ": "linie", "layer": "0",
                "punkte": [[0, 0], [10, 0]], "geschlossen": False,
            },
        })
        assert rv.status_code == 422
        assert "DRAG_GRAVIERER" in rv.get_json()["fehler"]


class TestAutoInlayEndpoint:
    def test_einfaches_rechteck(self, client):
        rv = client.post("/api/spezial-ops/auto-inlay", json={
            "parameter": {
                "spiel_mm": 0.1, "werkzeug_radius_mm": 1.0,
                "tasche_tiefe_mm": 3.0,
            },
            "geometrie": {
                "typ": "polylinie", "layer": "0",
                "punkte": [[0, 0], [50, 0], [50, 30], [0, 30]],
                "geschlossen": True,
            },
        })
        assert rv.status_code == 200, rv.get_json()
        data = rv.get_json()
        assert data["ergebnis"]["tasche_flaeche_mm2"] > 0
        assert data["ergebnis"]["plug_flaeche_mm2"] > 0
        assert data["tasche_geometrie"]["typ"] == "polylinie"
        assert data["plug_geometrie"]["geschlossen"] is True

    def test_offene_polylinie_422(self, client):
        rv = client.post("/api/spezial-ops/auto-inlay", json={
            "parameter": {"werkzeug_radius_mm": 1.0},
            "geometrie": {
                "typ": "linie", "layer": "0",
                "punkte": [[0, 0], [10, 0]], "geschlossen": False,
            },
        })
        assert rv.status_code == 422


class TestThreadMillingEndpoint:
    def test_m6_innengewinde(self, client, fraeser_werkzeug_id):
        rv = client.post("/api/spezial-ops/thread-milling", json={
            "parameter": {
                "werkzeug_id": fraeser_werkzeug_id,
                "spindel_rpm": 12000, "vorschub": 400, "eintauch_vorschub": 80,
                "nenn_durchmesser": 6.0, "gewinde_steigung": 1.0, "gewinde_tiefe": 8.0,
                "art": "innen",
            },
        })
        assert rv.status_code == 200, rv.get_json()
        data = rv.get_json()
        assert data["metadaten"]["thread_milling"] is True
        assert data["metadaten"]["anzahl_umdrehungen"] == 8.0


class TestCircularPocketPfade:
    def test_einfacher_kreis(self, client):
        rv = client.post("/api/spezial-ops/circular-pocket-pfade", json={
            "aussen_radius": 20, "werkzeug_durchmesser": 3, "stepover_prozent": 40,
        })
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["anzahl"] > 5


class TestRadialPocketPfade:
    def test_einfacher_radial(self, client):
        rv = client.post("/api/spezial-ops/radial-pocket-pfade", json={
            "aussen_radius": 15, "werkzeug_durchmesser": 3, "anzahl_speichen": 12,
        })
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["anzahl"] == 12


class TestPlanfraesen:
    def test_planfraesen(self, client, fraeser_werkzeug_id):
        rv = client.post("/api/spezial-ops/planfraesen", json={
            "parameter": {
                "werkzeug_id": fraeser_werkzeug_id,
                "spindel_rpm": 18000, "vorschub": 2000, "eintauch_vorschub": 600,
                "x_min": 0, "y_min": 0, "x_max": 100, "y_max": 80,
                "z_start": 0, "abtrag": 1.0, "maximaler_stepdown": 0.5,
            },
        })
        assert rv.status_code == 200, rv.get_json()
        data = rv.get_json()
        assert data["metadaten"]["strategie"] == "planfraesen"


class TestDreiDParallel:
    def _heightmap_payload(self):
        import base64
        import numpy as np
        z = np.zeros((20, 20), dtype="float32")
        return {
            "shape": [20, 20],
            "aufloesung": 1.0,
            "x_min": 0.0, "y_min": 0.0, "z_max": 0.0,
            "z_values_dtype": "float32",
            "z_values_base64": base64.b64encode(z.tobytes()).decode("ascii"),
        }

    def test_3d_parallel(self, client, isolierte_daten):
        # Kugelfraeser anlegen
        client.post("/api/tools/", json={
            "id": "user_kugel_test", "name": "Kugel 3mm",
            "typ": "kugelfraeser", "durchmesser": 3.0, "schaft_durchmesser": 3.0,
            "schneidlaenge": 12, "gesamtlaenge": 40, "schneiden": 2,
        })
        rv = client.post("/api/spezial-ops/3d-parallel", json={
            "parameter": {
                "werkzeug_id": "user_kugel_test",
                "spindel_rpm": 18000, "vorschub": 1500, "eintauch_vorschub": 400,
                "stepover_modus": "distanz", "stepover_distanz_mm": 2.0,
                "bahn_winkel_grad": 0, "aufmass_mm": 0, "toleranz_mm": 0.01,
            },
            "heightmap": self._heightmap_payload(),
        })
        assert rv.status_code == 200, rv.get_json()
        data = rv.get_json()
        assert data["metadaten"]["strategie"] == "3d_parallel"
        client.delete("/api/tools/user_kugel_test")

    def test_3d_parallel_fehlende_heightmap_422(self, client, fraeser_werkzeug_id):
        rv = client.post("/api/spezial-ops/3d-parallel", json={
            "parameter": {
                "werkzeug_id": fraeser_werkzeug_id,
                "spindel_rpm": 18000, "vorschub": 1500, "eintauch_vorschub": 400,
            },
        })
        assert rv.status_code == 422
