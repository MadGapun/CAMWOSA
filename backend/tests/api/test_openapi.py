"""Tests fuer OpenAPI-Spec-Generator (Master-Plan B3)."""

from __future__ import annotations

import pytest

from camwosa.api import create_app
from camwosa.api.openapi import generiere_spec


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    app.config["TESTING"] = True
    return app.test_client()


class TestSpecGenerator:
    def test_spec_hat_openapi_version(self, app):
        spec = generiere_spec(app)
        assert spec["openapi"] == "3.1.0"

    def test_spec_hat_info(self, app):
        spec = generiere_spec(app)
        assert "title" in spec["info"]
        assert "version" in spec["info"]
        assert spec["info"]["title"] == "CAMWOSA Backend API"

    def test_spec_hat_paths(self, app):
        spec = generiere_spec(app)
        # Mindestens die wichtigsten Endpoints sind drin
        assert "/health" in spec["paths"] or "/api/projects/new" in spec["paths"]
        assert "/api/heightmap/aus-bild" in spec["paths"]
        assert "/api/text/zu-pfad" in spec["paths"]
        assert "/api/wrap/pattern-skalieren" in spec["paths"]

    def test_spec_hat_tags(self, app):
        spec = generiere_spec(app)
        tag_namen = [t["name"] for t in spec["tags"]]
        # Mindestens die offensichtlichen Blueprints
        for erwartet in ("heightmap", "text", "wrap", "tools", "materials"):
            assert erwartet in tag_namen, f"Tag {erwartet} fehlt"

    def test_path_parameter_konvertiert(self, app):
        spec = generiere_spec(app)
        # /api/machines/<id> oder aehnlich → /api/machines/{id}
        path_strings = list(spec["paths"].keys())
        gibts_path_param = any("{" in p and "}" in p for p in path_strings)
        assert gibts_path_param, f"Keine Path-Parameter: {path_strings[:5]}"

    def test_jede_operation_hat_summary_und_tags(self, app):
        spec = generiere_spec(app)
        for pfad, pfad_eintrag in spec["paths"].items():
            for methode, op in pfad_eintrag.items():
                assert "summary" in op, f"{methode.upper()} {pfad} ohne summary"
                assert "tags" in op, f"{methode.upper()} {pfad} ohne tags"
                assert "operationId" in op


class TestOpenAPIEndpoint:
    def test_json_endpoint(self, client):
        rv = client.get("/api/openapi.json")
        assert rv.status_code == 200
        body = rv.get_json()
        assert body["openapi"] == "3.1.0"
        assert "paths" in body
        assert "info" in body

    def test_docs_endpoint_html(self, client):
        rv = client.get("/api/docs")
        assert rv.status_code == 200
        assert rv.content_type.startswith("text/html")
        body = rv.get_data(as_text=True)
        assert "swagger-ui" in body.lower()
        assert "openapi.json" in body

    def test_yaml_endpoint(self, client):
        rv = client.get("/api/openapi.yaml")
        # Entweder YAML oder 501 wenn PyYAML fehlt
        assert rv.status_code in (200, 501)
        if rv.status_code == 200:
            text = rv.get_data(as_text=True)
            assert "openapi:" in text and "paths:" in text
