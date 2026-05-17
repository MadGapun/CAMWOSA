"""Tests fuer Z-Grid-Diagnose."""

from __future__ import annotations

import math

import pytest

from camwosa.diagnostics.z_grid import (
    EbenheitsBefund,
    ZGridDaten,
    ZMessPunkt,
    analyse,
)


def _grid(z_offsets: dict[tuple[float, float], float]) -> ZGridDaten:
    """Helfer: Grid aus dict {(x,y): z_offset}."""
    return ZGridDaten(
        messpunkte=[
            ZMessPunkt(x=x, y=y, z=z) for (x, y), z in z_offsets.items()
        ],
    )


class TestEbeneOberflaeche:
    def test_perfekt_eben_meldet_ok(self):
        # 3x3 Grid auf z=0
        punkte = {(x, y): 0.0 for x in (0, 50, 100) for y in (0, 50, 100)}
        ergebnis = analyse(_grid(punkte))
        assert ergebnis.befund == EbenheitsBefund.EBEN_OK
        assert ergebnis.z_spreizung == 0.0
        assert ergebnis.neigung_grad == pytest.approx(0.0, abs=1e-9)
        assert "eben" in ergebnis.klartext.lower()

    def test_minimal_rauschen_meldet_ok(self):
        # Rauschen +/-0.05 mm — sollte noch OK sein
        zs = [0.05, -0.03, 0.02, -0.04, 0.01, -0.05, 0.03, 0.04, -0.02]
        punkte = {
            (x, y): zs[i]
            for i, (x, y) in enumerate(
                (x, y) for x in (0, 50, 100) for y in (0, 50, 100)
            )
        }
        ergebnis = analyse(_grid(punkte))
        assert ergebnis.befund == EbenheitsBefund.EBEN_OK


class TestLeichteNeigung:
    def test_neigung_0_2mm_meldet_leichte_neigung(self):
        # 0.2 mm Hoehe ueber 100 mm Strecke — leichte Neigung
        punkte: dict[tuple[float, float], float] = {}
        for x in (0, 50, 100):
            for y in (0, 50, 100):
                punkte[(x, y)] = 0.002 * x  # 0 .. 0.2 mm
        ergebnis = analyse(_grid(punkte))
        assert ergebnis.befund == EbenheitsBefund.LEICHTE_NEIGUNG
        assert ergebnis.neigung_grad > 0.05
        assert "Schruppen OK" in ergebnis.empfehlung or "Schlichten" in ergebnis.empfehlung


class TestStarkeNeigung:
    def test_neigung_1mm_meldet_starke_neigung(self):
        # 1 mm Spreizung
        punkte = {(x, y): 0.01 * x for x in (0, 50, 100) for y in (0, 50, 100)}
        ergebnis = analyse(_grid(punkte))
        assert ergebnis.befund == EbenheitsBefund.STARKE_NEIGUNG
        assert "Neu aufspannen" in ergebnis.empfehlung


class TestUnebeneOberflaeche:
    def test_3mm_spreizung_meldet_unebene_flaeche(self):
        punkte = {(x, y): 0.03 * x for x in (0, 50, 100) for y in (0, 50, 100)}
        ergebnis = analyse(_grid(punkte))
        assert ergebnis.befund == EbenheitsBefund.UNEBENE_OBERFLAECHE
        assert "planen" in ergebnis.empfehlung.lower()


class TestPlaneFit:
    def test_perfekte_ebene_minimaler_residual(self):
        # Reine Neigung — Residual sollte 0 sein nach best-fit
        punkte = {(x, y): 0.005 * x + 0.003 * y + 1.0
                  for x in (0, 30, 60, 100) for y in (0, 25, 75)}
        ergebnis = analyse(_grid(punkte))
        # Wenn plane perfekt gefittet wurde: max_lokal sollte praktisch 0 sein
        assert ergebnis.max_lokale_abweichung_mm < 1e-6

    def test_neigungsrichtung_45_grad_wenn_diagonal(self):
        # Steigung nur in +X+Y-Richtung -> Azimut ~ 45 Grad
        punkte = {(x, y): 0.005 * x + 0.005 * y
                  for x in (0, 50, 100) for y in (0, 50, 100)}
        ergebnis = analyse(_grid(punkte))
        # Azimut 45° in der "Richtung in die's hoch geht"
        assert ergebnis.neigung_richtung_grad == pytest.approx(45.0, abs=1.0)


class TestWerkzeugTypAnpassung:
    def test_strengere_schwellwerte_bei_schlichtwerkzeug(self):
        # 0.12 mm Spreizung
        punkte = {(0, 0): 0.0, (50, 0): 0.06, (100, 0): 0.12, (50, 50): 0.06}
        # Bei Schaftfraeser (schruppen): sollte EBEN_OK sein
        schaft = analyse(ZGridDaten(
            messpunkte=[ZMessPunkt(x=x, y=y, z=z) for (x, y), z in punkte.items()],
            werkzeug_typ="schaftfraeser",
        ))
        # Bei Kugelfraeser (schlichten): sollte LEICHTE_NEIGUNG sein
        kugel = analyse(ZGridDaten(
            messpunkte=[ZMessPunkt(x=x, y=y, z=z) for (x, y), z in punkte.items()],
            werkzeug_typ="kugelfraeser",
        ))
        assert schaft.befund == EbenheitsBefund.EBEN_OK
        assert kugel.befund == EbenheitsBefund.LEICHTE_NEIGUNG


class TestValidierung:
    def test_min_3_punkte_pflicht(self):
        with pytest.raises(Exception):  # pydantic ValidationError
            ZGridDaten(messpunkte=[
                ZMessPunkt(x=0, y=0, z=0),
                ZMessPunkt(x=1, y=1, z=1),
            ])

    def test_abweichungen_liste_passt_zu_punkten(self):
        punkte = {(0, 0): 0.0, (50, 0): 0.1, (100, 0): 0.2, (50, 50): 0.1}
        ergebnis = analyse(_grid(punkte))
        assert len(ergebnis.abweichungen) == 4
