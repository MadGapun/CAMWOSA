"""Tests fuer das CAD-Importer-Subsystem (Registry + DXF + SVG + STL)."""

from __future__ import annotations

from pathlib import Path

import ezdxf
import pytest

from camwosa.cad import CADImportFehler, lade_cad, registry


class TestRegistry:
    def test_dxf_registriert(self) -> None:
        assert "dxf" in registry().list_ids()

    def test_svg_registriert(self) -> None:
        assert "svg" in registry().list_ids()

    def test_stl_registriert(self) -> None:
        assert "stl" in registry().list_ids()

    def test_step_registriert(self) -> None:
        assert "step" in registry().list_ids()

    def test_extensions_mapping(self) -> None:
        ext = registry().list_extensions()
        assert ext.get(".dxf") == "dxf"
        assert ext.get(".svg") == "svg"
        assert ext.get(".stl") == "stl"
        assert ext.get(".step") == "step"
        assert ext.get(".stp") == "step"


class TestDXF:
    def test_dxf_durch_registry(self, tmp_path: Path) -> None:
        doc = ezdxf.new("R2010", setup=True)
        doc.units = ezdxf.units.MM
        doc.header["$INSUNITS"] = ezdxf.units.MM
        msp = doc.modelspace()
        msp.add_circle((10, 10), radius=5)
        pfad = tmp_path / "kreis.dxf"
        doc.saveas(str(pfad))

        erg = lade_cad(pfad)
        assert erg.format_id == "dxf"
        assert erg.einheit == "mm"
        assert len(erg.objekte) == 1


class TestSVG:
    def test_svg_rect_circle_line(self, tmp_path: Path) -> None:
        svg = (
            '<?xml version="1.0"?>'
            '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="60" viewBox="0 0 100 60">'
            '  <rect x="10" y="10" width="20" height="15"/>'
            '  <circle cx="50" cy="30" r="10"/>'
            '  <line x1="0" y1="0" x2="100" y2="60"/>'
            "</svg>"
        )
        pfad = tmp_path / "test.svg"
        pfad.write_text(svg, encoding="utf-8")

        erg = lade_cad(pfad)
        assert erg.format_id == "svg"
        typen = sorted(o.typ.value for o in erg.objekte)
        assert "kreis" in typen
        assert "linie" in typen
        assert "polylinie" in typen  # rect

    def test_svg_path(self, tmp_path: Path) -> None:
        svg = (
            '<?xml version="1.0"?>'
            '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">'
            '  <path d="M 10 10 L 90 10 L 90 90 L 10 90 Z"/>'
            "</svg>"
        )
        pfad = tmp_path / "p.svg"
        pfad.write_text(svg, encoding="utf-8")

        erg = lade_cad(pfad)
        assert len(erg.objekte) == 1
        # Z am Ende -> geschlossen
        assert erg.objekte[0].geschlossen is True

    def test_svg_y_spiegelung(self, tmp_path: Path) -> None:
        # Ein Kreis bei (50, 10) in SVG-Koordinaten (Y nach unten)
        # Bei Hoehe 60 sollte Y nach Spiegelung = 50 sein
        svg = (
            '<?xml version="1.0"?>'
            '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="60" viewBox="0 0 100 60">'
            '  <circle cx="50" cy="10" r="5"/>'
            "</svg>"
        )
        pfad = tmp_path / "y.svg"
        pfad.write_text(svg, encoding="utf-8")
        erg = lade_cad(pfad)
        kreis = erg.objekte[0]
        # SVG cy=10, Hoehe=60 -> CAM y = 50
        assert kreis.punkte[0].y == 50


class TestSTL:
    def test_stl_via_cad(self, tmp_path: Path) -> None:
        import trimesh
        m = trimesh.creation.box(extents=[10, 20, 30])
        pfad = tmp_path / "box.stl"
        m.export(str(pfad))

        erg = lade_cad(pfad)
        assert erg.format_id == "stl"
        assert erg.bounding_box is not None
        assert erg.metadaten["anzahl_dreiecke"] == 12  # Wuerfel = 12 Dreiecke


class TestFehler:
    def test_unbekanntes_format(self, tmp_path: Path) -> None:
        pfad = tmp_path / "x.xyz"
        pfad.write_text("foo")
        with pytest.raises(CADImportFehler, match="Kein Importer"):
            lade_cad(pfad)

    def test_nicht_existent(self, tmp_path: Path) -> None:
        with pytest.raises(CADImportFehler, match="nicht gefunden"):
            lade_cad(tmp_path / "weg.dxf")
