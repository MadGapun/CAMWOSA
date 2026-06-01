"""Tests fuer die CAM-Operations Kontur, Tasche, Bohren, Gravur."""

from __future__ import annotations

import math

import pytest
from shapely.geometry import LineString, Polygon

from camwosa.cam import (
    erzeuge_bohren_toolpath,
    erzeuge_gravur_toolpath,
    erzeuge_kontur_toolpath,
    erzeuge_tasche_toolpath,
)
from camwosa.cam.parameter import (
    BohrParameter,
    BohrStrategie,
    GravurParameter,
    KonturParameter,
    KonturSeite,
    TaschenParameter,
    TaschenStrategie,
)
from camwosa.dxf.parser import GeometrieObjekt, GeometrieTyp, Punkt2D
from camwosa.gcode.toolpath import BewegungsTyp, OperationsTyp


@pytest.fixture
def quadrat_50x50_dxf() -> GeometrieObjekt:
    return GeometrieObjekt(
        typ=GeometrieTyp.POLYLINIE,
        layer="KONTUR",
        punkte=[Punkt2D(0, 0), Punkt2D(50, 0), Punkt2D(50, 50), Punkt2D(0, 50)],
        geschlossen=True,
    )


@pytest.fixture
def quadrat_50x50_polygon() -> Polygon:
    return Polygon([(0, 0), (50, 0), (50, 50), (0, 50)])


@pytest.fixture
def kontur_param(schaftfraeser_6mm) -> KonturParameter:
    return KonturParameter(
        werkzeug_id=schaftfraeser_6mm.id,
        spindel_rpm=18000,
        vorschub=2000,
        eintauch_vorschub=400,
        sicherheitshoehe=5.0,
        max_tiefe=6.0,
        stepdown=2.0,
        seite=KonturSeite.AUSSEN,
    )


@pytest.fixture
def tasche_param(schaftfraeser_6mm) -> TaschenParameter:
    return TaschenParameter(
        werkzeug_id=schaftfraeser_6mm.id,
        spindel_rpm=18000,
        vorschub=2000,
        eintauch_vorschub=400,
        sicherheitshoehe=5.0,
        max_tiefe=4.0,
        stepdown=2.0,
        strategie=TaschenStrategie.PARALLEL,
        stepover_prozent=40,
    )


@pytest.fixture
def bohr_param(schaftfraeser_6mm) -> BohrParameter:
    return BohrParameter(
        werkzeug_id=schaftfraeser_6mm.id,
        spindel_rpm=15000,
        vorschub=500,
        eintauch_vorschub=300,
        sicherheitshoehe=5.0,
        max_tiefe=10.0,
        stepdown=10.0,
        strategie=BohrStrategie.PECK,
        peck_tiefe=2.0,
    )


@pytest.fixture
def gravur_param(vbit_60grad) -> GravurParameter:
    return GravurParameter(
        werkzeug_id=vbit_60grad.id,
        spindel_rpm=18000,
        vorschub=1500,
        eintauch_vorschub=300,
        sicherheitshoehe=5.0,
        max_tiefe=1.0,
        stepdown=0.5,
        max_zustellung=0.5,
    )


# ---------------------------------------------------------------------------
# Kontur
# ---------------------------------------------------------------------------


class TestKontur:
    def test_aussen_kontur_erzeugt_toolpath(
        self, quadrat_50x50_dxf, schaftfraeser_6mm, kontur_param
    ) -> None:
        tp = erzeuge_kontur_toolpath(quadrat_50x50_dxf, schaftfraeser_6mm, kontur_param)
        assert tp.operation_typ == OperationsTyp.KONTUR
        assert tp.werkzeug_id == schaftfraeser_6mm.id
        assert len(tp.bewegungen) > 0
        assert any(b.typ == BewegungsTyp.PLUNGE for b in tp.bewegungen)
        assert any(b.typ == BewegungsTyp.EILGANG for b in tp.bewegungen)

    def test_innen_kontur_kleiner_als_aussen(
        self, quadrat_50x50_polygon, schaftfraeser_6mm, kontur_param
    ) -> None:
        kontur_param.seite = KonturSeite.AUSSEN
        tp_aussen = erzeuge_kontur_toolpath(quadrat_50x50_polygon, schaftfraeser_6mm, kontur_param)

        kontur_param.seite = KonturSeite.INNEN
        tp_innen = erzeuge_kontur_toolpath(quadrat_50x50_polygon, schaftfraeser_6mm, kontur_param)

        # Innen-Kontur sollte naeher am Mittelpunkt liegen
        max_x_aussen = max(b.x for b in tp_aussen.bewegungen)
        max_x_innen = max(b.x for b in tp_innen.bewegungen)
        assert max_x_innen < max_x_aussen

    def test_max_tiefe_wird_erreicht(
        self, quadrat_50x50_polygon, schaftfraeser_6mm, kontur_param
    ) -> None:
        tp = erzeuge_kontur_toolpath(quadrat_50x50_polygon, schaftfraeser_6mm, kontur_param)
        min_z = min(b.z for b in tp.bewegungen)
        assert math.isclose(min_z, -kontur_param.max_tiefe, abs_tol=0.01)

    def test_anzahl_z_passes(
        self, quadrat_50x50_polygon, schaftfraeser_6mm, kontur_param
    ) -> None:
        # max_tiefe=6, stepdown=2 -> 3 Passes
        tp = erzeuge_kontur_toolpath(quadrat_50x50_polygon, schaftfraeser_6mm, kontur_param)
        plunge_count = sum(1 for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE)
        assert plunge_count == 3

    def test_werkzeug_zu_gross_innen_fehler(self, schaftfraeser_6mm, kontur_param) -> None:
        """Kleines Quadrat + grosser Fraeser + INNEN -> kein Toolpath moeglich."""
        klein = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])
        kontur_param.seite = KonturSeite.INNEN
        with pytest.raises(ValueError, match="zu gross"):
            erzeuge_kontur_toolpath(klein, schaftfraeser_6mm, kontur_param)

    def test_backplot_annotation_in_bewegungen(
        self, quadrat_50x50_polygon, schaftfraeser_6mm, kontur_param
    ) -> None:
        tp = erzeuge_kontur_toolpath(quadrat_50x50_polygon, schaftfraeser_6mm, kontur_param)
        # Erste Bewegung sollte einen Backplot-Kommentar haben
        assert "---" in tp.bewegungen[0].kommentar
        assert "Kontur" in tp.bewegungen[0].kommentar

    def test_tabs_setzen_z_in_letztem_pass_hoch(
        self, quadrat_50x50_polygon, schaftfraeser_6mm, kontur_param
    ) -> None:
        kontur_param.tabs_anzahl = 4
        kontur_param.tabs_hoehe = 1.5
        kontur_param.tabs_breite = 4
        tp = erzeuge_kontur_toolpath(quadrat_50x50_polygon, schaftfraeser_6mm, kontur_param)
        # Es muessen Bewegungen mit Kommentar "Tab" da sein
        tab_bewegungen = [b for b in tp.bewegungen if b.kommentar == "Tab"]
        assert len(tab_bewegungen) > 0
        # Tab-Bewegungen sollten Z auf z_unten + tabs_hoehe = -6 + 1.5 = -4.5 setzen
        for b in tab_bewegungen:
            assert b.z == pytest.approx(-4.5, abs=0.01)


# ---------------------------------------------------------------------------
# Tasche
# ---------------------------------------------------------------------------


class TestTasche:
    def test_parallel_strategie(
        self, quadrat_50x50_polygon, schaftfraeser_6mm, tasche_param
    ) -> None:
        tp = erzeuge_tasche_toolpath(quadrat_50x50_polygon, schaftfraeser_6mm, tasche_param)
        assert tp.operation_typ == OperationsTyp.TASCHE
        assert len(tp.bewegungen) > 0
        # Soll mehrere parallele Linien erzeugen
        eilgaenge = sum(1 for b in tp.bewegungen if b.typ == BewegungsTyp.EILGANG)
        assert eilgaenge >= 2

    def test_offset_kontur_strategie(
        self, quadrat_50x50_polygon, schaftfraeser_6mm, tasche_param
    ) -> None:
        tasche_param.strategie = TaschenStrategie.OFFSET_KONTUR
        tp = erzeuge_tasche_toolpath(quadrat_50x50_polygon, schaftfraeser_6mm, tasche_param)
        assert len(tp.bewegungen) > 0

    def test_spiral_aussen_strategie(
        self, quadrat_50x50_polygon, schaftfraeser_6mm, tasche_param
    ) -> None:
        tasche_param.strategie = TaschenStrategie.SPIRAL_AUSSEN
        tp = erzeuge_tasche_toolpath(quadrat_50x50_polygon, schaftfraeser_6mm, tasche_param)
        assert len(tp.bewegungen) > 0
        assert tp.metadaten["strategie"] == "spiral_aussen"

    def test_spiral_innen_strategie(
        self, quadrat_50x50_polygon, schaftfraeser_6mm, tasche_param
    ) -> None:
        tasche_param.strategie = TaschenStrategie.SPIRAL_INNEN
        tp = erzeuge_tasche_toolpath(quadrat_50x50_polygon, schaftfraeser_6mm, tasche_param)
        assert len(tp.bewegungen) > 0

    def test_max_tiefe_erreicht(
        self, quadrat_50x50_polygon, schaftfraeser_6mm, tasche_param
    ) -> None:
        tp = erzeuge_tasche_toolpath(quadrat_50x50_polygon, schaftfraeser_6mm, tasche_param)
        min_z = min(b.z for b in tp.bewegungen)
        assert min_z <= -tasche_param.max_tiefe + 0.01

    def test_offene_geometrie_ist_fehler(self, schaftfraeser_6mm, tasche_param) -> None:
        offene = LineString([(0, 0), (10, 0)])
        with pytest.raises(ValueError, match="nicht unterstuetzt"):
            erzeuge_tasche_toolpath(offene, schaftfraeser_6mm, tasche_param)


# ---------------------------------------------------------------------------
# Adaptive Clearing (Master-Plan E4)
# ---------------------------------------------------------------------------


class TestAdaptiveClearing:
    def test_adaptive_strategie_erzeugt_toolpath(
        self, quadrat_50x50_polygon, schaftfraeser_6mm, tasche_param
    ) -> None:
        tasche_param.strategie = TaschenStrategie.ADAPTIVE
        tp = erzeuge_tasche_toolpath(quadrat_50x50_polygon, schaftfraeser_6mm, tasche_param)
        assert len(tp.bewegungen) > 0
        assert tp.metadaten["strategie"] == "adaptive"

    def test_adaptive_hat_mehr_bewegungen_als_offset_kontur(
        self, quadrat_50x50_polygon, schaftfraeser_6mm, tasche_param
    ) -> None:
        """Kleinerer Stepover → mehr Bahnen → mehr Punkte."""
        tasche_param.strategie = TaschenStrategie.OFFSET_KONTUR
        tp_offset = erzeuge_tasche_toolpath(
            quadrat_50x50_polygon, schaftfraeser_6mm, tasche_param)
        tasche_param.strategie = TaschenStrategie.ADAPTIVE
        tp_adapt = erzeuge_tasche_toolpath(
            quadrat_50x50_polygon, schaftfraeser_6mm, tasche_param)
        assert len(tp_adapt.bewegungen) > len(tp_offset.bewegungen)

    def test_adaptive_amplitude_default_null_macht_kein_modulieren(
        self, quadrat_50x50_polygon, schaftfraeser_6mm, tasche_param
    ) -> None:
        """Mit amplitude=0 bleibt die Bahn auf der Offset-Kontur."""
        tasche_param.strategie = TaschenStrategie.ADAPTIVE
        tasche_param.adaptive_amplitude_faktor = 0.0
        tp = erzeuge_tasche_toolpath(quadrat_50x50_polygon, schaftfraeser_6mm, tasche_param)
        # Bei amplitude=0 soll Modulation no-op sein → Bahn bleibt achs-aligned
        # X-Werte sollten alle in {0..50}-Bereich liegen (Quadrat 50x50)
        xs = [b.x for b in tp.bewegungen]
        assert max(xs) - min(xs) <= 50.0 + 0.5

    def test_adaptive_amplitude_verschiebt_bahn(
        self, quadrat_50x50_polygon, schaftfraeser_6mm, tasche_param
    ) -> None:
        """Mit grosserer Amplitude wandern Punkte messbar von der reinen Offset-Bahn weg."""
        tasche_param.strategie = TaschenStrategie.ADAPTIVE
        tasche_param.adaptive_amplitude_faktor = 0.0
        tp_keine_amp = erzeuge_tasche_toolpath(
            quadrat_50x50_polygon, schaftfraeser_6mm, tasche_param)
        tasche_param.adaptive_amplitude_faktor = 0.15
        tp_mit_amp = erzeuge_tasche_toolpath(
            quadrat_50x50_polygon, schaftfraeser_6mm, tasche_param)
        # Mindestens ein Punkt sollte sich messbar unterscheiden
        # (gleiche Anzahl Bewegungen, weil gleiche Schritte)
        xs_a = [b.x for b in tp_keine_amp.bewegungen]
        xs_b = [b.x for b in tp_mit_amp.bewegungen]
        n = min(len(xs_a), len(xs_b))
        max_diff = max(abs(xs_a[i] - xs_b[i]) for i in range(n))
        assert max_diff > 0.1, f"Amplitude 0.15 sollte Punkte um >0.1mm verschieben (war {max_diff})"

    def test_adaptive_wellen_pro_mm_validation(self) -> None:
        """Negative Welligkeit muss Pydantic bei Construction ablehnen."""
        with pytest.raises(Exception):
            TaschenParameter(
                werkzeug_id="x",
                spindel_rpm=18000, vorschub=600, eintauch_vorschub=200,
                max_tiefe=5, stepdown=2,
                adaptive_wellen_pro_mm=-1.0,
            )


# ---------------------------------------------------------------------------
# Bohren
# ---------------------------------------------------------------------------


class TestBohren:
    def test_einzelne_bohrung_standard(self, schaftfraeser_6mm, bohr_param) -> None:
        bohr_param.strategie = BohrStrategie.STANDARD
        tp = erzeuge_bohren_toolpath([Punkt2D(50, 50)], schaftfraeser_6mm, bohr_param)
        assert tp.operation_typ == OperationsTyp.BOHREN
        # 1 Eilgang hin, 1 Plunge, 1 Eilgang rueckzug
        assert len(tp.bewegungen) >= 3
        assert tp.metadaten["anzahl"] == 1

    def test_peck_macht_zwischen_rueckzuege(self, schaftfraeser_6mm, bohr_param) -> None:
        # max_tiefe=10, peck_tiefe=2 -> mehrere Zyklen
        tp = erzeuge_bohren_toolpath([Punkt2D(0, 0)], schaftfraeser_6mm, bohr_param)
        plunges = sum(1 for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE)
        assert plunges == 5  # 2,4,6,8,10

    def test_mehrere_bohrungen(self, schaftfraeser_6mm, bohr_param) -> None:
        punkte = [Punkt2D(0, 0), Punkt2D(50, 0), Punkt2D(50, 50)]
        tp = erzeuge_bohren_toolpath(punkte, schaftfraeser_6mm, bohr_param)
        assert tp.metadaten["anzahl"] == 3

    def test_kreis_geometrie_zu_bohrung(self, schaftfraeser_6mm, bohr_param) -> None:
        kreis = GeometrieObjekt(
            typ=GeometrieTyp.KREIS,
            layer="0",
            punkte=[Punkt2D(25, 25)],
            geschlossen=True,
            attribute={"radius": 3},
        )
        tp = erzeuge_bohren_toolpath([kreis], schaftfraeser_6mm, bohr_param)
        assert tp.bewegungen[0].x == 25
        assert tp.bewegungen[0].y == 25

    def test_helix_loch_groesser_werkzeug(self, schaftfraeser_6mm, bohr_param) -> None:
        bohr_param.strategie = BohrStrategie.HELIX
        bohr_param.loch_durchmesser = 12.0  # 6mm Werkzeug, 12mm Loch
        bohr_param.helix_steigung = 1.0
        tp = erzeuge_bohren_toolpath([Punkt2D(0, 0)], schaftfraeser_6mm, bohr_param)
        # Sollte viele Bewegungen erzeugen (Helix-Spirale)
        assert len(tp.bewegungen) > 50

    def test_helix_loch_zu_klein_fehler(self, schaftfraeser_6mm, bohr_param) -> None:
        bohr_param.strategie = BohrStrategie.HELIX
        bohr_param.loch_durchmesser = 3.0  # kleiner als Werkzeug (6mm)
        with pytest.raises(ValueError, match="Loch-Durchmesser"):
            erzeuge_bohren_toolpath([Punkt2D(0, 0)], schaftfraeser_6mm, bohr_param)

    def test_reib_erzeugt_kreisbahn(self, schaftfraeser_6mm, bohr_param) -> None:
        bohr_param.strategie = BohrStrategie.REIB
        bohr_param.loch_durchmesser = 10.0
        tp = erzeuge_bohren_toolpath([Punkt2D(0, 0)], schaftfraeser_6mm, bohr_param)
        # Pruefe dass Bewegungen auf Bahnradius liegen (2mm vom Mittelpunkt)
        bahn_r = (10 - 6) / 2  # = 2 mm
        am_radius = [
            b for b in tp.bewegungen
            if abs(((b.x ** 2 + b.y ** 2) ** 0.5) - bahn_r) < 0.1
        ]
        assert len(am_radius) > 10


# ---------------------------------------------------------------------------
# Gravur
# ---------------------------------------------------------------------------


class TestGravur:
    def test_gravur_auf_linie(self, vbit_60grad, gravur_param) -> None:
        linie = LineString([(0, 0), (50, 0), (50, 50)])
        tp = erzeuge_gravur_toolpath(linie, vbit_60grad, gravur_param)
        assert tp.operation_typ == OperationsTyp.GRAVUR
        assert len(tp.bewegungen) > 0

    def test_gravur_auf_polygon_macht_aussen_und_innen(self, vbit_60grad, gravur_param) -> None:
        # Polygon mit Loch
        aussen = [(0, 0), (50, 0), (50, 50), (0, 50)]
        innen = [(20, 20), (30, 20), (30, 30), (20, 30)]
        polygon = Polygon(aussen, [innen])
        tp = erzeuge_gravur_toolpath(polygon, vbit_60grad, gravur_param)
        assert len(tp.bewegungen) > 0

    def test_v_carving_auf_polygon(self, vbit_60grad, gravur_param) -> None:
        from camwosa.cam.parameter import GravurStrategie
        gravur_param.strategie = GravurStrategie.V_CARVING
        gravur_param.max_tiefe = 3.0
        polygon = Polygon([(0, 0), (20, 0), (20, 20), (0, 20)])
        tp = erzeuge_gravur_toolpath(polygon, vbit_60grad, gravur_param)
        assert tp.metadaten["strategie"] == "v_carving"
        # Sollte mehrere Tiefen-Ebenen haben
        z_werte = {round(b.z, 1) for b in tp.bewegungen if b.typ.value == "linear"}
        assert len(z_werte) > 2  # mehrere Tiefen

    def test_v_carving_auf_linestring_fehler(self, vbit_60grad, gravur_param) -> None:
        from camwosa.cam.parameter import GravurStrategie
        gravur_param.strategie = GravurStrategie.V_CARVING
        with pytest.raises(ValueError, match="geschlossene Polygon"):
            erzeuge_gravur_toolpath(LineString([(0, 0), (10, 0)]), vbit_60grad, gravur_param)
