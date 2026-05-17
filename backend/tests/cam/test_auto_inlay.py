"""Tests fuer Auto-Inlay."""

from __future__ import annotations

import pytest
from shapely.geometry import Polygon
from shapely import wkt

from camwosa.cam.auto_inlay import (
    AutoInlayFehler,
    AutoInlayParameter,
    berechne_auto_inlay,
    ergebnis_zu_geometrien,
)
from camwosa.dxf.parser import GeometrieObjekt, GeometrieTyp, Punkt2D


def _rechteck(b: float, h: float) -> Polygon:
    return Polygon([(0, 0), (b, 0), (b, h), (0, h)])


def _kreis_polygon(r: float, segmente: int = 64) -> Polygon:
    import math
    return Polygon([
        (r * math.cos(2 * math.pi * i / segmente),
         r * math.sin(2 * math.pi * i / segmente))
        for i in range(segmente)
    ])


class TestBerechnung:
    def test_einfaches_rechteck_liefert_tasche_und_plug(self):
        rechteck = _rechteck(50, 30)
        ergebnis = berechne_auto_inlay(
            rechteck,
            AutoInlayParameter(spiel_mm=0.1, werkzeug_radius_mm=1.0),
        )
        assert ergebnis.tasche_flaeche_mm2 > 0
        assert ergebnis.plug_flaeche_mm2 > 0

    def test_plug_kleiner_als_tasche_um_spiel(self):
        rechteck = _rechteck(50, 30)
        spiel = 0.2
        ergebnis = berechne_auto_inlay(
            rechteck,
            AutoInlayParameter(spiel_mm=spiel, werkzeug_radius_mm=1.0),
        )
        # Tasche minus Plug = Spielraum drumherum
        # Bei spiel/seite=0.1 und Umfang ~160 mm:
        # Erwartete Flaechendifferenz ~ umfang * spiel = 160 * 0.2 = 32 mm²
        diff = ergebnis.tasche_flaeche_mm2 - ergebnis.plug_flaeche_mm2
        # Erwartet positiv und nicht null
        assert diff > 0

    def test_kleines_spiel_liefert_eng_anliegende_paarung(self):
        rechteck = _rechteck(100, 100)
        ergebnis_klein = berechne_auto_inlay(
            rechteck,
            AutoInlayParameter(spiel_mm=0.0, werkzeug_radius_mm=1.0),
        )
        # Beide praktisch gleich gross
        assert abs(
            ergebnis_klein.tasche_flaeche_mm2 - ergebnis_klein.plug_flaeche_mm2
        ) < 5  # ein paar mm² Rundungs-Toleranz

    def test_tasche_tiefe_und_plug_hoehe_korrekt(self):
        rechteck = _rechteck(50, 30)
        ergebnis = berechne_auto_inlay(
            rechteck,
            AutoInlayParameter(
                werkzeug_radius_mm=1.0,
                tasche_tiefe_mm=4.0,
                plug_uebermass_oben_mm=0.6,
            ),
        )
        assert ergebnis.tasche_tiefe_mm == 4.0
        assert ergebnis.plug_hoehe_mm == pytest.approx(4.6)


class TestFehlerFaelle:
    def test_zu_kleines_polygon_wirft(self):
        winzig = Polygon([(0, 0), (0.5, 0), (0.5, 0.5), (0, 0.5)])
        with pytest.raises(AutoInlayFehler, match="zu klein"):
            berechne_auto_inlay(winzig, AutoInlayParameter(werkzeug_radius_mm=0.1))

    def test_werkzeug_zu_gross_wirft(self):
        rechteck = _rechteck(10, 10)
        with pytest.raises(AutoInlayFehler, match="passt nicht"):
            berechne_auto_inlay(rechteck, AutoInlayParameter(werkzeug_radius_mm=10.0))

    def test_zu_grosses_spiel_degeneriert_plug(self):
        winzig = _rechteck(3, 3)
        with pytest.raises(AutoInlayFehler):
            berechne_auto_inlay(
                winzig,
                AutoInlayParameter(spiel_mm=1.0, werkzeug_radius_mm=0.5),
            )


class TestGeometrieObjektInput:
    def test_geometrieobjekt_polygon_funktioniert(self):
        geo = GeometrieObjekt(
            typ=GeometrieTyp.POLYLINIE, layer="0",
            punkte=[Punkt2D(0, 0), Punkt2D(50, 0), Punkt2D(50, 30), Punkt2D(0, 30)],
            geschlossen=True,
        )
        ergebnis = berechne_auto_inlay(
            geo, AutoInlayParameter(werkzeug_radius_mm=1.0),
        )
        assert ergebnis.tasche_flaeche_mm2 > 0

    def test_offene_polylinie_wirft(self):
        geo = GeometrieObjekt(
            typ=GeometrieTyp.LINIE, layer="0",
            punkte=[Punkt2D(0, 0), Punkt2D(10, 0)],
            geschlossen=False,
        )
        with pytest.raises(AutoInlayFehler):
            berechne_auto_inlay(
                geo, AutoInlayParameter(werkzeug_radius_mm=1.0),
            )


class TestErgebnisAlsGeometrie:
    def test_ergebnis_zu_geometrien_liefert_zwei_polylinien(self):
        rechteck = _rechteck(50, 30)
        ergebnis = berechne_auto_inlay(
            rechteck,
            AutoInlayParameter(werkzeug_radius_mm=1.0),
        )
        tasche, plug = ergebnis_zu_geometrien(ergebnis)
        assert tasche.typ == GeometrieTyp.POLYLINIE
        assert plug.typ == GeometrieTyp.POLYLINIE
        assert tasche.geschlossen
        assert plug.geschlossen
        assert tasche.layer == "auto_inlay_tasche"
        assert plug.layer == "auto_inlay_plug"

    def test_wkt_geom_lesbar(self):
        rechteck = _rechteck(50, 30)
        ergebnis = berechne_auto_inlay(
            rechteck,
            AutoInlayParameter(werkzeug_radius_mm=1.0),
        )
        # Parsing als shapely-WKT muss funktionieren
        t = wkt.loads(ergebnis.tasche_polygon_wkt)
        p = wkt.loads(ergebnis.plug_polygon_wkt)
        assert t.is_valid and not t.is_empty
        assert p.is_valid and not p.is_empty


class TestRunder():
    def test_kreis_funktioniert(self):
        kreis = _kreis_polygon(20)
        ergebnis = berechne_auto_inlay(
            kreis, AutoInlayParameter(spiel_mm=0.1, werkzeug_radius_mm=1.0),
        )
        assert ergebnis.tasche_flaeche_mm2 > 0
        assert ergebnis.plug_flaeche_mm2 < ergebnis.tasche_flaeche_mm2
