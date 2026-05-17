"""Tests fuer AI-Tiefenkarte (Master-Plan A36, Bild-zu-Relief Phase E).

Diese Tests verifizieren das Scaffolding — nicht die Modell-Inferenz selbst.
Wenn das ``[ai]``-Extra installiert ist, gibts einen Smoke-Test der einmal
durchlaeuft (Modell wird beim ersten Run heruntergeladen → kann lange dauern).
"""

from __future__ import annotations

from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from camwosa.stl.ai_tiefenkarte import (
    AIExtraFehlt,
    AITiefenparameter,
    DEFAULT_MODELL,
    VERFUEGBARE_MODELLE,
    heightmap_aus_bild_ai,
    ist_verfuegbar,
    modell_info,
)


def _png_bytes(w: int = 32, h: int = 32) -> bytes:
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    # Mit einem Gradient damit es ein interessantes Bild ist
    arr[:, :, 0] = np.linspace(0, 255, w)
    img = Image.fromarray(arr, mode="RGB")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


class TestModellInfo:
    def test_default_existiert(self):
        assert DEFAULT_MODELL in VERFUEGBARE_MODELLE

    def test_alle_modelle_haben_pflichtfelder(self):
        for mid, m in VERFUEGBARE_MODELLE.items():
            assert "huggingface" in m
            assert "groesse_mb" in m
            assert "qualitaet" in m

    def test_info_ohne_argument(self):
        info = modell_info()
        assert "ist_installiert" in info
        assert "default" in info
        assert "modelle" in info

    def test_info_unbekanntes_modell(self):
        info = modell_info("gibts-nicht")
        assert "fehler" in info

    def test_info_bekanntes_modell(self):
        info = modell_info(DEFAULT_MODELL)
        assert info["modell"] == DEFAULT_MODELL


class TestScaffolding:
    def test_ist_verfuegbar_gibt_bool_zurueck(self):
        assert isinstance(ist_verfuegbar(), bool)

    def test_unbekanntes_modell_raises(self):
        with pytest.raises(ValueError, match="Unbekanntes Modell"):
            heightmap_aus_bild_ai(_png_bytes(),
                                   AITiefenparameter(modell="gibts_nicht"))

    def test_ohne_extra_klare_fehlermeldung(self):
        """Wenn [ai]-Extra fehlt, muss AIExtraFehlt klare Botschaft liefern."""
        if ist_verfuegbar():
            pytest.skip("[ai]-Extra ist installiert — Negative-Test nicht moeglich")
        with pytest.raises(AIExtraFehlt) as exc_info:
            heightmap_aus_bild_ai(_png_bytes())
        msg = str(exc_info.value)
        assert "pip install" in msg
        assert "camwosa[ai]" in msg


class TestSmokeWennInstalliert:
    """Echter Inferenz-Test — nur wenn [ai] installiert ist.

    Achtung: erster Aufruf laedt 100+ MB Modell herunter.
    """

    @pytest.mark.skipif(
        not ist_verfuegbar(),
        reason="[ai]-Extra nicht installiert",
    )
    @pytest.mark.integration
    def test_inferenz_liefert_heightmap(self):
        hm = heightmap_aus_bild_ai(
            _png_bytes(w=64, h=64),
            AITiefenparameter(max_tiefe_mm=1.0, pixel_pro_mm=2.0),
        )
        assert hm.shape[0] > 0 and hm.shape[1] > 0
        assert hm.z_values.dtype == np.float32
        # Z muss <= 0 sein (in oder am Material)
        assert float(hm.z_values.max()) <= 0.01
        # Z muss >= -max_tiefe sein
        assert float(hm.z_values.min()) >= -1.01
