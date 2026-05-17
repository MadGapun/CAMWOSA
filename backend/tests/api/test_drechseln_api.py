"""API-Tests fuer den Drechsel-Endpoint."""

from __future__ import annotations

import pytest

from camwosa.api import create_app
from camwosa.db.loader import lade_werkzeuge


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _werkzeug_id() -> str:
    return lade_werkzeuge()[0].id


class TestDrechselEndpoint:
    def test_erfolgreiche_drechsel_operation(self, client):
        rv = client.post("/api/operations/drechseln", json={
            "werkzeug_id": _werkzeug_id(),
            "parameter": {
                "werkzeug_id": _werkzeug_id(),
                "spindel_rpm": 10000,
                "vorschub": 300,
                "eintauch_vorschub": 150,
                "sicherheitshoehe": 5,
                "max_tiefe": 15,
                "stepdown": 1.5,
                "rohmaterial_radius_mm": 20,
                "aufmass_schlichten_mm": 0.3,
                "schlicht_zustellung_mm": 0.5,
                "drehzahl_werkstueck_upm": 300,
                "profil": [[0, 18], [100, 18]],
                "strategie": "schrupp_und_schlicht",
            },
        })
        assert rv.status_code == 200
        tp = rv.get_json()
        assert len(tp["bewegungen"]) > 5
        assert tp["metadaten"]["ist_drechseln"] is True

    def test_ungueltiges_werkzeug(self, client):
        rv = client.post("/api/operations/drechseln", json={
            "werkzeug_id": "gibts_nicht",
            "parameter": {
                "werkzeug_id": "x", "spindel_rpm": 10000, "vorschub": 300,
                "eintauch_vorschub": 150, "max_tiefe": 15, "stepdown": 1,
                "rohmaterial_radius_mm": 20, "profil": [[0, 18]],
            },
        })
        assert rv.status_code == 404

    def test_ungueltiges_profil(self, client):
        rv = client.post("/api/operations/drechseln", json={
            "werkzeug_id": _werkzeug_id(),
            "parameter": {
                "werkzeug_id": _werkzeug_id(),
                "spindel_rpm": 10000, "vorschub": 300,
                "eintauch_vorschub": 150, "max_tiefe": 15, "stepdown": 1,
                "rohmaterial_radius_mm": 5,
                "profil": [[0, 20]],  # Profil-Radius > Rohmaterial
            },
        })
        assert rv.status_code == 422

    def test_leeres_profil_raises(self, client):
        rv = client.post("/api/operations/drechseln", json={
            "werkzeug_id": _werkzeug_id(),
            "parameter": {
                "werkzeug_id": _werkzeug_id(),
                "spindel_rpm": 10000, "vorschub": 300,
                "eintauch_vorschub": 150, "max_tiefe": 15, "stepdown": 1,
                "rohmaterial_radius_mm": 20,
                "profil": [],
            },
        })
        assert rv.status_code == 422
