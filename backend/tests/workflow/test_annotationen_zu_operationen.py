"""Tests fuer Annotation -> Operation Auto-Generierung."""

from __future__ import annotations

from camwosa.db.models import Werkzeug, WerkzeugTyp
from camwosa.project.schema import GeometrieAnnotation, GeometrieAnnotationTyp
from camwosa.workflow.annotationen_zu_operationen import (
    annotationen_zu_operationen,
    waehle_werkzeug,
)


def _wz(id_: str, typ: WerkzeugTyp, d: float) -> Werkzeug:
    return Werkzeug(
        id=id_, name=id_, typ=typ,
        durchmesser=d, schaft_durchmesser=max(d, 3),
        schneidlaenge=15, gesamtlaenge=50, schneiden=2,
    )


def _bohrung(id_: str, x: float, y: float, d: float = 3.0, tiefe: float = 8.0):
    return GeometrieAnnotation(
        id=id_, typ=GeometrieAnnotationTyp.ANSCHLAGBOHRUNG,
        x=x, y=y, durchmesser_mm=d, tiefe_mm=tiefe,
    )


class TestWerkzeugWahl:
    def test_exakter_durchmesser_und_typ(self):
        wzs = [_wz("b3", WerkzeugTyp.BOHRER, 3), _wz("b4", WerkzeugTyp.BOHRER, 4)]
        gewaehlt = waehle_werkzeug(wzs, durchmesser_mm=3, bevorzugt=WerkzeugTyp.BOHRER)
        assert gewaehlt.id == "b3"

    def test_naechster_groesserer(self):
        wzs = [_wz("b4", WerkzeugTyp.BOHRER, 4), _wz("b6", WerkzeugTyp.BOHRER, 6)]
        gewaehlt = waehle_werkzeug(wzs, durchmesser_mm=3, bevorzugt=WerkzeugTyp.BOHRER)
        assert gewaehlt.id == "b4"

    def test_fallback_anderer_typ(self):
        wzs = [_wz("f6", WerkzeugTyp.SCHAFTFRAESER, 6)]
        gewaehlt = waehle_werkzeug(wzs, durchmesser_mm=3, bevorzugt=WerkzeugTyp.BOHRER)
        assert gewaehlt.id == "f6"

    def test_leere_liste_returns_none(self):
        assert waehle_werkzeug([], durchmesser_mm=3, bevorzugt=WerkzeugTyp.BOHRER) is None


class TestBohrungenGruppierung:
    def test_vier_anschlaege_gleiche_tiefe_zu_einer_operation(self):
        anns = [
            _bohrung("a1", 0, 0),
            _bohrung("a2", 100, 0),
            _bohrung("a3", 100, 100),
            _bohrung("a4", 0, 100),
        ]
        wzs = [_wz("b3", WerkzeugTyp.BOHRER, 3)]
        erg = annotationen_zu_operationen(anns, wzs)
        assert len(erg.operationen) == 1
        op = erg.operationen[0]
        assert op.typ == "bohren"
        assert len(op.parameter["__punkte"]) == 4
        assert op.parameter["werkzeug_id"] == "b3"

    def test_unterschiedliche_tiefen_in_eigene_operationen(self):
        anns = [
            _bohrung("a1", 0, 0, d=3, tiefe=8),
            _bohrung("a2", 10, 0, d=3, tiefe=8),
            _bohrung("a3", 20, 0, d=3, tiefe=15),
        ]
        wzs = [_wz("b3", WerkzeugTyp.BOHRER, 3)]
        erg = annotationen_zu_operationen(anns, wzs)
        assert len(erg.operationen) == 2
        # Tiefere Gruppe hat einen Punkt
        tiefen = [(op.parameter["max_tiefe"], len(op.parameter["__punkte"])) for op in erg.operationen]
        assert sorted(tiefen) == [(8, 2), (15, 1)]

    def test_hinweis_bei_werkzeug_durchmesser_mismatch(self):
        anns = [_bohrung("a1", 0, 0, d=3)]
        wzs = [_wz("b5", WerkzeugTyp.BOHRER, 5)]
        erg = annotationen_zu_operationen(anns, wzs)
        assert any("forderte" in h for h in erg.hinweise)


class TestAusschnitte:
    def test_ausschnitt_wird_tasche(self):
        ann = GeometrieAnnotation(
            id="aus1", typ=GeometrieAnnotationTyp.AUSSCHNITT,
            x=50, y=50, durchmesser_mm=10, tiefe_mm=3,
        )
        wzs = [_wz("f3", WerkzeugTyp.SCHAFTFRAESER, 3)]
        erg = annotationen_zu_operationen([ann], wzs)
        assert len(erg.operationen) == 1
        op = erg.operationen[0]
        assert op.typ == "tasche"
        assert op.parameter["__geometrie"]["radius"] == 5


class TestIgnorierte:
    def test_refpunkt_und_kommentar_uebersprungen(self):
        anns = [
            GeometrieAnnotation(id="r", typ=GeometrieAnnotationTyp.REFPUNKT, x=0, y=0),
            GeometrieAnnotation(id="k", typ=GeometrieAnnotationTyp.KOMMENTAR, x=0, y=0, text="x"),
        ]
        wzs = [_wz("b3", WerkzeugTyp.BOHRER, 3)]
        erg = annotationen_zu_operationen(anns, wzs)
        assert erg.operationen == []
        assert any("Refpunkt" in h for h in erg.hinweise)
        assert any("Kommentar" in h for h in erg.hinweise)


class TestKeineWerkzeuge:
    def test_hinweis_bei_leerer_werkzeug_liste(self):
        anns = [_bohrung("a1", 0, 0)]
        erg = annotationen_zu_operationen(anns, [])
        assert erg.operationen == []
        assert any("Keine Werkzeuge" in h for h in erg.hinweise)
