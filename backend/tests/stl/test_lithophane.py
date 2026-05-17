"""Tests fuer Lithophane (A45 / E8)."""

from __future__ import annotations

from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from camwosa.stl.lithophane import LithophaneParameter, heightmap_fuer_lithophane


def _bild(arr: np.ndarray) -> bytes:
    img = Image.fromarray(arr.astype(np.uint8), mode="L")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


class TestLithophane:
    def test_helle_pixel_min_dicke(self):
        # 1 weisses Pixel
        bild = _bild(np.array([[255]], dtype=np.uint8))
        hm = heightmap_fuer_lithophane(
            bild, LithophaneParameter(min_dicke_mm=0.8, max_dicke_mm=3.0,
                                       pixel_pro_mm=1.0))
        # Weisses Pixel -> Z = -min_dicke = -0.8
        assert hm.z_values[0, 0] == pytest.approx(-0.8, abs=0.05)

    def test_dunkle_pixel_max_dicke(self):
        bild = _bild(np.array([[0]], dtype=np.uint8))
        hm = heightmap_fuer_lithophane(
            bild, LithophaneParameter(min_dicke_mm=0.8, max_dicke_mm=3.0,
                                       pixel_pro_mm=1.0))
        # Schwarzes Pixel -> Z = -max_dicke = -3.0
        assert hm.z_values[0, 0] == pytest.approx(-3.0, abs=0.05)

    def test_mittelgrau_etwa_mitte(self):
        bild = _bild(np.array([[128]], dtype=np.uint8))
        hm = heightmap_fuer_lithophane(
            bild, LithophaneParameter(min_dicke_mm=0.8, max_dicke_mm=3.0,
                                       pixel_pro_mm=1.0))
        # 128/255 ≈ 0.502 — Material-Dicke ≈ 0.8 + 2.2 * (1-0.502) ≈ 1.9
        # Z ≈ -1.9
        z = hm.z_values[0, 0]
        assert -2.0 < z < -1.8

    def test_invalide_dicken_raises(self):
        with pytest.raises(ValueError, match="muss > min_dicke"):
            heightmap_fuer_lithophane(
                _bild(np.array([[128]], dtype=np.uint8)),
                LithophaneParameter(min_dicke_mm=3.0, max_dicke_mm=0.8),
            )

    def test_invertieren_dreht(self):
        # Bild: links weiss, rechts schwarz
        arr = np.array([[255, 0]], dtype=np.uint8)
        bild = _bild(arr)

        # Default: invertieren_quelle=False
        hm = heightmap_fuer_lithophane(
            bild, LithophaneParameter(min_dicke_mm=0.5, max_dicke_mm=2.5))
        # arr (1,2) -> shape (2, 1): index 0 = links (weiss = -0.5), 1 = rechts (-2.5)
        assert hm.z_values[0, 0] == pytest.approx(-0.5, abs=0.05)
        assert hm.z_values[1, 0] == pytest.approx(-2.5, abs=0.05)

        # invertieren_quelle=True: dreht
        hm_inv = heightmap_fuer_lithophane(
            bild, LithophaneParameter(min_dicke_mm=0.5, max_dicke_mm=2.5,
                                       invertieren_quelle=True))
        assert hm_inv.z_values[0, 0] == pytest.approx(-2.5, abs=0.05)
        assert hm_inv.z_values[1, 0] == pytest.approx(-0.5, abs=0.05)
