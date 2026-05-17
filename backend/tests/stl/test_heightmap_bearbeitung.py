"""Tests fuer Heightmap-Bearbeitungs-Tools (Master-Plan A35, Bild-zu-Relief Phase D)."""

from __future__ import annotations

import numpy as np
import pytest

from camwosa.stl.heightmap import Heightmap
from camwosa.stl.heightmap_bearbeitung import (
    detail_slider,
    edge_boost,
    gamma_korrektur,
    histogramm_stretch,
    selective_smoothing,
    zero_plane,
)


def _hm(z: np.ndarray, aufloesung: float = 1.0) -> Heightmap:
    z32 = z.astype(np.float32)
    return Heightmap(
        z_values=z32,
        aufloesung=aufloesung,
        x_min=0.0, y_min=0.0,
        z_max=float(z32.max()) if z32.size > 0 else 0.0,
    )


class TestGammaKorrektur:
    def test_gamma_eins_ist_no_op(self):
        # Heightmap-Shape ist (nx, ny). 3 X-Punkte, 1 Y-Punkt.
        z = np.array([[-1.0], [-0.5], [0.0]])
        hm = _hm(z)
        result = gamma_korrektur(hm, gamma=1.0)
        assert np.allclose(result.z_values, hm.z_values)

    def test_gamma_groesser_eins_macht_tiefer_dunkler(self):
        # Bei gamma=2: H_neu = H_alt^2, mid-tones werden kleiner
        # Pixel mit Z=-0.5 (max_t=1.0) hat H=0.5, H_neu = 0.25, Z_neu = -0.75
        z = np.array([[-1.0], [-0.5], [0.0]])
        hm = _hm(z)
        result = gamma_korrektur(hm, gamma=2.0)
        assert result.z_values[1, 0] == pytest.approx(-0.75, abs=0.01)
        # Raender bleiben bei -1 und 0
        assert result.z_values[0, 0] == pytest.approx(-1.0, abs=0.01)
        assert result.z_values[2, 0] == pytest.approx(0.0, abs=0.01)

    def test_gamma_negativ_oder_null_raises(self):
        hm = _hm(np.zeros((2, 2)))
        with pytest.raises(ValueError, match="gamma"):
            gamma_korrektur(hm, gamma=0)
        with pytest.raises(ValueError):
            gamma_korrektur(hm, gamma=-0.5)

    def test_flache_heightmap_bleibt_flach(self):
        hm = _hm(np.zeros((3, 3)))
        result = gamma_korrektur(hm, gamma=2.0)
        assert np.allclose(result.z_values, 0.0)


class TestHistogrammStretch:
    def test_stretcht_kontrast(self):
        # Werte alle zwischen Z=-0.3 und Z=-0.7 (mid-grau-bild)
        z = np.array([[-0.7], [-0.5], [-0.3]])
        hm = _hm(z)
        result = histogramm_stretch(hm, low_perzentil=0, high_perzentil=100)
        # Nach Stretching sollte der tiefste Wert <= -1.0+1e-3 (auf max_tiefe ausgestreckt)
        # und der hoechste Wert nahe 0 sein
        # max_tiefe der originalen Heightmap = 0.7 (z_min = -0.7)
        # Nach Stretch: tiefster Z = -0.7 (= max_tiefe), hoechster = 0
        assert result.z_values.min() == pytest.approx(-0.7, abs=0.01)
        assert result.z_values.max() == pytest.approx(0.0, abs=0.01)

    def test_ungueltige_perzentile_raises(self):
        hm = _hm(np.zeros((2, 2)))
        with pytest.raises(ValueError):
            histogramm_stretch(hm, low_perzentil=50, high_perzentil=30)
        with pytest.raises(ValueError):
            histogramm_stretch(hm, low_perzentil=-1, high_perzentil=50)
        with pytest.raises(ValueError):
            histogramm_stretch(hm, low_perzentil=50, high_perzentil=110)

    def test_flache_heightmap_unveraendert(self):
        hm = _hm(np.zeros((3, 3)))
        result = histogramm_stretch(hm)
        assert np.allclose(result.z_values, 0.0)


class TestZeroPlane:
    def test_hell_wird_auf_null_gesetzt(self):
        # Pixel mit Helligkeit > schwelle bekommen Z = 0
        # Bei max_tiefe=1: z=0 hat H=1, z=-0.5 hat H=0.5, z=-1 hat H=0
        z = np.array([[-1.0], [-0.6], [-0.4], [-0.1], [0.0]])
        hm = _hm(z)
        result = zero_plane(hm, schwelle=0.5)
        # z=-0.1 hat H=0.9 > 0.5 → wird 0
        # z=-0.4 hat H=0.6 > 0.5 → wird 0
        # z=-0.6 hat H=0.4 < 0.5 → bleibt
        # z=-1.0 hat H=0 → bleibt
        assert result.z_values[3, 0] == pytest.approx(0.0, abs=0.01)
        assert result.z_values[2, 0] == pytest.approx(0.0, abs=0.01)
        assert result.z_values[1, 0] == pytest.approx(-0.6, abs=0.01)
        assert result.z_values[0, 0] == pytest.approx(-1.0, abs=0.01)

    def test_ungueltige_schwelle_raises(self):
        hm = _hm(np.zeros((2, 2)))
        with pytest.raises(ValueError):
            zero_plane(hm, schwelle=1.5)
        with pytest.raises(ValueError):
            zero_plane(hm, schwelle=-0.1)


class TestEdgeBoost:
    def test_faktor_null_ist_no_op(self):
        z = np.array([[-1, -1, 0, 0], [-1, -1, 0, 0]], dtype=np.float32)
        hm = _hm(z)
        result = edge_boost(hm, faktor=0)
        assert np.allclose(result.z_values, hm.z_values)

    def test_kante_wird_tiefer(self):
        # Stufenkante: links flach (Z=0), rechts tief (Z=-1)
        z = np.array([
            [0, 0, -1, -1],
            [0, 0, -1, -1],
            [0, 0, -1, -1],
        ], dtype=np.float32)
        hm = _hm(z)
        result = edge_boost(hm, faktor=0.5)
        # An der Kante sollte das Material tiefer sein als ohne Boost
        # Die mittlere Spalte am Sprung muss <= Original sein
        assert result.z_values[1, 1] <= hm.z_values[1, 1] + 0.001

    def test_kleines_bild_kein_crash(self):
        # 2x2 ist zu klein fuer Sobel — Funktion gibt no-op zurueck
        z = np.array([[-1, 0], [0, -1]], dtype=np.float32)
        hm = _hm(z)
        result = edge_boost(hm, faktor=1.0)
        # Sollte mindestens nicht crashen und z_values gleiche Shape liefern
        assert result.z_values.shape == hm.z_values.shape


class TestSelectiveSmoothing:
    def test_radius_null_ist_no_op(self):
        z = np.array([[-1, 0], [0, -1]], dtype=np.float32)
        hm = _hm(z)
        result = selective_smoothing(hm, radius=0)
        assert np.allclose(result.z_values, hm.z_values)

    def test_alles_glaettet_komplett(self):
        # 5x5 mit einem einzigen Spike
        z = np.zeros((5, 5), dtype=np.float32)
        z[2, 2] = -1.0
        hm = _hm(z)
        result = selective_smoothing(hm, radius=1, bereich="alles")
        # Spike sollte gemildert sein
        assert result.z_values[2, 2] > -1.0
        # Nachbarn sollten leicht abgesenkt sein
        assert result.z_values[1, 2] < 0.0

    def test_hell_bereich_nur_dort(self):
        # 5x5 alles flach (Z=0, H=1) ausser eines Pixel tief
        # Da max_tiefe=1.0 (vom Spike), haben flache Pixel H=1.0 > 0.5
        # → werden geblurt
        z = np.zeros((5, 5), dtype=np.float32)
        z[2, 2] = -1.0  # Spike H=0
        hm = _hm(z)
        result = selective_smoothing(hm, radius=1, bereich="hell", schwelle=0.5)
        # Spike-Pixel (H=0) bleibt
        assert result.z_values[2, 2] == pytest.approx(-1.0, abs=0.01)

    def test_negativer_radius_raises(self):
        hm = _hm(np.zeros((3, 3)))
        with pytest.raises(ValueError):
            selective_smoothing(hm, radius=-1)

    def test_unbekannter_bereich_raises(self):
        hm = _hm(np.zeros((3, 3)))
        with pytest.raises(ValueError):
            selective_smoothing(hm, radius=1, bereich="unsinn")  # type: ignore[arg-type]


class TestDetailSlider:
    def test_detail_null_no_op(self):
        z = np.array([[-1, 0]], dtype=np.float32)
        hm = _hm(z)
        result = detail_slider(hm, detail=0)
        assert np.allclose(result.z_values, hm.z_values)

    def test_detail_negativ_glaettet(self):
        z = np.zeros((5, 5), dtype=np.float32)
        z[2, 2] = -1.0
        hm = _hm(z)
        result = detail_slider(hm, detail=-0.5)
        # Spike sollte gemildert sein
        assert result.z_values[2, 2] > -1.0

    def test_detail_positiv_schaerft_kanten(self):
        z = np.array([
            [0, 0, -1, -1],
            [0, 0, -1, -1],
            [0, 0, -1, -1],
        ], dtype=np.float32)
        hm = _hm(z)
        result = detail_slider(hm, detail=0.8)
        # Kante sollte schaerfer = mindestens an einem Punkt tiefer sein
        assert result.z_values.min() <= hm.z_values.min() + 0.001

    def test_out_of_range_raises(self):
        hm = _hm(np.zeros((2, 2)))
        with pytest.raises(ValueError):
            detail_slider(hm, detail=2.0)
        with pytest.raises(ValueError):
            detail_slider(hm, detail=-1.5)


class TestKompatibilitaetMitReliefToolpath:
    """Nach Bearbeitung muss die Heightmap noch fuer den Relief-Toolpath taugen."""

    def test_pipeline_funktioniert_nach_bearbeitung(self):
        from camwosa.cam.relief import ReliefStrategie, erzeuge_relief_toolpath
        from camwosa.cam.parameter import OperationParameter
        from camwosa.db.models import Werkzeug, WerkzeugTyp

        # Test-Heightmap
        z = np.array([
            [0, -0.2, -0.5, -1.0],
            [0, -0.2, -0.5, -1.0],
            [0, -0.2, -0.5, -1.0],
        ], dtype=np.float32)
        hm = _hm(z)
        # Gamma + Zero-Plane Pipeline
        hm2 = gamma_korrektur(hm, gamma=1.5)
        hm3 = zero_plane(hm2, schwelle=0.9)
        # Toolpath muss funktionieren
        wz = Werkzeug(
            id="t", name="Test", typ=WerkzeugTyp.KUGELFRAESER,
            durchmesser=2.0, schaft_durchmesser=3.175,
            schneidlaenge=10, gesamtlaenge=40, schneiden=2,
        )
        params = OperationParameter(
            werkzeug_id="t", spindel_rpm=18000, vorschub=600,
            eintauch_vorschub=200, max_tiefe=1.0, stepdown=0.5,
        )
        tp = erzeuge_relief_toolpath(hm3, wz, params,
                                     strategie=ReliefStrategie.RASTER_X)
        assert len(tp.bewegungen) > 0
