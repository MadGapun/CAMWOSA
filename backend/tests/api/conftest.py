"""Gemeinsame API-Test-Fixtures: Flask-Test-Client mit isolierten Daten."""

from __future__ import annotations

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
