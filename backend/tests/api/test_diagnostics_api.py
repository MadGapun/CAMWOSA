"""API-Tests fuer /api/diagnostics."""

from __future__ import annotations

import pytest


class TestZGridEndpoint:
    def test_eben_ok_meldung(self, client):
        rv = client.post("/api/diagnostics/z-grid", json={
            "messpunkte": [
                {"x": 0, "y": 0, "z": 0.0},
                {"x": 50, "y": 0, "z": 0.01},
                {"x": 0, "y": 50, "z": -0.01},
                {"x": 50, "y": 50, "z": 0.0},
            ],
        })
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["befund"] == "eben_ok"
        assert "Werkstueck" in data["klartext"]

    def test_zu_wenig_punkte_422(self, client):
        rv = client.post("/api/diagnostics/z-grid", json={
            "messpunkte": [{"x": 0, "y": 0, "z": 0}, {"x": 1, "y": 1, "z": 1}],
        })
        assert rv.status_code == 422

    def test_neigung_erkennung(self, client):
        rv = client.post("/api/diagnostics/z-grid", json={
            "messpunkte": [
                {"x": x, "y": y, "z": 0.01 * x}
                for x in (0, 50, 100) for y in (0, 50, 100)
            ],
        })
        assert rv.status_code == 200
        data = rv.get_json()
        assert data["befund"] in ("starke_neigung", "leichte_neigung")
        assert data["neigung_grad"] > 0.1
