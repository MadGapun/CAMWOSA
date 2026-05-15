"""Tests fuer Nesting (Verschnittoptimierung)."""

from __future__ import annotations

import pytest

from camwosa.nesting import (
    NestingStrategie,
    PlattenDefinition,
    TeilDefinition,
    neste,
)


class TestBinPacking:
    def test_lotus_schalen_passen_auf_eine_platte(self) -> None:
        """4 Rundscheiben Ø130 auf 600x400 Buche-Platte."""
        teile = [TeilDefinition(id="rohling", breite=130, hoehe=130, anzahl=4)]
        platten = [PlattenDefinition(id="buche_600x400", breite=600, hoehe=400)]
        ergebnis = neste(teile, platten, abstand_zwischen_teilen=5)

        assert len(ergebnis.platzierungen) == 4
        assert len(ergebnis.nicht_platziert) == 0
        assert "buche_600x400" in ergebnis.platten_genutzt

    def test_zu_viele_teile_ueberschuss(self) -> None:
        teile = [TeilDefinition(id="x", breite=100, hoehe=100, anzahl=10)]
        platten = [PlattenDefinition(id="klein", breite=200, hoehe=200)]  # max 4 passen
        ergebnis = neste(teile, platten, abstand_zwischen_teilen=5)
        assert len(ergebnis.nicht_platziert) >= 6

    def test_verschnitt_statistik(self) -> None:
        teile = [TeilDefinition(id="x", breite=100, hoehe=100, anzahl=2)]
        platten = [PlattenDefinition(id="y", breite=300, hoehe=200)]
        ergebnis = neste(teile, platten, abstand_zwischen_teilen=0)
        # 2x 100x100 = 20000 mm2. Platte = 60000. Verschnitt = 66.7%
        assert ergebnis.genutzte_flaeche == 20000
        assert ergebnis.gesamt_flaeche == 60000
        assert 60 < ergebnis.verschnitt_prozent < 70

    def test_leere_eingabe(self) -> None:
        ergebnis = neste([], [PlattenDefinition(id="x", breite=100, hoehe=100)])
        assert ergebnis.platzierungen == []
        ergebnis = neste([TeilDefinition(id="x", breite=10, hoehe=10)], [])
        assert ergebnis.platzierungen == []


class TestRotation:
    def test_teile_werden_rotiert_um_zu_passen(self) -> None:
        # Teil 80x40, Platte 50x100 - nur rotiert geht's
        teile = [TeilDefinition(id="x", breite=80, hoehe=40)]
        platten = [PlattenDefinition(id="y", breite=50, hoehe=100)]
        ergebnis = neste(teile, platten, abstand_zwischen_teilen=0)
        assert len(ergebnis.platzierungen) == 1
        # Teil muesste rotiert sein
        assert ergebnis.platzierungen[0].rotation_grad == 90.0

    def test_faserrichtung_verhindert_rotation(self) -> None:
        # Faser parallel Y -> darf nicht rotiert werden
        teile = [TeilDefinition(id="x", breite=80, hoehe=40, faser_parallel_y=True)]
        platten = [PlattenDefinition(id="y", breite=50, hoehe=100)]
        ergebnis = neste(teile, platten, abstand_zwischen_teilen=0)
        # Wuerde nur durch Rotation passen -> Verworfen
        assert len(ergebnis.nicht_platziert) == 1


class TestStrategie:
    def test_no_fit_polygon_nicht_implementiert(self) -> None:
        with pytest.raises(NotImplementedError, match="nest2D"):
            neste(
                [TeilDefinition(id="x", breite=10, hoehe=10)],
                [PlattenDefinition(id="y", breite=100, hoehe=100)],
                strategie=NestingStrategie.NO_FIT_POLYGON,
            )
