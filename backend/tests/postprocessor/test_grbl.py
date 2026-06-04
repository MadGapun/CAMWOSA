"""Tests fuer GRBL-Postprozessoren und Plugin-System."""

from __future__ import annotations

from pathlib import Path

import pytest

from camwosa.gcode.toolpath import (
    Bewegung,
    BewegungsTyp,
    OperationsTyp,
    Toolpath,
)
from camwosa.postprocessor import PostKontext, registry
from camwosa.postprocessor.base import PostProcessor


@pytest.fixture
def kontext(proverxl_maschine, schaftfraeser_6mm) -> PostKontext:
    return PostKontext(
        maschine=proverxl_maschine,
        werkzeug=schaftfraeser_6mm,
        operation_kommentar="Testkontur",
    )


@pytest.fixture
def einfacher_toolpath(schaftfraeser_6mm) -> Toolpath:
    return Toolpath(
        operation_id="op1",
        operation_typ=OperationsTyp.KONTUR,
        werkzeug_id=schaftfraeser_6mm.id,
        spindel_rpm=18000,
        sicherheitshoehe=5.0,
        kommentar="Testkontur",
        bewegungen=[
            Bewegung(BewegungsTyp.EILGANG, 0, 0, 5, kommentar="Anfahrt"),
            Bewegung(BewegungsTyp.PLUNGE, 0, 0, -2, feed=400),
            Bewegung(BewegungsTyp.LINEAR, 100, 0, -2, feed=2000),
            Bewegung(BewegungsTyp.LINEAR, 100, 100, -2, feed=2000),
            Bewegung(BewegungsTyp.LINEAR, 0, 100, -2, feed=2000),
            Bewegung(BewegungsTyp.LINEAR, 0, 0, -2, feed=2000),
            Bewegung(BewegungsTyp.EILGANG, 0, 0, 5, kommentar="Rueckzug"),
        ],
    )


class TestRegistry:
    def test_grbl_standard_registriert(self) -> None:
        assert "grbl_standard" in registry().list_ids()

    def test_grbl_genmitsu_registriert(self) -> None:
        assert "grbl_genmitsu" in registry().list_ids()

    def test_grbl_rotary_registriert(self) -> None:
        assert "grbl_genmitsu_rotary_y" in registry().list_ids()

    def test_unbekannte_id(self) -> None:
        with pytest.raises(KeyError, match="nicht registriert"):
            registry().get("xyz_unknown")


class TestGRBLStandard:
    def test_header_enthaelt_g21_g90(self, kontext: PostKontext) -> None:
        Klasse = registry().get("grbl_standard")
        post = Klasse()
        zeilen = post.header(kontext)
        assert "G21" in zeilen
        assert "G90" in zeilen
        assert "G17" in zeilen

    def test_spindel_an(self, kontext: PostKontext, einfacher_toolpath: Toolpath) -> None:
        post = registry().get("grbl_standard")()
        zeilen = post.spindle_on(kontext, 18000)
        assert zeilen == ["M3 S18000"]

    def test_eilgang_format(self, kontext: PostKontext) -> None:
        post = registry().get("grbl_standard")()
        b = Bewegung(BewegungsTyp.EILGANG, 10, 20, 5)
        out = post.rapid_move(kontext, b)
        assert out == ["G0 X10.000 Y20.000 Z5.000"]

    def test_linear_mit_feed(self, kontext: PostKontext) -> None:
        post = registry().get("grbl_standard")()
        b = Bewegung(BewegungsTyp.LINEAR, 10, 20, -2, feed=1500)
        out = post.linear_move(kontext, b)
        assert out == ["G1 X10.000 Y20.000 Z-2.000 F1500"]

    def test_kompletter_toolpath(self, kontext: PostKontext, einfacher_toolpath: Toolpath) -> None:
        post = registry().get("grbl_standard")()
        zeilen = post.post(kontext, einfacher_toolpath)
        assert any("M3 S18000" in z for z in zeilen)
        assert any("G0 X0.000 Y0.000 Z5.000" in z for z in zeilen)
        assert any("G1 X100.000 Y0.000 Z-2.000 F2000" in z for z in zeilen)

    def test_post_alle_mit_header_footer(
        self, kontext: PostKontext, einfacher_toolpath: Toolpath
    ) -> None:
        post = registry().get("grbl_standard")()
        zeilen = post.post_alle(kontext, [einfacher_toolpath])
        assert zeilen[0].startswith(";")
        assert "G21" in zeilen
        assert "M30" in zeilen
        assert "M5" in zeilen


class TestGRBLGenmitsu:
    def test_header_enthaelt_modus_hinweis(self, kontext: PostKontext) -> None:
        post = registry().get("grbl_genmitsu")()
        zeilen = post.header(kontext)
        assert any("Maschinen-Modus" in z for z in zeilen)


class TestRotary:
    def test_header_enthaelt_rotary_warnung(self, kontext: PostKontext) -> None:
        post = registry().get("grbl_genmitsu_rotary_y")()
        zeilen = post.header(kontext)
        assert any("ROTARY-MODUS" in z for z in zeilen)
        assert any("88.889" in z for z in zeilen)
        assert any("9999" in z for z in zeilen)


class TestPluginLoader:
    def test_user_postprozessor_laden(self, tmp_path: Path) -> None:
        # Erzeuge einen User-Postprozessor in tmp_path
        plugin_code = '''
from camwosa.postprocessor.base import PostProcessor

POSTPROCESSOR_ID = "test_user_post"

class TestUserPost(PostProcessor):
    name = "Test User Post"
    file_extension = ".gcode"

    def rapid_move(self, ctx, b):
        return [f"USER_RAPID {b.x} {b.y} {b.z}"]

    def linear_move(self, ctx, b):
        return [f"USER_LINEAR {b.x} {b.y} {b.z}"]

    def arc_move(self, ctx, b):
        return [f"USER_ARC {b.x} {b.y} {b.z}"]
'''
        (tmp_path / "mein_post.py").write_text(plugin_code, encoding="utf-8")
        anzahl = registry().lade_aus_verzeichnis(tmp_path)
        assert anzahl == 1
        assert "test_user_post" in registry().list_ids()
        Klasse = registry().get("test_user_post")
        assert issubclass(Klasse, PostProcessor)
        instanz = Klasse()
        assert instanz.name == "Test User Post"

    def test_plugin_ohne_id_fehler(self, tmp_path: Path) -> None:
        (tmp_path / "schlecht.py").write_text(
            "from camwosa.postprocessor.base import PostProcessor\n"
            "class X(PostProcessor):\n"
            "    def rapid_move(self, c, b): return []\n"
            "    def linear_move(self, c, b): return []\n"
            "    def arc_move(self, c, b): return []\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="POSTPROCESSOR_ID"):
            registry().lade_aus_verzeichnis(tmp_path)


class TestClusterP:
    """Postprozessor-Haertung: Spindel-Dwell (P1) + G54 (P4)."""

    def test_p1_dwell_nach_m3(self, proverxl_maschine, schaftfraeser_6mm):
        from camwosa.postprocessor.grbl_standard import GRBLStandard
        ctx = PostKontext(
            maschine=proverxl_maschine, werkzeug=schaftfraeser_6mm,
            spindel_hochlauf_s=2.0,
        )
        zeilen = GRBLStandard().spindle_on(ctx, 18000)
        assert zeilen == ["M3 S18000", "G4 P2"]

    def test_p1_default_kein_dwell(self, kontext):
        from camwosa.postprocessor.grbl_standard import GRBLStandard
        # Default-Kontext hat spindel_hochlauf_s=0 → rueckwaertskompatibel
        assert GRBLStandard().spindle_on(kontext, 18000) == ["M3 S18000"]

    def test_p4_header_hat_g54(self, kontext):
        from camwosa.postprocessor.grbl_standard import GRBLStandard
        assert "G54" in GRBLStandard().header(kontext)

    def test_p1_im_kompletten_job(self, proverxl_maschine, schaftfraeser_6mm, einfacher_toolpath):
        from camwosa.postprocessor.grbl_standard import GRBLStandard
        ctx = PostKontext(
            maschine=proverxl_maschine, werkzeug=schaftfraeser_6mm,
            spindel_hochlauf_s=1.5,
        )
        zeilen = GRBLStandard().post_alle(ctx, [einfacher_toolpath])
        assert any("G4 P1.5" in z for z in zeilen)
