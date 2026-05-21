"""Tests fuer Spanausduennung / Chip Thinning (Cluster J3)."""

from __future__ import annotations

import math

import pytest

from camwosa.feeds.rechner import (
    chip_thinning_faktor,
    korrigiere_vorschub_spanausduennung,
)


class TestChipThinningFaktor:
    def test_voll_eingriff_faktor_eins(self):
        # ae >= d/2 → kein Thinning
        assert chip_thinning_faktor(stepover_mm=3.0, werkzeug_durchmesser_mm=6.0) == 1.0
        assert chip_thinning_faktor(stepover_mm=6.0, werkzeug_durchmesser_mm=6.0) == 1.0

    def test_halber_durchmesser_grenzfall(self):
        # genau d/2 → Faktor 1
        assert chip_thinning_faktor(3.0, 6.0) == 1.0

    def test_kleiner_eingriff_faktor_groesser_eins(self):
        # ae = 0.6mm bei d=6mm (10% Stepover) → deutlicher Faktor
        f = chip_thinning_faktor(0.6, 6.0)
        assert f > 1.0
        # Referenz: ae/d=0.1 → 1/sqrt(1-(1-0.2)²) = 1/sqrt(1-0.64) = 1/sqrt(0.36) = 1.667
        assert f == pytest.approx(1.0 / math.sqrt(1 - 0.8**2), abs=1e-6)

    def test_kleinerer_eingriff_groesserer_faktor(self):
        f10 = chip_thinning_faktor(0.6, 6.0)   # 10%
        f5 = chip_thinning_faktor(0.3, 6.0)    # 5%
        assert f5 > f10

    def test_faktor_geklemmt_bei_4(self):
        # ae→0 → theoretisch unendlich, praktisch auf 4 geklemmt
        f = chip_thinning_faktor(0.001, 6.0)
        assert f == 4.0

    def test_ungueltiger_durchmesser(self):
        assert chip_thinning_faktor(1.0, 0.0) == 1.0


class TestVorschubKorrektur:
    def test_korrektur_erhoeht_vorschub(self):
        basis = 1000.0
        korr = korrigiere_vorschub_spanausduennung(basis, stepover_mm=0.6, werkzeug_durchmesser_mm=6.0)
        assert korr > basis
        assert korr == pytest.approx(basis * chip_thinning_faktor(0.6, 6.0))

    def test_voll_eingriff_unveraendert(self):
        basis = 1000.0
        korr = korrigiere_vorschub_spanausduennung(basis, stepover_mm=4.0, werkzeug_durchmesser_mm=6.0)
        assert korr == pytest.approx(basis)
