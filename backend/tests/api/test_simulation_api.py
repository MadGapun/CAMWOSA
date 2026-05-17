"""API-Tests fuer Voxel-Simulation."""

from __future__ import annotations

import pytest

from camwosa.api import create_app
from camwosa.db.loader import lade_werkzeuge


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _wz_id() -> str:
    return lade_werkzeuge()[0].id


def _einfacher_toolpath() -> dict:
    return {
        "operation_id": "op1",
        "operation_typ": "kontur",
        "werkzeug_id": _wz_id(),
        "spindel_rpm": 18000,
        "sicherheitshoehe": 5,
        "bewegungen": [
            {"typ": "eilgang", "x": 0, "y": 0, "z": 25},
            {"typ": "plunge", "x": 0, "y": 0, "z": 15, "feed": 400},
            {"typ": "linear", "x": 50, "y": 0, "z": 15, "feed": 2000},
        ],
    }


class TestVoxelEndpoint:
    def test_einfache_simulation(self, client):
        rv = client.post("/api/simulation/voxel", json={
            "werkzeug_id": _wz_id(),
            "toolpaths": [_einfacher_toolpath()],
            "werkstueck": {"laenge_x": 80, "breite_y": 40, "hoehe_z": 20},
            "aufloesung_mm": 2.0,
        })
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["abgetragenes_volumen_mm3"] > 0
        assert body["voxel_count"] > 0
        assert body["nx"] == 40 and body["ny"] == 20 and body["nz"] == 10

    def test_aufloesung_grenzen(self, client):
        rv = client.post("/api/simulation/voxel", json={
            "werkzeug_id": _wz_id(),
            "toolpaths": [_einfacher_toolpath()],
            "werkstueck": {"laenge_x": 50, "breite_y": 50, "hoehe_z": 20},
            "aufloesung_mm": 0.1,
        })
        assert rv.status_code == 422

    def test_unbekanntes_werkzeug(self, client):
        rv = client.post("/api/simulation/voxel", json={
            "werkzeug_id": "gibts_nicht",
            "toolpaths": [_einfacher_toolpath()],
            "werkstueck": {"laenge_x": 50, "breite_y": 50, "hoehe_z": 20},
        })
        assert rv.status_code == 404

    def test_kein_toolpath(self, client):
        rv = client.post("/api/simulation/voxel", json={
            "werkzeug_id": _wz_id(),
            "toolpaths": [],
            "werkstueck": {"laenge_x": 50, "breite_y": 50, "hoehe_z": 20},
        })
        assert rv.status_code == 422

    def test_multi_toolpath_summiert_abtrag(self, client):
        """Zweiter Toolpath traegt zusaetzlich Material ab, nicht das gleiche nochmal."""
        tp2 = _einfacher_toolpath()
        # Zweiter Pass an anderer Y-Position
        tp2["bewegungen"] = [
            {"typ": "eilgang", "x": 0, "y": 20, "z": 25},
            {"typ": "plunge", "x": 0, "y": 20, "z": 15, "feed": 400},
            {"typ": "linear", "x": 50, "y": 20, "z": 15, "feed": 2000},
        ]
        rv_single = client.post("/api/simulation/voxel", json={
            "werkzeug_id": _wz_id(),
            "toolpaths": [_einfacher_toolpath()],
            "werkstueck": {"laenge_x": 80, "breite_y": 40, "hoehe_z": 20},
            "aufloesung_mm": 2.0,
        })
        rv_multi = client.post("/api/simulation/voxel", json={
            "werkzeug_id": _wz_id(),
            "toolpaths": [_einfacher_toolpath(), tp2],
            "werkstueck": {"laenge_x": 80, "breite_y": 40, "hoehe_z": 20},
            "aufloesung_mm": 2.0,
        })
        assert rv_multi.get_json()["abgetragenes_volumen_mm3"] > rv_single.get_json()["abgetragenes_volumen_mm3"]
