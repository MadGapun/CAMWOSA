"""API-Tests fuer Projekt-Persistenz (Master-Plan D4 Backend-Round-Trip)."""

from __future__ import annotations

from io import BytesIO

import pytest

from camwosa.api import create_app
from camwosa.db.loader import lade_maschinen


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _erste_maschine_id() -> str:
    return lade_maschinen()[0].id


class TestProjektNeu:
    def test_neues_projekt_ok(self, client):
        rv = client.post("/api/projects/new", json={
            "name": "Mein Test",
            "maschine_id": _erste_maschine_id(),
            "rohmaterial": {
                "form": "platte", "laenge": 200, "breite": 200,
                "hoehe": 12, "material_id": "buche_massiv",
            },
        })
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["metadaten"]["name"] == "Mein Test"
        assert len(body["varianten"]) == 1
        assert body["varianten"][0]["id"] == "default"

    def test_unbekannte_maschine_404(self, client):
        rv = client.post("/api/projects/new", json={
            "name": "X", "maschine_id": "gibts_nicht",
            "rohmaterial": {"form": "platte", "laenge": 100, "breite": 100,
                            "hoehe": 10, "material_id": "buche_massiv"},
        })
        assert rv.status_code == 404


class TestRoundTrip:
    def test_neu_speichern_laden(self, client):
        # Neues Projekt
        rv = client.post("/api/projects/new", json={
            "name": "RoundTrip Test",
            "maschine_id": _erste_maschine_id(),
            "rohmaterial": {"form": "platte", "laenge": 300, "breite": 200,
                            "hoehe": 18, "material_id": "buche_massiv"},
        })
        assert rv.status_code == 200
        projekt = rv.get_json()

        # Speichern → Blob
        rv = client.post("/api/projects/save", json=projekt)
        assert rv.status_code == 200
        assert rv.content_type.startswith("application/zip")
        cwp_bytes = rv.data
        assert len(cwp_bytes) > 100

        # Laden via multipart/form-data
        rv = client.post("/api/projects/load",
            data={"datei": (BytesIO(cwp_bytes), "test.cwp")},
            content_type="multipart/form-data",
        )
        assert rv.status_code == 200
        geladen = rv.get_json()
        assert geladen["metadaten"]["name"] == "RoundTrip Test"
        assert geladen["maschine"]["id"] == _erste_maschine_id()
        assert len(geladen["varianten"]) == 1

    def test_load_ohne_datei_400(self, client):
        rv = client.post("/api/projects/load", data={})
        assert rv.status_code == 400

    def test_load_kaputte_datei_422(self, client):
        rv = client.post("/api/projects/load",
            data={"datei": (BytesIO(b"das ist kein zip"), "x.cwp")},
            content_type="multipart/form-data",
        )
        assert rv.status_code == 422
