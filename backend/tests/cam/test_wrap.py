"""Tests fuer Wrap-Mode (2D auf Zylinder)."""

from __future__ import annotations

import math

import pytest

from camwosa.cam.wrap import (
    GRAD_PRO_RAD,
    WrapParameter,
    erzeuge_wrap_toolpath,
    maximaler_y_wert,
    pruefe_design_fuer_radius,
    y_zu_a_grad,
)
from camwosa.db.models import Werkzeug, WerkzeugTyp
from camwosa.gcode.toolpath import BewegungsTyp


def _wz(d: float = 3.0) -> Werkzeug:
    return Werkzeug(
        id="wz_test", name="Test", typ=WerkzeugTyp.SCHAFTFRAESER,
        durchmesser=d, schaft_durchmesser=max(d, 6),
        schneidlaenge=15, gesamtlaenge=50, schneiden=2,
    )


def _p() -> WrapParameter:
    return WrapParameter(
        werkzeug_id="wz_test",
        spindel_rpm=18000, vorschub=600, eintauch_vorschub=200,
        werkstueck_radius_mm=20.0,
        max_tiefe=1.0, stepdown=0.5,
    )


class TestYZuA:
    def test_y_null_gibt_winkel_null(self):
        assert y_zu_a_grad(0.0, 20.0) == 0.0

    def test_eine_halbe_umdrehung(self):
        # Y = π × R = halber Umfang → 180°
        y = math.pi * 20.0
        assert y_zu_a_grad(y, 20.0) == pytest.approx(180.0, abs=0.001)

    def test_ganze_umdrehung(self):
        umfang = 2 * math.pi * 25.0
        assert y_zu_a_grad(umfang, 25.0) == pytest.approx(360.0, abs=0.001)

    def test_grad_pro_radiant(self):
        # Sicherstellen dass die Konstante stimmt (sonst rechnet alles falsch)
        assert GRAD_PRO_RAD == pytest.approx(57.295779, abs=0.001)

    def test_negativer_radius_raises(self):
        with pytest.raises(ValueError):
            y_zu_a_grad(10, -5)


class TestToolpathErzeugung:
    def test_einfacher_horizontaler_pfad(self):
        """Pfad in X-Richtung, Y=0 → A=0 ueberall, normaler 1-Pass-Schnitt."""
        wz = _wz()
        p = _p()
        punkte = [(0.0, 0.0), (50.0, 0.0)]
        tp = erzeuge_wrap_toolpath(punkte, wz, p)
        # Anfahrt + Plunge + Linear + Rueckzug
        assert len(tp.bewegungen) >= 4
        # Z-Werte: erst hoch, dann auf Werkstueck - tiefe, dann hoch
        plunges = [b for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE]
        assert len(plunges) == 2  # 2 Passes (stepdown 0.5, max 1.0)
        assert plunges[0].z == pytest.approx(20.0 - 0.5)
        assert plunges[1].z == pytest.approx(20.0 - 1.0)
        # Y bleibt 0 — Pfad bewegt sich nur in X
        linears = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
        assert all(b.y == 0.0 for b in linears)

    def test_y_bewegung_wird_in_winkel(self):
        """Bei Y = π×R sollte A genau 180° sein."""
        wz = _wz()
        p = _p()  # R=20
        halber_umfang = math.pi * 20.0  # ≈ 62.83
        tp = erzeuge_wrap_toolpath([(0.0, 0.0), (0.0, halber_umfang)], wz, p)
        linears = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
        # Erster Linear-Punkt bei A=0, letzter bei A=180
        assert linears[-1].y == pytest.approx(180.0, abs=0.01)

    def test_geschlossener_pfad_schliesst_zurueck(self):
        wz = _wz()
        p = _p()
        p.geschlossen = True
        punkte = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        tp = erzeuge_wrap_toolpath(punkte, wz, p)
        # Pro Pass: Plunge + 3 Linears (zu den 3 Folgepunkten) + 1 Schluss-Linear (zurueck zum Start)
        # Mit 2 Passes: 2*(1+3+1) = 10 Bewegungen + Anfahrt + Rueckzug = 12
        # Wir pruefen nur dass mehrere Linears vorhanden sind
        linears = [b for b in tp.bewegungen if b.typ == BewegungsTyp.LINEAR]
        assert len(linears) >= 6

    def test_metadaten(self):
        wz = _wz()
        p = _p()
        tp = erzeuge_wrap_toolpath([(0.0, 0.0), (10.0, 5.0)], wz, p)
        assert tp.metadaten["ist_wrap"] is True
        assert tp.metadaten["werkstueck_radius_mm"] == 20.0
        assert tp.metadaten["n_passes"] == 2
        assert tp.metadaten["umfang_mm"] == pytest.approx(2 * math.pi * 20.0)
        assert tp.metadaten["achse"] == "y_to_a"

    def test_leeres_design_raises(self):
        with pytest.raises(ValueError):
            erzeuge_wrap_toolpath([], _wz(), _p())


class TestDesignPruefung:
    def test_design_passt_auf_zylinder(self):
        """Schmales Design (Y-Spanne kleiner Umfang) → keine Warnung."""
        warnungen = pruefe_design_fuer_radius(
            [(0, 0), (10, 50)], radius_mm=20.0,
        )
        assert warnungen == []

    def test_design_groesser_als_umfang(self):
        """Y-Spanne > Umfang → Warnung."""
        # Umfang bei R=10: 62.83 mm
        warnungen = pruefe_design_fuer_radius(
            [(0, 0), (10, 100)], radius_mm=10.0,
        )
        assert any("wickelt sich mehrfach" in w for w in warnungen)

    def test_negative_y_warnung(self):
        warnungen = pruefe_design_fuer_radius(
            [(0, -10), (10, 10)], radius_mm=20.0,
        )
        assert any("negativ" in w for w in warnungen)

    def test_leeres_design(self):
        warnungen = pruefe_design_fuer_radius([], 20.0)
        assert any("leer" in w for w in warnungen)


class TestMaxY:
    def test_findet_max(self):
        assert maximaler_y_wert([(0, 1), (5, 10), (3, 7)]) == 10

    def test_leeres_design(self):
        assert maximaler_y_wert([]) == 0


# ---------------------------------------------------------------------------
# Wrap-Relief (Master-Plan A34, Bild-zu-Relief Phase C)
# ---------------------------------------------------------------------------

import numpy as np

from camwosa.cam.wrap import (
    WrapReliefParameter,
    WrapReliefStrategie,
    erzeuge_wrap_relief_toolpath,
    pruefe_heightmap_fuer_radius,
)
from camwosa.stl.heightmap import Heightmap


def _hm(z: np.ndarray, aufloesung: float = 1.0,
        x_min: float = 0.0, y_min: float = 0.0) -> Heightmap:
    z32 = z.astype(np.float32)
    return Heightmap(
        z_values=z32,
        aufloesung=aufloesung,
        x_min=x_min,
        y_min=y_min,
        z_max=float(z32.max()) if z32.size > 0 else 0.0,
    )


def _rp(R: float = 20.0, strategie: WrapReliefStrategie = WrapReliefStrategie.RASTER_X,
        serpentinen: bool = True) -> WrapReliefParameter:
    return WrapReliefParameter(
        werkzeug_id="wz_test",
        spindel_rpm=18000, vorschub=600, eintauch_vorschub=200,
        werkstueck_radius_mm=R,
        strategie=strategie,
        serpentinen=serpentinen,
    )


class TestWrapReliefPruefung:
    def test_radius_null_fehlt(self):
        hm = _hm(np.zeros((3, 3)))
        warn = pruefe_heightmap_fuer_radius(hm, 0)
        assert any("muss > 0" in w for w in warn)

    def test_leere_heightmap(self):
        hm = _hm(np.zeros((0, 0)))
        warn = pruefe_heightmap_fuer_radius(hm, 20)
        assert any("leer" in w for w in warn)

    def test_design_wickelt_mehrfach_um(self):
        # Bei R=5 (Umfang ≈ 31.4mm) und 50 Pixel á 1mm = 50mm Y-Spanne
        hm = _hm(np.zeros((10, 50)), aufloesung=1.0)
        warn = pruefe_heightmap_fuer_radius(hm, 5)
        assert any("mehrfach um" in w for w in warn)

    def test_tiefe_groesser_radius(self):
        z = np.full((3, 3), -25.0)
        hm = _hm(z)
        warn = pruefe_heightmap_fuer_radius(hm, 20)
        assert any("Drehachse" in w for w in warn)

    def test_alles_ok(self):
        # 10x10 mit aufloesung 1.0 → 10mm × 10mm, R=20 → Umfang ≈ 125mm, easy
        hm = _hm(np.zeros((10, 10)))
        warn = pruefe_heightmap_fuer_radius(hm, 20)
        assert warn == []


class TestWrapReliefToolpath:
    def test_basis_raster_x(self):
        # 3x2 Heightmap, alles flach Z=0 = Werkstueck-Oberflaeche
        hm = _hm(np.zeros((3, 2)), aufloesung=1.0)
        wz = _wz()
        tp = erzeuge_wrap_relief_toolpath(hm, wz, _rp(R=20))
        assert tp.metadaten["ist_wrap"] is True
        assert tp.metadaten["ist_relief"] is True
        assert tp.metadaten["werkstueck_radius_mm"] == 20.0
        # Sicherheitshoehe = R + sicherheit
        assert tp.bewegungen[0].z == pytest.approx(25.0)
        # Bei Z=0 in der Heightmap soll Werkzeug-Z = R sein
        plunge_zellen = [b for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE]
        assert all(b.z == pytest.approx(20.0) for b in plunge_zellen)

    def test_z_berechnung_mit_tiefen(self):
        # Pixel mit z=-1mm → Werkzeug-Z muss radius-1 = 19 sein
        z = np.array([[-1.0]], dtype=np.float32)
        hm = _hm(z)
        tp = erzeuge_wrap_relief_toolpath(hm, _wz(), _rp(R=20))
        plunge = next(b for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE)
        assert plunge.z == pytest.approx(19.0)

    def test_a_berechnung_y_zu_winkel(self):
        # Heightmap (1, 2): an y=0 → A=0, an y=1 → A= 1·57.2958/20 ≈ 2.865°
        hm = _hm(np.zeros((1, 2)), aufloesung=1.0)
        tp = erzeuge_wrap_relief_toolpath(hm, _wz(), _rp(R=20))
        plunge = [b for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE]
        assert plunge[0].y == pytest.approx(0.0)
        assert plunge[1].y == pytest.approx(GRAD_PRO_RAD / 20, abs=0.01)

    def test_blockiert_bei_radius_null(self):
        hm = _hm(np.zeros((2, 2)))
        with pytest.raises(ValueError, match="muss > 0"):
            erzeuge_wrap_relief_toolpath(hm, _wz(), _rp(R=0))

    def test_blockiert_bei_zu_tief(self):
        z = np.full((2, 2), -30.0)
        hm = _hm(z)
        with pytest.raises(ValueError, match="Drehachse"):
            erzeuge_wrap_relief_toolpath(hm, _wz(), _rp(R=20))

    def test_serpentinen_vs_kein_serpentinen(self):
        hm = _hm(np.zeros((4, 3)), aufloesung=1.0)
        tp_serp = erzeuge_wrap_relief_toolpath(
            hm, _wz(), _rp(R=20, serpentinen=True))
        tp_ohne = erzeuge_wrap_relief_toolpath(
            hm, _wz(), _rp(R=20, serpentinen=False))
        # Beide sollten gueltige Bewegungs-Listen liefern
        assert len(tp_serp.bewegungen) > 0
        assert len(tp_ohne.bewegungen) > 0
        # Serpentinen drehen die zweite Zeile rueckwaerts:
        # Erste Plunge in Zeile 0 = X=0, in Zeile 1 (serpentinen) = X=3
        plunges = [b for b in tp_serp.bewegungen if b.typ == BewegungsTyp.PLUNGE]
        # Zeile j=0: i=0 vorwaerts, Plunge bei X=0
        assert plunges[0].x == 0
        # Zeile j=1: i=3 rueckwaerts, Plunge bei X=3
        assert plunges[1].x == 3
        # Zeile j=2: i=0 wieder vorwaerts
        assert plunges[2].x == 0
        # Ohne Serpentinen: jede Zeile beginnt bei X=0
        plunges_ohne = [b for b in tp_ohne.bewegungen if b.typ == BewegungsTyp.PLUNGE]
        assert all(p.x == 0 for p in plunges_ohne)

    def test_raster_a_strategie(self):
        hm = _hm(np.zeros((2, 3)), aufloesung=1.0)
        tp = erzeuge_wrap_relief_toolpath(
            hm, _wz(), _rp(R=20, strategie=WrapReliefStrategie.RASTER_A))
        assert tp.metadaten["strategie"] == "raster_a"
        # Mit RASTER_A: pro X eine Sequenz durch alle Y
        plunges = [b for b in tp.bewegungen if b.typ == BewegungsTyp.PLUNGE]
        # 2 X-Werte = 2 Plunges
        assert len(plunges) == 2

    def test_warnungen_in_metadaten(self):
        # 5x80 mit aufloesung 1.0 → Y-Spanne 80mm, R=5 → Umfang 31.4mm → Warnung
        z = np.zeros((5, 80), dtype=np.float32)
        hm = _hm(z, aufloesung=1.0)
        # tiefe ok, also kein Block — Warnung in metadaten
        tp = erzeuge_wrap_relief_toolpath(hm, _wz(), _rp(R=5))
        assert any("mehrfach um" in w for w in tp.metadaten["warnungen"])


# ---------------------------------------------------------------------------
# Pattern-Skalierung (Master-Plan A38)
# ---------------------------------------------------------------------------

from camwosa.cam.wrap import (
    PatternSkalierungsModus,
    skaliere_pattern_fuer_werkstueck,
)


def _quadrat(seite: float = 10.0) -> list[tuple[float, float]]:
    return [(0, 0), (seite, 0), (seite, seite), (0, seite), (0, 0)]


class TestPatternSkalierung:
    def test_radius_null_raises(self):
        with pytest.raises(ValueError):
            skaliere_pattern_fuer_werkstueck(
                [_quadrat()],
                PatternSkalierungsModus.FESTE_SKALIERUNG,
                werkstueck_radius_mm=0,
            )

    def test_leere_eingabe_gibt_leeres_ergebnis(self):
        ergebnis, meta = skaliere_pattern_fuer_werkstueck(
            [], PatternSkalierungsModus.FESTE_SKALIERUNG,
            werkstueck_radius_mm=10,
        )
        assert ergebnis == []
        assert "werkstueck_umfang_mm" in meta

    def test_feste_skalierung_default_unveraendert(self):
        ergebnis, meta = skaliere_pattern_fuer_werkstueck(
            [_quadrat(10)],
            PatternSkalierungsModus.FESTE_SKALIERUNG,
            werkstueck_radius_mm=20,
        )
        # Ohne soll_breite/hoehe: Skalierung = 1
        assert meta["skalierung_x"] == 1.0
        assert meta["skalierung_y"] == 1.0
        # Origin auf (0, 0)
        assert ergebnis[0][0] == (0, 0)
        assert ergebnis[0][1] == (10, 0)

    def test_feste_skalierung_mit_soll_breite(self):
        ergebnis, meta = skaliere_pattern_fuer_werkstueck(
            [_quadrat(10)],
            PatternSkalierungsModus.FESTE_SKALIERUNG,
            werkstueck_radius_mm=20,
            soll_breite_mm=50,
            aspekt_erhalten=True,
        )
        # 10mm → 50mm = Skalierung x5 in beiden Richtungen
        assert meta["skalierung_x"] == 5.0
        assert meta["skalierung_y"] == 5.0
        assert ergebnis[0][1] == (50, 0)

    def test_auf_werkstueck_anpassen_y_wird_umfang(self):
        ergebnis, meta = skaliere_pattern_fuer_werkstueck(
            [_quadrat(10)],
            PatternSkalierungsModus.AUF_WERKSTUECK_ANPASSEN,
            werkstueck_radius_mm=10,
        )
        umfang = 2 * math.pi * 10  # ≈ 62.83
        # Y-Spanne muss = Umfang
        assert meta["y_spanne_endgueltig_mm"] == pytest.approx(umfang, rel=0.001)
        # Aspekt erhalten: X auch x6.28
        assert meta["skalierung_x"] == pytest.approx(umfang / 10, rel=0.001)

    def test_auf_werkstueck_anpassen_ohne_aspekt(self):
        ergebnis, meta = skaliere_pattern_fuer_werkstueck(
            [_quadrat(10)],
            PatternSkalierungsModus.AUF_WERKSTUECK_ANPASSEN,
            werkstueck_radius_mm=10,
            soll_breite_mm=20,
            aspekt_erhalten=False,
        )
        # X-Skalierung kommt aus soll_breite: 10mm → 20mm = x2
        assert meta["skalierung_x"] == 2.0
        # Y bleibt am Umfang
        umfang = 2 * math.pi * 10
        assert meta["skalierung_y"] == pytest.approx(umfang / 10, rel=0.001)

    def test_wiederholen_dupliziert(self):
        # Pattern 10mm hoch auf R=10 (Umfang 62.83mm) → 6 Wiederholungen
        ergebnis, meta = skaliere_pattern_fuer_werkstueck(
            [_quadrat(10)],
            PatternSkalierungsModus.WIEDERHOLEN,
            werkstueck_radius_mm=10,
        )
        assert meta["anzahl_wiederholungen"] == 6
        # 6x das urspruengliche Polygon
        assert len(ergebnis) == 6
        # Y-Spanne genau Umfang
        umfang = 2 * math.pi * 10
        assert meta["y_spanne_endgueltig_mm"] == pytest.approx(umfang)
        # Letzte Wiederholung soll ein y_min haben das nahe umfang/6 * 5 ist
        y_letzte_min = min(p[1] for p in ergebnis[-1])
        assert y_letzte_min == pytest.approx(umfang / 6 * 5, rel=0.01)

    def test_wiederholen_mit_x_skalierung(self):
        ergebnis, meta = skaliere_pattern_fuer_werkstueck(
            [_quadrat(10)],
            PatternSkalierungsModus.WIEDERHOLEN,
            werkstueck_radius_mm=10,
            soll_breite_mm=30,
        )
        # X-Skalierung x3
        assert meta["skalierung_x"] == 3.0
        # Letztes Wiederhol-Polygon hat x_max = 30
        x_maxs = [max(p[0] for p in poly) for poly in ergebnis]
        assert max(x_maxs) == pytest.approx(30.0)

    def test_metadaten_haben_pflichtfelder(self):
        _, meta = skaliere_pattern_fuer_werkstueck(
            [_quadrat()],
            PatternSkalierungsModus.AUF_WERKSTUECK_ANPASSEN,
            werkstueck_radius_mm=10,
        )
        for feld in (
            "modus", "original_breite_mm", "original_hoehe_mm",
            "werkstueck_umfang_mm", "skalierung_x", "skalierung_y",
            "y_spanne_endgueltig_mm",
        ):
            assert feld in meta
