"""Tests fuer auto_cam_erstellen."""

from __future__ import annotations

import pytest

from camwosa.db.models import (
    Arbeitsraum, ControllerTyp, Maschine, Material, MaterialKategorie,
    Rohmaterial, RohmaterialForm, Werkzeug, WerkzeugTyp,
)
from camwosa.workflow.auto_cam import (
    AufgabenTyp,
    auto_cam_erstellen,
    soll_schrupp_schlicht,
    waehle_bohrer,
    waehle_gravur_werkzeug,
    waehle_schrupp_werkzeug,
    waehle_schlicht_werkzeug,
)


def _maschine() -> Maschine:
    return Maschine(
        id="m", name="M", hersteller="x", modell="x",
        controller=ControllerTyp.GRBL,
        arbeitsraum=Arbeitsraum(x=400, y=400, z=110),
        max_vorschub=3000, sicherer_vorschub=2000, eilgang=3000,
        postprozessor="grbl_standard",
    )

def _material() -> Material:
    return Material(id="buche", name="Buche", kategorie=MaterialKategorie.HOLZ)

def _werkzeuge() -> list[Werkzeug]:
    def _w(id_, typ, d, **extra):
        return Werkzeug(
            id=id_, name=id_, typ=typ, durchmesser=d,
            schaft_durchmesser=max(d, 3),
            schneidlaenge=15, gesamtlaenge=50, schneiden=2,
            **extra,
        )
    return [
        _w("schaft_6mm", WerkzeugTyp.SCHAFTFRAESER, 6),
        _w("schaft_2mm", WerkzeugTyp.SCHAFTFRAESER, 2),
        _w("kugel_3mm", WerkzeugTyp.KUGELFRAESER, 3),
        _w("bohrer_3mm", WerkzeugTyp.BOHRER, 3),
        _w("vbit_60", WerkzeugTyp.V_BIT, 6, spitzenwinkel=60),
    ]


class TestWerkzeugAuswahl:
    def test_schrupp_findet_naechsten_durchmesser(self):
        wz = waehle_schrupp_werkzeug(_werkzeuge(), 6.5)
        assert wz is not None
        assert wz.id == "schaft_6mm"

    def test_schlicht_findet_kleineres_werkzeug(self):
        wz = waehle_schlicht_werkzeug(_werkzeuge(), maximal_durchmesser_mm=5.0)
        assert wz is not None
        assert wz.durchmesser <= 5.0

    def test_bohrer_typ_bevorzugt(self):
        wz = waehle_bohrer(_werkzeuge(), 3.0)
        assert wz is not None
        assert wz.typ == WerkzeugTyp.BOHRER

    def test_gravur_bevorzugt_v_bit(self):
        wz = waehle_gravur_werkzeug(_werkzeuge())
        assert wz is not None
        assert wz.typ in (WerkzeugTyp.V_BIT, WerkzeugTyp.GRAVIERSTICHEL)


class TestStrategieHeuristik:
    def test_flache_tasche_kein_schlicht(self):
        assert not soll_schrupp_schlicht(3.0, "weich")

    def test_tiefe_tasche_braucht_schlicht(self):
        assert soll_schrupp_schlicht(8.0, "weich")

    def test_hartholz_niedrigere_schwelle(self):
        assert soll_schrupp_schlicht(4.0, "hart")
        assert not soll_schrupp_schlicht(2.0, "hart")


class TestTaschenBuilder:
    def test_flache_tasche_einzige_op(self):
        erg = auto_cam_erstellen(
            AufgabenTyp.TASCHE,
            name="Test", maschine=_maschine(), material=_material(),
            werkzeuge=_werkzeuge(),
            parameter={"breite_mm": 50, "hoehe_mm": 30, "tiefe_mm": 3},
        )
        ops = erg.projekt.varianten[0].setups[0].operationen
        assert len(ops) == 1
        assert ops[0].name == "Tasche"
        # Bei tiefe=3 sollte ein „nur Schruppen"-Hinweis vorhanden sein
        assert any("nur Schruppen" in h for h in erg.hinweise)

    def test_tiefe_tasche_schrupp_und_schlicht(self):
        erg = auto_cam_erstellen(
            AufgabenTyp.TASCHE,
            name="Test", maschine=_maschine(), material=_material(),
            werkzeuge=_werkzeuge(),
            parameter={
                "breite_mm": 80, "hoehe_mm": 40, "tiefe_mm": 8,
                "werkzeug_durchmesser_mm": 6,
            },
        )
        ops = erg.projekt.varianten[0].setups[0].operationen
        assert len(ops) == 2
        assert ops[0].name == "Tasche Schruppen"
        assert ops[1].name == "Tasche Schlichten"
        # Schritte sollten WW dazwischen haben
        schritte = erg.projekt.varianten[0].setups[0].schritte
        typen = [s.typ for s in schritte]
        from camwosa.project.schritte import SchrittTyp
        assert SchrittTyp.WERKZEUGWECHSEL in typen
        # Schruppen-Tool ist groesser als Schlicht-Tool
        from camwosa.project.schritte import WerkzeugWechselSchritt
        ww = next(s for s in schritte if isinstance(s, WerkzeugWechselSchritt))
        assert ww.werkzeug_alt_id == "schaft_6mm"
        assert ww.werkzeug_neu_id != "schaft_6mm"

    def test_hartholz_niedrigere_schwelle_greift(self):
        erg = auto_cam_erstellen(
            AufgabenTyp.TASCHE,
            name="Test", maschine=_maschine(), material=_material(),
            werkzeuge=_werkzeuge(),
            parameter={"breite_mm": 50, "hoehe_mm": 30, "tiefe_mm": 4,
                        "material_haerte": "hart"},
        )
        # 4mm bei hartem Material → Schwelle 3mm → Schrupp+Schlicht
        ops = erg.projekt.varianten[0].setups[0].operationen
        assert len(ops) == 2


class TestAnschlagbohrungen:
    def test_4_ecken(self):
        erg = auto_cam_erstellen(
            AufgabenTyp.ANSCHLAGBOHRUNGEN,
            name="Anschlag", maschine=_maschine(), material=_material(),
            werkzeuge=_werkzeuge(),
            parameter={
                "werkstueck_breite_mm": 200, "werkstueck_hoehe_mm": 150,
                "randabstand_mm": 15, "durchmesser_mm": 3, "tiefe_mm": 8,
            },
        )
        op = erg.projekt.varianten[0].setups[0].operationen[0]
        assert op.typ == "bohren"
        punkte = op.parameter["__punkte"]
        assert len(punkte) == 4
        # Erster Punkt = Ecke unten links
        assert punkte[0] == [15, 15]
        # Dritter = Ecke oben rechts
        assert punkte[2] == [185, 135]


class TestBeschriftungWrap:
    def test_wrap_text_erzeugt_operation(self):
        erg = auto_cam_erstellen(
            AufgabenTyp.BESCHRIFTUNG_WRAP,
            name="Schriftzug", maschine=_maschine(), material=_material(),
            werkzeuge=_werkzeuge(),
            parameter={
                "text": "CAMWOSA",
                "werkstueck_radius_mm": 25, "gravur_tiefe_mm": 0.5,
            },
        )
        op = erg.projekt.varianten[0].setups[0].operationen[0]
        assert "CAMWOSA" in op.name
        assert op.parameter["__wrap_text"] == "CAMWOSA"
        assert op.parameter["__werkstueck_radius_mm"] == 25
        # Setup soll im Rotary-Modus sein
        assert erg.projekt.varianten[0].setups[0].maschinen_modus == "rotary_y"
        assert any("Text-zu-Pfad" in h for h in erg.hinweise)


class TestProjektMetadaten:
    def test_projekt_hat_metadata_und_variante(self):
        erg = auto_cam_erstellen(
            AufgabenTyp.TASCHE,
            name="Mein Test", maschine=_maschine(), material=_material(),
            werkzeuge=_werkzeuge(),
            parameter={"breite_mm": 30, "hoehe_mm": 20, "tiefe_mm": 2},
        )
        assert erg.projekt.metadaten.name == "Mein Test"
        assert erg.projekt.varianten[0].name == "Default"
        assert "auto_cam_erstellen" in erg.projekt.metadaten.notizen
