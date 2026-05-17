"""End-to-End-Tests fuer CRUD auf Stammdaten (Werkzeuge, Materialien, Spindeln)."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

from camwosa.api import create_app


@pytest.fixture
def isolierte_daten(tmp_path, monkeypatch):
    """Kopiert ../data nach tmp_path und biegt CAMWOSA_DATA_DIR um."""
    repo_data = Path(__file__).resolve().parents[3] / "data"
    ziel = tmp_path / "data"
    shutil.copytree(repo_data, ziel)
    monkeypatch.setenv("CAMWOSA_DATA_DIR", str(ziel))
    return ziel


@pytest.fixture
def client(isolierte_daten):
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ---------------------------------------------------------------------------
# Werkzeuge
# ---------------------------------------------------------------------------


class TestWerkzeugCRUD:
    NEU = {
        "id": "user_neuer_fraeser_1mm",
        "name": "User-Override 1mm",
        "typ": "schaftfraeser",
        "durchmesser": 1.0,
        "schaft_durchmesser": 3.175,
        "schneidlaenge": 5.0,
        "gesamtlaenge": 38.0,
        "schneiden": 2,
    }

    def test_anlegen(self, client, isolierte_daten):
        rv = client.post("/api/tools/", json=self.NEU)
        assert rv.status_code == 201
        assert (isolierte_daten / "tools" / "user_neuer_fraeser_1mm.json").exists()
        # Liste enthaelt das neue Tool
        liste = client.get("/api/tools/").get_json()
        assert any(t["id"] == "user_neuer_fraeser_1mm" for t in liste)

    def test_aktualisieren(self, client, isolierte_daten):
        client.post("/api/tools/", json=self.NEU)
        upd = {**self.NEU, "name": "Geaendert"}
        rv = client.put("/api/tools/user_neuer_fraeser_1mm", json=upd)
        assert rv.status_code == 200
        gespeichert = json.loads(
            (isolierte_daten / "tools" / "user_neuer_fraeser_1mm.json").read_text(encoding="utf-8")
        )
        assert gespeichert["name"] == "Geaendert"

    def test_loeschen_user_eintrag(self, client, isolierte_daten):
        client.post("/api/tools/", json=self.NEU)
        rv = client.delete("/api/tools/user_neuer_fraeser_1mm")
        assert rv.status_code == 200
        assert not (
            isolierte_daten / "tools" / "user_neuer_fraeser_1mm.json"
        ).exists()

    def test_loeschen_default_geht_nicht(self, client):
        # standard.json enthaelt Defaults — die koennen nicht geloescht werden
        liste = client.get("/api/tools/").get_json()
        assert liste, "Es sollten Default-Werkzeuge geladen sein"
        default_id = liste[0]["id"]
        rv = client.delete(f"/api/tools/{default_id}")
        assert rv.status_code == 409

    def test_validierung_bei_anlegen(self, client):
        rv = client.post("/api/tools/", json={"id": "ungueltig"})
        assert rv.status_code == 422

    def test_override_gewinnt_im_loader(self, client, isolierte_daten):
        # Wir ueberschreiben ein Default-Werkzeug per ID
        liste = client.get("/api/tools/").get_json()
        default_id = liste[0]["id"]
        original = liste[0]
        override = {**original, "name": "OVERRIDDEN"}
        client.put(f"/api/tools/{default_id}", json=override)

        liste2 = client.get("/api/tools/").get_json()
        treffer = [t for t in liste2 if t["id"] == default_id]
        assert len(treffer) == 1
        assert treffer[0]["name"] == "OVERRIDDEN"


# ---------------------------------------------------------------------------
# Materialien
# ---------------------------------------------------------------------------


class TestMaterialCRUD:
    NEU = {
        "id": "user_mdf_22",
        "name": "MDF 22mm (User)",
        "kategorie": "holzwerkstoff",
    }

    def test_anlegen_aktualisieren_loeschen(self, client, isolierte_daten):
        rv = client.post("/api/materials/", json=self.NEU)
        assert rv.status_code == 201

        rv2 = client.put("/api/materials/user_mdf_22", json={
            **self.NEU, "name": "MDF 22mm v2",
        })
        assert rv2.status_code == 200

        rv3 = client.delete("/api/materials/user_mdf_22")
        assert rv3.status_code == 200

    def test_default_loeschen_409(self, client):
        liste = client.get("/api/materials/").get_json()
        assert liste
        rv = client.delete(f"/api/materials/{liste[0]['id']}")
        assert rv.status_code == 409


# ---------------------------------------------------------------------------
# Spindeln
# ---------------------------------------------------------------------------


class TestSpindelCRUD:
    NEU = {
        "id": "user_test_spindel",
        "name": "Test-Spindel",
        "hersteller": "Test",
        "modell": "X",
        "typ": "manuell",
        "rpm_min": 5000,
        "rpm_max": 25000,
    }

    def test_anlegen_und_loeschen(self, client, isolierte_daten):
        rv = client.post("/api/spindles/", json=self.NEU)
        assert rv.status_code == 201
        rv2 = client.delete("/api/spindles/user_test_spindel")
        assert rv2.status_code == 200

    def test_validierung_rpm_range(self, client):
        rv = client.post("/api/spindles/", json={
            **self.NEU, "rpm_min": 30000, "rpm_max": 25000,
        })
        assert rv.status_code == 422


# ---------------------------------------------------------------------------
# Maschinen (Issue #22 — First-Run-Wizard inline-Anlegen)
# ---------------------------------------------------------------------------


class TestMaschineCRUD:
    NEU = {
        "id": "user_test_maschine",
        "name": "Testmaschine",
        "hersteller": "Test",
        "modell": "X",
        "controller": "GRBL",
        "arbeitsraum": {"x": 300, "y": 200, "z": 80},
        "max_vorschub": 2000,
        "sicherer_vorschub": 1500,
        "eilgang": 3000,
        "spindel_ids": [],
        "spindel_typ": "manuell",
        "spindel_rpm_min": 10000,
        "spindel_rpm_max": 30000,
        "sicherheitshoehe": 5.0,
        "postprozessor": "grbl_genmitsu_pvxl",
        "modi": ["standard_xyz"],
        "aktiver_modus": "standard_xyz",
    }

    def test_anlegen_und_loeschen(self, client, isolierte_daten):
        rv = client.post("/api/machines/", json=self.NEU)
        assert rv.status_code == 201, rv.get_json()
        gespeichert = rv.get_json()
        assert gespeichert["maschine"]["id"] == "user_test_maschine"

        rv2 = client.get("/api/machines/user_test_maschine")
        assert rv2.status_code == 200

        rv3 = client.delete("/api/machines/user_test_maschine")
        assert rv3.status_code == 200

    def test_aktualisieren(self, client, isolierte_daten):
        client.post("/api/machines/", json=self.NEU)
        rv = client.put("/api/machines/user_test_maschine", json={
            **self.NEU, "name": "Geaendert",
        })
        assert rv.status_code == 200
        assert rv.get_json()["maschine"]["name"] == "Geaendert"
        client.delete("/api/machines/user_test_maschine")

    def test_validierungsfehler_422(self, client):
        rv = client.post("/api/machines/", json={"name": "unvollstaendig"})
        assert rv.status_code == 422


# ---------------------------------------------------------------------------
# Smart-Helper-Endpoints
# ---------------------------------------------------------------------------


class TestSmartHelpers:
    def test_v_bit_spitzendurchmesser_60grad_voll(self, client):
        rv = client.post("/api/tools/helper/v-bit-spitzendurchmesser", json={
            "spitzenwinkel_grad": 60,
            "schneidlaenge_mm": 10,
            "durchmesser_max_mm": 12,
        })
        assert rv.status_code == 200
        # 2*tan(30deg)*10 ~ 11.547 < 12 -> Spitze ist 0
        assert rv.get_json()["spitzendurchmesser_mm"] == 0.0

    def test_v_bit_winkel_aus_gravurstichel(self, client):
        rv = client.post("/api/tools/helper/v-bit-winkel", json={
            "spitzendurchmesser_mm": 0.3,
            "durchmesser_max_mm": 3.175,
            "schneidlaenge_mm": 6.0,
        })
        assert rv.status_code == 200
        # Sollte ein plausibler Winkel um die 27 Grad sein
        winkel = rv.get_json()["spitzenwinkel_grad"]
        assert 20 < winkel < 35

    def test_helper_validiert_eingaben(self, client):
        rv = client.post("/api/tools/helper/v-bit-winkel", json={"foo": "bar"})
        assert rv.status_code == 422
