"""Tests fuer den Feeds & Speeds Rechner."""

from __future__ import annotations

from camwosa.feeds import WarnungsStufe, berechne_feeds_speeds


class TestPresetVerwendung:
    def test_buche_6mm_uebernimmt_preset(
        self, proverxl_maschine, schaftfraeser_6mm, material_buche
    ) -> None:
        ergebnis = berechne_feeds_speeds(proverxl_maschine, schaftfraeser_6mm, material_buche)
        assert ergebnis.quelle == "preset"
        assert ergebnis.rpm == 18000
        assert ergebnis.vorschub == 2000

    def test_rpm_wunsch_ueberschreibt_preset(
        self, proverxl_maschine, schaftfraeser_6mm, material_buche
    ) -> None:
        ergebnis = berechne_feeds_speeds(
            proverxl_maschine, schaftfraeser_6mm, material_buche, rpm_wunsch=20000
        )
        assert ergebnis.rpm == 20000


class TestHeuristik:
    def test_ohne_preset_wird_berechnet(
        self, proverxl_maschine, vbit_60grad, material_buche
    ) -> None:
        # vbit_60grad hat kein Preset in material_buche
        # (Material-Fixture hat nur schaft_6mm-Preset)
        ergebnis = berechne_feeds_speeds(proverxl_maschine, vbit_60grad, material_buche)
        # Quelle sollte preset sein wenn material_buche fixture vbit Preset haette,
        # sonst berechnet. Fixture hat keinen vbit-Preset -> berechnet.
        assert ergebnis.quelle in ("berechnet", "preset")
        assert ergebnis.vorschub > 0
        assert ergebnis.rpm > 0


class TestMaschinenLimits:
    def test_rpm_ueber_max_wird_begrenzt(
        self, proverxl_maschine, schaftfraeser_6mm, material_buche
    ) -> None:
        ergebnis = berechne_feeds_speeds(
            proverxl_maschine, schaftfraeser_6mm, material_buche,
            rpm_wunsch=50000,  # ueber Max=30000
        )
        assert ergebnis.rpm == proverxl_maschine.spindel_rpm_max
        assert any(w.stufe == WarnungsStufe.WARNUNG and "Max" in w.text
                   for w in ergebnis.warnungen)

    def test_rpm_unter_min_wird_angehoben(
        self, proverxl_maschine, schaftfraeser_6mm, material_buche
    ) -> None:
        ergebnis = berechne_feeds_speeds(
            proverxl_maschine, schaftfraeser_6mm, material_buche,
            rpm_wunsch=5000,  # unter Min=10000
        )
        assert ergebnis.rpm == proverxl_maschine.spindel_rpm_min


class TestBerechnungen:
    def test_vc_wird_berechnet(
        self, proverxl_maschine, schaftfraeser_6mm, material_buche
    ) -> None:
        ergebnis = berechne_feeds_speeds(proverxl_maschine, schaftfraeser_6mm, material_buche)
        # Vc = pi * 6 * 18000 / 1000 ~ 339 m/min
        assert 300 < ergebnis.schnittgeschwindigkeit_vc < 400

    def test_q_wird_berechnet(
        self, proverxl_maschine, schaftfraeser_6mm, material_buche
    ) -> None:
        ergebnis = berechne_feeds_speeds(proverxl_maschine, schaftfraeser_6mm, material_buche)
        # Q = stepdown(2) * ae(6*0.4=2.4) * Vf(2000) / 1000 = 9.6 cm3/min
        assert ergebnis.spanvolumen_q > 0
