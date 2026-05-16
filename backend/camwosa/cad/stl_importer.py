"""STL-Adapter fuer den CAD-Importer.

STL ist ein Mesh-Format, kein 2D-Geometrie-Format. Der Adapter hier liefert
keine GeometrieObjekte zurueck — stattdessen ist die Bounding-Box gefuellt und
metadaten enthalten ``stl_pfad``. Die eigentliche Verarbeitung passiert in
camwosa.stl (Heightmap-Berechnung) und der Relief-Operation.
"""

from __future__ import annotations

from pathlib import Path

from camwosa.cad.base import CADImporter, CADImportErgebnis, CADImportFehler, registry
from camwosa.dxf.parser import Punkt2D
from camwosa.stl import STLFehler, lade_stl


class STLImporter(CADImporter):
    format_id = "stl"
    name = "STL (Mesh)"
    extensions = (".stl",)
    beschreibung = "Stereolithography Mesh (ASCII + binary). Fuer Relief-Operationen."

    def kann_lesen(self, pfad: Path) -> bool:
        return pfad.suffix.lower() == ".stl"

    def lade(self, pfad: Path) -> CADImportErgebnis:
        try:
            dok = lade_stl(pfad)
        except STLFehler as e:
            raise CADImportFehler(str(e)) from e
        bbox = (
            Punkt2D(dok.bounding_box[0][0], dok.bounding_box[0][1]),
            Punkt2D(dok.bounding_box[1][0], dok.bounding_box[1][1]),
        )
        return CADImportErgebnis(
            format_id=self.format_id,
            einheit="mm",
            objekte=[],  # STL ist Mesh, kein 2D-Geometrieobjekt
            layer=[],
            bounding_box=bbox,
            metadaten={
                "stl_pfad": str(pfad),
                "z_min": dok.bounding_box[0][2],
                "z_max": dok.bounding_box[1][2],
                "anzahl_dreiecke": len(dok.mesh.faces),
            },
        )


registry().register("stl", STLImporter)
