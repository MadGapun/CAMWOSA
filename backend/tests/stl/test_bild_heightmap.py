"""Tests fuer Bild → Heightmap-Konvertierung."""

from __future__ import annotations

from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from camwosa.stl.bild_heightmap import (
    BildHeightmapParameter,
    heightmap_aus_bild,
    heightmap_statistik,
)


def _bild_bytes(arr: np.ndarray) -> bytes:
    """Hilfsfunktion: erzeugt ein PNG-Bytes-Objekt aus einem numpy-Array.

    ``arr`` shape (hoehe, breite), Werte 0..255, dtype uint8.
    """
    img = Image.fromarray(arr.astype(np.uint8), mode="L")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


class TestBasis:
    def test_einfaches_grayscale_bild(self):
        """Einfaches 4x3-Bild mit Gradient."""
        # arr (hoehe=3, breite=4): von schwarz (links) bis weiss (rechts)
        arr = np.array([
            [0, 85, 170, 255],
            [0, 85, 170, 255],
            [0, 85, 170, 255],
        ], dtype=np.uint8)
        bild = _bild_bytes(arr)

        hm = heightmap_aus_bild(bild, BildHeightmapParameter(
            max_tiefe_mm=2.0,
            pixel_pro_mm=1.0,
        ))
        # Heightmap shape ist (x, y) = (breite, hoehe) = (4, 3)
        assert hm.shape == (4, 3)
        assert hm.aufloesung == 1.0
        # Linke Spalte (x=0) ist schwarz → tief: Z = -2.0
        assert hm.z_values[0, 0] == pytest.approx(-2.0, abs=0.01)
        # Rechte Spalte (x=3) ist weiss → hoch: Z = 0
        assert hm.z_values[3, 0] == pytest.approx(0.0, abs=0.01)
        # Mitte ist Mitte
        assert hm.z_values[1, 0] == pytest.approx(-(1 - 85/255) * 2.0, abs=0.01)

    def test_invertieren(self):
        """invertieren=True dreht hell/dunkel."""
        arr = np.array([[0, 255]], dtype=np.uint8)  # 2x1, schwarz + weiss
        bild = _bild_bytes(arr)

        hm = heightmap_aus_bild(bild, BildHeightmapParameter(
            max_tiefe_mm=1.0,
            invertieren=True,
        ))
        # Mit invertieren: schwarz wird hoch (0), weiss wird tief (-1)
        # arr (1,2) → transponiert → (2,1)
        assert hm.z_values[0, 0] == pytest.approx(0.0, abs=0.01)
        assert hm.z_values[1, 0] == pytest.approx(-1.0, abs=0.01)

    def test_pixel_pro_mm_steuert_aufloesung(self):
        arr = np.zeros((10, 10), dtype=np.uint8)
        bild = _bild_bytes(arr)
        hm = heightmap_aus_bild(bild, BildHeightmapParameter(pixel_pro_mm=10.0))
        assert hm.aufloesung == pytest.approx(0.1)

    def test_farbbild_wird_grayscale(self):
        # 3x3 RGB-Bild
        rgb = np.zeros((3, 3, 3), dtype=np.uint8)
        rgb[:, :, 0] = 128  # roter Kanal mittel
        img = Image.fromarray(rgb, mode="RGB")
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        hm = heightmap_aus_bild(buf.read())
        assert hm.shape == (3, 3)
        # Sollte ueberall etwa gleicher Z-Wert sein (uniformer Grauwert)
        assert np.all(np.abs(hm.z_values - hm.z_values[0, 0]) < 0.01)


class TestZeroPlane:
    def test_zero_plane_setzt_helle_pixel_auf_null(self):
        arr = np.array([[100, 200]], dtype=np.uint8)  # 100/255≈0.39, 200/255≈0.78
        bild = _bild_bytes(arr)
        hm = heightmap_aus_bild(bild, BildHeightmapParameter(
            max_tiefe_mm=2.0,
            zero_plane_schwelle=0.5,
        ))
        # Pixel 100 (= 0.39) liegt unter 0.5 → bleibt: Z = -(1-0.39)*2 ≈ -1.22
        # Pixel 200 (= 0.78) liegt ueber 0.5 → wird auf 1.0 gesetzt: Z = 0
        assert hm.z_values[0, 0] == pytest.approx(-1.22, abs=0.05)
        assert hm.z_values[1, 0] == pytest.approx(0.0, abs=0.01)


class TestGlaettung:
    def test_glaetten_reduziert_aufzackungen(self):
        """Ein 5x5-Bild mit einem einzelnen schwarzen Pixel inmitten weiss
        sollte nach Glaetten einen weicheren Uebergang haben."""
        arr = np.full((5, 5), 255, dtype=np.uint8)
        arr[2, 2] = 0  # schwarzer Pixel in der Mitte
        bild = _bild_bytes(arr)

        # Ohne Glaetten
        hm_roh = heightmap_aus_bild(bild, BildHeightmapParameter(
            max_tiefe_mm=1.0, glaetten_radius=0,
        ))
        # Mit Glaetten Radius 1 (= 3x3 Box-Blur)
        hm_glatt = heightmap_aus_bild(bild, BildHeightmapParameter(
            max_tiefe_mm=1.0, glaetten_radius=1,
        ))

        # Der einzelne schwarze Pixel (in Heightmap: bei (2,2))
        # Roh: Z = -1.0 (voll abgetragen)
        # Glatt: Z ist gemittelt mit Nachbarn → weniger tief
        assert hm_roh.z_values[2, 2] == pytest.approx(-1.0, abs=0.01)
        assert hm_glatt.z_values[2, 2] > -1.0  # weniger tief
        assert hm_glatt.z_values[2, 2] < 0.0   # aber immer noch was abgetragen
        # Nachbarn waren vorher 0, jetzt leicht negativ
        assert hm_glatt.z_values[1, 2] < 0.0


class TestMaxDimension:
    def test_grosses_bild_wird_skaliert(self):
        arr = np.full((1000, 800), 128, dtype=np.uint8)
        bild = _bild_bytes(arr)
        hm = heightmap_aus_bild(bild, BildHeightmapParameter(
            max_dimension_px=200,
        ))
        # Originalverhaeltnis: 1000:800 = 5:4
        # Max-Dim 200 → groesste Seite (=1000=hoehe) wird 200, andere (=800=breite) wird 160
        # In Heightmap-Konvention (x=breite, y=hoehe): shape = (160, 200)
        assert max(hm.shape) == 200
        assert min(hm.shape) == 160

    def test_kleines_bild_unveraendert(self):
        arr = np.full((50, 50), 200, dtype=np.uint8)
        bild = _bild_bytes(arr)
        hm = heightmap_aus_bild(bild, BildHeightmapParameter(max_dimension_px=500))
        assert hm.shape == (50, 50)


class TestStatistik:
    def test_statistik_korrekte_felder(self):
        arr = np.array([[0, 128, 255]], dtype=np.uint8)
        bild = _bild_bytes(arr)
        hm = heightmap_aus_bild(bild, BildHeightmapParameter(
            max_tiefe_mm=4.0, pixel_pro_mm=2.0,
        ))
        stat = heightmap_statistik(hm)
        assert stat["shape_x"] == 3
        assert stat["shape_y"] == 1
        assert stat["aufloesung_mm"] == 0.5
        assert stat["breite_mm"] == 1.5
        assert stat["max_tiefe_mm"] == pytest.approx(4.0, abs=0.01)
        assert stat["z_max"] == pytest.approx(0.0, abs=0.01)


class TestKompatibilitaetMitReliefToolpath:
    """Die erzeugte Heightmap muss vom existing Relief-Toolpath-Generator akzeptiert werden."""

    def test_heightmap_funktioniert_mit_relief_erzeuger(self):
        from camwosa.cam.relief import ReliefStrategie, erzeuge_relief_toolpath
        from camwosa.cam.parameter import OperationParameter
        from camwosa.db.models import Werkzeug, WerkzeugTyp

        arr = np.array([
            [255, 200, 100, 0],
            [200, 150, 80,  20],
            [100, 80,  40,  10],
        ], dtype=np.uint8)
        bild = _bild_bytes(arr)
        hm = heightmap_aus_bild(bild, BildHeightmapParameter(
            max_tiefe_mm=2.0, pixel_pro_mm=2.0,
        ))

        werkzeug = Werkzeug(
            id="kugel_2mm", name="Kugelfraeser 2mm",
            typ=WerkzeugTyp.KUGELFRAESER,
            durchmesser=2.0, schaft_durchmesser=3.175,
            schneidlaenge=10, gesamtlaenge=40, schneiden=2,
        )
        params = OperationParameter(
            werkzeug_id="kugel_2mm",
            spindel_rpm=18000, vorschub=600, eintauch_vorschub=200,
            max_tiefe=2.0, stepdown=0.5,
        )
        tp = erzeuge_relief_toolpath(hm, werkzeug, params, strategie=ReliefStrategie.RASTER_X)
        # Sollte einen sauberen Toolpath ergeben
        assert len(tp.bewegungen) > 0
        # Alle Z-Werte muessen <= 0 sein (= im oder am Material)
        for b in tp.bewegungen:
            if b.z < 5.0:  # ignorieren wir die Sicherheitshoehe
                assert b.z <= 0.01
