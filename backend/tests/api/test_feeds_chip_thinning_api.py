"""API-Test fuer /api/feeds/chip-thinning (Cluster J3)."""

from __future__ import annotations


class TestChipThinningAPI:
    def test_endpoint_faktor(self, client):
        rv = client.post("/api/feeds/chip-thinning", json={
            "stepover_mm": 0.6, "werkzeug_durchmesser_mm": 6.0,
        })
        assert rv.status_code == 200
        assert rv.get_json()["faktor"] > 1.0

    def test_endpoint_korrigierter_vorschub(self, client):
        rv = client.post("/api/feeds/chip-thinning", json={
            "stepover_mm": 0.6, "werkzeug_durchmesser_mm": 6.0, "vorschub_mm_min": 1000,
        })
        assert rv.status_code == 200
        assert rv.get_json()["vorschub_korrigiert"] > 1000

    def test_endpoint_voll_eingriff_faktor_eins(self, client):
        rv = client.post("/api/feeds/chip-thinning", json={
            "stepover_mm": 4.0, "werkzeug_durchmesser_mm": 6.0,
        })
        assert rv.status_code == 200
        assert rv.get_json()["faktor"] == 1.0

    def test_endpoint_fehlende_felder(self, client):
        rv = client.post("/api/feeds/chip-thinning", json={"stepover_mm": 1.0})
        assert rv.status_code == 422
