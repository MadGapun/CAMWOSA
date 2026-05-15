"""Tests fuer den DXF-Parser.

Wir generieren die Test-DXFs zur Laufzeit mit ezdxf um keine Binary-Fixtures im
Repo zu haben und unabhaengig von externen Programmen wie Solid Edge zu sein.
"""

from __future__ import annotations

from pathlib import Path

import ezdxf
import pytest

from camwosa.dxf import (
    DXFFehler,
    GeometrieTyp,
    lade_dxf,
)


@pytest.fixture
def dxf_einfach(tmp_path: Path) -> Path:
    """Erzeugt ein DXF mit Linie, Kreis, Bogen, geschlossenem Polygon."""
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    doc.header["$INSUNITS"] = ezdxf.units.MM
    msp = doc.modelspace()
    doc.layers.add("KONTUR")
    doc.layers.add("BOHRUNGEN")

    msp.add_line((0, 0), (100, 0), dxfattribs={"layer": "KONTUR"})
    msp.add_circle((50, 50), radius=10, dxfattribs={"layer": "BOHRUNGEN"})
    msp.add_arc(
        center=(0, 0), radius=20, start_angle=0, end_angle=90,
        dxfattribs={"layer": "KONTUR"},
    )
    pl = msp.add_lwpolyline(
        [(0, 0), (50, 0), (50, 50), (0, 50)],
        close=True,
        dxfattribs={"layer": "KONTUR"},
    )
    pl.closed = True

    pfad = tmp_path / "einfach.dxf"
    doc.saveas(str(pfad))
    return pfad


@pytest.fixture
def dxf_mit_spline(tmp_path: Path) -> Path:
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = ezdxf.units.MM
    msp = doc.modelspace()
    msp.add_spline([(0, 0), (10, 20), (30, 0), (40, 20), (50, 0)])
    pfad = tmp_path / "spline.dxf"
    doc.saveas(str(pfad))
    return pfad


@pytest.fixture
def dxf_inch(tmp_path: Path) -> Path:
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = ezdxf.units.IN
    msp = doc.modelspace()
    msp.add_line((0, 0), (1, 0))
    pfad = tmp_path / "inch.dxf"
    doc.saveas(str(pfad))
    return pfad


@pytest.fixture
def dxf_leer(tmp_path: Path) -> Path:
    doc = ezdxf.new("R2010", setup=True)
    pfad = tmp_path / "leer.dxf"
    doc.saveas(str(pfad))
    return pfad


class TestEinfacheDXF:
    def test_alle_entities_geparst(self, dxf_einfach: Path) -> None:
        dok = lade_dxf(dxf_einfach)
        typen = [o.typ for o in dok.objekte]
        assert GeometrieTyp.LINIE in typen
        assert GeometrieTyp.KREIS in typen
        assert GeometrieTyp.BOGEN in typen
        assert GeometrieTyp.POLYLINIE in typen

    def test_layer_werden_erkannt(self, dxf_einfach: Path) -> None:
        dok = lade_dxf(dxf_einfach)
        assert "KONTUR" in dok.layer
        assert "BOHRUNGEN" in dok.layer

    def test_objekte_im_layer(self, dxf_einfach: Path) -> None:
        dok = lade_dxf(dxf_einfach)
        bohrungen = dok.objekte_im_layer("BOHRUNGEN")
        assert len(bohrungen) == 1
        assert bohrungen[0].typ == GeometrieTyp.KREIS

    def test_geschlossene_polylinie_wird_erkannt(self, dxf_einfach: Path) -> None:
        dok = lade_dxf(dxf_einfach)
        polygone = [o for o in dok.objekte if o.typ == GeometrieTyp.POLYLINIE]
        assert len(polygone) == 1
        assert polygone[0].geschlossen is True

    def test_geschlossene_konturen_enthaelt_kreis_und_polygon(self, dxf_einfach: Path) -> None:
        dok = lade_dxf(dxf_einfach)
        gk = dok.geschlossene_konturen()
        typen = {o.typ for o in gk}
        assert GeometrieTyp.KREIS in typen
        assert GeometrieTyp.POLYLINIE in typen

    def test_kreis_attribute(self, dxf_einfach: Path) -> None:
        dok = lade_dxf(dxf_einfach)
        kreis = next(o for o in dok.objekte if o.typ == GeometrieTyp.KREIS)
        assert kreis.attribute["radius"] == 10
        assert kreis.punkte[0].x == 50
        assert kreis.punkte[0].y == 50

    def test_bogen_attribute(self, dxf_einfach: Path) -> None:
        dok = lade_dxf(dxf_einfach)
        bogen = next(o for o in dok.objekte if o.typ == GeometrieTyp.BOGEN)
        assert bogen.attribute["radius"] == 20
        assert bogen.attribute["start_winkel"] == 0
        assert bogen.attribute["end_winkel"] == 90

    def test_einheit_mm(self, dxf_einfach: Path) -> None:
        dok = lade_dxf(dxf_einfach)
        assert dok.einheit == "mm"

    def test_bounding_box(self, dxf_einfach: Path) -> None:
        dok = lade_dxf(dxf_einfach)
        assert dok.bounding_box is not None
        min_p, max_p = dok.bounding_box
        # Linie 0..100 X, Kreis r=10 um (50,50) -> y=60. Bogen r=20 um (0,0).
        assert min_p.x <= -20  # Bogen Mittelpunkt 0,0 mit Radius 20
        assert max_p.x >= 100
        assert max_p.y >= 60


class TestSpline:
    def test_spline_wird_diskretisiert(self, dxf_mit_spline: Path) -> None:
        dok = lade_dxf(dxf_mit_spline)
        splines = [o for o in dok.objekte if o.typ == GeometrieTyp.SPLINE]
        assert len(splines) == 1
        assert len(splines[0].punkte) >= 5  # mindestens die Kontrollpunkte


class TestEinheiten:
    def test_inch_einheit_erkannt(self, dxf_inch: Path) -> None:
        dok = lade_dxf(dxf_inch)
        assert dok.einheit == "inch"


class TestLeer:
    def test_leeres_dxf(self, dxf_leer: Path) -> None:
        dok = lade_dxf(dxf_leer)
        assert dok.objekte == []
        assert dok.bounding_box is None


class TestFehler:
    def test_nicht_existierende_datei(self, tmp_path: Path) -> None:
        with pytest.raises(DXFFehler, match="nicht gefunden"):
            lade_dxf(tmp_path / "gibts_nicht.dxf")

    def test_kein_gueltiges_dxf(self, tmp_path: Path) -> None:
        pfad = tmp_path / "kaputt.dxf"
        pfad.write_text("DAS IST KEIN DXF", encoding="utf-8")
        with pytest.raises(DXFFehler):
            lade_dxf(pfad)
