"""Tests fuer Multi-Werkzeug-G-Code-Generierung aus einer Schritt-Liste."""

from __future__ import annotations

import pytest

from camwosa.db.models import (
    Arbeitsraum,
    ControllerTyp,
    Maschine,
    Werkzeug,
    WerkzeugTyp,
)
from camwosa.gcode.toolpath import Bewegung, BewegungsTyp, OperationsTyp, Toolpath
from camwosa.project.schema import OperationsKonfig, Setup
from camwosa.project.schritte import (
    AchsWechselSchritt,
    ManualNCSchritt,
    OperationSchritt,
    PauseSchritt,
    UmspannSchritt,
    WerkzeugWechselSchritt,
    WerkzeugWechselStrategie,
)
from camwosa.workflow.gcode_schritte import (
    gliedere_schritte_in_bloecke,
    schreibe_gcode_aus_schritten,
)


def _wz(id_: str, durchmesser: float) -> Werkzeug:
    return Werkzeug(
        id=id_, name=id_, typ=WerkzeugTyp.SCHAFTFRAESER,
        durchmesser=durchmesser, schaft_durchmesser=6,
        schneidlaenge=22, gesamtlaenge=50, schneiden=2,
    )


def _tp(x: float = 0) -> Toolpath:
    return Toolpath(
        operation_id="op",
        operation_typ=OperationsTyp.KONTUR,
        werkzeug_id="t",
        bewegungen=[
            Bewegung(typ=BewegungsTyp.EILGANG, x=0, y=0, z=5),
            Bewegung(typ=BewegungsTyp.LINEAR, x=x, y=0, z=-1, feed=500),
        ],
        spindel_rpm=18000,
        sicherheitshoehe=5,
    )


def _maschine() -> Maschine:
    return Maschine(
        id="m", name="M", hersteller="x", modell="x",
        controller=ControllerTyp.GRBL,
        arbeitsraum=Arbeitsraum(x=400, y=400, z=110),
        max_vorschub=3000, sicherer_vorschub=2000, eilgang=3000,
        postprozessor="grbl_standard",
    )


class TestGliederung:
    def test_separate_datei_erzeugt_neuen_block(self):
        wz6 = _wz("t6", 6)
        wz2 = _wz("t2", 2)
        schritte = [
            OperationSchritt(id="s1", operation_id="op_schruppen"),
            WerkzeugWechselSchritt(
                id="ww", werkzeug_neu_id="t2",
                strategie=WerkzeugWechselStrategie.SEPARATE_DATEI,
            ),
            OperationSchritt(id="s2", operation_id="op_schlichten"),
        ]
        bloecke = gliedere_schritte_in_bloecke(
            schritte,
            werkzeug_index={"t6": wz6, "t2": wz2},
            toolpaths_pro_operation={"op_schruppen": [_tp(10)], "op_schlichten": [_tp(20)]},
            start_werkzeug=wz6,
        )
        assert len(bloecke) == 2
        assert bloecke[0].werkzeug.id == "t6"
        assert bloecke[1].werkzeug.id == "t2"
        assert bloecke[0].toolpaths[0].bewegungen[-1].x == 10
        assert bloecke[1].toolpaths[0].bewegungen[-1].x == 20

    def test_inline_m6_bleibt_in_block(self):
        wz6 = _wz("t6", 6)
        wz2 = _wz("t2", 2)
        schritte = [
            OperationSchritt(id="s1", operation_id="op1"),
            WerkzeugWechselSchritt(
                id="ww", werkzeug_neu_id="t2",
                strategie=WerkzeugWechselStrategie.INLINE_M6,
            ),
            OperationSchritt(id="s2", operation_id="op2"),
        ]
        bloecke = gliedere_schritte_in_bloecke(
            schritte,
            werkzeug_index={"t6": wz6, "t2": wz2},
            toolpaths_pro_operation={"op1": [_tp(1)], "op2": [_tp(2)]},
            start_werkzeug=wz6,
        )
        assert len(bloecke) == 1
        assert len(bloecke[0].toolpaths) == 2
        # M6-Inline-Zeilen wurden an Position 1 (zwischen den zwei TPs) gemerkt
        assert any(
            any("M6" in z for z in zeilen)
            for _, zeilen in bloecke[0].inline_zeilen
        )

    def test_manual_nc_eingebettet(self):
        wz = _wz("t1", 6)
        schritte = [
            OperationSchritt(id="s1", operation_id="op1"),
            ManualNCSchritt(id="m1", gcode_zeilen=["M62 P0 ; Vakuum"]),
            OperationSchritt(id="s2", operation_id="op2"),
        ]
        bloecke = gliedere_schritte_in_bloecke(
            schritte,
            werkzeug_index={"t1": wz},
            toolpaths_pro_operation={"op1": [_tp()], "op2": [_tp()]},
            start_werkzeug=wz,
        )
        assert len(bloecke) == 1
        inline = bloecke[0].inline_zeilen
        assert any("Vakuum" in z for _, zeilen in inline for z in zeilen)

    def test_inaktiver_schritt_uebersprungen(self):
        wz = _wz("t1", 6)
        schritte = [
            OperationSchritt(id="s1", operation_id="op1"),
            OperationSchritt(id="s2", operation_id="op2", aktiviert=False),
        ]
        bloecke = gliedere_schritte_in_bloecke(
            schritte,
            werkzeug_index={"t1": wz},
            toolpaths_pro_operation={"op1": [_tp(1)], "op2": [_tp(2)]},
            start_werkzeug=wz,
        )
        assert len(bloecke[0].toolpaths) == 1


class TestGetrennteDatei:
    """M7: getrennte Dateien bei Umbau/Umkabeln (Maschine aus → Verbindung weg)."""

    def test_umspann_mit_flag_splittet_und_hinweis(self):
        wz = _wz("t1", 6)
        schritte = [
            OperationSchritt(id="s1", operation_id="op1"),
            UmspannSchritt(id="u1", anweisung="Auf Rotary umkabeln",
                           getrennte_datei=True),
            OperationSchritt(id="s2", operation_id="op2"),
        ]
        bloecke = gliedere_schritte_in_bloecke(
            schritte,
            werkzeug_index={"t1": wz},
            toolpaths_pro_operation={"op1": [_tp(1)], "op2": [_tp(2)]},
            start_werkzeug=wz,
        )
        assert len(bloecke) == 2
        assert "ausschalten" in bloecke[0].abschluss_hinweis.lower()
        assert "Auf Rotary umkabeln" in bloecke[0].abschluss_hinweis

    def test_umspann_ohne_flag_kein_split(self):
        wz = _wz("t1", 6)
        schritte = [
            OperationSchritt(id="s1", operation_id="op1"),
            UmspannSchritt(id="u1", anweisung="nur umspannen"),  # getrennte_datei default False
            OperationSchritt(id="s2", operation_id="op2"),
        ]
        bloecke = gliedere_schritte_in_bloecke(
            schritte,
            werkzeug_index={"t1": wz},
            toolpaths_pro_operation={"op1": [_tp(1)], "op2": [_tp(2)]},
            start_werkzeug=wz,
        )
        assert len(bloecke) == 1
        assert len(bloecke[0].toolpaths) == 2

    def test_achswechsel_default_splittet(self):
        wz = _wz("t1", 6)
        schritte = [
            OperationSchritt(id="s1", operation_id="op1"),
            AchsWechselSchritt(id="a1", modus_alt="standard_xyz", modus_neu="rotary_y"),
            OperationSchritt(id="s2", operation_id="op2"),
        ]
        bloecke = gliedere_schritte_in_bloecke(
            schritte,
            werkzeug_index={"t1": wz},
            toolpaths_pro_operation={"op1": [_tp(1)], "op2": [_tp(2)]},
            start_werkzeug=wz,
        )
        assert len(bloecke) == 2
        # Hinweis nennt den Modus-Wechsel
        assert "rotary_y" in bloecke[0].abschluss_hinweis

    def test_achswechsel_ohne_trennung(self):
        wz = _wz("t1", 6)
        schritte = [
            OperationSchritt(id="s1", operation_id="op1"),
            AchsWechselSchritt(id="a1", modus_alt="a", modus_neu="b",
                               getrennte_datei=False),
            OperationSchritt(id="s2", operation_id="op2"),
        ]
        bloecke = gliedere_schritte_in_bloecke(
            schritte,
            werkzeug_index={"t1": wz},
            toolpaths_pro_operation={"op1": [_tp(1)], "op2": [_tp(2)]},
            start_werkzeug=wz,
        )
        assert len(bloecke) == 1

    def test_hinweis_landet_im_gcode(self, tmp_path):
        wz = _wz("t1", 6)
        setup = Setup(
            id="setup_01", name="Zweiseitig",
            werkzeug_id="t1",
            operationen=[
                OperationsKonfig(id="op1", name="A", typ="tasche", parameter={}),
                OperationsKonfig(id="op2", name="B", typ="tasche", parameter={}),
            ],
            schritte=[
                OperationSchritt(id="s1", operation_id="op1"),
                UmspannSchritt(id="u1", anweisung="Spindel umverdrahten",
                               getrennte_datei=True),
                OperationSchritt(id="s2", operation_id="op2"),
            ],
        )
        pfade = schreibe_gcode_aus_schritten(
            setup, _maschine(),
            werkzeug_index={"t1": wz},
            toolpaths_pro_operation={"op1": [_tp(1)], "op2": [_tp(2)]},
            ziel_verzeichnis=tmp_path,
        )
        assert len(pfade) == 2
        inhalt1 = pfade[0].read_text(encoding="utf-8")
        assert "Maschine ausschalten" in inhalt1
        assert "Spindel umverdrahten" in inhalt1
        assert "naechste Datei laden" in inhalt1.lower() or "Datei laden" in inhalt1


class TestSchreibenAufDisk:
    def test_zwei_dateien_bei_separate_datei(self, tmp_path):
        wz6 = _wz("t6", 6)
        wz2 = _wz("t2", 2)
        setup = Setup(
            id="setup_01", name="Schruppen+Schlichten",
            werkzeug_id="t6",
            operationen=[
                OperationsKonfig(id="op_schruppen", name="Schruppen",
                                  typ="tasche", parameter={}),
                OperationsKonfig(id="op_schlichten", name="Schlichten",
                                  typ="tasche", parameter={}),
            ],
            schritte=[
                OperationSchritt(id="s1", operation_id="op_schruppen"),
                WerkzeugWechselSchritt(
                    id="ww", werkzeug_neu_id="t2",
                    strategie=WerkzeugWechselStrategie.SEPARATE_DATEI,
                    anweisung="2mm Fraeser einsetzen",
                ),
                OperationSchritt(id="s2", operation_id="op_schlichten"),
            ],
        )
        pfade = schreibe_gcode_aus_schritten(
            setup, _maschine(),
            werkzeug_index={"t6": wz6, "t2": wz2},
            toolpaths_pro_operation={
                "op_schruppen": [_tp(10)],
                "op_schlichten": [_tp(20)],
            },
            ziel_verzeichnis=tmp_path,
        )
        assert len(pfade) == 2
        assert all(p.exists() for p in pfade)
        # Datei 1 hat t6 im Namen
        assert "t6" in pfade[0].name
        # Datei 2 hat t2 im Namen
        assert "t2" in pfade[1].name

    def test_eine_datei_bei_inline_m6(self, tmp_path):
        wz6 = _wz("t6", 6)
        wz2 = _wz("t2", 2)
        setup = Setup(
            id="setup_01", name="x",
            werkzeug_id="t6",
            operationen=[
                OperationsKonfig(id="op1", name="A", typ="tasche", parameter={}),
                OperationsKonfig(id="op2", name="B", typ="tasche", parameter={}),
            ],
            schritte=[
                OperationSchritt(id="s1", operation_id="op1"),
                WerkzeugWechselSchritt(
                    id="ww", werkzeug_neu_id="t2",
                    strategie=WerkzeugWechselStrategie.INLINE_M6,
                ),
                OperationSchritt(id="s2", operation_id="op2"),
            ],
        )
        pfade = schreibe_gcode_aus_schritten(
            setup, _maschine(),
            werkzeug_index={"t6": wz6, "t2": wz2},
            toolpaths_pro_operation={"op1": [_tp(1)], "op2": [_tp(2)]},
            ziel_verzeichnis=tmp_path,
        )
        assert len(pfade) == 1
        inhalt = pfade[0].read_text(encoding="utf-8")
        assert "M6" in inhalt
        assert "M0" in inhalt
