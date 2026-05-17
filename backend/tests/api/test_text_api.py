"""API-Tests fuer Text-zu-Pfad-Endpoints (Master-Plan A37)."""

from __future__ import annotations

from pathlib import Path

import pytest

from camwosa.api import create_app
from camwosa.cad.text_zu_pfad import FONT_FALLBACK

HAT_FONT = any(Path(p).is_file() for p in FONT_FALLBACK)


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.mark.skipif(not HAT_FONT, reason="Kein TTF im System verfuegbar")
class TestTextZuPfad:
    def test_einfacher_text(self, client):
        rv = client.post("/api/text/zu-pfad",
            json={"text": "X", "hoehe_mm": 10.0})
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["anzahl_polygone"] >= 1
        assert len(body["polygone"]) >= 1
        assert "exterior" in body["polygone"][0]

    def test_o_hat_loecher(self, client):
        rv = client.post("/api/text/zu-pfad", json={"text": "O", "hoehe_mm": 10.0})
        assert rv.status_code == 200
        body = rv.get_json()
        # Mindestens eines der Polygone hat ein Loch
        hat_loch = any(len(p["loecher"]) >= 1 for p in body["polygone"])
        assert hat_loch

    def test_bounding_box(self, client):
        rv = client.post("/api/text/zu-pfad", json={"text": "AB", "hoehe_mm": 8.0})
        body = rv.get_json()
        bbox = body["bounding_box"]
        # Hoehe ungefaehr 8mm
        assert (bbox[3] - bbox[1]) == pytest.approx(8.0, rel=0.2)

    def test_leerer_text_400(self, client):
        rv = client.post("/api/text/zu-pfad", json={"text": ""})
        assert rv.status_code == 400

    def test_falscher_font_pfad_422(self, client):
        rv = client.post("/api/text/zu-pfad",
            json={"text": "A", "font_pfad": "C:/quatsch/nix.ttf"})
        assert rv.status_code == 422

    def test_punktlisten_endpoint(self, client):
        rv = client.post("/api/text/zu-pfad/punktlisten",
            json={"text": "X", "hoehe_mm": 10.0})
        assert rv.status_code == 200
        body = rv.get_json()
        assert "punktlisten" in body
        assert len(body["punktlisten"]) >= 1
        # Jede Punktliste besteht aus [x, y]-Listen
        for liste in body["punktlisten"]:
            assert len(liste) >= 3
            assert len(liste[0]) == 2
