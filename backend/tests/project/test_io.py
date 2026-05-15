"""Tests fuer .cwp-Speichern/Laden."""

from __future__ import annotations

from pathlib import Path

import pytest

from camwosa.project import (
    CWPFehler,
    CWP_SCHEMA_VERSION,
    GeometrieSnapshot,
    OperationsKonfig,
    Setup,
    SetupPause,
    SetupPauseTyp,
    extrahiere_geometrie,
    lade_cwp,
    neues_projekt,
    speichere_cwp,
)


@pytest.fixture
def projekt(proverxl_maschine, rohmaterial_buche_platte):
    return neues_projekt(
        "Lotus-Schale Variante 3",
        proverxl_maschine,
        rohmaterial_buche_platte,
        autor="Markus",
    )


class TestSpeichernLaden:
    def test_roundtrip(self, projekt, tmp_path: Path) -> None:
        pfad = tmp_path / "test.cwp"
        speichere_cwp(projekt, pfad)
        wieder = lade_cwp(pfad)
        assert wieder.metadaten.name == projekt.metadaten.name
        assert wieder.maschine.id == projekt.maschine.id
        assert len(wieder.varianten) == 1
        assert wieder.schema_version == CWP_SCHEMA_VERSION

    def test_speichern_aktualisiert_geaendert(self, projekt, tmp_path: Path) -> None:
        alt = projekt.metadaten.geaendert
        speichere_cwp(projekt, tmp_path / "x.cwp")
        # Nach dem Speichern sollte das geaendert-Feld neuer sein (oder gleich)
        assert projekt.metadaten.geaendert >= alt

    def test_eingebettete_geometrie(
        self, projekt, tmp_path: Path
    ) -> None:
        # Erzeuge eine Dummy-DXF-Datei
        dummy = tmp_path / "test.dxf"
        dummy.write_text("DUMMY DXF", encoding="utf-8")
        projekt.geometrien.append(GeometrieSnapshot(
            id="g1",
            name="Test Geometrie",
            quelle="dxf",
            eingebettete_datei=str(dummy),
        ))
        cwp_pfad = tmp_path / "x.cwp"
        speichere_cwp(projekt, cwp_pfad)

        # Extrahieren
        extrakt = extrahiere_geometrie(cwp_pfad, "g1", tmp_path / "extract")
        assert extrakt.exists()
        assert extrakt.read_text(encoding="utf-8") == "DUMMY DXF"


class TestSetupsUndPausen:
    def test_setup_mit_pause(self, projekt, tmp_path: Path) -> None:
        variante = projekt.varianten[0]
        variante.setups.append(Setup(
            id="setup1",
            name="2D-Rohling",
            werkzeug_id="schaft_6mm_2s_hm",
            operationen=[
                OperationsKonfig(
                    id="op1",
                    name="Aussenkontur",
                    typ="kontur",
                    parameter={"vorschub": 2000, "spindel_rpm": 18000},
                )
            ],
        ))
        variante.setups.append(Setup(
            id="setup2",
            name="Rotary",
            maschinen_modus="rotary_y",
            werkzeug_id="schaft_6mm_2s_hm",
            pause_vor=SetupPause(
                typ=SetupPauseTyp.UMSPANN,
                titel="Auf Rotary umspannen",
                anweisung="Backen + Reitstock einbauen.\nCNCjs 'ROTARY EIN' ausfuehren.",
            ),
        ))
        cwp = tmp_path / "x.cwp"
        speichere_cwp(projekt, cwp)
        wieder = lade_cwp(cwp)
        assert len(wieder.varianten[0].setups) == 2
        assert wieder.varianten[0].setups[1].pause_vor.typ == SetupPauseTyp.UMSPANN


class TestFehler:
    def test_nicht_existent(self, tmp_path: Path) -> None:
        with pytest.raises(CWPFehler, match="nicht gefunden"):
            lade_cwp(tmp_path / "gibts_nicht.cwp")

    def test_kein_zip(self, tmp_path: Path) -> None:
        pfad = tmp_path / "kaputt.cwp"
        pfad.write_text("kein zip")
        with pytest.raises(CWPFehler):
            lade_cwp(pfad)

    def test_neuere_schema_version_abgelehnt(self, projekt, tmp_path: Path) -> None:
        import json, zipfile
        pfad = tmp_path / "future.cwp"
        with zipfile.ZipFile(pfad, "w") as zf:
            data = projekt.model_dump()
            data["schema_version"] = 999
            zf.writestr("manifest.json", json.dumps(data, default=str))
        with pytest.raises(CWPFehler, match="neuer als unterstuetzt"):
            lade_cwp(pfad)


class TestNeuesProjekt:
    def test_default_variante(self, projekt) -> None:
        assert len(projekt.varianten) == 1
        assert projekt.varianten[0].id == "default"
        assert projekt.varianten[0].rohmaterial.material_id == "buche_massiv"
