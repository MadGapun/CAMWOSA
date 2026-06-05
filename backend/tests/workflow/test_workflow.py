"""Tests fuer Workflow-Modul: Setups, Pausen, Arbeitsplan, Sicherheits-Checks."""

from __future__ import annotations

from pathlib import Path

import pytest

from camwosa.gcode.toolpath import (
    Bewegung,
    BewegungsTyp,
    OperationsTyp,
    Toolpath,
)
from camwosa.project import (
    OperationsKonfig,
    Setup,
    SetupPause,
    SetupPauseTyp,
    Variante,
    neues_projekt,
)
from camwosa.workflow import (
    erzeuge_arbeitsplan_markdown,
    erzeuge_arbeitsplan_pdf,
    pruefe_workflow,
    schreibe_gcode_pro_setup,
)


@pytest.fixture
def variante_zwei_setups(proverxl_maschine, rohmaterial_buche_platte) -> Variante:
    return Variante(
        id="default",
        name="Default",
        rohmaterial=rohmaterial_buche_platte,
        setups=[
            Setup(
                id="setup1",
                name="2D-Rohling",
                maschinen_modus="standard_xyz",
                spannmittel="Schraubzwingen x 4",
                werkzeug_id="t01_schaft_6mm",
                geschaetzte_zeit_minuten=25,
            ),
            Setup(
                id="setup2",
                name="Rotary-Schruppen",
                maschinen_modus="rotary_y",
                spannmittel="Backen + Reitstock",
                werkzeug_id="t01_schaft_6mm",
                pause_vor=SetupPause(
                    typ=SetupPauseTyp.UMSPANN,
                    titel="Auf Rotary umspannen",
                    anweisung="Rotary einbauen, $101 pruefen, Macro ROTARY EIN",
                ),
                geschaetzte_zeit_minuten=45,
            ),
        ],
    )


class TestSicherheitsChecks:
    def test_modus_wechsel_ohne_pause_kritisch(
        self, rohmaterial_buche_platte
    ) -> None:
        v = Variante(
            id="x", name="X", rohmaterial=rohmaterial_buche_platte,
            setups=[
                Setup(id="s1", name="A", maschinen_modus="standard_xyz",
                      werkzeug_id="t1"),
                Setup(id="s2", name="B", maschinen_modus="rotary_y",
                      werkzeug_id="t1"),
            ],
        )
        bericht = pruefe_workflow(v)
        assert bericht.hat_blocker
        assert any("Modus-Wechsel" in p.text for p in bericht.probleme)

    def test_werkzeugwechsel_ohne_pause_warnt(
        self, rohmaterial_buche_platte
    ) -> None:
        v = Variante(
            id="x", name="X", rohmaterial=rohmaterial_buche_platte,
            setups=[
                Setup(id="s1", name="A", werkzeug_id="t1"),
                Setup(id="s2", name="B", werkzeug_id="t2"),
            ],
        )
        bericht = pruefe_workflow(v)
        assert any("Werkzeugwechsel" in p.text for p in bericht.probleme)

    def test_korrekte_konfig_ohne_blocker(self, variante_zwei_setups) -> None:
        bericht = pruefe_workflow(variante_zwei_setups)
        assert not bericht.hat_blocker

    def test_pause_ohne_anweisung_warnt(
        self, rohmaterial_buche_platte
    ) -> None:
        v = Variante(
            id="x", name="X", rohmaterial=rohmaterial_buche_platte,
            setups=[
                Setup(id="s1", name="A", werkzeug_id="t1",
                      pause_vor=SetupPause(
                          typ=SetupPauseTyp.OPTIONALER_STOP,
                          titel="Inspektion", anweisung="   ",
                      )),
            ],
        )
        bericht = pruefe_workflow(v)
        assert any("keine Anweisungs-Text" in p.text for p in bericht.probleme)


class TestArbeitsplan:
    def test_markdown_enthaelt_setups_und_pausen(
        self, variante_zwei_setups, proverxl_maschine
    ) -> None:
        md = erzeuge_arbeitsplan_markdown(
            variante_zwei_setups, "Lotus-Schale", proverxl_maschine
        )
        assert "Lotus-Schale" in md
        assert "2D-Rohling" in md
        assert "Rotary-Schruppen" in md
        assert "Auf Rotary umspannen" in md
        assert "ROTARY EIN" in md

    def test_markdown_zeigt_getrennte_datei_hinweis(
        self, rohmaterial_buche_platte, proverxl_maschine
    ) -> None:
        v = Variante(
            id="x", name="X", rohmaterial=rohmaterial_buche_platte,
            setups=[
                Setup(id="s1", name="Seite A", werkzeug_id="t1"),
                Setup(
                    id="s2", name="Rotary", maschinen_modus="rotary_y",
                    werkzeug_id="t1",
                    pause_vor=SetupPause(
                        typ=SetupPauseTyp.UMSPANN,
                        titel="Umkabeln auf Rotary",
                        anweisung="Y-Motor auf A umkabeln",
                        getrennte_datei=True,
                    ),
                ),
            ],
        )
        md = erzeuge_arbeitsplan_markdown(v, "Test", proverxl_maschine)
        # Eindeutige Phrase des getrennte_datei-Hinweises (der Footer enthaelt
        # generell "Maschine ausschalten" — daher auf die spezifische Phrase pruefen)
        assert "eigene G-Code-Datei" in md
        # Ohne Flag kein Hinweis
        v.setups[1].pause_vor.getrennte_datei = False
        md2 = erzeuge_arbeitsplan_markdown(v, "Test", proverxl_maschine)
        assert "eigene G-Code-Datei" not in md2

    def test_pdf_wird_erzeugt(
        self, variante_zwei_setups, proverxl_maschine, tmp_path: Path
    ) -> None:
        pfad = tmp_path / "plan.pdf"
        bytes_data = erzeuge_arbeitsplan_pdf(
            variante_zwei_setups, "Lotus-Schale", proverxl_maschine, ziel_pfad=pfad
        )
        assert pfad.exists()
        assert pfad.stat().st_size > 1000
        # PDF beginnt mit %PDF-
        assert bytes_data.startswith(b"%PDF-")


class TestGCodePerSetup:
    def test_eine_datei_pro_setup(
        self, variante_zwei_setups, proverxl_maschine,
        schaftfraeser_6mm, tmp_path: Path
    ) -> None:
        # Dummy-Toolpaths
        tp = Toolpath(
            operation_id="o1",
            operation_typ=OperationsTyp.KONTUR,
            werkzeug_id=schaftfraeser_6mm.id,
            spindel_rpm=18000,
            sicherheitshoehe=5,
            bewegungen=[
                Bewegung(BewegungsTyp.EILGANG, 0, 0, 5),
                Bewegung(BewegungsTyp.LINEAR, 100, 0, -2, feed=2000),
            ],
        )
        ergebnis = schreibe_gcode_pro_setup(
            variante_zwei_setups,
            proverxl_maschine,
            werkzeug_index={schaftfraeser_6mm.id: schaftfraeser_6mm},
            toolpaths_pro_setup={"setup1": [tp], "setup2": [tp]},
            ziel_verzeichnis=tmp_path,
        )
        assert "setup1" in ergebnis
        assert "setup2" in ergebnis
        assert ergebnis["setup1"].exists()
        # Datei-Endung sollte .nc sein (Genmitsu-Postprozessor)
        assert ergebnis["setup1"].suffix == ".nc"
