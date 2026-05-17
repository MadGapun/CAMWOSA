"""Tests fuer Geometrie-Annotation-Endpoints."""

from __future__ import annotations

import pytest

from camwosa.api import create_app
from camwosa.project.schema import (
    GeometrieAnnotation,
    GeometrieAnnotationTyp,
    GeometrieSnapshot,
)


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


class TestAnnotationModell:
    def test_anschlagbohrung_minimal(self):
        a = GeometrieAnnotation(
            id="anschlag_1",
            typ=GeometrieAnnotationTyp.ANSCHLAGBOHRUNG,
            x=10, y=20, z=0,
            durchmesser_mm=3.0, tiefe_mm=8.0,
        )
        assert a.typ == GeometrieAnnotationTyp.ANSCHLAGBOHRUNG

    def test_refpunkt_ohne_durchmesser(self):
        a = GeometrieAnnotation(
            id="ref", typ=GeometrieAnnotationTyp.REFPUNKT, x=0, y=0,
        )
        assert a.durchmesser_mm is None
        assert a.tiefe_mm is None

    def test_geometrie_snapshot_mit_annotationen(self):
        snap = GeometrieSnapshot(
            id="g1", name="Modell", quelle="stl",
            annotationen=[
                GeometrieAnnotation(
                    id="a1", typ=GeometrieAnnotationTyp.ANSCHLAGBOHRUNG,
                    x=5, y=5, durchmesser_mm=3, tiefe_mm=5,
                ),
            ],
        )
        roh = snap.model_dump(mode="json")
        wieder = GeometrieSnapshot.model_validate(roh)
        assert wieder.annotationen[0].typ == GeometrieAnnotationTyp.ANSCHLAGBOHRUNG


class TestAnnotationEndpoints:
    def test_typen(self, client):
        rv = client.get("/api/annotationen/typen")
        assert rv.status_code == 200
        typen = rv.get_json()
        assert "anschlagbohrung" in typen
        assert "refpunkt" in typen

    def test_validate_ok(self, client):
        rv = client.post("/api/annotationen/validate", json={
            "id": "a1", "typ": "anschlagbohrung",
            "x": 0, "y": 0, "durchmesser_mm": 3, "tiefe_mm": 5,
        })
        assert rv.status_code == 200
        assert rv.get_json()["gueltig"]

    def test_validate_invalid(self, client):
        rv = client.post("/api/annotationen/validate", json={
            "id": "a1",  # typ fehlt
        })
        assert rv.status_code == 422

    def test_zu_operationen(self, client):
        rv = client.post("/api/annotationen/zu-operationen", json={
            "annotationen": [
                {"id": "a1", "typ": "anschlagbohrung", "x": 0, "y": 0,
                 "durchmesser_mm": 3, "tiefe_mm": 8},
                {"id": "a2", "typ": "anschlagbohrung", "x": 100, "y": 0,
                 "durchmesser_mm": 3, "tiefe_mm": 8},
                {"id": "r", "typ": "refpunkt", "x": 50, "y": 50},
            ],
        })
        assert rv.status_code == 200
        body = rv.get_json()
        assert len(body["operationen"]) == 1  # 2 Bohrungen gruppiert
        op = body["operationen"][0]
        assert op["typ"] == "bohren"
        assert len(op["parameter"]["__punkte"]) == 2
        assert any("Refpunkt" in h for h in body["hinweise"])

    def test_zu_operationen_invalid_annotation(self, client):
        rv = client.post("/api/annotationen/zu-operationen", json={
            "annotationen": [{"id": "x"}],  # typ fehlt
        })
        assert rv.status_code == 422

    def test_validate_liste_dedup_und_fehler(self, client):
        rv = client.post("/api/annotationen/validate-liste", json={
            "annotationen": [
                {"id": "a1", "typ": "refpunkt", "x": 0, "y": 0},
                {"id": "a1", "typ": "refpunkt", "x": 1, "y": 1},  # dup
                {"id": "a2", "typ": "bullshit", "x": 0, "y": 0},  # invalid
                {"id": "a3", "typ": "anschlagbohrung", "x": 5, "y": 5,
                 "durchmesser_mm": 3, "tiefe_mm": 5},
            ],
        })
        assert rv.status_code == 200
        data = rv.get_json()
        assert not data["gueltig"]  # wegen dup + bullshit
        assert len(data["annotationen"]) == 2  # a1 (erstes) + a3
        assert len(data["fehler"]) == 2
