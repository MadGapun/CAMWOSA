"""API-Tests fuer Rotary-Profil-CRUD (alles editierbar)."""

from __future__ import annotations


def _profil(pid="user_rotary_test"):
    return {
        "id": pid, "name": "Test-Rotary", "hersteller": "X", "modell": "Y",
        "spannfutter_backen_anzahl": 3,
        "spannfutter_max_durchmesser_mm": 80,
        "spannfutter_min_durchmesser_mm": 5,
        "hat_reitstock": False,
        "max_werkstueck_laenge_mm": 300,
        "durchschiebbar": True,
        "grbl_y_steps_pro_grad": 88.889,
        "grbl_y_limit_aufheben": True,
        "notizen": "",
    }


class TestRotaryCRUD:
    def test_anlegen_und_lesen(self, client):
        rv = client.post("/api/rotary/profile", json=_profil())
        assert rv.status_code == 201, rv.get_json()
        # taucht in der Liste auf
        ids = {p["id"] for p in client.get("/api/rotary/profile").get_json()}
        assert "user_rotary_test" in ids

    def test_aktualisieren(self, client):
        client.post("/api/rotary/profile", json=_profil())
        geaendert = _profil()
        geaendert["max_werkstueck_laenge_mm"] = 555
        rv = client.put("/api/rotary/profile/user_rotary_test", json=geaendert)
        assert rv.status_code == 200, rv.get_json()
        det = client.get("/api/rotary/profile/user_rotary_test").get_json()
        assert det["max_werkstueck_laenge_mm"] == 555

    def test_loeschen_user_override(self, client):
        client.post("/api/rotary/profile", json=_profil())
        rv = client.delete("/api/rotary/profile/user_rotary_test")
        assert rv.status_code == 200, rv.get_json()
        assert rv.get_json()["geloescht"] is True

    def test_anlegen_invalide_422(self, client):
        rv = client.post("/api/rotary/profile", json={"id": "x"})  # Pflichtfelder fehlen
        assert rv.status_code == 422
