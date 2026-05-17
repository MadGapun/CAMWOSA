"""Tests fuer den Rotary-Postprozessor im Drechsel-Modus."""

from __future__ import annotations

import pytest

from camwosa.cam.drechseln import erzeuge_drechsel_toolpath
from camwosa.cam.parameter import DrechselParameter, DrechselStrategie
from camwosa.gcode.toolpath import Bewegung, BewegungsTyp, OperationsTyp, Toolpath
from camwosa.postprocessor import PostKontext, registry


@pytest.fixture
def kontext(proverxl_maschine, schaftfraeser_6mm) -> PostKontext:
    return PostKontext(
        maschine=proverxl_maschine,
        werkzeug=schaftfraeser_6mm,
    )


@pytest.fixture
def rotary_post():
    return registry().get("grbl_genmitsu_rotary_y")()


@pytest.fixture
def drechsel_toolpath(schaftfraeser_6mm) -> Toolpath:
    p = DrechselParameter(
        werkzeug_id=schaftfraeser_6mm.id,
        spindel_rpm=10000, vorschub=300, eintauch_vorschub=150,
        sicherheitshoehe=5, max_tiefe=15, stepdown=2.0,
        rohmaterial_radius_mm=20,
        aufmass_schlichten_mm=0.3,
        schlicht_zustellung_mm=1.0,
        drehzahl_werkstueck_upm=250,
        profil=[(0, 18), (100, 18)],
        strategie=DrechselStrategie.SCHRUPP_UND_SCHLICHT,
    )
    return erzeuge_drechsel_toolpath(schaftfraeser_6mm.id, p)


@pytest.fixture
def normaler_toolpath(schaftfraeser_6mm) -> Toolpath:
    """Toolpath OHNE Drechseln-Marker — Postprozessor soll normal arbeiten."""
    return Toolpath(
        operation_id="op_normal",
        operation_typ=OperationsTyp.KONTUR,
        werkzeug_id=schaftfraeser_6mm.id,
        spindel_rpm=18000, sicherheitshoehe=5.0,
        bewegungen=[
            Bewegung(BewegungsTyp.EILGANG, 0, 0, 5),
            Bewegung(BewegungsTyp.LINEAR, 10, 0, -1, feed=500),
        ],
    )


class TestDrechselErkennung:
    def test_drechsel_toolpath_loest_warnung_aus(self, rotary_post, kontext, drechsel_toolpath):
        zeilen = rotary_post.post_alle(kontext, [drechsel_toolpath])
        gesamt = "\n".join(zeilen)
        assert "DRECHSEL-JOB" in gesamt
        assert "250" in gesamt  # Werkstueck-Drehzahl
        assert "Rotary-Aufsatz" in gesamt
        assert "ROTARY EIN" in gesamt

    def test_drechsel_vorlauf_pro_toolpath(self, rotary_post, kontext, drechsel_toolpath):
        zeilen = rotary_post.post_alle(kontext, [drechsel_toolpath])
        gesamt = "\n".join(zeilen)
        assert "Strategie 'schrupp_und_schlicht'" in gesamt
        assert "Rohmaterial-Radius: 20" in gesamt
        # CNCjs-Wait-Macro damit User Rotary bestaetigt
        assert "%wait" in gesamt

    def test_drechsel_nachlauf(self, rotary_post, kontext, drechsel_toolpath):
        zeilen = rotary_post.post_alle(kontext, [drechsel_toolpath])
        gesamt = "\n".join(zeilen)
        assert "DRECHSELN beendet" in gesamt

    def test_normaler_toolpath_kein_drechsel_banner(
        self, rotary_post, kontext, normaler_toolpath,
    ):
        zeilen = rotary_post.post_alle(kontext, [normaler_toolpath])
        gesamt = "\n".join(zeilen)
        assert "DRECHSEL-JOB" not in gesamt
        assert "DRECHSELN" not in gesamt

    def test_mehrere_drechsel_paths_listet_alle_drehzahlen(
        self, rotary_post, kontext, schaftfraeser_6mm,
    ):
        def _tp(upm: float) -> Toolpath:
            p = DrechselParameter(
                werkzeug_id=schaftfraeser_6mm.id,
                spindel_rpm=10000, vorschub=300, eintauch_vorschub=150,
                sicherheitshoehe=5, max_tiefe=15, stepdown=2.0,
                rohmaterial_radius_mm=20,
                drehzahl_werkstueck_upm=upm,
                profil=[(0, 18), (100, 18)],
            )
            return erzeuge_drechsel_toolpath(schaftfraeser_6mm.id, p)

        zeilen = rotary_post.post_alle(kontext, [_tp(200), _tp(400)])
        gesamt = "\n".join(zeilen)
        # Header listet alle Drehzahlen
        assert "200" in gesamt and "400" in gesamt
        # Zwei separate Drechsel-Banner pro Toolpath
        assert gesamt.count("--- DRECHSELN: Strategie") == 2

    def test_helix_toolpath_zeigt_steigung_und_sync_feed(
        self, rotary_post, kontext, schaftfraeser_6mm,
    ):
        p = DrechselParameter(
            werkzeug_id=schaftfraeser_6mm.id,
            spindel_rpm=10000, vorschub=300, eintauch_vorschub=150,
            sicherheitshoehe=5, max_tiefe=15, stepdown=2.0,
            rohmaterial_radius_mm=20,
            drehzahl_werkstueck_upm=250,
            profil=[(0, 18), (100, 18)],
            strategie=DrechselStrategie.HELIX,
            helix_steigung_mm_pro_umdrehung=2.5,
            helix_tiefe_mm=3.0,
            helix_anzahl_passes=2,
        )
        tp = erzeuge_drechsel_toolpath(schaftfraeser_6mm.id, p)
        zeilen = rotary_post.post_alle(kontext, [tp])
        gesamt = "\n".join(zeilen)
        assert "Helix-Steigung: 2.5 mm/Umdrehung" in gesamt
        assert "Helix-Tiefe: 3.0 mm in 2 Pass" in gesamt
        # 2.5 * 250 = 625
        assert "625" in gesamt
        assert "A-Drehzahl genau einhalten" in gesamt

    def test_y_in_grad_format_bleibt(self, rotary_post, kontext, drechsel_toolpath):
        """Sanity-Check: das ueberschriebene linear_move-Format ueberlebt."""
        zeilen = rotary_post.post_alle(kontext, [drechsel_toolpath])
        g1_zeilen = [z for z in zeilen if z.startswith("G1 ")]
        assert g1_zeilen
        # G1-Format muss X, Y, Z, F enthalten
        for z in g1_zeilen[:3]:
            assert " X" in z and " Y" in z and " Z" in z and " F" in z
