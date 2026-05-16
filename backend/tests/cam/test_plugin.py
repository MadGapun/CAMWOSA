"""Tests fuer Operations-Plugin-System."""

from __future__ import annotations

from pathlib import Path

import pytest

from camwosa.cam.plugin import OperationPlugin, registry
from camwosa.gcode.toolpath import (
    Bewegung,
    BewegungsTyp,
    OperationsTyp,
    Toolpath,
)


class TestRegistry:
    def test_neu_registrieren(self) -> None:
        class TestOp(OperationPlugin):
            name = "Test"
            beschreibung = "Test"
            def erzeuge_toolpath(self, g, w, p):
                return Toolpath(
                    operation_id="t", operation_typ=OperationsTyp.KONTUR,
                    werkzeug_id=w.id, spindel_rpm=12000, sicherheitshoehe=5,
                    bewegungen=[],
                )
        registry().register("test_plugin", TestOp)
        assert "test_plugin" in registry().list_ids()
        op = registry().get("test_plugin")()
        assert op.name == "Test"

    def test_unbekanntes_plugin(self) -> None:
        with pytest.raises(KeyError):
            registry().get("xyz_existiert_nicht_123")


class TestLader:
    def test_user_plugin_laden(self, tmp_path: Path) -> None:
        code = '''
from camwosa.cam.plugin import OperationPlugin
from camwosa.gcode.toolpath import Toolpath, OperationsTyp

OPERATION_ID = "user_test_op_42"

class UserOp(OperationPlugin):
    name = "User Test"

    def erzeuge_toolpath(self, g, w, p):
        return Toolpath(
            operation_id="ut", operation_typ=OperationsTyp.KONTUR,
            werkzeug_id=w.id, spindel_rpm=12000, sicherheitshoehe=5,
            bewegungen=[],
        )
'''
        (tmp_path / "user_op.py").write_text(code, encoding="utf-8")
        anzahl = registry().lade_aus_verzeichnis(tmp_path)
        assert anzahl == 1
        assert "user_test_op_42" in registry().list_ids()

    def test_plugin_ohne_id_fehler(self, tmp_path: Path) -> None:
        (tmp_path / "x.py").write_text(
            "from camwosa.cam.plugin import OperationPlugin\n"
            "class X(OperationPlugin):\n"
            "    def erzeuge_toolpath(self, g, w, p): pass\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="OPERATION_ID"):
            registry().lade_aus_verzeichnis(tmp_path)
