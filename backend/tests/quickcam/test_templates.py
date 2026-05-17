"""Tests fuer QuickCAM-Templates und API-Endpoint."""

from __future__ import annotations

import pytest

from camwosa.api import create_app
from camwosa.db.loader import lade_maschinen, lade_materialien, lade_werkzeuge
from camwosa.quickcam import (
    erzeuge_aus_template,
    template_index,
    templates,
)


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


class TestTemplateRegistry:
    def test_alle_templates_definiert(self):
        ids = {t.id for t in templates()}
        assert "tasche_rechteckig" in ids
        assert "gravur_text" in ids
        assert "bohrloch_raster" in ids
        assert "kontur_ausschneiden" in ids

    def test_template_index_lookup(self):
        t = template_index()["tasche_rechteckig"]
        assert t.operation_typ == "tasche"
        assert any(p.name == "breite_mm" for p in t.parameter)


class TestErzeugen:
    def test_tasche_erzeugt_komplettes_projekt(self):
        maschine = lade_maschinen()[0]
        werkzeug = next(w for w in lade_werkzeuge() if w.durchmesser == 6.0)
        material = next(m for m in lade_materialien() if m.id == "buche_massiv")

        projekt = erzeuge_aus_template(
            "tasche_rechteckig",
            {"breite_mm": 80, "hoehe_mm": 40, "tiefe_mm": 5},
            maschine=maschine, werkzeug=werkzeug, material=material,
        )
        assert projekt.varianten[0].setups[0].name == "Rechteckige Tasche"
        op = projekt.varianten[0].setups[0].operationen[0]
        assert op.typ == "tasche"
        assert op.parameter["max_tiefe"] == 5
        # CuttingPreset-Werte sind eingeflossen
        assert op.parameter["spindel_rpm"] > 0
        assert op.parameter["vorschub"] > 0

    def test_bohrloch_raster_punkte(self):
        maschine = lade_maschinen()[0]
        werkzeug = lade_werkzeuge()[0]
        material = lade_materialien()[0]
        projekt = erzeuge_aus_template(
            "bohrloch_raster",
            {"spalten": 3, "zeilen": 2, "abstand_x_mm": 25,
             "abstand_y_mm": 30, "tiefe_mm": 10},
            maschine=maschine, werkzeug=werkzeug, material=material,
        )
        op = projekt.varianten[0].setups[0].operationen[0]
        punkte = op.parameter["__geometrie"]["punkte"]
        assert len(punkte) == 6
        assert [0, 0] in punkte
        assert [50, 30] in punkte

    def test_unbekanntes_template(self):
        with pytest.raises(KeyError):
            erzeuge_aus_template(
                "gibts_nicht", {},
                maschine=lade_maschinen()[0],
                werkzeug=lade_werkzeuge()[0],
                material=lade_materialien()[0],
            )


class TestAPI:
    def test_liste(self, client):
        rv = client.get("/api/quickcam/templates")
        assert rv.status_code == 200
        items = rv.get_json()
        assert len(items) >= 4
        assert all("id" in t and "parameter" in t for t in items)

    def test_details(self, client):
        rv = client.get("/api/quickcam/templates/tasche_rechteckig")
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["operation_typ"] == "tasche"

    def test_erzeugen(self, client):
        maschine = lade_maschinen()[0]
        werkzeug = next(w for w in lade_werkzeuge() if w.durchmesser == 6.0)
        material = next(m for m in lade_materialien() if m.id == "buche_massiv")
        rv = client.post("/api/quickcam/erzeugen", json={
            "template_id": "tasche_rechteckig",
            "eingaben": {"breite_mm": 60, "hoehe_mm": 40, "tiefe_mm": 5},
            "maschine_id": maschine.id,
            "werkzeug_id": werkzeug.id,
            "material_id": material.id,
        })
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["projekt"]["varianten"][0]["setups"][0]["name"] == "Rechteckige Tasche"

    def test_erzeugen_pflichtfeld_fehlt(self, client):
        rv = client.post("/api/quickcam/erzeugen", json={"template_id": "x"})
        assert rv.status_code == 422

    def test_erzeugen_unbekanntes_template(self, client):
        rv = client.post("/api/quickcam/erzeugen", json={
            "template_id": "ungueltig",
            "maschine_id": lade_maschinen()[0].id,
            "werkzeug_id": lade_werkzeuge()[0].id,
            "material_id": lade_materialien()[0].id,
        })
        assert rv.status_code == 404
