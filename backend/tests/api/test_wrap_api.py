"""API-Tests fuer Wrap-Mode."""

from __future__ import annotations

import math

import pytest

from camwosa.api import create_app
from camwosa.db.loader import lade_werkzeuge


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _werkzeug() -> str:
    return lade_werkzeuge()[0].id


class TestWrapEndpoint:
    def test_erfolgreicher_wrap(self, client):
        rv = client.post("/api/operations/wrap", json={
            "werkzeug_id": _werkzeug(),
            "punkte_xy": [[0, 0], [50, 0], [50, 20], [0, 20]],
            "parameter": {
                "werkzeug_id": _werkzeug(),
                "spindel_rpm": 18000,
                "vorschub": 600,
                "eintauch_vorschub": 200,
                "werkstueck_radius_mm": 25.0,
                "max_tiefe": 0.5,
                "stepdown": 0.5,
            },
        })
        assert rv.status_code == 200
        tp = rv.get_json()
        assert tp["metadaten"]["ist_wrap"] is True
        # Erstes linear-Bewegung bei Y=0 → A=0°
        linears = [b for b in tp["bewegungen"] if b["typ"] == "linear"]
        assert len(linears) > 0

    def test_unbekanntes_werkzeug(self, client):
        rv = client.post("/api/operations/wrap", json={
            "werkzeug_id": "gibts_nicht",
            "punkte_xy": [[0, 0], [10, 10]],
            "parameter": {
                "werkzeug_id": "x", "spindel_rpm": 18000,
                "vorschub": 600, "eintauch_vorschub": 200,
                "werkstueck_radius_mm": 20, "max_tiefe": 1,
            },
        })
        assert rv.status_code == 404

    def test_leere_punkte_raises_oder_warnt(self, client):
        rv = client.post("/api/operations/wrap", json={
            "werkzeug_id": _werkzeug(),
            "punkte_xy": [],
            "parameter": {
                "werkzeug_id": _werkzeug(),
                "spindel_rpm": 18000, "vorschub": 600, "eintauch_vorschub": 200,
                "werkstueck_radius_mm": 20, "max_tiefe": 1,
            },
        })
        assert rv.status_code == 422

    def test_pruefe_endpoint(self, client):
        rv = client.post("/api/operations/wrap/pruefe", json={
            "punkte_xy": [[0, 0], [10, 200]],   # Y=200 > Umfang(20)=125
            "werkstueck_radius_mm": 20,
        })
        assert rv.status_code == 200
        body = rv.get_json()
        assert not body["gueltig"]
        assert any("wickelt sich mehrfach" in w for w in body["warnungen"])

    def test_y_zu_a_in_bewegung(self, client):
        """Bei Y=π·R sollte A=180° im Output stehen."""
        r = 20.0
        halber_umfang = math.pi * r
        rv = client.post("/api/operations/wrap", json={
            "werkzeug_id": _werkzeug(),
            "punkte_xy": [[0, 0], [0, halber_umfang]],
            "parameter": {
                "werkzeug_id": _werkzeug(),
                "spindel_rpm": 18000, "vorschub": 600, "eintauch_vorschub": 200,
                "werkstueck_radius_mm": r, "max_tiefe": 0.5,
            },
        })
        tp = rv.get_json()
        linears = [b for b in tp["bewegungen"] if b["typ"] == "linear"]
        # Letzter Linear hat Y ≈ 180°
        assert abs(linears[-1]["y"] - 180.0) < 0.01


# ---------------------------------------------------------------------------
# Pattern-Skalierung — Master-Plan A38
# ---------------------------------------------------------------------------


class TestPatternSkalieren:
    def test_einfaches_quadrat_auf_werkstueck(self, client):
        rv = client.post("/api/wrap/pattern-skalieren", json={
            "polygone": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
            "modus": "auf_werkstueck_anpassen",
            "werkstueck_radius_mm": 10,
        })
        assert rv.status_code == 200
        body = rv.get_json()
        umfang = 2 * math.pi * 10
        assert body["metadaten"]["y_spanne_endgueltig_mm"] == pytest.approx(umfang, rel=0.001)

    def test_feste_skalierung(self, client):
        rv = client.post("/api/wrap/pattern-skalieren", json={
            "polygone": [[[0, 0], [10, 0], [10, 10], [0, 10]]],
            "modus": "feste_skalierung",
            "werkstueck_radius_mm": 20,
            "soll_breite_mm": 50,
        })
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["metadaten"]["skalierung_x"] == 5.0

    def test_wiederholen(self, client):
        rv = client.post("/api/wrap/pattern-skalieren", json={
            "polygone": [[[0, 0], [10, 0], [10, 10], [0, 10]]],
            "modus": "wiederholen",
            "werkstueck_radius_mm": 10,
        })
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["metadaten"]["anzahl_wiederholungen"] == 6
        assert len(body["polygone"]) == 6

    def test_unbekannter_modus_400(self, client):
        rv = client.post("/api/wrap/pattern-skalieren", json={
            "polygone": [[[0, 0], [10, 10]]],
            "modus": "unsinn",
            "werkstueck_radius_mm": 10,
        })
        assert rv.status_code == 400

    def test_fehlende_polygone_400(self, client):
        rv = client.post("/api/wrap/pattern-skalieren", json={
            "modus": "auf_werkstueck_anpassen",
            "werkstueck_radius_mm": 10,
        })
        assert rv.status_code == 400


class TestWrapToolpathBatch:
    def test_einfacher_toolpath(self, client):
        rv = client.post("/api/wrap/toolpath", json={
            "polygone": [[[0, 0], [10, 5], [10, 10], [0, 5]]],
            "werkzeug_id": _werkzeug(),
            "spindel_rpm": 18000, "vorschub": 600, "eintauch_vorschub": 200,
            "werkstueck_radius_mm": 20,
            "max_tiefe": 0.5, "stepdown": 0.5,
        })
        assert rv.status_code == 200
        body = rv.get_json()
        assert len(body["bewegungen"]) > 0
        assert body["anzahl_polygone"] == 1

    def test_unbekanntes_werkzeug_404(self, client):
        rv = client.post("/api/wrap/toolpath", json={
            "polygone": [[[0, 0], [10, 5]]],
            "werkzeug_id": "gibts_nicht",
            "spindel_rpm": 18000, "vorschub": 600, "eintauch_vorschub": 200,
            "werkstueck_radius_mm": 20,
        })
        assert rv.status_code == 404

    def test_leere_polygone_400(self, client):
        rv = client.post("/api/wrap/toolpath", json={
            "polygone": [],
            "werkzeug_id": _werkzeug(),
            "spindel_rpm": 18000, "vorschub": 600, "eintauch_vorschub": 200,
        })
        assert rv.status_code == 400

    def test_mehrere_polygone_kombiniert(self, client):
        rv = client.post("/api/wrap/toolpath", json={
            "polygone": [
                [[0, 0], [10, 0], [10, 5], [0, 5]],
                [[20, 0], [30, 0], [30, 5], [20, 5]],
            ],
            "werkzeug_id": _werkzeug(),
            "spindel_rpm": 18000, "vorschub": 600, "eintauch_vorschub": 200,
            "werkstueck_radius_mm": 20,
            "max_tiefe": 0.5, "stepdown": 0.5,
        })
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["anzahl_polygone"] == 2
        # Mindestens 2x Plunge fuer 2 Polygone
        plunges = [b for b in body["bewegungen"] if b["typ"] == "plunge"]
        assert len(plunges) >= 2
