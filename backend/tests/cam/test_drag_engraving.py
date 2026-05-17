"""Tests fuer Drag-Engraving-Operation."""

from __future__ import annotations

import pytest

from camwosa.cam.drag_engraving import (
    DragEngravingFehler,
    DragEngravingParameter,
    erzeuge_drag_engraving_toolpath,
)
from camwosa.db.models import Werkzeug, WerkzeugTyp
from camwosa.dxf.parser import GeometrieObjekt, GeometrieTyp, Punkt2D
from camwosa.gcode.toolpath import BewegungsTyp


def _drag_werkzeug() -> Werkzeug:
    return Werkzeug(
        id="t_drag", name="Drag-Engraver",
        typ=WerkzeugTyp.DRAG_GRAVIERER,
        durchmesser=0.5, schaft_durchmesser=6.0,
        schneidlaenge=2.0, gesamtlaenge=40.0, schneiden=1,
    )


def _schaftfraeser() -> Werkzeug:
    return Werkzeug(
        id="t_schaft", name="Schaftfraeser 3mm",
        typ=WerkzeugTyp.SCHAFTFRAESER,
        durchmesser=3.0, schaft_durchmesser=3.0,
        schneidlaenge=12.0, gesamtlaenge=30.0, schneiden=2,
    )


def _linie(punkte: list[tuple[float, float]]) -> GeometrieObjekt:
    return GeometrieObjekt(
        typ=GeometrieTyp.LINIE if len(punkte) == 2 else GeometrieTyp.POLYLINIE,
        layer="0",
        punkte=[Punkt2D(*p) for p in punkte],
        geschlossen=False,
    )


class TestVorbedingungen:
    def test_falsches_werkzeug_wirft(self):
        with pytest.raises(DragEngravingFehler, match="DRAG_GRAVIERER"):
            erzeuge_drag_engraving_toolpath(
                _linie([(0, 0), (10, 0)]),
                _schaftfraeser(),
                DragEngravingParameter(werkzeug_id="t_schaft"),
            )

    def test_diamantgravierer_auch_erlaubt(self):
        diamant = Werkzeug(
            id="t_diam", name="Diamant",
            typ=WerkzeugTyp.DIAMANTGRAVIERER,
            durchmesser=0.3, schaft_durchmesser=6,
            schneidlaenge=2, gesamtlaenge=40, schneiden=1,
        )
        tp = erzeuge_drag_engraving_toolpath(
            _linie([(0, 0), (10, 0)]),
            diamant,
            DragEngravingParameter(werkzeug_id="t_diam"),
        )
        assert tp.spindel_rpm == 0.0

    def test_leere_geometrie_wirft(self):
        with pytest.raises(DragEngravingFehler):
            erzeuge_drag_engraving_toolpath(
                GeometrieObjekt(typ=GeometrieTyp.PUNKT, layer="0", punkte=[]),
                _drag_werkzeug(),
                DragEngravingParameter(werkzeug_id="t_drag"),
            )


class TestToolpath:
    def test_einfache_linie_erzeugt_minimum_bewegungen(self):
        tp = erzeuge_drag_engraving_toolpath(
            _linie([(0, 0), (50, 0)]),
            _drag_werkzeug(),
            DragEngravingParameter(werkzeug_id="t_drag", tiefe=0.15),
        )
        assert tp.spindel_rpm == 0.0
        # Erwartet: Eilgang zu Start, Plunge, Linear, Rueckzug
        typen = [b.typ for b in tp.bewegungen]
        assert BewegungsTyp.EILGANG in typen
        assert BewegungsTyp.PLUNGE in typen
        assert BewegungsTyp.LINEAR in typen

    def test_tiefe_immer_negativ(self):
        tp = erzeuge_drag_engraving_toolpath(
            _linie([(0, 0), (10, 0)]),
            _drag_werkzeug(),
            DragEngravingParameter(werkzeug_id="t_drag", tiefe=0.2),
        )
        plunge = next(b for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE)
        assert plunge.z < 0, "Plunge sollte negative Z haben"
        linear = next(b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR)
        assert linear.z == plunge.z

    def test_eintauch_vorschub_langsam(self):
        tp = erzeuge_drag_engraving_toolpath(
            _linie([(0, 0), (10, 0)]),
            _drag_werkzeug(),
            DragEngravingParameter(
                werkzeug_id="t_drag", vorschub=800, eintauch_vorschub=80,
            ),
        )
        plunge = next(b for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE)
        assert plunge.feed == 80
        linear = next(b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR)
        assert linear.feed == 800

    def test_metadaten_marker_gesetzt(self):
        tp = erzeuge_drag_engraving_toolpath(
            _linie([(0, 0), (10, 0)]),
            _drag_werkzeug(),
            DragEngravingParameter(werkzeug_id="t_drag", tiefe=0.2),
        )
        assert tp.metadaten and tp.metadaten.get("drag_engraving") is True
        assert tp.metadaten["tiefe_mm"] == 0.2


class TestEckenDwell:
    def test_dwell_an_scharfer_90grad_ecke(self):
        # L-Form: 90° Knick — sollte Dwell erzeugen
        tp = erzeuge_drag_engraving_toolpath(
            _linie([(0, 0), (10, 0), (10, 10)]),
            _drag_werkzeug(),
            DragEngravingParameter(
                werkzeug_id="t_drag",
                dwell_an_ecken_sekunden=0.15,
                ecken_winkel_schwelle_grad=30,
            ),
        )
        dwell_kommentare = [b.kommentar for b in tp.bewegungen if b.kommentar and "DWELL" in b.kommentar]
        assert len(dwell_kommentare) == 1

    def test_gerade_linie_kein_dwell(self):
        # 3 kolineare Punkte — KEIN Knick
        tp = erzeuge_drag_engraving_toolpath(
            _linie([(0, 0), (5, 0), (10, 0)]),
            _drag_werkzeug(),
            DragEngravingParameter(
                werkzeug_id="t_drag",
                dwell_an_ecken_sekunden=0.2,
                ecken_winkel_schwelle_grad=10,
            ),
        )
        dwell_kommentare = [b.kommentar for b in tp.bewegungen if b.kommentar and "DWELL" in b.kommentar]
        assert dwell_kommentare == []

    def test_dwell_kann_deaktiviert_werden(self):
        # dwell_an_ecken_sekunden=0 -> keine Pausen
        tp = erzeuge_drag_engraving_toolpath(
            _linie([(0, 0), (10, 0), (10, 10)]),
            _drag_werkzeug(),
            DragEngravingParameter(werkzeug_id="t_drag", dwell_an_ecken_sekunden=0),
        )
        dwell_kommentare = [b.kommentar for b in tp.bewegungen if b.kommentar and "DWELL" in b.kommentar]
        assert dwell_kommentare == []


class TestLeadIn:
    def test_tangentiales_lead_in_erzeugt_vor_position(self):
        tp = erzeuge_drag_engraving_toolpath(
            _linie([(10, 0), (50, 0)]),
            _drag_werkzeug(),
            DragEngravingParameter(
                werkzeug_id="t_drag",
                lead_in_tangential_mm=3.0,
            ),
        )
        # Es sollte einen Plunge geben bei (10-3=7, 0) — also vor dem Startpunkt
        plunges = [b for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE]
        assert len(plunges) >= 1
        assert plunges[0].x == pytest.approx(7.0)

    def test_kein_lead_in_default(self):
        tp = erzeuge_drag_engraving_toolpath(
            _linie([(10, 0), (50, 0)]),
            _drag_werkzeug(),
            DragEngravingParameter(werkzeug_id="t_drag"),  # default lead_in=0
        )
        plunge = next(b for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE)
        # Plunge sollte direkt am Startpunkt sein
        assert plunge.x == 10.0
