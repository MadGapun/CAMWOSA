"""Tests fuer Bitmap-Trace (Cluster L1)."""

from __future__ import annotations

from io import BytesIO

import numpy as np
import pytest
from PIL import Image, ImageDraw

from camwosa.cad.bitmap_trace import (
    BitmapTraceFehler,
    BitmapTraceParameter,
    trace_bitmap,
)
from camwosa.dxf.parser import GeometrieTyp


def _png_bytes(img: Image.Image) -> bytes:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _schwarzes_quadrat(groesse=100, rand=20) -> bytes:
    """Weisses Bild mit schwarzem Quadrat in der Mitte."""
    img = Image.new("L", (groesse, groesse), color=255)
    d = ImageDraw.Draw(img)
    d.rectangle([rand, rand, groesse - rand, groesse - rand], fill=0)
    return _png_bytes(img)


def _schwarzer_kreis(groesse=100, radius=35) -> bytes:
    img = Image.new("L", (groesse, groesse), color=255)
    d = ImageDraw.Draw(img)
    c = groesse // 2
    d.ellipse([c - radius, c - radius, c + radius, c + radius], fill=0)
    return _png_bytes(img)


def _zwei_quadrate() -> bytes:
    img = Image.new("L", (200, 100), color=255)
    d = ImageDraw.Draw(img)
    d.rectangle([10, 30, 50, 70], fill=0)
    d.rectangle([150, 30, 190, 70], fill=0)
    return _png_bytes(img)


class TestGrundfunktion:
    def test_quadrat_liefert_eine_kontur(self):
        geos = trace_bitmap(_schwarzes_quadrat(), BitmapTraceParameter(pixel_pro_mm=2))
        assert len(geos) == 1
        assert geos[0].typ == GeometrieTyp.POLYLINIE
        assert geos[0].geschlossen
        assert geos[0].layer == "bitmap_trace"

    def test_quadrat_ist_rechteckig(self):
        geos = trace_bitmap(_schwarzes_quadrat(groesse=100, rand=20),
                            BitmapTraceParameter(pixel_pro_mm=4, glaettung_toleranz_mm=0.5))
        pts = [(p.x, p.y) for p in geos[0].punkte]
        # nach Douglas-Peucker sollte ein Quadrat ~4-8 Ecken haben (nicht 100)
        assert 4 <= len(pts) <= 12

    def test_kreis_hat_viele_punkte(self):
        geos = trace_bitmap(_schwarzer_kreis(),
                            BitmapTraceParameter(pixel_pro_mm=4, glaettung_toleranz_mm=0.1))
        # ein Kreis braucht mehr Stuetzpunkte als ein Quadrat
        assert len(geos[0].punkte) > 12

    def test_zwei_formen_zwei_konturen(self):
        geos = trace_bitmap(_zwei_quadrate(), BitmapTraceParameter(pixel_pro_mm=2))
        assert len(geos) == 2


class TestSkalierung:
    def test_ziel_breite(self):
        geos = trace_bitmap(_schwarzes_quadrat(groesse=100, rand=20),
                            BitmapTraceParameter(pixel_pro_mm=4, ziel_breite_mm=50.0))
        xs = [p.x for g in geos for p in g.punkte]
        breite = max(xs) - min(xs)
        assert breite == pytest.approx(50.0, abs=1.0)

    def test_ohne_ziel_breite_aus_aufloesung(self):
        # 100px bei 4 px/mm, Quadrat von px 20..80 = 60px = 15mm breit
        geos = trace_bitmap(_schwarzes_quadrat(groesse=100, rand=20),
                            BitmapTraceParameter(pixel_pro_mm=4))
        xs = [p.x for g in geos for p in g.punkte]
        breite = max(xs) - min(xs)
        assert breite == pytest.approx(15.0, abs=1.5)


class TestInvertieren:
    def test_invertieren_traced_helle_bereiche(self):
        # Schwarzes Bild mit weissem Quadrat → invertieren=True traced das Quadrat
        img = Image.new("L", (100, 100), color=0)
        d = ImageDraw.Draw(img)
        d.rectangle([20, 20, 80, 80], fill=255)
        geos = trace_bitmap(_png_bytes(img),
                            BitmapTraceParameter(pixel_pro_mm=2, invertieren=True))
        assert len(geos) == 1


class TestFilter:
    def test_min_flaeche_verwirft_fleck(self):
        # Grosses Quadrat + winziger Fleck → Fleck wird verworfen
        img = Image.new("L", (200, 200), color=255)
        d = ImageDraw.Draw(img)
        d.rectangle([50, 50, 150, 150], fill=0)  # gross
        d.rectangle([10, 10, 13, 13], fill=0)    # winzig
        geos = trace_bitmap(_png_bytes(img),
                            BitmapTraceParameter(pixel_pro_mm=4, min_flaeche_mm2=5.0))
        # nur das grosse Quadrat
        assert len(geos) == 1


class TestFehler:
    def test_leere_form_wirft(self):
        # rein weisses Bild → keine dunkle Form
        img = Image.new("L", (50, 50), color=255)
        with pytest.raises(BitmapTraceFehler):
            trace_bitmap(_png_bytes(img))

    def test_ungueltige_schwelle(self):
        with pytest.raises(BitmapTraceFehler):
            trace_bitmap(_schwarzes_quadrat(), BitmapTraceParameter(schwelle=1.5))

    def test_kaputte_bilddaten(self):
        with pytest.raises(BitmapTraceFehler):
            trace_bitmap(b"das ist kein bild")
